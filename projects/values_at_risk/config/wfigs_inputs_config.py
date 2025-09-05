import asyncio
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable

from akdof_shared.io.file_cache_manager import FileCacheManager, PurgeMethod
from akdof_shared.io.async_requester import AsyncArcGisRequester
from akdof_shared.utils.create_file_diff import create_file_diff
from akdof_shared.gis.input_feature_layer import InputFeatureLayerCache, InputFeatureLayer, InputFeatureLayersConfig

from config.process_config import PROJ_DIR
from config.logging_config import FLM

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

_SHARED_SEMAPHORE = asyncio.Semaphore(15)
_SHARED_REQUESTER = AsyncArcGisRequester(logger=_LOGGER)
_SHARED_THREAD_EXECUTOR = ThreadPoolExecutor(thread_name_prefix="wfigs_inputs_config")

def wfigs_feature_layer_cache_factory(cache_path: Path) -> InputFeatureLayerCache:
    resource_info_fcm = FileCacheManager(
        path=cache_path / "resource_info",
        max_age=timedelta(days=1),
        max_count=3,
        purge_method=PurgeMethod.OLDEST_WHILE_MAX_COUNT_EXCEEDED,
        cache_compare_func=create_file_diff
    )
    features_fcm = FileCacheManager(
        path=cache_path / "features",
        max_age=timedelta(days=30),
        max_count=3,
        purge_method=PurgeMethod.OLDEST_WHILE_MAX_COUNT_EXCEEDED
    )
    input_feature_layer_cache = InputFeatureLayerCache(
        resource_info=resource_info_fcm,
        features=features_fcm,
    )
    return input_feature_layer_cache

def input_wfigs_layer_factory(url: str, alias: str, sql_where_clause: str | None = None) -> InputFeatureLayer:
    ifl = InputFeatureLayer(
        url=url,
        alias=alias,
        sql_where_clause=sql_where_clause,
        cache=wfigs_feature_layer_cache_factory(cache_path=PROJ_DIR / "data" / "cache" / "wfigs_input_feature_layers" / alias),
        logger=_LOGGER,
        semaphore=_SHARED_SEMAPHORE,
        requester=_SHARED_REQUESTER,
        thread_executor=_SHARED_THREAD_EXECUTOR,
    )
    return ifl

DISPATCH_CENTER_IDS: Iterable[str] = ("AKACDC", "AKCGFC", "AKNFDC", "AKTNFC", "AKYFDC")

INPUT_FEATURE_LAYERS_CONFIG = InputFeatureLayersConfig((
    input_wfigs_layer_factory(
        url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_YearToDate/FeatureServer/0",
        alias="wfigs_locations_ytd",
        sql_where_clause=f"DispatchCenterID IN ({','.join(f"'{center_id}'" for center_id in DISPATCH_CENTER_IDS)})"
    ),
    input_wfigs_layer_factory(
        url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters_YearToDate/FeatureServer/0",
        alias="wfigs_perimeters_ytd",
        sql_where_clause=f"attr_DispatchCenterID IN ({','.join(f"'{center_id}'" for center_id in DISPATCH_CENTER_IDS)})"
    ),
))