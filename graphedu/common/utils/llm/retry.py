"""Async retry utilities for LLM operations.

This module provides retry functionality for async operations,
particularly useful for handling transient failures in LLM API calls.
"""

from collections.abc import Callable, Coroutine
import logging
from typing import Any, TypeVar

from langchain_core.exceptions import OutputParserException
from tenacity import before_log, retry, retry_if_exception_type, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


async def Retryable[T](  # noqa: N802
    fn: Callable[..., Coroutine[Any, Any, T]],
    args: list[Any] | None = None,
    kwargs: dict[str, Any] | None = None,
    default: T | None = None,
    raise_when_failed: bool = False,
    retry_when_exception: type[BaseException] = OutputParserException,
    max_attempts: int = 2,
    wait_time: int = 0,
) -> T | None:
    """运行函数并在失败时重试

    :param fn: 要调用的函数
    :param args: 函数参数
    :param kwargs: 函数关键字参数
    :param default: 默认值，如果值为 None 或 False，则返回 None
    :param raise_when_failed: 失败时执行的操作，如果值为 False，则返回 default 的值；若为 True，则直接抛出异常
    :param retry_when_exception: 重试的异常类型
    :param max_attempts: 最大重试次数
    :param wait_time: 重试之间的等待时间
    :return: 调用结果或 None
    """

    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_fixed(wait_time),
        retry=retry_if_exception_type(retry_when_exception),
        before=before_log(logger, logging.DEBUG),
    )
    async def _retryable_call(fn_, args_, kwargs_):
        if args_ is None:
            args_ = []
        if kwargs_ is None:
            kwargs_ = {}
        return await fn_(*args_, **kwargs_)

    try:
        return await _retryable_call(fn, args, kwargs)
    except retry_when_exception as e:
        logger.error(f"重试失败: {e}")
        if raise_when_failed:
            raise
        return default
