import os
from pathlib import Path

PROJ_DIR: Path = Path(os.getenv("AKDOF_ROOT")) / "projects" / "values_at_risk"
"""Project root directory."""