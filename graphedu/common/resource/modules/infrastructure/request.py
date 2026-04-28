"""HTTP client resource management module.

This module provides synchronous and asynchronous HTTP client implementations using httpx
with support for connection pooling, timeout configuration, and Server-Sent Events (SSE).

The HTTP clients are designed to be reused across multiple requests for optimal performance
through connection pooling and HTTP keep-alive.

Classes:
    HttpClient: Synchronous HTTP client
    AsyncHttpClient: Asynchronous HTTP client
"""

from collections.abc import AsyncIterable
import logging
import traceback
from typing import Self

import httpx
from httpx import HTTPError as HttpxHTTPError, TimeoutException as HttpxTimeoutException

from graphedu.common.exceptions.common.resource import (
    HTTPClientException,
    HTTPConnectionException,
    HTTPRequestException,
    HTTPTimeoutException,
)
from graphedu.common.resource.core.base import BaseAsyncResource, BaseSyncResource

logger = logging.getLogger(__name__)


class HttpClient(BaseSyncResource):
    """Synchronous HTTP client for making HTTP requests.

    This client provides a synchronous interface to HTTP using httpx with support
    for connection pooling. The client should be reused across multiple requests
    for optimal performance.

    Attributes:
        config: httpx client configuration dictionary (timeout, headers, etc.)
        _client: httpx.Client instance for making HTTP requests
    """

    config: dict | None = None
    _client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get the underlying httpx.Client instance.

        Returns:
            The httpx.Client instance if initialized

        Raises:
            HTTPClientException: If client is not initialized
        """
        if not self._client:
            logger.debug("Attempted to access uninitialized HTTP client")
            raise HTTPClientException(
                operation="access",
                reason="HTTP client not initialized. Call init() first.",
            )
        return self._client

    def init(self, config: dict | None = None) -> Self:
        """Initialize the HTTP synchronous client with configuration.

        This method creates an httpx.Client instance with the provided configuration.
        The client maintains a connection pool for efficient connection reuse.

        Args:
            config: httpx.Client configuration options such as:
                - timeout (float): Request timeout in seconds
                - headers (dict): Default headers for all requests
                - verify (bool): SSL verification (default: True)
                - follow_redirects (bool): Whether to follow redirects

        Returns:
            Self: Returns the client instance for method chaining

        Raises:
            HTTPClientException: If client initialization fails

        Examples:
            >>> client.init({'timeout': 30.0, 'headers': {'User-Agent': 'MyApp'}})
        """
        self.config = config or {}
        try:
            self._client = httpx.Client(**self.config)
            logger.debug(f"HTTP sync client created with config: {self.config}")
            logger.info("HTTP sync client initialized")
            return self
        except HttpxHTTPError as e:
            logger.debug(
                f"HTTP sync client initialization failed. "
                f"Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPClientException(
                operation="initialize",
                reason=f"{type(e).__name__}: {e}",
                details={
                    "config": self.config,
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.debug(
                f"Unexpected error during HTTP sync client initialization. "
                f"Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPClientException(
                operation="initialize",
                reason=f"{type(e).__name__}: {e}",
                details={
                    "config": self.config,
                    "error_type": type(e).__name__,
                },
            ) from e

    def shutdown(self, _: Self = None) -> None:
        """Shutdown the HTTP synchronous client and release resources.

        This method closes the httpx.Client and releases all connections in the pool.
        It should be called when the client is no longer needed.

        Args:
            _: Optional parameter for compatibility with resource lifecycle

        Raises:
            HTTPClientException: If client shutdown fails

        Examples:
            >>> client.shutdown()
        """
        if self._client:
            try:
                self._client.close()
                self._client = None
                logger.info("HTTP sync client closed gracefully")
            except HttpxHTTPError as e:
                logger.debug(
                    f"HTTP sync client shutdown failed. "
                    f"Error: {type(e).__name__}: {e}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )
                raise HTTPClientException(
                    operation="shutdown",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e
            except Exception as e:
                logger.debug(
                    f"Unexpected error during HTTP sync client shutdown. "
                    f"Error: {type(e).__name__}: {e}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )
                raise HTTPClientException(
                    operation="shutdown",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e

    def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
    ) -> tuple[int, str]:
        """Send a GET request to the specified URL.

        This method sends an HTTP GET request with optional query parameters,
        custom headers, and timeout override.

        Args:
            url: The target URL for the GET request
            params: Query parameters to append to the URL
            headers: Custom headers for this specific request
            timeout: Override the default timeout for this request (seconds)

        Returns:
            A tuple of (status_code, response_body) where status_code is the
            HTTP status code and response_body is the response text content

        Raises:
            HTTPClientException: If HTTP client is not initialized
            HTTPTimeoutException: If the request times out
            HTTPConnectionException: If connection fails
            HTTPRequestException: If the request fails for other reasons

        Examples:
            >>> status, body = client.get(
            ...     'https://api.example.com/users',
            ...     params={'page': 1},
            ...     headers={'Accept': 'application/json'}
            ... )
        """
        if not self._client:
            logger.debug("Attempted to send GET request with uninitialized HTTP client")
            raise HTTPClientException(
                operation="send GET request",
                reason="HTTP client not initialized. Call init() first.",
            )

        try:
            response = self._client.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            logger.debug(f"GET request completed: {url} -> {response.status_code}")
            return response.status_code, response.text
        except HttpxTimeoutException as e:
            logger.debug(
                f"HTTP GET request timed out. URL: {url}, Timeout: {timeout}s\nTraceback:\n{traceback.format_exc()}"
            )
            raise HTTPTimeoutException(
                url=url,
                timeout=timeout,
                details={
                    "method": "GET",
                    "error_type": type(e).__name__,
                },
            ) from e
        except HttpxHTTPError as e:
            logger.debug(
                f"HTTP GET request failed. "
                f"URL: {url}, Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPConnectionException(
                url=url,
                reason=f"{type(e).__name__}: {e}",
                details={
                    "method": "GET",
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.debug(
                f"Unexpected error during HTTP GET request. "
                f"URL: {url}, Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPRequestException(
                method="GET",
                url=url,
                reason=f"{type(e).__name__}: {e}",
                details={
                    "error_type": type(e).__name__,
                },
            ) from e

    def post(
        self,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
    ) -> tuple[int, str]:
        """Send a POST request to the specified URL.

        This method sends an HTTP POST request with JSON data payload,
        custom headers, and timeout override.

        Args:
            url: The target URL for the POST request
            data: JSON payload to send in the request body
            headers: Custom headers for this specific request
            timeout: Override the default timeout for this request (seconds)

        Returns:
            A tuple of (status_code, response_body) where status_code is the
            HTTP status code and response_body is the response text content

        Raises:
            HTTPClientException: If HTTP client is not initialized
            HTTPTimeoutException: If the request times out
            HTTPConnectionException: If connection fails
            HTTPRequestException: If the request fails for other reasons

        Examples:
            >>> status, body = client.post(
            ...     'https://api.example.com/users',
            ...     data={'name': 'John', 'email': 'john@example.com'},
            ...     headers={'Content-Type': 'application/json'}
            ... )
        """
        if not self._client:
            logger.debug("Attempted to send POST request with uninitialized HTTP client")
            raise HTTPClientException(
                operation="send POST request",
                reason="HTTP client not initialized. Call init() first.",
            )

        try:
            response = self._client.post(
                url,
                json=data,
                headers=headers,
                timeout=timeout,
            )
            logger.debug(f"POST request completed: {url} -> {response.status_code}")
            return response.status_code, response.text
        except HttpxTimeoutException as e:
            logger.debug(
                f"HTTP POST request timed out. URL: {url}, Timeout: {timeout}s\nTraceback:\n{traceback.format_exc()}"
            )
            raise HTTPTimeoutException(
                url=url,
                timeout=timeout,
                details={
                    "method": "POST",
                    "error_type": type(e).__name__,
                },
            ) from e
        except HttpxHTTPError as e:
            logger.debug(
                f"HTTP POST request failed. "
                f"URL: {url}, Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPConnectionException(
                url=url,
                reason=f"{type(e).__name__}: {e}",
                details={
                    "method": "POST",
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.debug(
                f"Unexpected error during HTTP POST request. "
                f"URL: {url}, Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPRequestException(
                method="POST",
                url=url,
                reason=f"{type(e).__name__}: {e}",
                details={
                    "error_type": type(e).__name__,
                },
            ) from e


class AsyncHttpClient(BaseAsyncResource):
    """Asynchronous HTTP client for making HTTP requests.

    This client provides an asynchronous interface to HTTP using httpx with support
    for connection pooling, SSE streaming, and non-blocking I/O. The client should
    be reused across multiple requests for optimal performance.

    Attributes:
        config: httpx async client configuration dictionary
        _client: httpx.AsyncClient instance for making HTTP requests
    """

    config: dict | None = None
    _client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the underlying httpx.AsyncClient instance.

        Returns:
            The httpx.AsyncClient instance if initialized

        Raises:
            HTTPClientException: If client is not initialized
        """
        if not self._client:
            logger.debug("Attempted to access uninitialized HTTP async client")
            raise HTTPClientException(
                operation="access",
                reason="HTTP async client not initialized. Call init() first.",
            )
        return self._client

    async def init(self, config: dict | None = None) -> Self:
        """Initialize the HTTP asynchronous client with configuration.

        This method creates an httpx.AsyncClient instance with the provided
        configuration. The client maintains a connection pool for efficient
        connection reuse in async contexts.

        Args:
            config: httpx.AsyncClient configuration options such as:
                - timeout (float): Request timeout in seconds
                - headers (dict): Default headers for all requests
                - verify (bool): SSL verification (default: True)
                - follow_redirects (bool): Whether to follow redirects
                - limits (httpx.Limits): Connection limits

        Returns:
            Self: Returns the client instance for method chaining

        Raises:
            HTTPClientException: If client initialization fails
        """
        self.config = config or {}
        try:
            self._client = httpx.AsyncClient(**self.config)
            logger.debug(f"HTTP async client created with config: {self.config}")
            logger.info("HTTP async client initialized")
            return self
        except HttpxHTTPError as e:
            logger.debug(
                f"HTTP async client initialization failed. "
                f"Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPClientException(
                operation="initialize",
                reason=f"{type(e).__name__}: {e}",
                details={
                    "config": self.config,
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.debug(
                f"Unexpected error during HTTP async client initialization. "
                f"Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPClientException(
                operation="initialize",
                reason=f"{type(e).__name__}: {e}",
                details={
                    "config": self.config,
                    "error_type": type(e).__name__,
                },
            ) from e

    async def shutdown(self, _: Self = None) -> None:
        """Shutdown the HTTP asynchronous client and release resources.

        This method closes the httpx.AsyncClient and releases all connections
        in the pool. It should be called when the client is no longer needed.

        Args:
            _: Optional parameter for compatibility with resource lifecycle

        Raises:
            HTTPClientException: If client shutdown fails
        """
        if self._client:
            try:
                await self._client.aclose()
                self._client = None
                logger.info("HTTP async client closed gracefully")
            except HttpxHTTPError as e:
                logger.debug(
                    f"HTTP async client shutdown failed. "
                    f"Error: {type(e).__name__}: {e}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )
                raise HTTPClientException(
                    operation="shutdown",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e
            except Exception as e:
                logger.debug(
                    f"Unexpected error during HTTP async client shutdown. "
                    f"Error: {type(e).__name__}: {e}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )
                raise HTTPClientException(
                    operation="shutdown",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e

    async def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
    ) -> tuple[int, str]:
        """Send an asynchronous GET request to the specified URL.

        This method sends an HTTP GET request with optional query parameters,
        custom headers, and timeout override.

        Args:
            url: The target URL for the GET request
            params: Query parameters to append to the URL
            headers: Custom headers for this specific request
            timeout: Override the default timeout for this request (seconds)

        Returns:
            A tuple of (status_code, response_body) where status_code is the
            HTTP status code and response_body is the response text content

        Raises:
            HTTPClientException: If HTTP client is not initialized
            HTTPTimeoutException: If the request times out
            HTTPConnectionException: If connection fails
            HTTPRequestException: If the request fails for other reasons

        Examples:
            >>> status, body = await client.get(
            ...     'https://api.example.com/users',
            ...     params={'page': 1}
            ... )
        """
        if not self._client:
            logger.debug("Attempted to send async GET request with uninitialized HTTP client")
            raise HTTPClientException(
                operation="send async GET request",
                reason="HTTP async client not initialized. Call init() first.",
            )

        try:
            response = await self._client.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            logger.debug(f"Async GET request completed: {url} -> {response.status_code}")
            return response.status_code, response.text
        except HttpxTimeoutException as e:
            logger.debug(
                f"HTTP async GET request timed out. "
                f"URL: {url}, Timeout: {timeout}s\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPTimeoutException(
                url=url,
                timeout=timeout,
                details={
                    "method": "GET",
                    "error_type": type(e).__name__,
                },
            ) from e
        except HttpxHTTPError as e:
            logger.debug(
                f"HTTP async GET request failed. "
                f"URL: {url}, Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPConnectionException(
                url=url,
                reason=f"{type(e).__name__}: {e}",
                details={
                    "method": "GET",
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.debug(
                f"Unexpected error during HTTP async GET request. "
                f"URL: {url}, Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPRequestException(
                method="GET",
                url=url,
                reason=f"{type(e).__name__}: {e}",
                details={
                    "error_type": type(e).__name__,
                },
            ) from e

    async def post(
        self,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
    ) -> tuple[int, str]:
        """Send an asynchronous POST request to the specified URL.

        This method sends an HTTP POST request with JSON data payload,
        custom headers, and timeout override.

        Args:
            url: The target URL for the POST request
            data: JSON payload to send in the request body
            headers: Custom headers for this specific request
            timeout: Override the default timeout for this request (seconds)

        Returns:
            A tuple of (status_code, response_body) where status_code is the
            HTTP status code and response_body is the response text content

        Raises:
            HTTPClientException: If HTTP client is not initialized
            HTTPTimeoutException: If the request times out
            HTTPConnectionException: If connection fails
            HTTPRequestException: If the request fails for other reasons

        Examples:
            >>> status, body = await client.post(
            ...     'https://api.example.com/users',
            ...     data={'name': 'John', 'email': 'john@example.com'}
            ... )
        """
        if not self._client:
            logger.debug("Attempted to send async POST request with uninitialized HTTP client")
            raise HTTPClientException(
                operation="send async POST request",
                reason="HTTP async client not initialized. Call init() first.",
            )

        try:
            response = await self._client.post(
                url,
                json=data,
                headers=headers,
                timeout=timeout,
            )
            logger.debug(f"Async POST request completed: {url} -> {response.status_code}")
            return response.status_code, response.text
        except HttpxTimeoutException as e:
            logger.debug(
                f"HTTP async POST request timed out. "
                f"URL: {url}, Timeout: {timeout}s\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPTimeoutException(
                url=url,
                timeout=timeout,
                details={
                    "method": "POST",
                    "error_type": type(e).__name__,
                },
            ) from e
        except HttpxHTTPError as e:
            logger.debug(
                f"HTTP async POST request failed. "
                f"URL: {url}, Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPConnectionException(
                url=url,
                reason=f"{type(e).__name__}: {e}",
                details={
                    "method": "POST",
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.debug(
                f"Unexpected error during HTTP async POST request. "
                f"URL: {url}, Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPRequestException(
                method="POST",
                url=url,
                reason=f"{type(e).__name__}: {e}",
                details={
                    "error_type": type(e).__name__,
                },
            ) from e

    async def stream_post(
        self,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
    ) -> AsyncIterable[str]:
        """Send an asynchronous POST request with streaming response.

        This method establishes a streaming connection for receiving
        chunked response data (e.g., SSE events). It returns an async
        generator that yields each line of the response.

        The async generator properly manages the HTTP connection lifecycle
        within an ``async with`` block — the connection stays open as long
        as the caller keeps iterating and is automatically closed when the
        generator is exhausted or closed.

        Args:
            url: The target URL
            data: JSON-serializable request body
            headers: Custom headers for this request
            timeout: Override the default timeout for this request (seconds).
                     For streaming, this is the per-chunk read timeout, not
                     the total request duration.

        Yields:
            str: Each line of the streaming response body

        Raises:
            HTTPClientException: If HTTP client is not initialized
            HTTPTimeoutException: If reading a chunk times out
            HTTPConnectionException: If connection fails
            HTTPRequestException: If the request fails for other reasons

        Examples:
            >>> async for line in client.stream_post(url, data=payload, headers=hdrs):
            ...     if line.startswith("data: "):
            ...         print(line[6:])
        """
        if not self._client:
            logger.debug("Attempted to send streaming POST request with uninitialized HTTP client")
            raise HTTPClientException(
                operation="streaming POST request",
                reason="HTTP async client not initialized. Call init() first.",
            )

        try:
            async with self._client.stream(
                "POST",
                url,
                json=data,
                headers=headers,
                timeout=timeout,
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    error_text = error_body.decode("utf-8", errors="replace")
                    logger.debug(
                        f"Streaming POST received non-200 status. "
                        f"URL: {url}, Status: {response.status_code}, Body: {error_text[:500]}"
                    )
                    raise HTTPRequestException(
                        method="POST",
                        url=url,
                        reason=f"HTTP {response.status_code}: {error_text[:500]}",
                        details={
                            "status_code": response.status_code,
                            "response_body": error_text[:1000],
                        },
                    )

                async for line in response.aiter_lines():
                    yield line
        except HTTPRequestException:
            raise
        except HttpxTimeoutException as e:
            logger.debug(
                f"Streaming POST request timed out. URL: {url}, Timeout: {timeout}s\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPTimeoutException(
                url=url,
                timeout=timeout,
                details={
                    "method": "POST",
                    "request_type": "streaming",
                    "error_type": type(e).__name__,
                },
            ) from e
        except HttpxHTTPError as e:
            logger.debug(
                f"Streaming POST request failed. "
                f"URL: {url}, Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPConnectionException(
                url=url,
                reason=f"{type(e).__name__}: {e}",
                details={
                    "method": "POST",
                    "request_type": "streaming",
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.debug(
                f"Unexpected error during streaming POST request. "
                f"URL: {url}, Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPRequestException(
                method="POST",
                url=url,
                reason=f"{type(e).__name__}: {e}",
                details={
                    "request_type": "streaming",
                    "error_type": type(e).__name__,
                },
            ) from e

    async def sse(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
    ) -> tuple[int, AsyncIterable[str]]:
        """Send an asynchronous GET request with Server-Sent Events (SSE) streaming.

        This method establishes a streaming connection to receive Server-Sent Events
        from the server. It returns an async iterable that yields SSE data chunks.

        Args:
            url: The target URL for the SSE endpoint
            params: Query parameters to append to the URL
            headers: Custom headers for this request (typically include 'Accept: text/event-stream')
            timeout: Override the default timeout for this request (seconds)

        Returns:
            A tuple of (status_code, async_iterator) where the async iterator
            yields SSE data chunks as strings

        Raises:
            HTTPClientException: If HTTP client is not initialized
            HTTPTimeoutException: If the request times out
            HTTPConnectionException: If connection fails
            HTTPRequestException: If the request fails for other reasons

        Examples:
            >>> status, stream = await client.sse('https://api.example.com/events')
            >>> async for chunk in stream:
            ...     print(f"Received: {chunk}")
        """
        if not self._client:
            logger.debug("Attempted to send SSE request with uninitialized HTTP client")
            raise HTTPClientException(
                operation="send SSE request",
                reason="HTTP async client not initialized. Call init() first.",
            )

        try:
            # Use streaming response for SSE
            async with self._client.stream(
                "GET",
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            ) as response:
                logger.debug(f"SSE connection established: {url} -> {response.status_code}")
                # Return status code and async iterator
                return response.status_code, self._sse_generator(response)
        except HttpxTimeoutException as e:
            logger.debug(
                f"HTTP SSE request timed out. URL: {url}, Timeout: {timeout}s\nTraceback:\n{traceback.format_exc()}"
            )
            raise HTTPTimeoutException(
                url=url,
                timeout=timeout,
                details={
                    "method": "GET",
                    "request_type": "SSE",
                    "error_type": type(e).__name__,
                },
            ) from e
        except HttpxHTTPError as e:
            logger.debug(
                f"HTTP SSE request failed. "
                f"URL: {url}, Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPConnectionException(
                url=url,
                reason=f"{type(e).__name__}: {e}",
                details={
                    "method": "GET",
                    "request_type": "SSE",
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.debug(
                f"Unexpected error during HTTP SSE request. "
                f"URL: {url}, Error: {type(e).__name__}: {e}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            raise HTTPRequestException(
                method="GET",
                url=url,
                reason=f"{type(e).__name__}: {e}",
                details={
                    "request_type": "SSE",
                    "error_type": type(e).__name__,
                },
            ) from e

    async def _sse_generator(self, response: httpx.Response) -> AsyncIterable[str]:
        """Generate an async iterator for SSE data chunks.

        This is a helper method that converts the raw byte stream from an
        SSE response into decoded string chunks.

        Args:
            response: The httpx.Response object with active streaming connection

        Yields:
            str: Decoded SSE data chunks

        Examples:
            >>> async for chunk in _sse_generator(response):
            ...     process_chunk(chunk)
        """
        try:
            async for chunk in response.aiter_bytes():
                yield chunk.decode("utf-8")
        except Exception as e:
            logger.debug(
                f"Error reading SSE stream. Error: {type(e).__name__}: {e}\nTraceback:\n{traceback.format_exc()}"
            )
            # Re-raise as HTTPRequestException for consistent error handling
            raise HTTPRequestException(
                method="SSE_READ",
                reason=f"{type(e).__name__}: {e}",
                details={
                    "error_type": type(e).__name__,
                },
            ) from e
