"""Core processing configuration for Alaska fire region KMZ generation."""

import os
from pathlib import Path
from typing import Iterable, Literal

PROJ_DIR: Path = Path(os.getenv("AKDOF_ROOT")) / "projects" / "regional_kmz_for_ftp"
"""Project root directory"""

AK_FIRE_REGIONS_GDB: Path = PROJ_DIR / "data" / "ak_fire_regions.gdb"
"""
File GDB containing the feature layer specified by global constant `AK_FIRE_REGIONS_LAYER_NAME`.
This is saved locally to cut down on unnecessary queries to static data.
"""

AK_FIRE_REGIONS_LAYER_NAME: str = "AK_Fire_Regions_4326"
"""
Name of the Ak fire regions feature layer inside of the File GDB specified by global constant `AK_FIRE_REGIONS_GDB`.
EPSG 4326 is being used for the sake of consistency with the desired output spatial reference for KMZs.
Because we will set `arcpy.env.outputCoordinateSystem` to EPSG 4326 before processing, input layers will be projected on-the-fly,
so this is not an essential detail.
"""

OUTPUT_KMZ_DIRECTORY: Path = PROJ_DIR / "data" / "temp" / "output_kmz"
"""Temporary storage directory for KMZ files before upload to FTP or AGOL."""

LYRX_DIRECTORY: Path = PROJ_DIR / "data" / "layer_files"
"""
Where layer files that define the symbology used during KMZ generation get stored.
File names must be idential to the associated `InputFeatureLayer` `alias` attribute.
See `inputs_config.py` for context.
"""

PROCESSING_CYCLE: Literal["nightly", "annual"] = "nightly"
"""Whether to run the nightly process or annual process. During a nightly process, input feature layers with an annual processing frequency are ignored."""

PROCESSING_REGIONS: Iterable[
    Literal["CGF", "CRS", "DAS", "FAS", "GAD", "HNS", "KKS", "MSS", "SWS", "TAD", "TAS", "TNF", "UYD"]
] = ("CGF", "CRS", "DAS", "FAS", "GAD", "HNS", "KKS", "MSS", "SWS", "TAD", "TAS", "TNF", "UYD")
"""
Which wildland fire regions to produce KMZs for.
Note that MID region is left out. Data covering MID will be present in the FAS and DAS KMZs.
"""

AKSD_KMZ_ITEM_IDS: dict[
    Literal["CGF", "CRS", "DAS", "FAS", "GAD", "HNS", "KKS", "MSS", "SWS", "TAD", "TAS", "TNF", "UYD"], str
] = {
    "CGF": "a5a1c26a6f4e40a9a379d83f31e58016",
    "CRS": "a5c24acb1d58449ca424de31d6a9df4f",
    "DAS": "ad942d609bd44a7d8429a62456dce8c5",
    "FAS": "dd16fb0838a44b3c8ba859d31751ac0a",
    "GAD": "cde75859ddbb42a4962cef50bc89ed10",
    "HNS": "ec57970044eb4009b38f244a188acbc2",
    "KKS": "36adb7c26b6c4591b208013139570ee0",
    "MSS": "391a1156f54e4382a92060f5078d721a",
    "SWS": "a88725eb1a864ee3960e1bb5d4f793d8",
    "TAD": "250c45c8953149f7a9ddb49fb08b200d",
    "TAS": "2c5d83173292409c95d6b71b0ea90144",
    "TNF": "7ce7d28c9c914bd8b8b401f5190607ad",
    "UYD": "ca0511121b5344bfb049a91c2ec9ac6f",
}
"""
Keys specify wildland fire regions. 
Values specify ArcGIS Online Item ID's for each region-level AKSD KMZ file.
Note that all other KMZs produced will get uploaded to ftp.wildfire.gov. This is why we only specify Item IDs for the AKSD KMZs.
"""
