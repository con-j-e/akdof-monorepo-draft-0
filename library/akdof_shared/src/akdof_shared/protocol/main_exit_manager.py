import asyncio
from enum import IntEnum
from datetime import datetime as dt, timezone as tz
import inspect
from logging import Logger
from pathlib import Path
from typing import Callable, Iterable, Any, NamedTuple

from file_logging_manager import FileLoggingManager
from utils.gmail_sender import GmailSender

class CleanExitFailure(Exception): pass

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
  
class CleanupCallable(NamedTuple):
    func: Callable
    kwargs: dict[str, Any] = dict()
  
class MainExitManager:
    def __init__(
        self,
        project_directory: Path,
        file_logging_manager: FileLoggingManager,
        main_logger: Logger,
        gmail_sender: GmailSender,
        cleanup_callables: Iterable[CleanupCallable] | None = None
    ):
        self.project_directory = project_directory
        self.file_logging_manager = file_logging_manager
        self.main_logger = main_logger
        self.gmail_sender = gmail_sender
        self.cleanup_callables = cleanup_callables or tuple()

        self._start_datetime = dt.now(tz.utc)

    def clean_exit(self) -> ExitStatus:
        for func, kwargs in self.cleanup_callables:
            try:
                if inspect.iscoroutinefunction(func):
                    asyncio.run(func(**kwargs))
                else:
                    func(**kwargs)
            except Exception as e:
                self.main_logger.error(f"MainManager for {self.project_directory} failed calling {func}: {self.file_logging_manager.format_exception(e)}")
        try:
            self.file_logging_manager.flush_all_handlers()
            exit_status = self.file_logging_manager.check_log_files_for_status(start_datetime=self._start_datetime)
            log_check_emails = self.file_logging_manager.write_log_check_emails(start_datetime=self._start_datetime)
            for log_file, log_messages in log_check_emails.items():
                self.gmail_sender.plain_text(
                    subject=f"LOGGING NOTIFICATION: {self.project_directory.stem}, {log_file.stem}",
                    body="\n\n".join(log_messages)
                )
            self.file_logging_manager.close_all_handlers()
            self.file_logging_manager.check_log_files_to_archive()
        except Exception as e:
            raise CleanExitFailure(f"MainManager for {self.project_directory} failed to exit cleanly") from e

        return exit_status