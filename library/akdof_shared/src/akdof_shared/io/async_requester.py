import asyncio
import logging
import ssl
from typing import Literal, Mapping, TypedDict
import random

import aiohttp

from akdof_shared.protocol.file_logging_manager import FileLoggingManager

class StatusCodeInstructions(TypedDict, total=False):
    """
    Instructions for handling a specific or pattern matched HTTP status code attached to an `aiohttp.ClientResponseError` object.
    Companion to the `StatusCodePlanner` used in the `AsyncRequester` class.

    Attributes:
        sleep_seconds: How long to wait before retrying (AsyncRequester will default this to 1)
        attempt_increment: How much to increment the retry counter (AsyncRequester will default this to 1)
    """
    sleep_seconds: int | float
    attempt_increment: int | float

StatusCodePlanner = dict[int | str, StatusCodeInstructions]
"""
Plan for how to handle different status codes or status code patterns.
First matching key encountered during iteration will determine handling instructions.
Companion to the `AsyncRequester` class.

Attributes:
    Keys: [int | str]: Integer matching exact code to handle, or string that begins with digit(s) matching a range of codes to handle.
    Values: [StatusCodeInstructions]: Instructions for how to handle the status code or range of codes.
"""

DEFAULT_STATUS_CODE_PLANNER: StatusCodePlanner = {
   408: {"sleep_seconds": 2, "attempt_increment": 1},
   429: {"sleep_seconds": 10, "attempt_increment": 0.5},
   502: {"sleep_seconds": 5, "attempt_increment": 0.8},
   503: {"sleep_seconds": 8, "attempt_increment": 0.8},
   504: {"sleep_seconds": 6, "attempt_increment": 1},
   "5": {"sleep_seconds": 3, "attempt_increment": 1},
}
"""
Default retry strategy for common HTTP errors that should be retried:

- 408 Request Timeout: Server didn't receive complete request in time
- 429 Too Many Requests: Rate limiting - client sending requests too quickly  
- 502 Bad Gateway: Upstream server returned invalid response
- 503 Service Unavailable: Server temporarily overloaded or down for maintenance
- 504 Gateway Timeout: Upstream server didn't respond in time
- "5" (5xx pattern): Any other server error (500-599 range)
"""

class AsyncRequester:
    """Base class for sending asynchronous requests"""

    def __init__(self, timeout: int = 900, logger: logging.Logger | None = None):
        self.timeout = timeout
        self.logger = logger or logging.getLogger("null")
        if not self.logger.handlers:
            self.logger.addHandler(logging.NullHandler())
        self._session = None
        self._dispatchers = None

    def __del__(self):
        """Best-effort fallback to clean up session resources. Explicit resource cleanup with the close() method or the use of an async context manager is preferred."""
        if hasattr(self, '_session') and self._session and not self._session.closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._session.close())
            except Exception:
                pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @property
    def session(self):
        """Get the current session, creating it if necessary"""
        self._ensure_session()
        return self._session

    @property
    def dispatchers(self):
        """Get the current dispatchers, creating them if necessary"""
        self._ensure_session()
        return self._dispatchers

    async def close(self):
        """Manually close the session if it exists and is open"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def send_request(
        self,
        url: str,
        request_method: Literal["get", "post"],
        read_method: Literal["text", "json", "bytes"],
        status_code_plan: StatusCodePlanner | None = DEFAULT_STATUS_CODE_PLANNER,
        return_headers: bool = False,
        retry_max_attempts: int = 3,
        **kwargs,
    ) -> str | dict | bytes | tuple[str | dict | bytes, Mapping[str, str]]:
        """
        Common interface for GET and POST requests.
        Sends requests using retry logic that can be customized for specific status codes or status code patterns.

        Parameters
        ----------
        url : str
        request_method : Literal["get", "post"]
        read_method : Literal["text", "json", "bytes"]
        status_code_plan : dict[int | str, StatusCodeInstructions] | None, optional
        return_headers : bool, optional

        Returns
        -------
        str | dict | bytes | tuple[str | dict | bytes, Mapping[str, str]]
            Content type determined by read_method argument.
            If return_headers is True, returns tuple of ( content , headers ).

        Raises
        ------
        aiohttp.ClientResponseError
            Planned for error status code(s) persisted across all retry attempts, or an unplanned for error status code was encountered.
        aiohttp.ContentTypeError
            Invalid content type persisted across all retry attempts.
        """
        self._ensure_session()
        if status_code_plan is None:
            status_code_plan = dict()

        attempt_counter = 0
        while attempt_counter < retry_max_attempts:
            try:
                async with self.dispatchers[request_method](url, **kwargs) as response:
                    response.raise_for_status()
                    content = await self.dispatchers[read_method](response)
                    return (content, response.headers) if return_headers else content
            except aiohttp.ContentTypeError as e:
                attempt_counter += 1
                if attempt_counter >= retry_max_attempts:
                    raise
                self.logger.debug(f"{url} EXCEPTION: {FileLoggingManager.format_exception(e)}")
                self.logger.debug(f"{url} RESPONSE HEADERS: {dict(response.headers)}")
                content_type = response.headers.get("content-type", "")
                try:
                    fallback_read_method = self._get_read_method_from_content_type(content_type)
                    content = await self.dispatchers[fallback_read_method](response)
                    self.logger.debug(f"{url} RESPONSE CONTENT: {str(content)[:5000]}")
                except Exception as _:
                    self.logger.debug(f"{url} RESPONSE CONTENT: Failed to read response content.")
                await asyncio.sleep(
                    self._randomize_and_backoff_sleep(
                        base_sleep=5,
                        attempt_counter=attempt_counter
                    )
                )
            except aiohttp.ClientResponseError as e:  
                caught = False
                for status_code, instructions in status_code_plan.items():
                    if isinstance(status_code, int) and e.status == status_code:
                        caught = True
                    elif isinstance(status_code, str):
                        pattern = "".join([char for char in status_code if char.isdigit()])
                        if pattern == str(e.status)[: len(pattern)]:
                            caught = True
                    if caught:
                        attempt_counter += instructions.get("attempt_increment", 1)
                        if attempt_counter >= retry_max_attempts:
                            raise
                        self.logger.debug(f"{url} EXCEPTION: {FileLoggingManager.format_exception(e)}")
                        self.logger.debug(f"{url} RESPONSE HEADERS: {dict(response.headers)}")
                        await asyncio.sleep(
                            self._randomize_and_backoff_sleep(
                                base_sleep=instructions.get("sleep_seconds", 2),
                                attempt_counter=attempt_counter
                            )
                        )
                        break
                if not caught:
                    raise

    def _ensure_session(self):
        """Lazily initialize session and dispatchers if not already created"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
            self._dispatchers = {
                "get": self._session.get,
                "post": self._session.post,
                "text": self._read_text,
                "json": self._read_json,
                "bytes": self._read_bytes,
            }
                 
    async def _read_text(self, response: aiohttp.ClientResponse):
        return await response.text()

    async def _read_json(self, response: aiohttp.ClientResponse):
        return await response.json()

    async def _read_bytes(self, response: aiohttp.ClientResponse):
        return await response.read()

    def _get_read_method_from_content_type(self, content_type: str) -> Literal["text", "json", "bytes"]:
        """Determine appropriate read method based on content type header"""
        content_type_lower = content_type.lower()
        if "json" in content_type_lower:
            return "json"
        elif content_type_lower.startswith("text/"):
            return "text"
        else:
            return "bytes"

    def _randomize_and_backoff_sleep(self, base_sleep: int | float, attempt_counter: int | float) -> int | float:
        """Backoff sleep times based on attempt count, and add an element of randomization to avoid a 'stampeding herd' situation"""
        backoff_sleep = base_sleep * max(attempt_counter, 1)
        jitter_range = max(backoff_sleep * 0.1, 0.25)
        jitter = random.uniform(-jitter_range, jitter_range)
        return max(backoff_sleep + jitter, 0.5)
    

class AsyncArcGisRequester(AsyncRequester):
    
    async def paginate_json_features(self, url: str, params: dict, max_record_count: int, ssl: ssl.SSLContext | bool = True) -> list[dict]:

        json_responses = list()
        paginating_params = {**params, "resultRecordCount": max_record_count, "resultOffset": 0}

        paginating = True
        while paginating:
            json_response = await self.send_request(
                url=url,
                request_method="get",
                read_method="json",
                params=paginating_params,
                ssl=ssl
            )
            json_responses.append(json_response)
            paginating_params["resultOffset"] += max_record_count
            paginating = json_response.get("exceededTransferLimit", False)

        return json_responses
