from akdof_shared.protocol.file_logging_manager import FileLoggingManager

from config.process_config import PROJ_DIR

FLM = FileLoggingManager(
    log_directory=PROJ_DIR / "data" / "logs",
    logging_level="DEBUG",
    log_files_to_check="full_directory"
)