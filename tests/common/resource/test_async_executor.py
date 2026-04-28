"""AsyncExecutor resource module unit tests.

测试覆盖范围：
- init 和 shutdown 流程
- 核心功能测试 (run, batch, _run_isolated)
- 边界条件测试 (连接失败、配置错误、清理失败、未初始化调用)
- 属性访问测试
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Coroutine
from unittest.mock import MagicMock, patch

import pytest

from graphedu.common.exceptions import (
    AsyncExecutorNotInitializedException,
    AsyncExecutorShutdownException,
    AsyncExecutorSubmitException,
    AsyncExecutorValidationException,
)
from graphedu.common.resource.modules.infrastructure.async_executor import AsyncExecutor


# =============================================================================
# 配置 Fixtures
# =============================================================================


@pytest.fixture
def default_max_workers() -> int:
    """提供默认的 max_workers 值。"""
    return 5


@pytest.fixture
def custom_max_workers() -> int:
    """提供自定义的 max_workers 值。"""
    return 10


@pytest.fixture
def invalid_max_workers_negative() -> int:
    """提供无效的负数 max_workers 值。"""
    return -1


@pytest.fixture
def invalid_max_workers_zero() -> int:
    """提供无效的零值 max_workers。"""
    return 0


# =============================================================================
# Mock 对象 Fixtures
# =============================================================================


@pytest.fixture
def mock_thread_pool_executor() -> MagicMock:
    """提供 Mock 的 ThreadPoolExecutor。"""
    mock_executor = MagicMock(spec=ThreadPoolExecutor)
    mock_executor.submit = MagicMock()
    mock_executor.shutdown = MagicMock()
    return mock_executor


@pytest.fixture
def mock_future() -> MagicMock:
    """提供 Mock 的 Future 对象。"""
    mock_fut = MagicMock()
    mock_fut.result = MagicMock()
    return mock_fut


# =============================================================================
# 未初始化的客户端 Fixtures（用于测试边界情况）
# =============================================================================


@pytest.fixture
def async_executor_uninit() -> AsyncExecutor:
    """提供未初始化的 AsyncExecutor 实例。"""
    return AsyncExecutor()


# =============================================================================
# 测试类：初始化流程
# =============================================================================


class TestAsyncExecutorInit:
    """测试 AsyncExecutor 的初始化流程。"""

    def test_init_with_default_max_workers(self, async_executor_uninit, default_max_workers):
        """测试使用默认 max_workers 初始化。

        验证：
        - ThreadPoolExecutor 被创建
        - max_workers 设置正确
        - 返回 self 以支持链式调用
        """
        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            mock_tpe.return_value = mock_executor

            result = async_executor_uninit.init()

            assert result is async_executor_uninit  # 链式调用
            assert async_executor_uninit.max_workers == default_max_workers
            assert async_executor_uninit._executor == mock_executor
            mock_tpe.assert_called_once_with(
                max_workers=default_max_workers, thread_name_prefix="AsyncExecutorThread"
            )

    def test_init_with_custom_max_workers(self, async_executor_uninit, custom_max_workers):
        """测试使用自定义 max_workers 初始化。

        验证：
        - ThreadPoolExecutor 使用正确的 max_workers 创建
        - max_workers 属性设置正确
        """
        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            mock_tpe.return_value = mock_executor

            async_executor_uninit.init(max_workers=custom_max_workers)

            assert async_executor_uninit.max_workers == custom_max_workers
            mock_tpe.assert_called_once_with(
                max_workers=custom_max_workers, thread_name_prefix="AsyncExecutorThread"
            )

    def test_init_with_none_max_workers_uses_default(self, async_executor_uninit):
        """测试传入 None 作为 max_workers 时使用默认值。

        验证：
        - 使用类默认值 5
        - ThreadPoolExecutor 正确创建
        """
        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            mock_tpe.return_value = mock_executor

            async_executor_uninit.init(max_workers=None)

            assert async_executor_uninit.max_workers == 5
            mock_tpe.assert_called_once()

    def test_init_with_negative_max_workers_raises_exception(
        self, async_executor_uninit, invalid_max_workers_negative
    ):
        """测试使用负数 max_workers 抛出 AsyncExecutorValidationException。

        验证：
        - 抛出正确的异常类型
        - 异常信息包含参数名和原因
        """
        with pytest.raises(AsyncExecutorValidationException) as exc_info:
            async_executor_uninit.init(max_workers=invalid_max_workers_negative)

        assert exc_info.value.kwargs.get("parameter") == "max_workers"
        assert "Must be a positive integer" in exc_info.value.message
        assert str(invalid_max_workers_negative) in exc_info.value.message

    def test_init_with_zero_max_workers_raises_exception(
        self, async_executor_uninit, invalid_max_workers_zero
    ):
        """测试使用零值 max_workers 抛出 AsyncExecutorValidationException。

        验证：
        - 抛出正确的异常类型
        """
        with pytest.raises(AsyncExecutorValidationException) as exc_info:
            async_executor_uninit.init(max_workers=invalid_max_workers_zero)

        assert exc_info.value.kwargs.get("parameter") == "max_workers"

    def test_init_with_thread_pool_creation_error_raises_exception(self, async_executor_uninit):
        """测试 ThreadPoolExecutor 创建失败时抛出 AsyncExecutorSubmitException。

        验证：
        - ThreadPoolExecutor 创建失败时转换为正确的异常
        - 异常消息包含失败原因
        """
        with patch(
            "graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor",
            side_effect=RuntimeError("Cannot create thread pool"),
        ):
            with pytest.raises(AsyncExecutorSubmitException) as exc_info:
                async_executor_uninit.init()

            assert "ThreadPoolExecutor creation failed" in exc_info.value.message


# =============================================================================
# 测试类：关闭流程
# =============================================================================


class TestAsyncExecutorShutdown:
    """测试 AsyncExecutor 的关闭流程。"""

    def test_shutdown_success(self, async_executor_uninit):
        """测试成功关闭线程池。

        验证：
        - shutdown 方法被调用
        - wait=True 等待所有任务完成
        - _executor 被设置为 None
        """
        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            mock_tpe.return_value = mock_executor

            async_executor_uninit.init()
            async_executor_uninit.shutdown()

            mock_executor.shutdown.assert_called_once_with(wait=True)
            assert async_executor_uninit._executor is None

    def test_shutdown_without_init_is_safe(self, async_executor_uninit):
        """测试未初始化时关闭不报错。

        验证：
        - 不抛出异常
        - _executor 保持为 None
        """
        async_executor_uninit.shutdown()
        assert async_executor_uninit._executor is None

    def test_shutdown_with_error_raises_exception(self, async_executor_uninit):
        """测试关闭失败时抛出 AsyncExecutorShutdownException。

        验证：
        - shutdown 失败时抛出正确的异常
        - 异常消息包含失败原因
        - _executor 仍被设置为 None（finally 块）
        """
        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            mock_executor.shutdown.side_effect = RuntimeError("Shutdown failed")
            mock_tpe.return_value = mock_executor

            async_executor_uninit.init()

            with pytest.raises(AsyncExecutorShutdownException) as exc_info:
                async_executor_uninit.shutdown()

            assert "Shutdown failed" in exc_info.value.message
            # finally 块确保 _executor 被清理
            assert async_executor_uninit._executor is None


# =============================================================================
# 测试类：属性访问
# =============================================================================


class TestAsyncExecutorProperties:
    """测试 AsyncExecutor 的属性访问。"""

    def test_max_workers_property_default(self, async_executor_uninit):
        """测试 max_workers 属性的默认值。"""
        assert async_executor_uninit.max_workers == 5

    def test_max_workers_property_after_init(self, async_executor_uninit, custom_max_workers):
        """测试初始化后 max_workers 属性的值。"""
        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor"):
            async_executor_uninit.init(max_workers=custom_max_workers)
            assert async_executor_uninit.max_workers == custom_max_workers

    def test_mode_property(self, async_executor_uninit):
        """测试 mode 属性返回 'sync'。"""
        assert async_executor_uninit.mode == "sync"


# =============================================================================
# 测试类：核心功能 - run
# =============================================================================


class TestAsyncExecutorRun:
    """测试 AsyncExecutor 的 run 方法。"""

    @pytest.mark.asyncio
    async def test_run_success(self, async_executor_uninit, mock_future):
        """测试成功运行协程。

        验证：
        - 协程在隔离线程中执行
        - 返回正确的结果
        """
        async def test_coro():
            return "test_result"

        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            # Mock submit 返回 mock_future
            mock_executor.submit.return_value = mock_future
            mock_future.result.return_value = "test_result"
            mock_tpe.return_value = mock_executor

            async_executor_uninit.init()
            result = async_executor_uninit.run(test_coro())

            assert result == "test_result"
            mock_executor.submit.assert_called_once()
            # 验证 _run_isolated 方法被调用
            args = mock_executor.submit.call_args[0]
            assert args[0] == async_executor_uninit._run_isolated

    def test_run_without_init_raises_exception(self, async_executor_uninit):
        """测试未初始化时调用 run 抛出 AsyncExecutorNotInitializedException。

        验证：
        - 抛出正确的异常类型
        """
        # 使用 mock 协程对象，避免创建真实的协程导致资源警告
        mock_coro = MagicMock(spec=Coroutine)

        with pytest.raises(AsyncExecutorNotInitializedException):
            async_executor_uninit.run(mock_coro)

    def test_run_with_broken_thread_pool_raises_exception(self, async_executor_uninit):
        """测试线程池损坏时抛出 AsyncExecutorSubmitException。

        验证：
        - BrokenThreadPool 被捕获并转换为正确的异常
        """
        # 创建一个模拟的 BrokenThreadPool 异常
        class MockBrokenThreadPool(Exception):
            pass

        async def test_coro():
            return "result"

        # Mock concurrent.futures.thread 模块中的 BrokenThreadPool
        with patch("graphedu.common.resource.async_executor.concurrent.futures.thread.BrokenThreadPool", MockBrokenThreadPool):
            with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
                mock_executor = MagicMock(spec=ThreadPoolExecutor)
                mock_executor.submit.side_effect = MockBrokenThreadPool("Thread pool is broken")
                mock_tpe.return_value = mock_executor

                async_executor_uninit.init()

                with pytest.raises(AsyncExecutorSubmitException) as exc_info:
                    async_executor_uninit.run(test_coro())

                assert "Thread pool is broken or shutdown" in exc_info.value.message

    def test_run_with_coroutine_exception_propagates(self, async_executor_uninit, mock_future):
        """测试协程中的异常正常传播。

        验证：
        - 协程中抛出的异常不会被捕获
        - 异常会向上传播
        """
        async def failing_coro():
            raise ValueError("Coroutine failed")

        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            mock_executor.submit.return_value = mock_future
            mock_future.result.side_effect = ValueError("Coroutine failed")
            mock_tpe.return_value = mock_executor

            async_executor_uninit.init()

            with pytest.raises(ValueError, match="Coroutine failed"):
                async_executor_uninit.run(failing_coro())

    def test_run_with_asyncio_gather_result(self, async_executor_uninit, mock_future):
        """测试运行返回 asyncio.gather 结果的协程。

        验证：
        - 能够正确处理复杂异步操作的返回值
        """
        async def gather_coro():
            results = await asyncio.gather(
                asyncio.sleep(0, result="result1"),
                asyncio.sleep(0, result="result2"),
            )
            return results

        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            mock_executor.submit.return_value = mock_future
            mock_future.result.return_value = ["result1", "result2"]
            mock_tpe.return_value = mock_executor

            async_executor_uninit.init()
            result = async_executor_uninit.run(gather_coro())

            assert result == ["result1", "result2"]


# =============================================================================
# 测试类：核心功能 - batch
# =============================================================================


class TestAsyncExecutorBatch:
    """测试 AsyncExecutor 的 batch 方法。"""

    def test_batch_success(self, async_executor_uninit):
        """测试批量执行协程成功。

        验证：
        - 所有协程都被执行
        - 结果按顺序返回
        - 使用 asyncio.gather 并发执行
        """
        # 使用 mock 协程对象，避免创建真实的协程导致资源警告
        mock_coro1 = MagicMock(spec=Coroutine)
        mock_coro2 = MagicMock(spec=Coroutine)
        mock_coro3 = MagicMock(spec=Coroutine)
        coros = [mock_coro1, mock_coro2, mock_coro3]

        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            mock_fut = MagicMock()
            mock_fut.result.return_value = ["result1", "result2", "result3"]
            mock_executor.submit.return_value = mock_fut
            mock_tpe.return_value = mock_executor

            async_executor_uninit.init()
            results = async_executor_uninit.batch(coros)

            assert results == ["result1", "result2", "result3"]
            mock_executor.submit.assert_called_once()

    def test_batch_without_init_raises_exception(self, async_executor_uninit):
        """测试未初始化时调用 batch 抛出 AsyncExecutorNotInitializedException。"""
        # 使用 mock 协程对象，避免创建真实的协程导致资源警告
        mock_coro = MagicMock(spec=Coroutine)

        with pytest.raises(AsyncExecutorNotInitializedException):
            async_executor_uninit.batch([mock_coro])

    def test_batch_with_empty_list_raises_exception(self, async_executor_uninit):
        """测试传入空列表抛出 AsyncExecutorValidationException。

        验证：
        - 抛出正确的异常类型
        - 异常信息包含参数名和原因
        """
        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor"):
            async_executor_uninit.init()

            with pytest.raises(AsyncExecutorValidationException) as exc_info:
                async_executor_uninit.batch([])

            assert exc_info.value.kwargs.get("parameter") == "coros"
            assert "Cannot execute empty coroutine list" in exc_info.value.message

    def test_batch_with_single_coroutine(self, async_executor_uninit):
        """测试批量执行单个协程。

        验证：
        - 单个协程也能正常工作
        - 返回包含单个结果的列表
        """
        async def single_coro():
            return "single_result"

        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            mock_fut = MagicMock()
            mock_fut.result.return_value = ["single_result"]
            mock_executor.submit.return_value = mock_fut
            mock_tpe.return_value = mock_executor

            async_executor_uninit.init()
            results = async_executor_uninit.batch([single_coro()])

            assert results == ["single_result"]

    def test_batch_with_exception_in_coroutine(self, async_executor_uninit):
        """测试批量执行中某个协程失败。

        验证：
        - 异常正常传播
        """
        async def failing_coro():
            raise ValueError("Batch failed")

        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            mock_fut = MagicMock()
            mock_fut.result.side_effect = ValueError("Batch failed")
            mock_executor.submit.return_value = mock_fut
            mock_tpe.return_value = mock_executor

            async_executor_uninit.init()

            with pytest.raises(ValueError, match="Batch failed"):
                async_executor_uninit.batch([failing_coro()])


# =============================================================================
# 测试类：核心功能 - _run_isolated
# =============================================================================


class TestAsyncExecutorRunIsolated:
    """测试 AsyncExecutor 的 _run_isolated 方法。"""

    def test_run_isolated_creates_new_event_loop(self, async_executor_uninit):
        """测试 _run_isolated 创建新的事件循环。

        验证：
        - 创建独立的事件循环
        - 设置为当前线程的事件循环
        - 正确执行协程
        """
        async def test_coro():
            return "isolated_result"

        with patch("graphedu.common.resource.async_executor.asyncio.new_event_loop") as mock_new_loop:
            with patch("graphedu.common.resource.async_executor.asyncio.set_event_loop") as mock_set_loop:
                mock_loop = MagicMock()
                mock_new_loop.return_value = mock_loop
                mock_loop.run_until_complete.return_value = "isolated_result"

                result = async_executor_uninit._run_isolated(test_coro())

                assert result == "isolated_result"
                mock_new_loop.assert_called_once()
                mock_set_loop.assert_called_once_with(mock_loop)
                mock_loop.run_until_complete.assert_called_once()
                mock_loop.close.assert_called_once()

    def test_run_isolated_closes_loop_on_success(self, async_executor_uninit):
        """测试协程成功执行后关闭事件循环。"""
        async def test_coro():
            return "result"

        with patch("graphedu.common.resource.async_executor.asyncio.new_event_loop") as mock_new_loop:
            with patch("graphedu.common.resource.async_executor.asyncio.set_event_loop"):
                mock_loop = MagicMock()
                mock_new_loop.return_value = mock_loop
                mock_loop.run_until_complete.return_value = "result"

                async_executor_uninit._run_isolated(test_coro())

                mock_loop.close.assert_called_once()

    def test_run_isolated_closes_loop_on_exception(self, async_executor_uninit):
        """测试协程失败时仍关闭事件循环。"""
        async def failing_coro():
            raise ValueError("Failed in isolated thread")

        with patch("graphedu.common.resource.async_executor.asyncio.new_event_loop") as mock_new_loop:
            with patch("graphedu.common.resource.async_executor.asyncio.set_event_loop"):
                mock_loop = MagicMock()
                mock_new_loop.return_value = mock_loop
                mock_loop.run_until_complete.side_effect = ValueError("Failed in isolated thread")

                with pytest.raises(ValueError, match="Failed in isolated thread"):
                    async_executor_uninit._run_isolated(failing_coro())

                # finally 块确保 loop 被关闭
                mock_loop.close.assert_called_once()

    def test_run_isolated_with_close_error(self, async_executor_uninit):
        """测试关闭事件循环失败时不影响结果。

        验证：
        - 即使关闭失败，协程的结果仍然返回
        - 关闭错误只记录警告
        """
        async def test_coro():
            return "result"

        with patch("graphedu.common.resource.async_executor.asyncio.new_event_loop") as mock_new_loop:
            with patch("graphedu.common.resource.async_executor.asyncio.set_event_loop"):
                mock_loop = MagicMock()
                mock_new_loop.return_value = mock_loop
                mock_loop.run_until_complete.return_value = "result"
                mock_loop.close.side_effect = RuntimeError("Close failed")

                # 应该成功返回结果，尽管关闭失败
                result = async_executor_uninit._run_isolated(test_coro())
                assert result == "result"

    def test_run_isolated_with_complex_async_operation(self, async_executor_uninit):
        """测试在隔离线程中执行复杂异步操作。"""
        async def complex_coro():
            # 模拟复杂的异步操作
            await asyncio.sleep(0)
            task1 = asyncio.create_task(asyncio.sleep(0, result="task1"))
            task2 = asyncio.create_task(asyncio.sleep(0, result="task2"))
            results = await asyncio.gather(task1, task2)
            return sum(results)  # ["task1", "task2"] -> "task1task2"

        with patch("graphedu.common.resource.async_executor.asyncio.new_event_loop") as mock_new_loop:
            with patch("graphedu.common.resource.async_executor.asyncio.set_event_loop"):
                mock_loop = MagicMock()
                mock_new_loop.return_value = mock_loop
                mock_loop.run_until_complete.return_value = "task1task2"

                result = async_executor_uninit._run_isolated(complex_coro())
                assert result == "task1task2"


# =============================================================================
# 测试类：边界情况
# =============================================================================


class TestAsyncExecutorEdgeCases:
    """测试 AsyncExecutor 的边界情况。"""

    def test_multiple_init_calls(self, async_executor_uninit):
        """测试多次调用 init。

        验证：
        - 可以重新初始化
        - 旧的 executor 被替换
        """
        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor1 = MagicMock(spec=ThreadPoolExecutor)
            mock_executor2 = MagicMock(spec=ThreadPoolExecutor)
            mock_tpe.side_effect = [mock_executor1, mock_executor2]

            async_executor_uninit.init(max_workers=5)
            first_executor = async_executor_uninit._executor

            async_executor_uninit.init(max_workers=10)
            second_executor = async_executor_uninit._executor

            assert first_executor is not second_executor
            assert async_executor_uninit.max_workers == 10

    def test_multiple_shutdown_calls(self, async_executor_uninit):
        """测试多次调用 shutdown。

        验证：
        - 多次调用是安全的
        - 不会抛出异常
        """
        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            mock_tpe.return_value = mock_executor

            async_executor_uninit.init()
            async_executor_uninit.shutdown()
            async_executor_uninit.shutdown()  # 第二次调用

            # shutdown 应该只被调用一次（第二次因为 _executor 是 None 而直接返回）
            mock_executor.shutdown.assert_called_once()

    def test_run_after_shutdown_raises_exception(self, async_executor_uninit):
        """测试 shutdown 后调用 run 抛出异常。

        验证：
        - shutdown 后不能执行新任务
        - 抛出 AsyncExecutorNotInitializedException
        """
        # 使用 mock 协程对象，避免创建真实的协程导致资源警告
        mock_coro = MagicMock(spec=Coroutine)

        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor"):
            async_executor_uninit.init()
            async_executor_uninit.shutdown()

            with pytest.raises(AsyncExecutorNotInitializedException):
                async_executor_uninit.run(mock_coro)

    def test_batch_after_shutdown_raises_exception(self, async_executor_uninit):
        """测试 shutdown 后调用 batch 抛出异常。"""
        # 使用 mock 协程对象，避免创建真实的协程导致资源警告
        mock_coro = MagicMock(spec=Coroutine)

        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor"):
            async_executor_uninit.init()
            async_executor_uninit.shutdown()

            with pytest.raises(AsyncExecutorNotInitializedException):
                async_executor_uninit.batch([mock_coro])

    def test_init_with_very_large_max_workers(self, async_executor_uninit):
        """测试使用非常大的 max_workers 初始化。

        验证：
        - 大数值也能正常处理
        """
        with patch("graphedu.common.resource.async_executor.concurrent.futures.ThreadPoolExecutor") as mock_tpe:
            mock_executor = MagicMock(spec=ThreadPoolExecutor)
            mock_tpe.return_value = mock_executor

            async_executor_uninit.init(max_workers=10000)

            assert async_executor_uninit.max_workers == 10000
            mock_tpe.assert_called_once_with(max_workers=10000, thread_name_prefix="AsyncExecutorThread")
