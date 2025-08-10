import pandas as pd
import geopandas as gpd
from pathlib import Path
import json

from config.py.process_config import PROJ_DIR, LOG_LEVEL
from config.py.inputs_config import INPUT_FEATURE_LAYERS_CONFIG

from akwf_utils.logging_utils import FileLoggingManager as LogManager, format_logged_exception
from akwf_utils.time_utils import now_utc_iso
from akwf_utils.retry_utils import with_retry_async
from akwf_gis.json_io import gdf_to_arcgis_json
from akwf_gis.feature_layer_editor import FeatureLayerEditor, ResultingFeatureCountInvalid, BatchEditException, EditFailureResponse
from akwf_gis.arcgis_gdf_conversion_prep import format_gdf_using_arcgis_config, ArcGisTargetLayerConfig
from akwf_io.async_requester import AsyncRequester

_LOGGER = LogManager.get_file_logger(name=__name__, log_file=PROJ_DIR / "logs" / f"{Path(__file__).stem}.log", log_level=LOG_LEVEL)

async def update_target_layer(target_layer_config: ArcGisTargetLayerConfig, token: str, features_to_update: dict[str, gpd.GeoDataFrame]):
        
    try:
        editor_requester = AsyncRequester(timeout=3600, logger=_LOGGER)
        for alias, gdf in features_to_update.items():
            arcgis_json = _format_agol_json_features(gdf=gdf, alias=alias, target_layer_config=target_layer_config)
            editor = FeatureLayerEditor(
                base_url=target_layer_config.url,
                token=token,
                feature_deletion_query=f"local_gov = '{alias}'",
                features_to_add=arcgis_json["features"],
                logger=_LOGGER,
                requester=editor_requester,
            )
            try:
                edit_metrics = await with_retry_async(
                    func=editor.apply_edits_with_validation,
                    retry_exceptions=(ResultingFeatureCountInvalid, BatchEditException, EditFailureResponse),
                    retry_max_attempts=2,
                    retry_delay=30,
                    retry_logger=_LOGGER
                )
                _LOGGER.info(f"{alias}: {json.dumps(edit_metrics)}")
            except Exception as e:
                input_feature_layer = INPUT_FEATURE_LAYERS_CONFIG.get_layer(alias=alias)
                input_feature_layer.rollback_features_cache()
                _LOGGER.warning(f"{alias}: Feature cache rolled back due to error updating the target layer.")
                _LOGGER.error(f"{alias}: {format_logged_exception(e)}")
    finally:
        await editor_requester.close()


def _format_agol_json_features(gdf: gpd.GeoDataFrame, alias: str, target_layer_config: ArcGisTargetLayerConfig) -> dict:

    gdf = gdf.reset_index(drop=True)
    gdf["local_gov"] = alias
    gdf["datetime_processed"] = now_utc_iso()
    gdf["feature_id"] = pd.util.hash_pandas_object(gdf, index=False)

    if "owner" not in gdf.columns and ("first_name" in gdf.columns and "last_name" in gdf.columns):
        gdf["owner"] = (gdf["last_name"].fillna("").astype(str) + ", " + gdf["first_name"].fillna("").astype(str)).str.strip(", ")
        
    if "total_value" not in gdf.columns and ("land_value" in gdf.columns and "building_value" in gdf.columns):
        land_numeric = pd.to_numeric(gdf["land_value"], errors='coerce')
        building_numeric = pd.to_numeric(gdf["building_value"], errors='coerce')
        mask = land_numeric.notna() | building_numeric.notna()
        gdf.loc[mask, "total_value"] = land_numeric.fillna(0) + building_numeric.fillna(0)

    formatted_gdf = format_gdf_using_arcgis_config(gdf=gdf, target_layer_config=target_layer_config, logger=_LOGGER)
    arcgis_json = gdf_to_arcgis_json(gdf=formatted_gdf)

    return arcgis_json
