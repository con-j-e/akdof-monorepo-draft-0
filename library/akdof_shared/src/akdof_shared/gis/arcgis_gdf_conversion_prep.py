from dataclasses import dataclass
from typing import Iterable
import json
import logging

import geopandas as gpd
import pandas as pd

@dataclass
class FieldDefinition:
    """Represents a field definition from an ArcGIS Online hosted feature layer JSON schema"""
    name: str
    type: str
    alias: str
    sqlType: str
    nullable: bool
    editable: bool
    domain: str | None = None
    defaultValue: str | int | float | None = None
    length: int | None = None
    required: bool | None = None

@dataclass
class ArcGisTargetLayerConfig:
    """
    Configuration to inform data type conversions and/or formatting applied to a GeoDataFrame,
    in preparation for converting rows to ArcGIS JSON features that will be added to the target hosted feature layer.

    Attributes
    -------
    url : str
        URL endpoint for the target hosted feature layer
    field : list[FieldDefinition]
        A list of field definitions, as defined in the JSON schema of the target hosted feature layer
    """
    url: str
    fields: list[FieldDefinition]
      
    @classmethod
    def load(cls, json_path: str):
        """Load the `ArcGISTargetLayerConfig` from a locally saved JSON file"""
        with open(json_path) as f:
            data = json.load(f)
        return cls._from_dict(data)
   
    @classmethod
    def _from_dict(cls, data: dict):
        """Create the `ArcGISTargetLayerConfig` from a Python dictionary"""
        fields = [FieldDefinition(**field_data) for field_data in data["fields"]]
        return cls(url=data["url"], fields=fields)

def format_gdf_using_arcgis_config(
    gdf: gpd.GeoDataFrame,
    target_layer_config: ArcGisTargetLayerConfig,
    config_ignore: Iterable[str] | None = ("OBJECTID", "GlobalID", "Shape__Area", "Shape__Length"),
    logger: logging.Logger | None = None
) -> gpd.GeoDataFrame:
    """
    Converts Pandas data types of the columns in `gdf` according to field definitions in `target_layer_config`.
    Column names that do not match a `target_layer_config` field name will be dropped.
    If any field names from `target_layer_config` are not found in the GDF columns, empty columns will be created for these fields.
    Any value in a column in `gdf` that violates the associated field length specification from `target_layer_config` will be truncated down to the maximum allowed length.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        GDF which will be formatted according to `target_layer_config`
    target_layer_config : ArcGisTargetLayerConfig
        Configuration to inform data type conversions and/or formatting applied to a GeoDataFrame
    config_ignore : Iterable[str] | None, optional
        Field names in the `target_layer_config` field definitions to ignore, by default ("OBJECTID", "GlobalID", "Shape__Area", "Shape__Length")
    logger : Logger | None, optional
        Logger used to record field truncation warnings
        
    Returns
    -------
    gpd.GeoDataFrame
        Formatted GDF
    """
    config_ignore = config_ignore or tuple()
    columns_to_keep = [field.name for field in target_layer_config.fields if field.name not in config_ignore]
    columns_to_keep.append(gdf.geometry.name)

    for c in columns_to_keep:
        if c not in gdf.columns:
            gdf[c] = pd.NA
    gdf = gdf[columns_to_keep]

    gdf = _convert_gdf_column_types_to_match_arcgis_field_types(
        gdf=gdf,
        target_layer_config=target_layer_config
    )
    gdf = _truncate_gdf_column_values_to_match_arcgis_field_length(
        gdf=gdf,
        target_layer_config=target_layer_config,
        logger=logger
    )
    return gdf

def _convert_gdf_column_types_to_match_arcgis_field_types(
    gdf: gpd.GeoDataFrame,
    target_layer_config: ArcGisTargetLayerConfig
) -> gpd.GeoDataFrame:
    """Converts GDF column data types to match associated fields in the target layer configuration"""
    field_types = {field.name: field.type for field in target_layer_config.fields}
    for c in gdf.columns:
        if c == gdf.geometry.name:
            continue
        esri_type = field_types[c]
        pd_type = _esri_field_type_to_pd(esri_type)
        try:
            if pd_type in ["Int32", "Int64", "float64"]:
                converted = pd.to_numeric(gdf[c], errors="coerce").astype(pd_type)
            else:
                converted = gdf[c].astype(pd_type)
            gdf = gdf.drop(columns=c)
            gdf[c] = converted
        except Exception as e:
            raise TypeError(f"Failed to convert column '{c}' to type '{pd_type}' (ESRI type: {esri_type})") from e
    return gdf
        
def _truncate_gdf_column_values_to_match_arcgis_field_length(
    gdf: gpd.GeoDataFrame,
    target_layer_config: ArcGisTargetLayerConfig,
    logger: logging.Logger | None = None
) -> gpd.GeoDataFrame:
    """Truncates column values which once converted to JSON attributes would cause a feature layer edit operation to fail due to length requirements"""
    field_lengths = {field.name: field.length for field in target_layer_config.fields if field.length is not None}
    for c in gdf.columns:
        if c not in field_lengths:
            continue
        max_length_raw = gdf[c].str.len().max()
        gdf[c] = gdf[c].apply(lambda x: x[:field_lengths[c]] if pd.notna(x) else x)
        max_length_truncated = gdf[c].str.len().max()
        if (pd.notna(max_length_raw) and pd.notna(max_length_truncated)) and (max_length_raw != max_length_truncated) and logger:
            logger.warning(f"One or more values in column '{c}' were truncated to satisfy target layer field length requirements")
            logger.info(f"Prior to truncation, the maximum value length in column '{c}' was {max_length_raw} characters")
            logger.info(f"After truncation, the maximum value length in column '{c}' is {max_length_truncated} characters")
    return gdf

def _esri_field_type_to_pd(field_type: str) -> str:
    """
    Matches common ESRI field type string identifiers to corresponding Pandas data type string identifiers.
    Intended to fail fast if an unplanned for ESRI field type is encountered. Additional mappings can be added on an as-needed basis. 
    """
    field_type_map = {
        "esriFieldTypeString": "string",
        "esriFieldTypeInteger": "Int32",
        "esriFieldTypeBigInteger": "Int64",
        "esriFieldTypeDouble": "float64",
    }
    if field_type not in field_type_map:
        raise ValueError(f"Preferred Pandas data type to match with ESRI field type '{field_type}' has not been defined")
    return field_type_map[field_type]