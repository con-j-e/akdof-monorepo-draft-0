import json
from typing import Literal

import geopandas as gpd

from akdof_shared.utils.with_retry import with_retry_async
from akdof_shared.gis.spatial_json_conversion import gdf_to_arcgis_json
from akdof_shared.gis.feature_layer_editor import FeatureLayerEditor, ResultingFeatureCountInvalid, BatchEditException, EditFailureResponse
from akdof_shared.gis.arcgis_gdf_conversion_prep import format_gdf_using_arcgis_config, ArcGisTargetLayerConfig
from akdof_shared.io.async_requester import AsyncRequester

from config.process_config import PROJ_DIR
from config.logging_config import FLM

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

async def update_target_layers(features_to_update: dict[str, gpd.GeoDataFrame], token: str) -> dict[Literal["success"], bool]:
    """
    Updates ArcGIS Online feature layers by replacing all features with new data.
    
    Parameters
    ----------
    features_to_update : dict[str, gpd.GeoDataFrame]
        Layer aliases mapped to their replacement GeoDataFrames.
        Aliases are used to identify associated static configuration files
        that determine how data gets formatted in preparation for the update.
    token : str
        ArcGIS authentication token for API access.
        
    Returns
    -------
    dict[Literal["success"], bool]
        Success status indicating whether all layer updates completed without error.
    """
    try:
        success_status = True
        editor_requester = AsyncRequester(logger=_LOGGER)
        for alias, gdf in features_to_update.items():
            target_layer_config = ArcGisTargetLayerConfig.load(json_path=PROJ_DIR / "config" / "target_layer_config" / f"{alias}.json")
            formatted_gdf = format_gdf_using_arcgis_config(gdf=gdf, target_layer_config=target_layer_config, logger=_LOGGER)
            arcgis_json = gdf_to_arcgis_json(gdf=formatted_gdf)

            editor = FeatureLayerEditor(
                base_url=target_layer_config.url,
                token=token,
                feature_deletion_query="1=1",
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
                _LOGGER.error(f"{alias}: {FLM.format_exception(e)}")
                success_status = False
    finally:
        await editor_requester.close()
    
    return {"success": success_status}