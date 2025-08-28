import asyncio

import geopandas as gpd

from config.logging_config import FLM
from config.inputs_config import INPUT_FEATURE_LAYERS_CONFIG

from akdof_shared.gis.input_feature_layer import FeaturesGdf
from akdof_shared.gis.gdf_change_detection import gdf_no_index_change_detection

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

async def load_parcel_feature_history() -> dict[str, list[FeaturesGdf]]:
    """
    Load parcel feature history for all configured input layers.
    
    Refreshes features for all configured layers, then loads feature history 
    (2 cache entries) for layers that successfully refreshed. Exceptions are
    logged but don't halt processing of other layers.
    
    Returns
    -------
    dict[str, list[FeaturesGdf]]
        Feature history by layer alias, containing current and previous features.
    """
    refresh_features_results = await asyncio.gather(
        *(layer.track_method_call("refresh_features") for layer in INPUT_FEATURE_LAYERS_CONFIG),
        return_exceptions=True
    )
    
    exceptions = [e for e in refresh_features_results if isinstance(e, Exception)]
    for e in exceptions:
        _LOGGER.error(FLM.format_exception(e))

    results = [r for r in refresh_features_results if not isinstance(r, Exception)]
    valid_feature_refresh_aliases = [alias for r in results for alias in r.keys()]

    feature_history_results = await asyncio.gather(
        *(layer.track_method_call("load_feature_history", cache_count=2, apply_field_map=True) for layer in INPUT_FEATURE_LAYERS_CONFIG if layer.alias in valid_feature_refresh_aliases),
        return_exceptions=True
    )

    exceptions = [e for e in feature_history_results if isinstance(e, Exception)]
    for e in exceptions:
        _LOGGER.error(FLM.format_exception(e))

    results = [r for r in feature_history_results if not isinstance(r, Exception)]
    return {alias: feature_history for r in results for alias, feature_history in r.items()}

def identify_parcel_features_to_update(feature_history_results: dict[str, list[FeaturesGdf]]) -> dict[str, gpd.GeoDataFrame]:
    """
    Identify parcel features requiring updates based on change detection.
    
    Compares current and previous feature versions for each layer alias.
    Returns only layers with detected changes (additions, modifications, or deletions).
    
    Parameters
    ----------
    feature_history_results : dict[str, list[FeaturesGdf]]
        Feature history by layer alias, containing current and previous features.
    
    Returns
    -------
    dict[str, gpd.GeoDataFrame]
        Current features for layers with detected changes, keyed by alias.
    """
    features_to_update = dict()
    for alias, feature_history in feature_history_results.items():
        if len(feature_history) != 2:
            _LOGGER.error(f"{alias} produced a feature history with only {len(feature_history)} entries. Unable to proceed with feature update logic.")
            continue
        new_gdf = feature_history[0].gdf
        old_gdf = feature_history[1].gdf
        change_detection = gdf_no_index_change_detection(new_gdf=new_gdf, old_gdf=old_gdf)
        if any(len(gdf) > 0 for gdf in change_detection.values()):
            _LOGGER.info(f"{alias} has updated parcel records")
            features_to_update[alias] = new_gdf

    return features_to_update