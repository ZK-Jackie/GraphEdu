"""Concurrent programming utilities.

This module provides utilities for concurrent and asynchronous programming,
including rate limiting and synchronization primitives.
"""

import asyncio
from collections.abc import Awaitable, Callable
import time
from typing import ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


class AsyncRateLimiter:
    """Token bucket rate limiter for controlling request rates (QPS).

    Features:
    - Precise QPS control
    - Configurable burst capacity
    - Supports dynamic rate adjustment
    - Optional callback on rate limit hit
    """

    _rate_limit: float
    _burst_capacity: float
    _tokens: float
    _last_refill_time: float
    _lock: asyncio.Lock
    _on_limit_callback: Callable[[float], Awaitable[None]] | None
    _default_timeout: float | None

    def __init__(
        self,
        rate_limit: float,
        burst_capacity: float | None = None,
        on_limit_callback: Callable[[float], Awaitable[None]] | None = None,
        default_timeout: float | None = None,
    ):
        """Initialize rate limiter.

        Args:
            rate_limit: Maximum requests per second
            burst_capacity: Maximum token bucket size (defaults to rate_limit)
            on_limit_callback: Optional callback when rate limit is hit (receives wait time)
            default_timeout: Default maximum waiting time in seconds (None means wait indefinitely)
        """
        self._rate_limit = rate_limit
        self._burst_capacity = burst_capacity if burst_capacity is not None else rate_limit
        self._tokens = self._burst_capacity  # Start with full bucket
        self._last_refill_time = time.time()
        self._lock = asyncio.Lock()
        self._on_limit_callback = on_limit_callback
        self._default_timeout = default_timeout

    @property
    def rate_limit(self) -> float:
        """Current rate limit in requests per second."""
        return self._rate_limit

    @rate_limit.setter
    def rate_limit(self, new_rate: float) -> None:
        """Update rate limit."""
        if new_rate <= 0:
            raise ValueError("Rate limit must be positive")
        self._rate_limit = new_rate
        # Optionally adjust burst capacity if it was tied to the rate limit
        if self._burst_capacity == self._rate_limit:
            self._burst_capacity = new_rate

    @property
    def burst_capacity(self) -> float:
        """Maximum token bucket size."""
        return self._burst_capacity

    @burst_capacity.setter
    def burst_capacity(self, new_capacity: float) -> None:
        """Update burst capacity."""
        if new_capacity <= 0:
            raise ValueError("Burst capacity must be positive")
        self._burst_capacity = new_capacity

    async def acquire(self, timeout: float | None = None) -> bool:
        """Acquire permission to proceed. Blocks until a token is available or timeout occurs.

        Args:
            timeout: Maximum time to wait in seconds (None means wait indefinitely)

        Returns:
            bool: True if token was acquired, False if timed out
        """
        start_time = time.monotonic()

        while True:
            wait_time = await self._try_acquire()

            # Token acquired
            if wait_time <= 0:
                return True

            # Check timeout
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                remaining = timeout - elapsed

                # Timeout reached
                if remaining <= 0:
                    return False

                # Adjust wait time to not exceed timeout
                wait_time = min(wait_time, remaining)

            # Call the callback if provided
            if self._on_limit_callback:
                await self._on_limit_callback(wait_time)

            # Wait outside the lock to avoid blocking other operations
            await asyncio.sleep(wait_time)

    async def _try_acquire(self) -> float:
        """Try to acquire a token and return the wait time if not available.

        Returns:
            float: 0 if acquired, positive wait time if need to wait
        """
        async with self._lock:
            now = time.time()
            time_passed = now - self._last_refill_time

            # Refill tokens based on time passed
            new_tokens = time_passed * self._rate_limit
            self._tokens = min(self._burst_capacity, self._tokens + new_tokens)
            self._last_refill_time = now

            if self._tokens >= 1:
                self._tokens -= 1
                return 0

            # Calculate wait time for next token
            return (1 - self._tokens) / self._rate_limit

    def wrap(self, func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        """Decorator to apply rate limiting to an async function.

        Args:
            func: Async function to rate limit

        Returns:
            Rate-limited wrapper function
        """

        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Extract timeout from kwargs if present
            timeout = kwargs.pop("_rate_limit_timeout", None) if kwargs else None

            # Wait for token availability
            acquired = await self.acquire(timeout=timeout)
            if not acquired:
                raise TimeoutError("Rate limit acquire timed out")

            return await func(*args, **kwargs)

        return wrapper

    async def __aenter__(self):
        """Support for async context manager."""
        acquired = await self.acquire()
        if not acquired:
            raise TimeoutError("Rate limit acquire timed out")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        pass
