"""
Redis 客户端测试模块

测试同步和异步 Redis 客户端的功能，包括：
- 初始化和关闭
- 连接池管理
- Redis 客户端创建
- 异常处理
- 生命周期管理
"""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import ConnectionError, RedisError

from graphedu.common.config.modules.datasource.redis import RedisConfig
from graphedu.common.exceptions.common.resource import CacheConnectionException, CachePoolException
from graphedu.common.resource import AsyncRedisClient, RedisClient


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_connection_pool() -> Generator[MagicMock, None, None]:
    """Mock 同步 Redis 连接池"""
    pool = MagicMock()
    pool.disconnect = MagicMock()
    return pool


@pytest.fixture
def mock_async_connection_pool() -> Generator[AsyncMock, None, None]:
    """Mock 异步 Redis 连接池"""
    pool = AsyncMock()
    pool.disconnect = AsyncMock()
    return pool


@pytest.fixture
def mock_redis() -> Generator[MagicMock, None, None]:
    """Mock 同步 Redis 客户端"""
    redis = MagicMock(spec=Redis)
    redis.ping.return_value = True
    redis.set.return_value = True
    redis.get.return_value = b"test_value"
    redis.delete.return_value = 1
    return redis


@pytest.fixture
def mock_async_redis() -> Generator[AsyncMock, None, None]:
    """Mock 异步 Redis 客户端"""
    redis = AsyncMock(spec=AsyncRedis)
    redis.ping.return_value = True
    redis.set.return_value = True
    redis.get.return_value = b"test_value"
    redis.delete.return_value = 1
    return redis


@pytest.fixture
def redis_config_with_credentials() -> RedisConfig:
    """带凭据的 Redis 配置"""
    return RedisConfig(dsn="redis://:password@localhost:6379/0")


@pytest.fixture
def redis_config_without_credentials() -> RedisConfig:
    """不带凭据的 Redis 配置"""
    return RedisConfig(dsn="redis://localhost:6379/0")


# =============================================================================
# RedisClient 测试（同步客户端）
# =============================================================================

class TestRedisClientInit:
    """测试 RedisClient 初始化"""

    def test_init_with_valid_config(self, redis_config_without_credentials: RedisConfig, mock_connection_pool: MagicMock):
        """测试使用有效配置初始化客户端"""
        client = RedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.ConnectionPool.from_url', return_value=mock_connection_pool) as mock_from_url:
            result = client.init(redis_config_without_credentials)

            # 验证返回值是 self（支持链式调用）
            assert result is client
            # 验证配置已设置
            assert client.config == redis_config_without_credentials
            # 验证连接池已创建
            assert client._connection_pool == mock_connection_pool
            # 验证 from_url 被正确调用
            mock_from_url.assert_called_once_with(str(redis_config_without_credentials.dsn))

    def test_init_with_redis_error(self, redis_config_without_credentials: RedisConfig):
        """测试 Redis 连接错误时的异常处理"""
        client = RedisClient()
        error_msg = "Connection refused"

        with patch('graphedu.common.resource.modules.cache.redis.ConnectionPool.from_url') as mock_pool:
            mock_pool.side_effect = RedisError(error_msg)

            with pytest.raises(CacheConnectionException) as exc_info:
                client.init(redis_config_without_credentials)

            # 验证异常信息 - 参数存储在 kwargs 中
            assert exc_info.value.kwargs["cache_type"] == "Redis"
            assert error_msg in exc_info.value.kwargs["reason"]
            assert exc_info.value.kwargs["details"]["url"] == redis_config_without_credentials.dsn.host
            assert exc_info.value.kwargs["details"]["error_type"] == "RedisError"

    def test_init_with_connection_error(self, redis_config_without_credentials: RedisConfig):
        """测试网络连接错误时的异常处理"""
        client = RedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.ConnectionPool.from_url') as mock_pool:
            mock_pool.side_effect = ConnectionError("Network unreachable")

            with pytest.raises(CacheConnectionException) as exc_info:
                client.init(redis_config_without_credentials)

            assert exc_info.value.kwargs["cache_type"] == "Redis"
            assert "Network unreachable" in exc_info.value.kwargs["reason"]

    def test_init_with_unexpected_error(self, redis_config_without_credentials: RedisConfig):
        """测试初始化时的意外错误"""
        client = RedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.ConnectionPool.from_url') as mock_pool:
            mock_pool.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(CacheConnectionException) as exc_info:
                client.init(redis_config_without_credentials)

            assert exc_info.value.kwargs["cache_type"] == "Redis"
            assert exc_info.value.kwargs["details"]["error_type"] == "RuntimeError"


class TestRedisClientPool:
    """测试 RedisClient 连接池"""

    def test_pool_property_when_initialized(self, redis_config_without_credentials: RedisConfig, mock_connection_pool: MagicMock):
        """测试已初始化时获取连接池"""
        client = RedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.ConnectionPool.from_url', return_value=mock_connection_pool):
            client.init(redis_config_without_credentials)

            assert client.pool == mock_connection_pool

    def test_pool_property_when_not_initialized(self):
        """测试未初始化时获取连接池"""
        client = RedisClient()
        assert client.pool is None


class TestRedisClientGetRedis:
    """测试 RedisClient.get_redis 方法"""

    def test_get_redis_success(self, redis_config_without_credentials: RedisConfig,
                                mock_connection_pool: MagicMock, mock_redis: MagicMock):
        """测试成功获取 Redis 客户端"""
        client = RedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.ConnectionPool.from_url', return_value=mock_connection_pool):
            client.init(redis_config_without_credentials)

        with patch('graphedu.common.resource.modules.cache.redis.Redis', return_value=mock_redis) as mock_redis_class:
            redis = client.get_redis()

            # 验证返回了 Redis 实例
            assert redis == mock_redis
            # 验证 Redis 构造函数被正确调用
            mock_redis_class.assert_called_once_with(connection_pool=mock_connection_pool, decode_responses=True)

    def test_get_redis_without_init(self):
        """测试未初始化时获取 Redis 客户端"""
        client = RedisClient()

        with pytest.raises(CachePoolException) as exc_info:
            client.get_redis()

        assert exc_info.value.kwargs["operation"] == "create"
        assert "not initialized" in exc_info.value.kwargs["reason"]


class TestRedisClientShutdown:
    """测试 RedisClient.shutdown 方法"""

    def test_shutdown_success(self, redis_config_without_credentials: RedisConfig, mock_connection_pool: MagicMock):
        """测试成功关闭客户端"""
        client = RedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.ConnectionPool.from_url', return_value=mock_connection_pool):
            client.init(redis_config_without_credentials)

        # 调用 shutdown
        client.shutdown()

        # 验证 disconnect 被调用
        mock_connection_pool.disconnect.assert_called_once()
        # 验证连接池被清空
        assert client._connection_pool is None

    def test_shutdown_with_redis_error(self, redis_config_without_credentials: RedisConfig, mock_connection_pool: MagicMock):
        """测试关闭时发生 Redis 错误"""
        client = RedisClient()
        mock_connection_pool.disconnect.side_effect = RedisError("Disconnect failed")

        with patch('graphedu.common.resource.modules.cache.redis.ConnectionPool.from_url', return_value=mock_connection_pool):
            client.init(redis_config_without_credentials)

        with pytest.raises(CachePoolException) as exc_info:
            client.shutdown()

        assert exc_info.value.kwargs["operation"] == "disconnect"
        assert "Disconnect failed" in exc_info.value.kwargs["reason"]

    def test_shutdown_when_not_initialized(self):
        """测试未初始化时关闭客户端（应该静默成功）"""
        client = RedisClient()
        # 应该不抛出异常
        client.shutdown()
        assert client._connection_pool is None


class TestRedisClientAttributes:
    """测试 RedisClient 属性"""

    def test_mode_attribute(self):
        """测试 mode 属性"""
        client = RedisClient()
        assert client.mode == "sync"

    def test_config_initial_value(self):
        """测试 config 初始值"""
        client = RedisClient()
        assert client.config is None


# =============================================================================
# AsyncRedisClient 测试（异步客户端）
# =============================================================================

class TestAsyncRedisClientInit:
    """测试 AsyncRedisClient 初始化"""

    @pytest.mark.asyncio
    async def test_init_with_valid_config(self, redis_config_without_credentials: RedisConfig, mock_async_connection_pool: AsyncMock):
        """测试使用有效配置初始化客户端"""
        client = AsyncRedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.AsyncConnectionPool.from_url', return_value=mock_async_connection_pool) as mock_from_url:
            result = await client.init(redis_config_without_credentials)

            # 验证返回值是 self（支持链式调用）
            assert result is client
            # 验证配置已设置
            assert client.config == redis_config_without_credentials
            # 验证连接池已创建
            assert client._connection_pool == mock_async_connection_pool
            # 验证 from_url 被正确调用
            mock_from_url.assert_called_once_with(str(redis_config_without_credentials.dsn))

    @pytest.mark.asyncio
    async def test_init_with_dict_config(self, mock_async_connection_pool: AsyncMock):
        """测试使用字典配置初始化客户端"""
        client = AsyncRedisClient()
        config_dict = {'dsn': 'redis://localhost:6379/0'}

        with patch('graphedu.common.resource.modules.cache.redis.AsyncConnectionPool.from_url', return_value=mock_async_connection_pool):
            await client.init(config_dict)

            # 验证配置被正确转换为 RedisConfig
            assert isinstance(client.config, RedisConfig)
            assert str(client.config.dsn) == 'redis://localhost:6379/0'

    @pytest.mark.asyncio
    async def test_init_with_redis_error(self, redis_config_without_credentials: RedisConfig):
        """测试 Redis 连接错误时的异常处理"""
        client = AsyncRedisClient()
        error_msg = "Connection refused"

        with patch('graphedu.common.resource.modules.cache.redis.AsyncConnectionPool.from_url') as mock_pool:
            mock_pool.side_effect = RedisError(error_msg)

            with pytest.raises(CacheConnectionException) as exc_info:
                await client.init(redis_config_without_credentials)

            # 验证异常信息 - 参数存储在 kwargs 中
            assert exc_info.value.kwargs["cache_type"] == "Redis (Async)"
            assert error_msg in exc_info.value.kwargs["reason"]
            assert exc_info.value.kwargs["details"]["url"] == redis_config_without_credentials.dsn.host

    @pytest.mark.asyncio
    async def test_init_with_unexpected_error(self, redis_config_without_credentials: RedisConfig):
        """测试初始化时的意外错误"""
        client = AsyncRedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.AsyncConnectionPool.from_url') as mock_pool:
            mock_pool.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(CacheConnectionException) as exc_info:
                await client.init(redis_config_without_credentials)

            assert exc_info.value.kwargs["cache_type"] == "Redis (Async)"
            assert exc_info.value.kwargs["details"]["error_type"] == "RuntimeError"


class TestAsyncRedisClientPool:
    """测试 AsyncRedisClient 连接池"""

    @pytest.mark.asyncio
    async def test_pool_property_when_initialized(self, redis_config_without_credentials: RedisConfig, mock_async_connection_pool: AsyncMock):
        """测试已初始化时获取连接池"""
        client = AsyncRedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.AsyncConnectionPool.from_url', return_value=mock_async_connection_pool):
            await client.init(redis_config_without_credentials)

            assert client.pool == mock_async_connection_pool

    def test_pool_property_when_not_initialized(self):
        """测试未初始化时获取连接池"""
        client = AsyncRedisClient()
        assert client.pool is None


class TestAsyncRedisClientGetRedis:
    """测试 AsyncRedisClient.get_redis 方法"""

    @pytest.mark.asyncio
    async def test_get_redis_success(self, redis_config_without_credentials: RedisConfig,
                                      mock_async_connection_pool: AsyncMock, mock_async_redis: AsyncMock):
        """测试成功获取异步 Redis 客户端"""
        client = AsyncRedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.AsyncConnectionPool.from_url', return_value=mock_async_connection_pool):
            await client.init(redis_config_without_credentials)

        with patch('graphedu.common.resource.modules.cache.redis.AsyncRedis', return_value=mock_async_redis) as mock_redis_class:
            redis = client.get_redis()

            # 验证返回了 AsyncRedis 实例
            assert redis == mock_async_redis
            # 验证 AsyncRedis 构造函数被正确调用
            mock_redis_class.assert_called_once_with(connection_pool=mock_async_connection_pool)

    def test_get_redis_without_init(self):
        """测试未初始化时获取 Redis 客户端"""
        client = AsyncRedisClient()

        with pytest.raises(CachePoolException) as exc_info:
            client.get_redis()

        assert exc_info.value.kwargs["operation"] == "create"
        assert "not initialized" in exc_info.value.kwargs["reason"]


class TestAsyncRedisClientShutdown:
    """测试 AsyncRedisClient.shutdown 方法"""

    @pytest.mark.asyncio
    async def test_shutdown_success(self, redis_config_without_credentials: RedisConfig, mock_async_connection_pool: AsyncMock):
        """测试成功关闭客户端"""
        client = AsyncRedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.AsyncConnectionPool.from_url', return_value=mock_async_connection_pool):
            await client.init(redis_config_without_credentials)

        # 调用 shutdown
        await client.shutdown()

        # 验证 disconnect 被调用
        mock_async_connection_pool.disconnect.assert_called_once()
        # 验证连接池被清空
        assert client._connection_pool is None

    @pytest.mark.asyncio
    async def test_shutdown_with_redis_error(self, redis_config_without_credentials: RedisConfig, mock_async_connection_pool: AsyncMock):
        """测试关闭时发生 Redis 错误"""
        client = AsyncRedisClient()
        mock_async_connection_pool.disconnect.side_effect = RedisError("Disconnect failed")

        with patch('graphedu.common.resource.modules.cache.redis.AsyncConnectionPool.from_url', return_value=mock_async_connection_pool):
            await client.init(redis_config_without_credentials)

        with pytest.raises(CachePoolException) as exc_info:
            await client.shutdown()

        assert exc_info.value.kwargs["operation"] == "disconnect"
        assert "Disconnect failed" in exc_info.value.kwargs["reason"]

    @pytest.mark.asyncio
    async def test_shutdown_when_not_initialized(self):
        """测试未初始化时关闭客户端（应该静默成功）"""
        client = AsyncRedisClient()
        # 应该不抛出异常
        await client.shutdown()
        assert client._connection_pool is None


class TestAsyncRedisClientRedisGenerator:
    """测试 AsyncRedisClient.redis_generator 类方法"""

    def test_redis_generator(self, mock_async_redis: AsyncMock):
        """测试 redis_generator 类方法（用于依赖注入）"""
        client = AsyncRedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.AsyncRedis', return_value=mock_async_redis):  # noqa: SIM117
            with patch.object(client, 'get_redis', return_value=mock_async_redis):
                redis = AsyncRedisClient.redis_generator(client)

                # 验证返回的是 Redis 实例
                assert redis == mock_async_redis


class TestAsyncRedisClientAttributes:
    """测试 AsyncRedisClient 属性"""

    def test_mode_attribute(self):
        """测试 mode 属性"""
        client = AsyncRedisClient()
        assert client.mode == "async"

    def test_config_initial_value(self):
        """测试 config 初始值"""
        client = AsyncRedisClient()
        assert client.config is None


# =============================================================================
# 集成测试 - 生命周期管理
# =============================================================================

class TestRedisClientLifecycle:
    """测试同步 Redis 客户端的生命周期"""

    def test_full_lifecycle(self, redis_config_without_credentials: RedisConfig,
                            mock_connection_pool: MagicMock, mock_redis: MagicMock):
        """测试完整的生命周期：初始化 -> 使用 -> 关闭"""
        client = RedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.ConnectionPool.from_url', return_value=mock_connection_pool):
            # 1. 初始化
            client.init(redis_config_without_credentials)
            assert client._connection_pool is not None
            assert client.config == redis_config_without_credentials

            # 2. 使用
            with patch('graphedu.common.resource.modules.cache.redis.Redis', return_value=mock_redis):
                redis = client.get_redis()
                assert redis == mock_redis

            # 3. 关闭
            client.shutdown()
            assert client._connection_pool is None

    def test_reinitialize_after_shutdown(self, redis_config_without_credentials: RedisConfig,
                                         mock_connection_pool: MagicMock):
        """测试关闭后重新初始化"""
        client = RedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.ConnectionPool.from_url', return_value=mock_connection_pool):
            # 第一次初始化
            client.init(redis_config_without_credentials)
            assert client._connection_pool is not None

            # 关闭
            client.shutdown()
            assert client._connection_pool is None

            # 重新初始化
            client.init(redis_config_without_credentials)
            assert client._connection_pool is not None


class TestAsyncRedisClientLifecycle:
    """测试异步 Redis 客户端的生命周期"""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, redis_config_without_credentials: RedisConfig,
                                   mock_async_connection_pool: AsyncMock, mock_async_redis: AsyncMock):
        """测试完整的生命周期：初始化 -> 使用 -> 关闭"""
        client = AsyncRedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.AsyncConnectionPool.from_url', return_value=mock_async_connection_pool):
            # 1. 初始化
            await client.init(redis_config_without_credentials)
            assert client._connection_pool is not None
            assert client.config == redis_config_without_credentials

            # 2. 使用
            with patch('graphedu.common.resource.modules.cache.redis.AsyncRedis', return_value=mock_async_redis):
                redis = client.get_redis()
                assert redis == mock_async_redis

            # 3. 关闭
            await client.shutdown()
            assert client._connection_pool is None

    @pytest.mark.asyncio
    async def test_reinitialize_after_shutdown(self, redis_config_without_credentials: RedisConfig,
                                               mock_async_connection_pool: AsyncMock):
        """测试关闭后重新初始化"""
        client = AsyncRedisClient()

        with patch('graphedu.common.resource.modules.cache.redis.AsyncConnectionPool.from_url', return_value=mock_async_connection_pool):
            # 第一次初始化
            await client.init(redis_config_without_credentials)
            assert client._connection_pool is not None

            # 关闭
            await client.shutdown()
            assert client._connection_pool is None

            # 重新初始化
            await client.init(redis_config_without_credentials)
            assert client._connection_pool is not None
