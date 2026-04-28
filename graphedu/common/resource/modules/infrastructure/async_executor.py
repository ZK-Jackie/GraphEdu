"""Async executor module for running asynchronous code in isolated threads.

This module provides an executor that runs async functions in dedicated threads
with their own event loops, ensuring isolation from the main thread's event loop.
"""

import asyncio
from collections.abc import Coroutine
import concurrent
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Any, Self

from graphedu.common.exceptions import (
    AsyncExecutorNotInitializedException,
    AsyncExecutorShutdownException,
    AsyncExecutorSubmitException,
    AsyncExecutorValidationException,
)
from graphedu.common.resource.core.base import BaseSyncResource

logger = logging.getLogger(__name__)


class AsyncExecutor(BaseSyncResource):
    """Thread-isolated async executor that avoids conflicts with the main event loop.

    This executor creates a thread pool where each thread runs its own event loop,
    allowing async code to execute safely in environments where the main thread
    already has an event loop or where thread isolation is required.

    Attributes:
        max_workers (int): Maximum number of worker threads in the pool.
        _executor (ThreadPoolExecutor | None): Internal thread pool instance.

    Raises:
        AsyncExecutorValidationException: If max_workers parameter is invalid.
        AsyncExecutorNotInitializedException: If methods are called before init().
        AsyncExecutorSubmitException: If task submission fails.
        AsyncExecutorTimeoutException: If operation times out.
        AsyncExecutorShutdownException: If shutdown process fails.
    """

    max_workers: int = 5
    _executor: ThreadPoolExecutor | None = None

    def init(self, max_workers: int | None = 5) -> Self:
        """Initialize the async executor with a thread pool.

        Creates a thread pool with the specified number of worker threads.
        Each thread will have its own isolated event loop.

        Args:
            max_workers: Maximum number of worker threads. Must be a positive integer.
                         Defaults to 5 if None is provided.

        Returns:
            Self: Returns self for method chaining.

        Raises:
            AsyncExecutorValidationException: If max_workers is not a positive integer.

        Examples:
            >>> executor = AsyncExecutor()
            >>> executor.init(max_workers=10)
            >>> result = executor.run(some_async_function())
        """
        if max_workers is not None and max_workers <= 0:
            raise AsyncExecutorValidationException(
                parameter="max_workers", reason=f"Must be a positive integer, got {max_workers}"
            )

        self.max_workers = max_workers or self.max_workers

        try:
            self._executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers, thread_name_prefix="AsyncExecutorThread"
            )
            logger.info(f"AsyncExecutor initialized with {self.max_workers} workers")
        except Exception as e:
            logger.error(f"Failed to initialize AsyncExecutor: {e}")
            raise AsyncExecutorSubmitException(reason=f"ThreadPoolExecutor creation failed: {e}") from None

        return self

    def run(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """Run an async coroutine in an isolated thread.

        Submits the coroutine to the thread pool where it runs in a dedicated
        event loop. The calling thread blocks until the coroutine completes.

        Args:
            coro: The coroutine object to execute.

        Returns:
            Any: The result of the coroutine execution.

        Raises:
            AsyncExecutorNotInitializedException: If init() has not been called.
            AsyncExecutorSubmitException: If task submission to the pool fails.
            Exception: Any exception raised by the coroutine execution.

        Examples:
            >>> async def fetch_data():
            ...     return await some_async_io_operation()
            >>> result = executor.run(fetch_data())
        """
        if self._executor is None:
            raise AsyncExecutorNotInitializedException

        try:
            future = self._executor.submit(self._run_isolated, coro)
            return future.result()
        except concurrent.futures.thread.BrokenThreadPool:
            logger.error("Thread pool is broken, cannot submit task")
            raise AsyncExecutorSubmitException(reason="Thread pool is broken or shutdown") from None
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            raise

    def batch(self, coros: list[Coroutine[Any, Any, Any]]) -> list[Any]:
        """Run multiple async coroutines concurrently in an isolated thread.

        All coroutines are executed concurrently using asyncio.gather within
        a single isolated thread with its own event loop.

        Args:
            coros: List of coroutine objects to execute.

        Returns:
            list[Any]: List of results from the coroutines, in the same order
                      as the input coroutines.

        Raises:
            AsyncExecutorNotInitializedException: If init() has not been called.
            AsyncExecutorValidationException: If coros list is empty.
            AsyncExecutorSubmitException: If task submission fails.
            Exception: Any exception raised by the coroutine execution.

        Examples:
            >>> async def task1():
            ...     return await fetch_data(1)
            >>> async def task2():
            ...     return await fetch_data(2)
            >>> results = executor.batch([task1(), task2()])
        """
        if self._executor is None:
            raise AsyncExecutorNotInitializedException

        if not coros:
            raise AsyncExecutorValidationException(parameter="coros", reason="Cannot execute empty coroutine list")

        async def _gather() -> list[Any]:
            """Gather multiple coroutines and return their results."""
            return list(await asyncio.gather(*coros))

        logger.debug(f"AsyncExecutor running {len(coros)} coroutines in isolated thread")
        return self.run(_gather())

    def _run_isolated(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """Run a coroutine in a completely isolated thread environment.

        Creates a new event loop for the current thread, executes the coroutine,
        and ensures proper cleanup. This method is designed to be called from
        within the thread pool.

        Args:
            coro: The coroutine object to execute.

        Returns:
            Any: The result of the coroutine execution.

        Raises:
            Exception: Any exception raised during coroutine execution or loop management.

        Note:
            This method should not be called directly. It is intended for internal
            use by the thread pool worker.
        """
        # Create independent event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(coro)
        except Exception as e:
            logger.error(f"Error in isolated thread execution: {e}")
            raise
        finally:
            # Clean up the event loop
            try:
                loop.close()
            except Exception as e:
                logger.warning(f"Error closing event loop in isolated thread: {e}")

    def shutdown(self, _: Self = None) -> None:
        """Safely shutdown the thread pool.

        Waits for all pending tasks to complete before closing the thread pool.
        After shutdown, the executor cannot be used to run new tasks.

        Args:
            _: Ignored parameter (required by BaseSyncResource interface).

        Raises:
            AsyncExecutorShutdownException: If the shutdown process fails.

        Examples:
            >>> executor.shutdown()
        """
        if self._executor is None:
            logger.warning("AsyncExecutor shutdown called but executor is not initialized")
            return

        try:
            self._executor.shutdown(wait=True)
            logger.info("AsyncExecutor shutdown complete")
        except Exception as e:
            logger.error(f"AsyncExecutor shutdown failed: {e}")
            raise AsyncExecutorShutdownException(reason=str(e)) from None
        finally:
            self._executor = None
