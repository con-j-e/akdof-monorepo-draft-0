from abc import ABC
import asyncio
from datetime import datetime as dt, timezone as tz
import inspect
from logging import Logger
from pathlib import Path
import sys
from typing import Callable, Iterable, Any, NamedTuple

from akdof_shared.protocol.file_logging_manager import FileLoggingManager
from akdof_shared.protocol.datetime_info import now_utc_iso
from akdof_shared.utils.gmail_sender import GmailSender

class CleanupCallable(NamedTuple):
    func: Callable
    kwargs: dict[str, Any] = dict()

class _MainExitBase(ABC):
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

        self.exit_status = None
        self._start_datetime = dt.now(tz.utc)

    def _shutdown_logging(self):
        try:
            self.file_logging_manager.flush_all_handlers()
            self.file_logging_manager.close_all_handlers()
        except Exception as e:
            self._write_stderr(e)

    def _send_email_notifications(self):
        try:
            log_check_emails = self.file_logging_manager.write_log_check_emails(self._start_datetime)
            for log_file, log_messages in log_check_emails.items():
                self.gmail_sender.plain_text(
                    subject=f"LOGGING NOTIFICATION: {self.project_directory.stem}, {log_file.stem}",
                    body="\n\n".join(log_messages)
                )
        except Exception as e:
            self._write_stderr(e)

    def _set_exit_status(self):
        try:
            self.exit_status = self.file_logging_manager.check_log_files_for_status(self._start_datetime)
        except Exception as e:
            self._write_stderr(e)

    def _archive_logs(self):
        try:
            self.file_logging_manager.check_log_files_to_archive()
        except Exception as e:
            self._write_stderr(e)

    def _write_stderr(self, e: Exception):
        try:
            message = f"{now_utc_iso()} --->\n{self.file_logging_manager.format_exception(exc_val=e, full_traceback=True)}\n\n\n\n\n"
        except Exception:
            message = "STDERR LOGGING FAILURE"
        print(message, file=sys.stderr, flush=True)

class MainExitManager(_MainExitBase):

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.main_logger.critical(self.file_logging_manager.format_exception(exc_val, full_traceback=True))
        self._make_cleanup_calls()
        self._shutdown_logging()
        self._send_email_notifications()
        self._set_exit_status()
        self._archive_logs()
        return True

    def _make_cleanup_calls(self):
        for func, kwargs in self.cleanup_callables:
            try:
                if inspect.iscoroutinefunction(func):
                    asyncio.run(func(**kwargs))
                else:
                    func(**kwargs)
            except Exception as e:
                self.main_logger.error(f"MainExitManager for {self.project_directory.stem} failed calling {func}: {self.file_logging_manager.format_exception(e)}")

class AsyncMainExitManager(_MainExitBase):

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.main_logger.critical(self.file_logging_manager.format_exception(exc_val, full_traceback=True))
        await self._make_cleanup_calls()
        self._shutdown_logging()
        self._send_email_notifications()
        self._set_exit_status()
        self._archive_logs()
        return True

    async def _make_cleanup_calls(self):
        for func, kwargs in self.cleanup_callables:
            try:
                if inspect.iscoroutinefunction(func):
                    await func(**kwargs)
                else:
                    func(**kwargs)
            except Exception as e:
                self.main_logger.error(f"MainExitManager for {self.project_directory.stem} failed calling {func}: {self.file_logging_manager.format_exception(e)}")