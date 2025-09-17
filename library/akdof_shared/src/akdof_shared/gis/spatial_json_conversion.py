from collections import defaultdict
import json
from typing import Literal

import geomet.esri
import geopandas as gpd
import pandas as pd

def arcgis_json_to_gdf(arcgis_json: dict) -> gpd.GeoDataFrame:
    """Loads ArcGIS json features into a GeoDataFrame"""

    spatial_reference = arcgis_json.get("spatialReference", dict())
    wkid = spatial_reference.get("wkid", None)
    latest_wkid = spatial_reference.get("latestWkid", None)
    epsg = latest_wkid if latest_wkid else wkid
    if epsg is None:
        raise RuntimeError("`arcgis_json` has no spatialReference property. Refusing to convert data formats without explicit spatial reference information.")
    
    geojson_features = list(map(_arcgis_feature_to_geojson, arcgis_json["features"]))
    gdf = gpd.GeoDataFrame.from_features(features=geojson_features, crs=f"EPSG:{epsg}")

    unique_id_field = arcgis_json.get("uniqueIdField", dict())
    unique_id_field_name = unique_id_field.get("name", None)
    is_system_maintained = unique_id_field.get("isSystemMaintained", False)
    if is_system_maintained and unique_id_field_name and unique_id_field_name in gdf.columns:
        gdf = gdf.set_index(keys=unique_id_field_name, drop=True, verify_integrity=True)

    return gdf

# consider replacing object_id_column_name: str | None with switch convert_index_to_unique_id: bool
# the caller should be explicit with their treatment of unique identifiers. if it operates as such, make it the index on the gdf.
def gdf_to_arcgis_json(gdf: gpd.GeoDataFrame, geometry_column_name: str = "geometry", object_id_column_name: str | None = None) -> dict:
    """Creates ArcGIS json features from a GeoDataFrame"""

    arcgis_json = dict()

    crs = getattr(gdf, "crs", None)
    if crs is None or crs.to_epsg() is None:
        raise RuntimeError("`gdf` has no crs property or a valid EPSG code cannot be determined from the crs property. Refusing to convert data formats without explicit spatial reference information.")
    arcgis_json["spatialReference"] = {"latestWkid": crs.to_epsg()}
    
    gdf_geom_types = gdf[geometry_column_name].geom_type.unique()
    gdf_geom_types = [gt for gt in gdf_geom_types if pd.notna(gt)]
    arcgis_geom_types = pd.Series(gdf_geom_types).apply(_translate_geom_type_to_esri)
    if (len(arcgis_geom_types) != 1) or (arcgis_geom_types.iloc[0] is None):
        raise RuntimeError(f"Expecting non-null geometry types of `gdf` to translate to exactly one valid arcgis geometry type. Instead translated: {arcgis_geom_types}")
    arcgis_json["geometryType"] = arcgis_geom_types.iloc[0]

    if object_id_column_name:
        arcgis_json["objectIdFieldName"] = object_id_column_name

    geojson = json.loads(gdf.to_json(drop_id=True))

    arcgis_json["features"] = list(map(_geojson_feature_to_arcgis, geojson["features"]))

    return arcgis_json

def json_features_to_dataframe(features: list[dict], format: Literal["arcgis", "geojson"]) -> pd.DataFrame:
    """Loads json features from one of two standardized geospatial formats into a DataFrame."""

    if format not in ("arcgis", "geojson"):
        raise ValueError(f"Invalid argument: {format}. Accepted values are 'arcgis' or 'geojson'.")

    df_dict = defaultdict(list)
    attributes_or_properties = {
        "arcgis": "attributes",
        "geojson": "properties",
    }[format]
    for feat in features:
        for key, val in feat[attributes_or_properties].items():
            df_dict[key].append(val)
        for key, val in feat.items():
            if key == attributes_or_properties:
                continue
            df_dict[key].append(val)
    return pd.DataFrame(df_dict)

def _arcgis_feature_to_geojson(arcgis_feature: dict) -> dict:
    """Converts a single ArcGIS JSON feature to a single GeoJSON feature"""
    geojson_feature = dict()
    geojson_feature["properties"] = arcgis_feature["attributes"]
    try:
        geojson_feature["geometry"] = geomet.esri.loads(json.dumps(arcgis_feature["geometry"]))
    except KeyError:
        geojson_feature["geometry"] = None
    return geojson_feature

def _geojson_feature_to_arcgis(geojson_feature: dict) -> dict:
    """
    Converts a single GeoJSON feature to a single ArcGIS feature.

    Default wgs84 spatialReference property is not retained. The caller should explicitly provide a spatial reference for their features.
    """
    arcgis_feature = dict()
    arcgis_feature["attributes"] = geojson_feature["properties"]
    arcgis_geometry = None
    if geojson_feature["geometry"] is not None:
        arcgis_geometry = geomet.esri.dumps(geojson_feature["geometry"])
        arcgis_geometry.pop("spatialReference", None)
    arcgis_feature["geometry"] = arcgis_geometry
    return arcgis_feature
    
def _translate_geom_type_to_esri(geom_type: str) -> str | None:
    """Translates geometry types from GeoPandas / Shapely to the ESRI geometry types used by the ESRI JSON format"""

    translations = {
        "Point": "esriGeometryPoint",
        "MultiPoint": "esriGeometryMultiPoint",
        "LineString": "esriGeometryPolyline",
        "MultiLineString": "esriGeometryPolyline",
        "Polygon": "esriGeometryPolygon",
        "MultiPolygon": "esriGeometryPolygon",
    }
    return translations.get(geom_type, None)
