import asyncio
import json
from logging import Logger
import logging

import aiohttp

from akdof_shared.gis.arcgis_api_validation import validate_arcgis_json
from akdof_shared.gis.arcgis_helpers import get_feature_count_and_extent, get_object_ids
from akdof_shared.io.async_requester import AsyncRequester, StatusCodePlanner

class EditFailureResponse(Exception): pass
class BatchEditException(Exception): pass
class ResultingFeatureCountInvalid(Exception): pass

class FeatureLayerEditor:

    status_code_planner: StatusCodePlanner = {
        408: {"sleep_seconds": 2, "attempt_increment": 1},
        429: {"sleep_seconds": 10, "attempt_increment": 0.5},
        502: {"sleep_seconds": 5, "attempt_increment": 0.8},
        503: {"sleep_seconds": 8, "attempt_increment": 0.8},
        504: {"sleep_seconds": 10, "attempt_increment": 0.5},
    }
    """
    - 408 Request Timeout: Server didn't receive complete request in time
    - 429 Too Many Requests: Rate limiting - client sending requests too quickly  
    - 502 Bad Gateway: Upstream server returned invalid response
    - 503 Service Unavailable: Server temporarily overloaded or down for maintenance
    - 504 Gateway Timeout: Upstream server didn't respond in time
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        feature_deletion_query: str | None = None,
        features_to_add: list[dict] | None = None,
        logger: Logger | None = None,
        requester: AsyncRequester | None = None,
        deletes_batch_size: int = 5_000,
        adds_batch_size: int = 2_500,
    ):
        self.base_url = base_url
        self.token = token
        self.feature_deletion_query = feature_deletion_query
        self.features_to_add = features_to_add
        self.logger = logger
        self.requester = requester
        self.deletes_batch_size = deletes_batch_size
        self.adds_batch_size = adds_batch_size

        if self.feature_deletion_query is None and self.features_to_add is None:
            raise ValueError(f"`feature_deletion_query` and / or `features_to_add` must be provided for FeatureLayerEditor to do any work.")
        self.feature_deletion_query = self.feature_deletion_query or "1<>1"
        self.features_to_add = self.features_to_add or list()

        if self.logger is None:
            self.logger = logging.getLogger("null")
        if not self.logger.handlers:
            self.logger.addHandler(logging.NullHandler())

        if self.requester is None:
            self.requester = AsyncRequester(logger=self.logger)
            self.logger.info(f"Created default instance-specific requester for {self.base_url}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.requester.close()

    async def apply_edits_with_validation(self) -> dict[str, str | int]:

        initial_feature_count, _ = get_feature_count_and_extent(base_url=self.base_url, token=self.token)
        object_ids_to_delete = get_object_ids(base_url=self.base_url, where=self.feature_deletion_query, token=self.token)
        target_feature_count = initial_feature_count - len(object_ids_to_delete) + len(self.features_to_add)

        try:
            await self._edit_request(features_to_add=self.features_to_add, object_ids_to_delete=object_ids_to_delete)
        except (aiohttp.ClientResponseError, aiohttp.ContentTypeError) as e:
            if e.status in (413, 504):
                self.logger.debug(f"{self.base_url} edit attempt failed with an HTTP {e.status} response: {e.message}")
                self.logger.debug(f"{self.base_url} beginning batched edit operations...")
                updated_object_ids_to_delete = get_object_ids(base_url=self.base_url, where=self.feature_deletion_query, token=self.token)
                await self._batched_edits(features_to_add=self.features_to_add, object_ids_to_delete=updated_object_ids_to_delete)
            else:
                raise

        await asyncio.sleep(2)
        resulting_feature_count, _ = get_feature_count_and_extent(base_url=self.base_url, token=self.token)
        if resulting_feature_count != target_feature_count:
            raise ResultingFeatureCountInvalid(f"{self.base_url} now has {resulting_feature_count} features. The edit operation should have resulted in {target_feature_count} features.")

        return {
            "url": self.base_url,
            "features_to_add": len(self.features_to_add),
            "features_to_delete": len(object_ids_to_delete),
            "initial_feature_count": initial_feature_count,
            "resulting_feature_count": resulting_feature_count,
            "feature_count_change": resulting_feature_count - initial_feature_count,
            "target_feature_count_discrepancy": resulting_feature_count - target_feature_count
        }
    
    async def _batched_edits(self, features_to_add: list[dict] | None = None, object_ids_to_delete: list[int] | None = None):

        batches = [list(object_ids_to_delete[i: i + self.deletes_batch_size]) for i in range(0, len(object_ids_to_delete), self.deletes_batch_size)]
        self.logger.debug(f"{self.base_url} sending {len(batches)} requests, using batch sizes of {self.deletes_batch_size} to delete a total of {len(object_ids_to_delete)} features...")
        for batch_count, oid_batch in enumerate(batches, start=1):
            await self._edit_request(object_ids_to_delete=oid_batch)
            self.logger.debug(f"{self.base_url} DELETES: batch {batch_count} of {len(batches)} complete")
        
        batches = [list(features_to_add[i: i + self.adds_batch_size]) for i in range(0, len(features_to_add), self.adds_batch_size)]
        self.logger.debug(f"{self.base_url} sending {len(batches)} requests, using batch sizes of {self.adds_batch_size} to add a total of {len(features_to_add)} features...")
        for batch_count, feat_batch in enumerate(batches, start=1):
            await self._edit_request(features_to_add=feat_batch)
            self.logger.debug(f"{self.base_url} ADDS: batch {batch_count} of {len(batches)} complete")

    async def _edit_request(self, features_to_add: list[dict] | None = None, object_ids_to_delete: list[int] | None = None):

        features_to_add = features_to_add or list()
        object_ids_to_delete = object_ids_to_delete or list()
        apply_edits_data = {
            "adds": json.dumps(features_to_add),
            "deletes": json.dumps(object_ids_to_delete),
            "rollbackOnFailure": "true",
            "f": "json",
            "token": self.token
        }
        apply_edits_response_json = await self.requester.send_request(
            url=f"{self.base_url}/applyEdits",
            request_method="post",
            read_method="json",
            status_code_plan=self.status_code_planner,
            data=apply_edits_data,
            timeout=aiohttp.ClientTimeout(total=120)
        )
        validate_arcgis_json(json_response=apply_edits_response_json, expected_keys=("addResults", "deleteResults"))
        self._validate_apply_edits_response(apply_edits_response_json)
        
    def _validate_apply_edits_response(self, apply_edits_response: dict):
        """
        Searches response from an applyEdits POST request for messages indicating a failure of any kind.
        """
        failure = False
        for result_type in ("addResults", "deleteResults"):
            for result in apply_edits_response.get(result_type, []):
                if result.get("success", False) is False:
                    failure = True
                    self.logger.debug(f"{self.base_url}: {(result_type, result)}")
        if failure:
            raise EditFailureResponse(f"Failures were detected in an applyEdits response for {self.base_url}.")