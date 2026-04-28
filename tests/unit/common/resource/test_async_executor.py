"""
async_executor.py 资源类测试

测试 AsyncExecutor 资源类的功能，包括初始化、运行协程、批量处理和关闭。
"""

import asyncio

import pytest

from graphedu.common.exceptions import (
    AsyncExecutorNotInitializedException,
    AsyncExecutorValidationException,
)
from graphedu.common.resource.modules.infrastructure.async_executor import AsyncExecutor


class TestAsyncExecutorInit:
    """AsyncExecutor 初始化测试"""

    def test_init_with_default_max_workers(self):
        """测试使用默认 max_workers 初始化"""
        executor = AsyncExecutor()
        executor.init()

        assert executor.max_workers == 5
        assert executor._executor is not None

    def test_init_with_custom_max_workers(self):
        """测试使用自定义 max_workers 初始化"""
        executor = AsyncExecutor()
        executor.init(max_workers=10)

        assert executor.max_workers == 10
        assert executor._executor is not None

    def test_init_with_none_max_workers(self):
        """测试使用 None 作为 max_workers（应使用默认值）"""
        executor = AsyncExecutor()
        executor.init(max_workers=None)

        assert executor.max_workers == 5

    def test_init_with_invalid_max_workers_zero(self):
        """测试使用 0 作为 max_workers（应该抛出异常）"""
        executor = AsyncExecutor()

        with pytest.raises(AsyncExecutorValidationException) as exc_info:
            executor.init(max_workers=0)

        assert "max_workers" in str(exc_info.value)

    def test_init_with_invalid_max_workers_negative(self):
        """测试使用负数作为 max_workers（应该抛出异常）"""
        executor = AsyncExecutor()

        with pytest.raises(AsyncExecutorValidationException) as exc_info:
            executor.init(max_workers=-1)

        assert "max_workers" in str(exc_info.value)

    def test_init_returns_self(self):
        """测试 init 返回 self"""
        executor = AsyncExecutor()
        result = executor.init(max_workers=3)

        assert result is executor


class TestAsyncExecutorRun:
    """AsyncExecutor.run 方法测试"""

    def test_run_async_function(self):
        """测试运行异步函数"""
        executor = AsyncExecutor()
        executor.init()

        async def sample_async():
            await asyncio.sleep(0.01)
            return 42

        result = executor.run(sample_async())
        assert result == 42

        executor.shutdown()

    def test_run_async_function_with_params(self):
        """测试运行带参数的异步函数"""
        executor = AsyncExecutor()
        executor.init()

        async def add(a: int, b: int) -> int:
            await asyncio.sleep(0.01)
            return a + b

        result = executor.run(add(10, 20))
        assert result == 30

        executor.shutdown()

    def test_run_without_init(self):
        """测试在未初始化的情况下调用 run（应该抛出异常）"""
        executor = AsyncExecutor()

        async def sample_async():
            return 42

        with pytest.raises(AsyncExecutorNotInitializedException):
            executor.run(sample_async())

    def test_run_multiple_times(self):
        """测试多次运行异步函数"""
        executor = AsyncExecutor()
        executor.init()

        async def get_value(value: int):
            await asyncio.sleep(0.01)
            return value * 2

        for i in range(5):
            result = executor.run(get_value(i))
            assert result == i * 2

        executor.shutdown()

    def test_run_with_exception(self):
        """测试运行会抛出异常的异步函数"""
        executor = AsyncExecutor()
        executor.init()

        async def raise_exception():
            await asyncio.sleep(0.01)
            raise ValueError("Test exception")

        with pytest.raises(ValueError, match="Test exception"):
            executor.run(raise_exception())

        executor.shutdown()

    def test_run_with_complex_object(self):
        """测试运行返回复杂对象的异步函数"""
        executor = AsyncExecutor()
        executor.init()

        async def create_dict():
            await asyncio.sleep(0.01)
            return {"key": "value", "list": [1, 2, 3]}

        result = executor.run(create_dict())
        assert result == {"key": "value", "list": [1, 2, 3]}

        executor.shutdown()


class TestAsyncExecutorBatch:
    """AsyncExecutor.batch 方法测试"""

    def test_batch_multiple_coroutines(self):
        """测试批量运行多个协程"""
        executor = AsyncExecutor()
        executor.init()

        async def task(value: int):
            await asyncio.sleep(0.01)
            return value * 2

        coros = [task(i) for i in range(5)]
        results = executor.batch(coros)

        assert results == [0, 2, 4, 6, 8]

        executor.shutdown()

    def test_batch_with_empty_list(self):
        """测试批量运行空列表（应该抛出异常）"""
        executor = AsyncExecutor()
        executor.init()

        with pytest.raises(AsyncExecutorValidationException) as exc_info:
            executor.batch([])

        assert "coros" in str(exc_info.value).lower()

        executor.shutdown()

    def test_batch_without_init(self):
        """测试在未初始化的情况下调用 batch（应该抛出异常）"""
        executor = AsyncExecutor()

        async def sample():
            return 42

        with pytest.raises(AsyncExecutorNotInitializedException):
            executor.batch([sample()])

    def test_batch_with_exceptions(self):
        """测试批量运行，部分协程抛出异常"""
        executor = AsyncExecutor()
        executor.init()

        async def task(value: int):
            await asyncio.sleep(0.01)
            if value == 2:
                raise ValueError("Value is 2")
            return value * 2

        coros = [task(i) for i in range(5)]

        # 应该抛出异常
        with pytest.raises(ValueError, match="Value is 2"):
            executor.batch(coros)

        executor.shutdown()

    def test_batch_order_preserved(self):
        """测试批量运行结果顺序保持不变"""
        executor = AsyncExecutor()
        executor.init()

        async def delayed_task(value: int, delay: float):
            await asyncio.sleep(delay)
            return value

        # 注意：故意使用不同的延迟顺序
        coros = [
            delayed_task(1, 0.03),
            delayed_task(2, 0.01),
            delayed_task(3, 0.02),
        ]

        results = executor.batch(coros)

        # 结果应该按照输入顺序返回
        assert results == [1, 2, 3]

        executor.shutdown()

    def test_batch_large_number_of_coroutines(self):
        """测试批量运行大量协程"""
        executor = AsyncExecutor()
        executor.init(max_workers=10)

        async def simple_task(value: int):
            await asyncio.sleep(0.001)
            return value

        coros = [simple_task(i) for i in range(100)]
        results = executor.batch(coros)

        assert len(results) == 100
        assert results == list(range(100))

        executor.shutdown()


class TestAsyncExecutorShutdown:
    """AsyncExecutor.shutdown 方法测试"""

    def test_shutdown_after_init(self):
        """测试初始化后关闭"""
        executor = AsyncExecutor()
        executor.init()

        assert executor._executor is not None

        executor.shutdown()

        assert executor._executor is None

    def test_shutdown_without_init(self):
        """测试在未初始化的情况下关闭（应该不抛出异常）"""
        executor = AsyncExecutor()

        # 应该可以正常关闭，只是记录警告
        executor.shutdown()

        assert executor._executor is None

    def test_shutdown_twice(self):
        """测试多次关闭"""
        executor = AsyncExecutor()
        executor.init()

        executor.shutdown()
        assert executor._executor is None

        # 第二次关闭应该不抛出异常
        executor.shutdown()
        assert executor._executor is None

    def test_cannot_use_after_shutdown(self):
        """测试关闭后不能使用（应该抛出异常）"""
        executor = AsyncExecutor()
        executor.init()

        async def sample():
            return 42

        executor.shutdown()

        with pytest.raises(AsyncExecutorNotInitializedException):
            executor.run(sample())


class TestAsyncExecutorEdgeCases:
    """AsyncExecutor 边界情况测试"""

    def test_run_nested_async_functions(self):
        """测试运行嵌套的异步函数"""
        executor = AsyncExecutor()
        executor.init()

        async def inner():
            await asyncio.sleep(0.01)
            return "inner"

        async def outer():
            await asyncio.sleep(0.01)
            result = await inner()
            return f"outer-{result}"

        result = executor.run(outer())
        assert result == "outer-inner"

        executor.shutdown()

    def test_run_with_await_in_loop(self):
        """测试在循环中使用 await"""
        executor = AsyncExecutor()
        executor.init()

        async def collect_results():
            results = []
            for i in range(3):
                await asyncio.sleep(0.01)
                results.append(i)
            return results

        result = executor.run(collect_results())
        assert result == [0, 1, 2]

        executor.shutdown()

    def test_run_with_timeout_simulation(self):
        """测试运行带超时模拟的协程"""
        executor = AsyncExecutor()
        executor.init()

        async def slow_task():
            await asyncio.sleep(0.1)
            return "done"

        # 这应该正常完成（不超时）
        result = executor.run(slow_task())
        assert result == "done"

        executor.shutdown()

    def test_batch_with_single_coroutine(self):
        """测试批量运行单个协程"""
        executor = AsyncExecutor()
        executor.init()

        async def single_task():
            await asyncio.sleep(0.01)
            return 42

        results = executor.batch([single_task()])

        assert results == [42]

        executor.shutdown()


class TestAsyncExecutorIntegration:
    """AsyncExecutor 集成测试"""

    def test_full_lifecycle(self):
        """测试完整的生命周期"""
        executor = AsyncExecutor()

        # 初始状态
        assert executor._executor is None

        # 初始化
        executor.init(max_workers=3)
        assert executor.max_workers == 3
        assert executor._executor is not None

        # 使用
        async def task(value):
            await asyncio.sleep(0.01)
            return value ** 2

        result = executor.run(task(5))
        assert result == 25

        batch_results = executor.batch([task(i) for i in range(3)])
        assert batch_results == [0, 1, 4]

        # 关闭
        executor.shutdown()
        assert executor._executor is None

    def test_reinitialize_after_shutdown(self):
        """测试关闭后重新初始化"""
        executor = AsyncExecutor()

        # 第一次初始化和使用
        executor.init(max_workers=2)
        assert executor.max_workers == 2

        async def task1():
            return "first"

        result = executor.run(task1())
        assert result == "first"

        executor.shutdown()

        # 第二次初始化和使用
        executor.init(max_workers=5)
        assert executor.max_workers == 5

        async def task2():
            return "second"

        result = executor.run(task2())
        assert result == "second"

        executor.shutdown()
