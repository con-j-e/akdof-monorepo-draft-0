"""
Entry point to ArcPy subprocess for KMZ generation.

An isolated subprocess is used to prevent ArcPy imports from affecting the main runtime environment.
Exits with ExitStatus enum values (1 = operations normal).
"""

import sys

from core.arcpy_create_kmzs import arcpy_create_kmzs

if __name__ == "__main__":
    sys.exit(arcpy_create_kmzs())