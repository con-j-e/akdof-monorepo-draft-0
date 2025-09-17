import pytest

from akdof_shared.gis.spatial_json_conversion import (
    json_features_to_dataframe,
    gdf_to_arcgis_json,
    json_features_to_dataframe,
    _arcgis_feature_to_geojson,
    _geojson_feature_to_arcgis,
    _translate_geom_type_to_esri
)