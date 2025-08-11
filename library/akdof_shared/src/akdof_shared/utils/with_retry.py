import asyncio
from logging import Logger
import time
from typing import Any, Callable

from akdof_shared.protocol.file_logging_manager import FileLoggingManager as FLM

def with_retry(
    func: Callable,
    *args,
    retry_exceptions: tuple = (Exception,),
    retry_max_attempts: int = 3,
    retry_delay: float = 1.0,
    retry_backoff: float = 2.0,
    retry_logger: Logger | None = None,
    **kwargs,
) -> Any:
    """
    Calls `func` with generic retry logic.

    Parameters
    ----------
    func : Callable
        Function to call with retry logic. Will recieve any *args and **kwargs passed to with_retry()
    retry_exceptions : tuple, optional
        Exceptions that will initiate retry attempts, by default (Exception,)
    retry_max_attempts : int, optional
        How many times to try calling `func` before raising `retry_exceptions`, by default 3
    retry_delay : float, optional
        Seconds to delay after first unsuccesful `func` call, by default 1.0
    retry_backoff : float, optional
        Multiplier applied to `retry_delay` after every unsuccesful `func` call, by default 2.0
    retry_logger : Logger | None, optional
        For logging debug level messages upon each failed `func` call, by default None

    Returns
    -------
    Any
        Returns from `func`
    """
    current_delay = retry_delay
    for attempt in range(retry_max_attempts):
        try:
            return func(*args, **kwargs)
        except retry_exceptions as e:
            if attempt == retry_max_attempts - 1:
                raise
            if retry_logger:
                retry_logger.debug(
                    f"{func.__name__} attempt {attempt + 1} failed with {FLM.format_exception(e)}. Retrying in {current_delay}s..."
                )
            time.sleep(current_delay)
            current_delay *= retry_backoff

async def with_retry_async(
    func: Callable,
    *args,
    retry_exceptions: tuple = (Exception,),
    retry_max_attempts: int = 3,
    retry_delay: float = 1.0,
    retry_backoff: float = 2.0,
    retry_logger: Logger | None = None,
    **kwargs,
) -> Any:
    """
    Awaits `func` with generic retry logic.

    Parameters
    ----------
    func : Callable
        Coroutine returning function to call with retry logic. Will recieve any *args and **kwargs passed to with_retry()
    retry_exceptions : tuple, optional
        Exceptions that will initiate retry attempts, by default (Exception,)
    retry_max_attempts : int, optional
        How many times to try calling `func` before raising `retry_exceptions`, by default 3
    retry_delay : float, optional
        Seconds to delay after first unsuccesful `func` call, by default 1.0
    retry_backoff : float, optional
        Multiplier applied to `retry_delay` after every unsuccesful `func` call, by default 2.0
    retry_logger : Logger | None, optional
        For logging debug level messages upon each failed `func` call, by default None

    Returns
    -------
    Any
        Returns from `func`
    """
    current_delay = retry_delay
    for attempt in range(retry_max_attempts):
        try:
            return await func(*args, **kwargs)
        except retry_exceptions as e:
            if attempt == retry_max_attempts - 1:
                raise
            if retry_logger:
                retry_logger.debug(
                    f"{func.__name__} attempt {attempt + 1} failed with {FLM.format_exception(e)}. Retrying in {current_delay}s..."
                )
            await asyncio.sleep(current_delay)
            current_delay *= retry_backoff