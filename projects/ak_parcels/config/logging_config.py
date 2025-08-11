from akdof_shared.protocol.file_logging_manager import FileLoggingManager

from config.process_config import PROJ_DIR

FLM = FileLoggingManager(
    log_directory=PROJ_DIR / "logs",
    logging_level="DEBUG",
)