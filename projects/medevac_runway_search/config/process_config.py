import os
from pathlib import Path

from akdof_shared.gis.arcgis_gdf_conversion_prep import ArcGisTargetLayerConfig

PROJ_DIR = Path(os.getenv("AKDOF_ROOT")) / "projects" / "medevac_runway_search"
"""Project root directory"""

TARGET_EPSG: int = 3857
"""
Spatial reference used by all hosted feature layers which are updated by this project.
NOTE spatial analysis concerning flight distances and flight time estimates is run geodesically using a WGS84 ellipsoid.
"""

PROCESSING_EPSG: int = 3338
"""Spatial reference used for any Euclidean operation requiring the preservation of distance and area."""

FAA_DATA_SHEET_CONFIG = PROJ_DIR / "config" / "json" / "faa_data_sheet_config.json"

TARGET_LAYER_CONFIG = ArcGisTargetLayerConfig.load(
    json_path=PROJ_DIR / "config" / "target_layer_config"
)
"""Data type and field length configuration for hosted feature layers which get updated by this project"""