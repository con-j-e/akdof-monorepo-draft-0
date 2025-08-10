import asyncio
from pathlib import Path

import geopandas as gpd

from config.logging_config import FLM

from config.py.inputs_config import INPUT_FEATURE_LAYERS_CONFIG

from akwf_gis.input_feature_layer import FeaturesGdf
from akwf_gis.gis_utils import gdf_no_index_change_detection
from akwf_utils.logging_utils import FileLoggingManager as LogManager, format_logged_exception

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

async def load_parcel_feature_history() -> dict[str, list[FeaturesGdf]]:

    refresh_features_results = await asyncio.gather(
        *(layer.track_method_call("refresh_features") for layer in INPUT_FEATURE_LAYERS_CONFIG),
        return_exceptions=True
    )
    
    exceptions = [e for e in refresh_features_results if isinstance(e, Exception)]
    for e in exceptions:
        _LOGGER.error(format_logged_exception(e))

    results = [r for r in refresh_features_results if not isinstance(r, Exception)]
    valid_feature_refresh_aliases = [alias for r in results for alias in r.keys()]

    feature_history_results = await asyncio.gather(
        *(layer.track_method_call("load_feature_history", cache_count=2, apply_field_map=True) for layer in INPUT_FEATURE_LAYERS_CONFIG if layer.alias in valid_feature_refresh_aliases),
        return_exceptions=True
    )

    exceptions = [e for e in feature_history_results if isinstance(e, Exception)]
    for e in exceptions:
        _LOGGER.error(format_logged_exception(e))

    results = [r for r in feature_history_results if not isinstance(r, Exception)]
    return {alias: feature_history for r in results for alias, feature_history in r.items()}


def identify_parcel_features_to_update(feature_history_results: dict[str, list[FeaturesGdf]]) -> dict[str, gpd.GeoDataFrame]:

    features_to_update = dict()
    for alias, feature_history in feature_history_results.items():
        if len(feature_history) != 2:
            raise RuntimeError(f"{alias} produced a feature history with only {len(feature_history)} entries. Unable to proceed with feature update logic.")
        new_gdf = feature_history[0].gdf
        old_gdf = feature_history[1].gdf
        change_detection = gdf_no_index_change_detection(new_gdf=new_gdf, old_gdf=old_gdf)
        #if any(len(gdf) > 0 for gdf in change_detection.values()):
        if True:
            _LOGGER.info(f"{alias} has updated parcel records")
            features_to_update[alias] = new_gdf

    return features_to_update

