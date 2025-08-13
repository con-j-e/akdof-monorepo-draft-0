from datetime import datetime as dt
from datetime import timezone as tz
from enum import IntEnum
import logging
from pathlib import Path
import re
import time
import traceback
from typing import Iterable, Literal, NamedTuple

import pandas as pd

from akdof_shared.protocol.datetime_info import datetime_from_iso, iso_from_datetime, enforce_utc, iso_file_naming, now_utc_iso

class ConfiguredLoggersConflict(Exception): pass
class InvalidLogFileFormat(Exception): pass
class InvalidLogManifestInput(Exception): pass

class ExitStatus(IntEnum):
    """
    Status codes that all Python programs run as `__main__` are expected to exit with.
    These codes represent the highest severity level of one or more events that were logged.

    Attributes
    ----------
    OK : 0
        Operations normal.
    WARNING : 30
        Something occurred that is out of the ordinary, or that might indicate a problem.
    ERROR : 40
        A non-critical error occurred. The main program is expected to have continued running.
    CRITICAL : 50
        A critical error occurred. The main program is expected to have terminated prematurely.
    """
    OK = 0
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class WarningFilterAttributes(NamedTuple):
    """
    Attributes used when identifying warning level log records to filter out.

    Attributes
    ----------
    message : str
        Matched against the log record message.
    module : str | None
        Matched against the log record module. Optional.
    lineno : int | None
        Matched against the log record line number. Optional.
    developer_explanation : str | None
        Contextual information for why this warning can safely be ignored. Optional.
    """
    message: str
    module: str | None
    lineno: int | None
    developer_explanation: str | None

class LogWarningFilter(logging.Filter):
    """Prevents specific warning messages from being logged."""

    def __init__(self, suppressed_warnings: Iterable[WarningFilterAttributes]):
        super().__init__()
        self.suppressed_warnings = suppressed_warnings

    def filter(self, record: logging.LogRecord):
        if record.levelname != "WARNING":
            return True

        message_to_filter = record.getMessage()
        for warning in self.suppressed_warnings:
            if (
                (message_to_filter == warning.message)
                and (warning.module is None or record.module == warning.module)
                and (warning.lineno is None or record.lineno == warning.lineno)
            ):
                return False

        return True
   
class FileLoggingManager:
    """
    A single `FileLoggingManager` instance manages the file logging protocol for a project. 
    
    Attributes
    ----------
    log_directory : Path
        Directory where all log files managed by the instance will be saved.
    logging_level : Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
        Logging level which all loggers managed by the instance will use, by default "INFO".
    log_email_notification_level : Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "WARNING"
        Lowest logging level at which log messages will be included in an email body returned by `write_log_check_emails()`, by default "WARNING".
    root_logger_suppressed_warnings : Iterable[WarningFilterAttributes] | None = None
        `WarningFilterAttributes` that will be used to filter warnings out of the root logger, by default None.
    log_files_to_check : Literal["current_configured", "full_directory"] = "current_configured"
        Rule for which log files `check_log_files_for_status()`, `write_log_check_emails()`, and `check_log_files_to_archive()` will consider.
        "current_configured" considers every log file that the FileLoggingManager instance configured during its lifetime.
        "full_directory" non-recursively considers every log file inside of `log_directory`.
        By default "current_configured".
    log_file_max_lines : int = 2_000
        Maximum number of lines a log file can have before it will be archived by a `check_log_files_to_archive()` call, by default 2,000.
    """
    _default_header: str = "asctime|levelname|module|lineno|message\n"

    _default_format: str = "%(asctime)s|%(levelname)s|%(module)s|%(lineno)d|%(message)s"

    class _DefaultFormatter(logging.Formatter):
        """
        Sets the converter to use UTC for all time information.
        Formats time information as ISO 8601 strings.
        Replaces any `|` in a log message with `<replaced_pipe>`.
        Replaces any `\\n` in a log message with `<br>`.
        """
        converter = time.gmtime

        def formatTime(self, record: logging.LogRecord, datefmt: str | None = None):
            dt_obj = dt.fromtimestamp(timestamp=record.created, tz=tz.utc)
            return iso_from_datetime(dt_obj)
        
        def format(self, record: logging.LogRecord):
            record.msg = record.getMessage().replace("|", "<replaced_pipe>").replace("\n", "<br>")
            record.args = None
            return super().format(record)


    class _LogManifest(dict[Path, pd.DataFrame]):
        """Internal data structure used by public methods `check_log_files_for_status()`, `write_log_check_email_bodies()`, and `check_log_files_to_archive()`"""

        def __init__(self, raw_dict: dict[Path, pd.DataFrame], datetime_filter: dt | None = None):

            for log_file, log_df in raw_dict.items():
                try:
                    log_df["log_datetime"] = log_df["asctime"].apply(lambda x: datetime_from_iso(x))
                    log_df.sort_values("log_datetime", ascending=False, inplace=True)
                    if datetime_filter:
                        datetime_filter = enforce_utc(datetime_filter)
                        raw_dict[log_file] = log_df[log_df["log_datetime"] >= datetime_filter]
                except Exception as e:
                    raise InvalidLogManifestInput(f"Log file at path {log_file} produced a DataFrame that failed LogManifest processing") from e

            super().__init__(raw_dict)

    def __init__(
        self,
        log_directory: Path,
        logging_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
        log_email_notification_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "WARNING",
        root_logger_suppressed_warnings: Iterable[WarningFilterAttributes] | None = None,
        log_files_to_check: Literal["current_configured", "full_directory"] = "current_configured",
        log_file_max_lines: int = 2_000,
    ):
        self.log_directory = log_directory
        self.logging_level = logging_level
        self.log_email_notification_level = log_email_notification_level
        self.root_logger_suppressed_warnings = root_logger_suppressed_warnings
        self.log_files_to_check = log_files_to_check
        self.log_file_max_lines = log_file_max_lines

        self._archive_directory = self.log_directory / "_archive_"
        self._configured_loggers: dict[Path, logging.Logger] = dict()

        self.log_directory.mkdir(parents=True, exist_ok=True)
        self._archive_directory.mkdir(parents=True, exist_ok=True)

        self._configure_root_logger()

    def get_file_logger(
        self,
        logger_name: str | None,
        file_name: str,
        warning_filter: LogWarningFilter | None = None,
    ) -> logging.Logger:
        """Configure and return a file logger, which the calling `FileLoggingManager` instance will then manage"""
        log_file = (self.log_directory / f"{Path(file_name).stem}.log").resolve()
        if log_file in self._configured_loggers:
            raise ConfiguredLoggersConflict(
                f"Logger with name '{self._configured_loggers[log_file].name}' is already logging to {log_file}"
            )
        logger = logging.getLogger(name=logger_name)

        level_dict = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        level = level_dict[self.logging_level]

        logger.setLevel(level=level)
        logger.propagate = False
        if warning_filter:
            logger.addFilter(filter=warning_filter)

        handler = logging.FileHandler(filename=log_file, errors="backslashreplace")
        handler.setLevel(level=level)
        handler.setFormatter(fmt=self._DefaultFormatter(self._default_format))

        logger.handlers.clear()
        logger.addHandler(hdlr=handler)

        with open(log_file, "r") as file:
            lines = sum(1 for _ in file)
        if lines == 0:
            with open(log_file, "w") as file:
                file.write(self._default_header)

        self._configured_loggers[log_file] = logger

        return logger

    def flush_all_handlers(self):
        """Flush handlers for every logger in the configured loggers cache"""
        for logger in self._configured_loggers.values():
            for handler in logger.handlers:
                handler.flush()

    def close_all_handlers(self):
        """Remove and close handlers for every logger in the configured loggers cache"""
        for logger in self._configured_loggers.values():
            for handler in logger.handlers:
                logger.removeHandler(handler)
                handler.close()

    def check_log_files_for_status(self, start_datetime: dt) -> ExitStatus:
        """
        Determine program `ExitStatus` based on maximum severity logging level that occurred since `start_datetime`
        across all `log_files_to_check` for the `FileLoggingManager` instance
        """
        log_manifest = self._load_log_manifest(datetime_filter=start_datetime)

        level_severity = {"CRITICAL": ExitStatus.CRITICAL, "ERROR": ExitStatus.ERROR, "WARNING": ExitStatus.WARNING}

        severity_codes = {ExitStatus.OK}
        for log_df in log_manifest.values():
            for level in level_severity:
                if level in log_df["levelname"].values:
                    severity_codes.add(level_severity[level])

        return max(severity_codes)

    def write_log_check_emails(self, start_datetime: dt) -> dict[Path, list[str]]:
        """
        Reads all `log_files_to_check` for the `FileLoggingManager` instance and
        writes lists of lines having a log level greater than or equal to `log_email_notification_level`
        that occurred since `start_datetime`, and associates line lists with source log files.
        Information intended to be sent in the body of automated email notifications.
        """
        log_manifest = self._load_log_manifest(datetime_filter=start_datetime)

        level_dict = {
            "DEBUG": ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
            "INFO": ("INFO", "WARNING", "ERROR", "CRITICAL"),
            "WARNING": ("WARNING", "ERROR", "CRITICAL"),
            "ERROR": ("ERROR", "CRITICAL"),
            "CRITICAL": ("CRITICAL",),
        }

        log_check_emails = dict()
        for log_file, log_df in log_manifest.items():
            log_df = log_df[log_df["levelname"].isin(level_dict[self.log_email_notification_level])]
            if len(log_df) < 1:
                continue
            email_body = list()
            for row in log_df.itertuples(index=False):
                email_body.append(f"{row.asctime} | {row.levelname} | {row.module} | {row.lineno} | {row.message}")
            log_check_emails[log_file] = email_body

        return log_check_emails

    def check_log_files_to_archive(self):
        """Checks the length of all `log_files_to_check` for the `FileLoggingManager` instance and archives files accordingly"""
        log_manifest = self._load_log_manifest()
        for log_file, log_df in log_manifest.items():
            if len(log_df) >= self.log_file_max_lines:
                log_file.rename(self._archive_directory / f"{log_file.stem}_{iso_file_naming(now_utc_iso())}.log")

    @staticmethod
    def format_exception(
        exc_val: BaseException, full_traceback: bool = False, maximum_characters: int | None = 5_000
    ) -> str:
        """
        Formats exception information for file logging.
        Replaces new lines with html line breaks, removes '^' and '~' characters,
        replaces long whitespace with a single space, and truncates message string down to `maximum_characters`.
        """
        if full_traceback:
            exc_str = "".join(traceback.format_exception(type(exc_val), exc_val, exc_val.__traceback__))
        else:
            exc_str = f"{type(exc_val).__name__}: {exc_val}"

        exc_str = exc_str.replace("\n", "<br>").replace("^", "").replace("~", "")
        exc_str = re.sub(r"\s+", " ", exc_str)

        if maximum_characters and len(exc_str) > maximum_characters:
            exc_str = f"{exc_str[:maximum_characters]}..."

        return exc_str
    
    def _configure_root_logger(self):
        """Default root logger configuration"""
        logging.captureWarnings(True)
        self.get_file_logger(
            logger_name=None,
            file_name="_root_",
            warning_filter=LogWarningFilter(self.root_logger_suppressed_warnings) if self.root_logger_suppressed_warnings else None
        )

    def _load_log_manifest(self, datetime_filter: dt | None = None) -> _LogManifest:
        """Loads all `log_files_to_check` for the `FileLoggingManager` instance into DataFrames and produces the `_LogManifest`"""

        if self.log_files_to_check == "current_configured":
            log_files_to_check = [log_file.resolve() for log_file in self._configured_loggers]
        elif self.log_files_to_check == "full_directory":
            log_files_to_check = [log_file.resolve() for log_file in (self.log_directory).glob("*.log")]
        else:
            raise ValueError(f"Value passed to instance attribute `log_files_to_check` violates accepted string literal arguments")

        raw_dict = dict()
        for log_file in log_files_to_check:
            if not log_file.exists():
                raise FileNotFoundError(f"{log_file} not found.")
            try:
                log_df = pd.read_csv(log_file, delimiter="|")
            except Exception as e:
                raise InvalidLogFileFormat(f"Failed to load log file at {log_file} into Pandas DataFrame") from e
            raw_dict[log_file] = log_df
        
        return self._LogManifest(raw_dict=raw_dict, datetime_filter=datetime_filter)