import os
from pathlib import Path

from akdof_shared.gis.arcgis_gdf_conversion_prep import ArcGisTargetLayerConfig

PROJ_DIR = Path(os.getenv("AKDOF_ROOT")) / "projects" / "ak_parcels"
"""Project root directory"""

TARGET_EPSG = 3857
"""Spatial reference used by hosted feature layer which gets updated by this project"""

TARGET_LAYER_CONFIG = ArcGisTargetLayerConfig.load(
    json_path=PROJ_DIR / "config" / "target_layer_config.json"
)
"""Data type and field length configuration for the hosted feature layer which gets updated by this project"""