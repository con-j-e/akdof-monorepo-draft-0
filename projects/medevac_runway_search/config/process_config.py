import os
from pathlib import Path

PROJ_DIR = Path(os.getenv("AKDOF_ROOT")) / "projects" / "medevac_runway_search"
"""Project root directory"""

TARGET_EPSG: int = 3857
"""Spatial reference used by all hosted feature layers which are updated by this project."""

PROCESSING_EPSG: int = 3338
"""
Spatial reference used for any Euclidean operation requiring the preservation of distance and area.
NOTE spatial analysis concerning flight distances and flight time estimates is run geodesically using a WGS84 ellipsoid.
"""