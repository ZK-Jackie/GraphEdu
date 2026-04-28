"""
测试辅助工具模块

提供测试中使用的辅助函数、Mock 工厂和测试工具类。
"""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest


class MockFactories:
    """Mock 对象工厂类"""

    @staticmethod
    def create_mock_pg_session() -> Mock:
        """创建模拟的 PostgreSQL Session"""
        session = Mock()
        session.commit.return_value = None
        session.rollback.return_value = None
        session.close.return_value = None
        session.query.return_value = Mock()
        return session

    @staticmethod
    def create_mock_async_pg_session() -> AsyncMock:
        """创建模拟的异步 PostgreSQL Session"""
        session = AsyncMock()
        session.commit.return_value = None
        session.rollback.return_value = None
        session.close.return_value = None
        session.execute.return_value = Mock()
        return session

    @staticmethod
    def create_mock_redis_connection() -> Mock:
        """创建模拟的 Redis 连接"""
        redis = Mock()
        redis.ping.return_value = True
        redis.get.return_value = b"test_value"
        redis.set.return_value = True
        redis.delete.return_value = 1
        redis.exists.return_value = 1
        redis.hget.return_value = b"test_hash_value"
        redis.hset.return_value = True
        redis.hdel.return_value = 1
        redis.expire.return_value = True
        return redis

    @staticmethod
    def create_mock_async_redis_connection() -> AsyncMock:
        """创建模拟的异步 Redis 连接"""
        redis = AsyncMock()
        redis.ping.return_value = True
        redis.get.return_value = b"test_value"
        redis.set.return_value = True
        redis.delete.return_value = 1
        redis.exists.return_value = 1
        redis.hget.return_value = b"test_hash_value"
        redis.hset.return_value = True
        redis.hdel.return_value = 1
        redis.expire.return_value = True
        return redis

    @staticmethod
    def create_mock_neo4j_driver() -> Mock:
        """创建模拟的 Neo4j 驱动"""
        driver = Mock()
        driver.verify_connectivity.return_value = None
        driver.execute_query.return_value = (
            [{"key": "value"}],
            Mock(counters=Mock(nodes_created=1)),
            ["key"],
        )
        driver.close.return_value = None
        return driver

    @staticmethod
    def create_mock_async_neo4j_driver() -> AsyncMock:
        """创建模拟的异步 Neo4j 驱动"""
        driver = AsyncMock()
        driver.verify_connectivity.return_value = None
        driver.execute_query.return_value = (
            [{"key": "value"}],
            Mock(counters=Mock(nodes_created=1)),
            ["key"],
        )
        driver.close.return_value = None
        return driver

    @staticmethod
    def create_mock_s3_client() -> Mock:
        """创建模拟的 S3 客户端"""
        client = Mock()
        client.upload_file.return_value = None
        client.download_file.return_value = None
        client.upload_fileobj.return_value = None
        client.delete_object.return_value = None
        client.head_object.return_value = {"ETag": '"test-etag-123"'}
        client.generate_presigned_url.return_value = "http://localhost:9000/bucket/object?params"
        return client

    @staticmethod
    def create_mock_httpx_response(status_code: int = 200, text: str = '{"success": true}') -> Mock:
        """创建模拟的 httpx 响应"""
        response = Mock()
        response.status_code = status_code
        response.text = text
        response.content = text.encode()
        response.json.return_value = {"success": True}
        return response


class AsyncTestHelpers:
    """异步测试辅助类"""

    @staticmethod
    @asynccontextmanager
    async def create_async_temp_file(content: bytes, suffix: str = ".tmp") -> AsyncGenerator[Path]:
        """
        创建临时文件并返回路径（异步上下文管理器）

        Args:
            content: 文件内容
            suffix: 文件后缀

        Yields:
            Path: 临时文件路径
        """
        import tempfile

        from aiofiles import open as aio_open

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            temp_path = Path(f.name)

        try:
            async with aio_open(temp_path, 'wb') as f:
                await f.write(content)
            yield temp_path
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @staticmethod
    async def run_async(coro):
        """
        运行异步协程并返回结果

        Args:
            coro: 要执行的协程

        Returns:
            协程的返回值
        """
        return await coro


class TestAssertions:
    """测试断言辅助类"""

    @staticmethod
    def assert_resource_initialized(resource: Any) -> None:
        """
        断言资源已正确初始化

        Args:
            resource: 资源对象
        """
        assert resource is not None
        # 根据资源类型检查特定属性
        if hasattr(resource, '_pg_engine'):
            assert resource._pg_engine is not None
        elif hasattr(resource, '_connection_pool'):
            assert resource._connection_pool is not None
        elif hasattr(resource, '_driver'):
            assert resource._driver is not None
        elif hasattr(resource, '_s3_client'):
            assert resource._s3_client is not None
        elif hasattr(resource, '_client'):
            assert resource._client is not None

    @staticmethod
    def assert_resource_shutdown(resource: Any) -> None:
        """
        断言资源已正确关闭

        Args:
            resource: 资源对象
        """
        # 根据资源类型检查特定属性
        if hasattr(resource, '_pg_engine'):
            assert resource._pg_engine is None
        elif hasattr(resource, '_connection_pool'):
            assert resource._connection_pool is None
        elif hasattr(resource, '_driver'):
            assert resource._driver is None
        elif hasattr(resource, '_s3_client'):
            assert resource._s3_client is None
        elif hasattr(resource, '_client'):
            assert resource._client is None


class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def random_string(length: int = 10) -> str:
        """生成随机字符串"""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def random_bytes(size: int = 1024) -> bytes:
        """生成随机字节"""
        import os
        return os.urandom(size)

    @staticmethod
    def create_bytesio(content: bytes | None = None) -> BytesIO:
        """创建 BytesIO 对象"""
        return BytesIO(content or b"test content")

    @staticmethod
    def create_sample_users(count: int = 3) -> list[dict]:
        """创建示例用户数据"""
        return [
            {
                "id": i,
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "role_id": 2,
            }
            for i in range(1, count + 1)
        ]

    @staticmethod
    def create_sample_files(count: int = 3) -> list[str]:
        """创建示例文件名列表"""
        return [f"file{i}.txt" for i in range(1, count + 1)]


class ExceptionTestHelpers:
    """异常测试辅助类"""

    @staticmethod
    def assert_exception_raised(
        exception_class: type[Exception],
        callable_obj: callable,
        *args,
        **kwargs
    ) -> Exception:
        """
        断言特定异常被抛出并返回异常实例

        Args:
            exception_class: 期望的异常类
            callable_obj: 可调用对象
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Exception: 捕获的异常实例
        """
        with pytest.raises(exception_class) as exc_info:
            callable_obj(*args, **kwargs)
        return exc_info.value

    @staticmethod
    def assert_exception_attributes(
        exception: Exception,
        expected_attributes: dict[str, Any]
    ) -> None:
        """
        断言异常具有预期的属性

        Args:
            exception: 异常实例
            expected_attributes: 期望的属性字典
        """
        for attr_name, expected_value in expected_attributes.items():
            actual_value = getattr(exception, attr_name, None)
            assert actual_value == expected_value, (
                f"异常属性 {attr_name} 不匹配: "
                f"期望 {expected_value}, 实际 {actual_value}"
            )


class ResourceTestHelpers:
    """资源测试专用辅助类"""

    @staticmethod
    def create_temp_config_file(config_dict: dict, file_path: Path) -> None:
        """
        创建临时配置文件

        Args:
            config_dict: 配置字典
            file_path: 文件路径
        """
        import json
        with open(file_path, 'w') as f:
            json.dump(config_dict, f)

    @staticmethod
    def cleanup_resource(resource: Any) -> None:
        """
        清理资源（如果支持 shutdown）

        Args:
            resource: 资源对象
        """
        if hasattr(resource, 'shutdown'):
            try:
                if asyncio.iscoroutinefunction(resource.shutdown):
                    # 如果是异步方法，需要在事件循环中运行
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果事件循环正在运行，创建任务
                        asyncio.create_task(resource.shutdown())
                    else:
                        # 如果事件循环没有运行，直接运行
                        loop.run_until_complete(resource.shutdown())
                else:
                    # 同步方法直接调用
                    resource.shutdown()
            except Exception:
                # 忽略清理过程中的异常
                pass
