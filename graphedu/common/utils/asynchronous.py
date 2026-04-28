"""Asynchronous utility functions and executors.

This module provides utilities for working with asyncio, including:
- Event loop policy switching
- Running sync functions in async context using thread/process pools
- Async executor with isolated thread context
"""

import asyncio
from collections.abc import Callable, Coroutine
import concurrent
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures.process import ProcessPoolExecutor
import logging
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

_T = TypeVar("_T")

WINDOWS_POLICIES = ["WindowsProactorEventLoopPolicy", "WindowsSelectorEventLoopPolicy"]
LINUX_POLICIES = ["DefaultEventLoopPolicy", "SelectorEventLoopPolicy", "AsyncIOEventLoopPolicy"]


def switch_asyncio_policy(
    windows: str = "WindowsProactorEventLoopPolicy", linux: str = "uvloop.EventLoopPolicy", use_logger: bool = False
) -> None:
    """Switch the asyncio event loop policy based on the operating system.

    Args:
        windows: Windows event loop policy. Supports asyncio built-in policy names
            or import paths like "gbulb.GLibEventLoopPolicy".
        linux: Linux event loop policy. Supports asyncio built-in policy names
            or import paths like "uvloop.EventLoopPolicy".
        use_logger: Whether to use logger for reporting status.
    """
    from .files import OS_DARWIN, OS_LINUX, OS_WIN, get_os_type
    from .objects import import_from_string

    os_type = get_os_type()
    reporter = logger.info if use_logger else print
    try:
        # 根据操作系统类型组织 asyncio 策略
        if os_type == OS_WIN:
            if windows in WINDOWS_POLICIES:
                windows = f"asyncio.{windows}"
            policy_instance = import_from_string(windows)()
        elif os_type in (OS_LINUX, OS_DARWIN):
            if linux in LINUX_POLICIES:
                linux = f"asyncio.{linux}"
            policy_instance = import_from_string(linux)()
        else:
            raise ValueError("Unsupported OS type")
        # 设置 asyncio 策略
        asyncio.set_event_loop_policy(policy_instance)
        reporter(f"Successfully set event loop policy to: {policy_instance}")
    except Exception as e:
        reporter(f"Failed to set event loop policy for: `{e}`, using default event loop policy.")


async def thread_run_sync[T](pool: ThreadPoolExecutor | None, func: Callable[..., T], *args) -> T:
    """Run a synchronous function asynchronously using a thread pool.

    Args:
        pool: Thread pool executor. The caller is responsible for creating and closing the pool.
        func: Synchronous function to execute.
        *args: Function arguments.

    Returns:
        The return value of the function.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(pool, func, *args)


async def process_run_sync[T](pool: ProcessPoolExecutor | None, func: Callable[[...], T], *args) -> T:
    """Run a synchronous function asynchronously using a process pool.

    Args:
        pool: Process pool executor. The caller is responsible for creating and closing the pool.
        func: Synchronous function to execute.
        *args: Function arguments.

    Returns:
        The return value of the function.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(pool, func, *args)


async def batch_run_sync(func: Callable, *args):
    """Run a synchronous function asynchronously with multiple arguments in batch.

    Args:
        func: Synchronous function to execute.
        *args: Multiple argument lists to pass to the same function.

    Returns:
        List of results from each function call.
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await asyncio.gather(*[loop.run_in_executor(pool, func, arg) for arg in args])


def run_async(func: Callable, *args) -> Any:
    """Run an async function from a synchronous context.

    This function handles both cases: when an event loop exists and when
    a new one needs to be created.

    Args:
        func: Async function to execute.
        *args: Function arguments.

    Returns:
        The return value of the async function.
    """
    is_self_create = False
    try:
        # Try to get the current thread's event loop
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # No event loop exists, create a new one
        is_self_create = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # If event loop is running, submit async task to current loop
        fut = asyncio.run_coroutine_threadsafe(func(args), loop)
        try:
            return fut.result(timeout=10)  # Wait for async task completion
        except TimeoutError:
            logger.warning("Timeout during async cleanup")
    else:
        # Manually run event loop to execute
        try:
            loop.run_until_complete(func(*args))
        except Exception:
            raise
        finally:
            if is_self_create:
                loop.close()


class AsyncExecutor:
    """Async executor with strong thread isolation to avoid conflicts with main thread event loop.

    This executor runs coroutines in a separate thread with its own event loop,
    providing complete isolation from the main thread's async context.

    Attributes:
        executor: Thread pool executor for running isolated event loops.

    Args:
        max_workers: Maximum number of worker threads.
    """

    def __init__(self, max_workers=4):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers, thread_name_prefix="AsyncExecutorThread")

    def run(self, coro: Coroutine[Any, Any, _T]) -> _T:
        """Run an async function synchronously (forced execution in isolated thread).

        Args:
            coro: Coroutine object to execute.

        Returns:
            The return value of the coroutine.
        """
        future = self.executor.submit(self._run_isolated, coro)
        return future.result()

    def batch(self, coros: list[Coroutine[Any, Any, _T]]) -> tuple[Any]:
        """Run multiple async functions in batch.

        Args:
            coros: List of coroutine objects to execute.

        Returns:
            Tuple of results from all coroutines.
        """

        async def _gather():
            return await asyncio.gather(*coros)

        logger.debug(f"AsyncExecutor running {coros} in thread")
        return self.run(_gather())

    # noinspection PyMethodMayBeStatic
    def _run_isolated(self, coro: Coroutine[Any, Any, _T]) -> _T:
        """Run a coroutine in a completely isolated thread environment.

        Each thread has its own independent event loop, completely
        decoupled from the main thread.

        Args:
            coro: Coroutine to execute.

        Returns:
            The return value of the coroutine.
        """
        # Each thread has an independent event loop, completely decoupled from main thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        except Exception:
            raise
        finally:
            loop.close()

    def shutdown(self):
        """Safely shutdown the thread pool."""
        self.executor.shutdown(wait=True)
        logger.info("AsyncExecutor shutdown complete.")
