import asyncio
from datetime import datetime as dt
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import ssl

import json
from typing import Literal, Iterable, Any
import logging

from pydantic import BaseModel, ConfigDict, Field, HttpUrl
import geopandas as gpd

from akdof_shared.gis.arcgis_helpers import (
    get_feature_layer_resource_info,
    get_feature_count_and_extent
)
from akdof_shared.utils.drop_none_vals import drop_none_vals
from akdof_shared.io.async_requester import AsyncArcGisRequester
from akdof_shared.gis.spatial_json_conversion import arcgis_json_to_gdf
from akdof_shared.gis.arcgis_api_validation import validate_arcgis_json, ArcGisApiErrorResponse, ArcGisApiKeyError
from akdof_shared.io.file_cache_manager import FileCacheManager, CacheCompareError
from akdof_shared.protocol.datetime_info import now_utc_iso, iso_file_naming
from akdof_shared.protocol.file_logging_manager import FileLoggingManager

class InputFeatureLayerError(Exception): pass
class InvalidFeaturesResponse(InputFeatureLayerError): pass
class UnclearSpatialReference(InputFeatureLayerError): pass
class InvalidIndex(InputFeatureLayerError): pass
class PaginationNotSupported(InputFeatureLayerError): pass
class ResourceNotInitialized(InputFeatureLayerError): pass
class MetadataConflict(InputFeatureLayerError): pass
class DuplicateAlias(InputFeatureLayerError): pass

class FeaturesGdf:
    def __init__(self, gdf: gpd.GeoDataFrame, query_parameters: dict[str, Any], spatial_query_parameters: dict[str, Any], features_cached_dt: dt):
        self.gdf = gdf
        self.query_parameters = query_parameters
        self.spatial_query_parameters = spatial_query_parameters
        self.features_cached_dt = features_cached_dt
    
class InputFeatureLayerCache(BaseModel):
    """Configuration for an `InputFeatureLayer` cache"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    resource_info: FileCacheManager = Field(
        description="Configuration for caching feature layer resource info"
    )
    features: FileCacheManager = Field(
        description="Configuration for caching features"
    )

class InputFeatureLayer(BaseModel):
    """
    Configuration and data access for ArcGIS Online feature layers.

    See [request parameters](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/#request-parameters)
    for additional information about class attributes that influence behavior of GET requests to the `url`/query? endpoint:
    `token`, `output_epsg`, `sql_where_clause`, `spatial_query_parameters`, `outfields`.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: HttpUrl = Field(
        description="ArcGIS Online REST API Feature Layer endpoint"
    )
    alias: str = Field(
        description="Unique readable identifier to associate with this feature layer"
    )
    cache: InputFeatureLayerCache = Field(
        description="Configuration for cache locations and caching behavior"
    )
    certificate_chain: Path | None = Field(
        default=None,
        description="File path to custom certificate chain to use for SSL verification when making requests to feature layer url endpoint"
    )
    token: str | None = Field(
        default=None,
        description="Token required for accessing the ArcGIS Online REST API Feature Layer endpoint"
    )
    sql_where_clause: str | None = Field(
        default=None,
        description="SQL WHERE clause used to filter features by their attributes when querying the ArcGIS Online REST API Feature Layer endpoint"
    )
    spatial_query_parameters: dict | Iterable[dict] | None = Field(
        default=None,
        description="""
            Any parameters that will apply spatial filtering when querying the ArcGIS Online REST API Feature Layer endpoint.
            Expected dictionary keys are 'inSR', 'geometry', 'geometryType', and 'spatialRel'.
            An iterable of spatial query parameters can be passed to generate multiple requests using different spatial filters.
        """
    )
    output_epsg: int | None = Field(
        default=None,
        description="EPSG code of desired spatial reference for any geometry recieved from the ArcGIS Online REST API Feature Layer endpoint"
    )
    outfields: list[str] = Field(
        default=["*"],
        description="List of fields to return when querying the ArcGIS Online REST API Feature Layer endpoint"
    )
    field_map: dict[str, str] | None = Field(
        default=None,
        description="Mapping of source field names to target field names for renaming"
    )
    processing_frequency: Literal["always", "annual"] = Field(
        default="always",
        description="How often an input feature layer will expose relevant data to the main process"
    )
    logger: logging.Logger | None = Field(
        default=None,
        description="Logger that class methods will use for observing events related to a class instance"
    )
    semaphore: asyncio.Semaphore | None = Field(
        default=None,
        description="Defines an upper limit for the number concurrent asynchronous operations"
    )
    requester: AsyncArcGisRequester | None = Field(
        default=None,
        description="Coordinates async requests to ArcGIS REST APIs"
    )
    thread_executor: ThreadPoolExecutor | None = Field(
        default=None,
        description="Thread pool executor for concurrent file reads and writes"
    )

    def model_post_init(self, __context):

        if self.logger is None:
            self.logger = logging.getLogger("null")
        if not self.logger.handlers:
            self.logger.addHandler(logging.NullHandler())

        self.logger.debug(f"Post-init complete for {self.alias}")

    async def refresh_features(self) -> Literal[True]:

        self._validate_required_resources("semaphore", "requester", "thread_executor")

        if not self._supports_pagination():
            raise PaginationNotSupported(f"{self.alias} does not support pagination! Consider implementing an alternate code path using objectId based queries.")
        
        target_feature_count, target_extent = self._get_feature_count_and_extent()

        complete_parameters, query_parameters, spatial_query_parameters = self._collect_params_with_metadata()
        json_responses = await self._get_features_by_pagination(params=complete_parameters)
        self._validate_feature_json_responses(json_responses)

        if len({json.dumps(resp["spatialReference"], sort_keys=True) for resp in json_responses}) != 1:
            raise UnclearSpatialReference(f"{self.alias}: Multiple spatial references found in feature layer query responses.")
        spatial_reference = json_responses[0]["spatialReference"]

        arcgis_json = drop_none_vals({
            "features": [feat for resp in json_responses for feat in resp["features"]],
            "spatialReference": spatial_reference,
            "uniqueIdField": self._unique_id_field()
        })
        if len(arcgis_json["features"]) < target_feature_count:
            raise InvalidFeaturesResponse(f"{self.alias}: Returned {len(arcgis_json['features'])} features, when the target feature count was {target_feature_count}.")
        
        cache = {
            "target_feature_count": target_feature_count,
            "target_extent": target_extent,
            "query_parameters": query_parameters,
            "spatial_query_parameters": spatial_query_parameters,
            "arcgis_json": arcgis_json
        }

        file_path = self.cache.features.path / f"{iso_file_naming(now_utc_iso())}.json"
        def _write_feature_cache(file_path: Path, content: dict):
            with open(file_path, "w") as file:
                json.dump(content, file, indent=4)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.thread_executor, _write_feature_cache, file_path, cache)

        return True

    async def load_feature_history(self, cache_count: int | Literal["all"] = "all", apply_field_map: bool = False, validate_index: bool = False) -> list[FeaturesGdf]:

        self._validate_required_resources("thread_executor")

        cache_manifest = self.cache.features.load_manifest() if cache_count == "all" else self.cache.features.parse_manifest(target_length=cache_count)

        def _read_feature_cache(file_path: Path, features_cached_dt: dt) -> dict[dt, dict]:
            with open(file_path, "r") as file:
                cache = json.load(file)
            return {features_cached_dt: cache}
        
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.thread_executor, _read_feature_cache, file_path, features_cached_dt)
            for file_path, features_cached_dt in cache_manifest.items()
        ]

        feature_cache = await asyncio.gather(*tasks)
        feature_cache = {features_cached_dt: cache for d in feature_cache for features_cached_dt, cache in d.items()}

        feature_history = list()
        for features_cached_dt, cache in feature_cache.items():
            gdf = arcgis_json_to_gdf(arcgis_json=cache["arcgis_json"])
            if apply_field_map and self.field_map:
                gdf = gdf.rename(columns=self.field_map, errors="raise")
            if validate_index:
                self._validate_gdf_index(gdf=gdf)
            feature_history.append(
                FeaturesGdf(
                    gdf=gdf,
                    query_parameters=cache["query_parameters"],
                    spatial_query_parameters=cache["spatial_query_parameters"],
                    features_cached_dt=features_cached_dt
                )
            )

        feature_history.sort(key=lambda x: x.features_cached_dt, reverse=True)
        
        return feature_history
    
    async def load_latest_features(self, apply_field_map: bool = False, validate_index: bool = False) -> FeaturesGdf | None:
        feature_history = await self.load_feature_history(cache_count=1, apply_field_map=apply_field_map, validate_index=validate_index)
        return next(iter(feature_history, None))
        
    async def track_method_call(self, method_name: str, *args, **kwargs) -> dict[str, Any]:

        if not hasattr(self, method_name):
            raise AttributeError(f"'{type(self).__name__}' has no method '{method_name}'")
        
        method = getattr(self, method_name)
        
        if not callable(method):
            raise TypeError(f"'{method_name}' is not callable")
        if not asyncio.iscoroutinefunction(method):
            raise TypeError(f"Method '{method_name}' is not an async method")
        
        try:
            result = await method(*args, **kwargs)
            return {self.alias: result}
        except Exception as e:
            raise type(e)(f"{self.alias}: {str(e)}") from e
    
    def rollback_features_cache(self, cache_count: int | Literal["all"] = 1):
        cache_manifest = self.cache.features.load_manifest() if cache_count == "all" else self.cache.features.parse_manifest(target_length=cache_count)
        for path in cache_manifest.keys():
            path.unlink()

    def _get_feature_layer_resource_info(self) -> dict:

        file_path = self.cache.resource_info.latest_entry()
        if file_path:
            with open(file_path, "r") as file:
                resource_info = json.load(file)
        else:
            resource_info = get_feature_layer_resource_info(base_url=str(self.url), token=self.token, verify=self.certificate_chain or True)
            with open(self.cache.resource_info.path / f"{iso_file_naming(now_utc_iso())}.json", "w") as file:
                json.dump(resource_info, file, indent=4)

            try:
                output_path = self.cache.resource_info.compare_latest_entries()
                if output_path:
                    self.logger.warning(f"{self.alias} resource info cache generated a new diff! {output_path}")
            except (NotImplementedError, CacheCompareError) as e:
                self.logger.warning(f"{self.alias}: {FileLoggingManager.format_exception(e)}")

        return resource_info
    
    def _max_record_count(self) -> int:

        resource_info = self._get_feature_layer_resource_info()
        max_record_count = resource_info.get("maxRecordCount", None)
        geometry_type = resource_info.get("geometryType", None)

        if geometry_type and max_record_count:
            if "Polygon" in geometry_type or "Line" in geometry_type:
                max_record_count = min((max_record_count, 4_000))
            if "Point" in geometry_type:
                max_record_count = min((max_record_count, 32_000))

        if max_record_count is None:
            self.logger.warning(f"InputFeatureLayer {self.alias} does not provide a maxRecordCount. Defaulting to 1000.")
            return 1_000
        
        return max_record_count
        
    def _supports_pagination(self) -> bool:
        resource_info = self._get_feature_layer_resource_info()
        advanced_query_capabilities = resource_info.get("advancedQueryCapabilities", dict())
        supports_pagination = advanced_query_capabilities.get("supportsPagination", False)
        return supports_pagination

    def _unique_id_field(self) -> dict[str, str] | None:
        resource_info = self._get_feature_layer_resource_info()
        unique_id_field = resource_info.get("uniqueIdField", dict())
        if unique_id_field.get("name", None) and unique_id_field.get("isSystemMaintained", False):
            return unique_id_field
        self.logger.warning(f"InputFeatureLayer {self.alias} does not specify a system-maintained unique ID field.")
        return None
        
    def _unique_id_field_name(self) -> str | None:
        unique_id_field = self._unique_id_field()
        return unique_id_field["name"] if unique_id_field else None
        
    def _get_feature_count_and_extent(self) -> tuple[int, dict]:
        return get_feature_count_and_extent(base_url=str(self.url), where=self.sql_where_clause or "1=1", token=self.token, out_sr=self.output_epsg, spatial_query_params=self.spatial_query_parameters, verify=self.certificate_chain or True)

    def _collect_params_with_metadata(self) -> tuple[dict, dict, dict | None]:

        unique_id_field_name = self._unique_id_field_name()
        if unique_id_field_name:
            outfields = [unique_id_field_name, *self.outfields]
        else:
            outfields = self.outfields

        query_parameters = drop_none_vals({
            "f": "json",
            "outfields": ",".join(outfields),
            "where": self.sql_where_clause or "1=1",
            "token": self.token,
            "outSR": self.output_epsg,
        })

        if self.spatial_query_parameters:
            spatial_query_parameters = self.spatial_query_parameters
            complete_parameters = spatial_query_parameters | query_parameters
        else:
            spatial_query_parameters = None
            complete_parameters = query_parameters

        query_parameters.pop("token", None)

        return (complete_parameters, query_parameters, spatial_query_parameters)

    async def _get_features_by_pagination(self, params: dict) -> list[dict]:

        ssl_context = None
        if isinstance(self.certificate_chain, Path):
            ssl_context = ssl.create_default_context(cafile=self.certificate_chain)
        async with self.semaphore:
            json_responses = await self.requester.paginate_json_features(url=f"{self.url}/query?", params=params, max_record_count=self._max_record_count(), ssl=ssl_context or True)
        return json_responses
    
    def _validate_feature_json_responses(self, json_responses: list[dict]):
        exc = False
        for resp in json_responses:
            try:
                validate_arcgis_json(resp, expected_keys=("features", "spatialReference"), expected_keys_requirement="all")
            except (ArcGisApiErrorResponse, ArcGisApiKeyError) as e:
                self.logger.error(f"{self.alias}: {FileLoggingManager.format_exception(e)}")
                exc = True
        if exc:
            raise InvalidFeaturesResponse(f"{self.alias}: One or more JSON responses failed validation. See logs for details.")
        
    def _validate_gdf_index(self, gdf: gpd.GeoDataFrame) -> bool:
        unique_id_field_name = self._unique_id_field_name()
        if not (unique_id_field_name is not None and gdf.index.name is not None and unique_id_field_name == gdf.index.name):
            raise InvalidIndex(f"{self.alias} produced a GeoDataFrame with an index that does not pass validation!")
        
    def _validate_required_resources(self, *resource_names: str) -> None:
        missing = [name for name in resource_names if getattr(self, name) is None]
        if missing:
            raise ResourceNotInitialized(f"{self.alias} missing required resources: {', '.join(missing)}. Refusing method call.")

class InputFeatureLayersConfig:
    """Configuration for a projects input feature layer dependencies."""

    def __init__(self, input_layers: Iterable[InputFeatureLayer]):
        self.input_layers = list(input_layers)

        seen = set()
        aliases = [fl.alias for fl in self.input_layers]
        duplicates = {alias for alias in aliases if alias in seen or seen.add(alias)}
        if duplicates:
            raise DuplicateAlias(f"Duplicate aliases found: {sorted(duplicates)}")
        self.layers_dict = {fl.alias: fl for fl in self.input_layers}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.shutdown_thread_executors()
        await self.close_requesters()

    def __iter__(self):
        return iter(self.input_layers)

    def __len__(self):
        return len(self.input_layers)

    def get_layer(self, alias: str) -> InputFeatureLayer:
        return self.layers_dict[alias]
    
    def update_resource_info(self):
        for layer in self.input_layers:
            layer._get_feature_layer_resource_info()
    
    def shutdown_thread_executors(self):
        unique_thread_executors = {layer.thread_executor for layer in self.input_layers if isinstance(layer.thread_executor, ThreadPoolExecutor)}
        for thread_executor in unique_thread_executors:
                thread_executor.shutdown(wait=False, cancel_futures=True)

    async def close_requesters(self):
        unique_requesters = {layer.requester for layer in self.input_layers if isinstance(layer.requester, AsyncArcGisRequester)}
        for requester in unique_requesters:
            await requester.close()