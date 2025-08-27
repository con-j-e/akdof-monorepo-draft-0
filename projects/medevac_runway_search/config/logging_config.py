"""Centralized logging configuration for project-wide file logging."""

from akdof_shared.protocol.file_logging_manager import FileLoggingManager

from config.process_config import PROJ_DIR

FLM = FileLoggingManager(
    log_directory=PROJ_DIR / "data" / "logs",
    logging_level="DEBUG",
)
"""
Project-wide file logging manager.

The caller can modify the logging level parameter in accordance with development / production needs.
"""