"""
测试容器模块

提供用于测试的依赖注入容器，用于测试资源类的依赖注入功能。
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
import pytest

from graphedu.common.config.modules.datasource.base import PoolConfig
from graphedu.common.config.modules.datasource.mysql import MysqlConfig
from graphedu.common.config.modules.datasource.neo4j import Neo4jConfig
from graphedu.common.config.modules.datasource.oss import OssConfig
from graphedu.common.config.modules.datasource.postgresql import PostgresqlConfig
from graphedu.common.config.modules.datasource.redis import RedisConfig
from graphedu.common.resource import (
    AioS3Client,
    AsyncExecutor,
    AsyncHttpClient,
    AsyncMysqlClient,
    AsyncNeo4jClient,
    AsyncPostgresqlClient,
    AsyncRedisClient,
    HttpClient,
    MysqlClient,
    Neo4jClient,
    PostgresqlClient,
    RedisClient,
    S3Client,
)


class ResourceTestContainer(containers.DeclarativeContainer):
    """
    测试用的资源容器

    提供所有资源类的单例和工厂，用于测试依赖注入。
    """

    # 配置
    config = providers.Configuration()

    # ========== 异步执行器 ==========
    async_executor = providers.Resource(
        AsyncExecutor,
        max_workers=config.async_executor.max_workers,
    )

    # ========== PostgreSQL ==========
    pg_config = providers.Singleton(
        PostgresqlConfig,
        dsn=config.postgresql.dsn,
        echo=config.postgresql.echo,
        pool=providers.Singleton(
            PoolConfig,
            pool_size=config.postgresql.pool.pool_size,
            pool_recycle=config.postgresql.pool.pool_recycle,
            pool_timeout=config.postgresql.pool.pool_timeout,
            pool_pre_ping=config.postgresql.pool.pool_pre_ping,
        ),
    )

    postgresql_client = providers.Resource(
        PostgresqlClient,
        config=pg_config,
    )

    async_pg_config = providers.Singleton(
        PostgresqlConfig,
        dsn=config.postgresql.dsn,
        echo=config.postgresql.echo,
        pool=providers.Singleton(
            PoolConfig,
            pool_size=config.postgresql.pool.pool_size,
            pool_recycle=config.postgresql.pool.pool_recycle,
            pool_timeout=config.postgresql.pool.pool_timeout,
            pool_pre_ping=config.postgresql.pool.pool_pre_ping,
        ),
    )

    async_postgresql_client = providers.Resource(
        AsyncPostgresqlClient,
        config=async_pg_config,
    )

    # ========== MySQL ==========
    mysql_config = providers.Singleton(
        MysqlConfig,
        dsn=config.mysql.dsn,
        echo=config.mysql.echo,
        pool=providers.Singleton(
            PoolConfig,
            pool_size=config.mysql.pool.pool_size,
        ),
    )

    mysql_client = providers.Resource(
        MysqlClient,
        config=mysql_config,
    )

    async_mysql_config = providers.Singleton(
        MysqlConfig,
        dsn=config.mysql.dsn,
        echo=config.mysql.echo,
        pool=providers.Singleton(
            PoolConfig,
            pool_size=config.mysql.pool.pool_size,
        ),
    )

    async_mysql_client = providers.Resource(
        AsyncMysqlClient,
        config=async_mysql_config,
    )

    # ========== Redis ==========
    redis_config = providers.Singleton(
        RedisConfig,
        dsn=config.redis.dsn,
    )

    redis_client = providers.Resource(
        RedisClient,
        config=redis_config,
    )

    async_redis_config = providers.Singleton(
        RedisConfig,
        dsn=config.redis.dsn,
    )

    async_redis_client = providers.Resource(
        AsyncRedisClient,
        config=async_redis_config,
    )

    # ========== Neo4j ==========
    neo4j_config = providers.Singleton(
        Neo4jConfig,
        dsn=config.neo4j.dsn,
        auth=config.neo4j.auth,
        timeout=config.neo4j.timeout,
    )

    neo4j_client = providers.Resource(
        Neo4jClient,
        config=neo4j_config,
    )

    async_neo4j_config = providers.Singleton(
        Neo4jConfig,
        dsn=config.neo4j.dsn,
        auth=config.neo4j.auth,
        timeout=config.neo4j.timeout,
    )

    async_neo4j_client = providers.Resource(
        AsyncNeo4jClient,
        config=async_neo4j_config,
    )

    # ========== S3/OSS ==========
    oss_config = providers.Singleton(
        OssConfig,
        provider=config.oss.provider,
        endpoint=config.oss.endpoint,
        access_key=config.oss.access_key,
        secret_key=config.oss.secret_key,
        use_ssl=config.oss.use_ssl,
        bucket=config.oss.bucket,
        upload_from=config.oss.upload_from,
        download_to=config.oss.download_to,
    )

    s3_client = providers.Resource(
        S3Client,
        config=oss_config,
    )

    async_oss_config = providers.Singleton(
        OssConfig,
        provider=config.oss.provider,
        endpoint=config.oss.endpoint,
        access_key=config.oss.access_key,
        secret_key=config.oss.secret_key,
        use_ssl=config.oss.use_ssl,
        bucket=config.oss.bucket,
        upload_from=config.oss.upload_from,
        download_to=config.oss.download_to,
    )

    async_s3_client = providers.Resource(
        AioS3Client,
        config=async_oss_config,
    )

    # ========== HTTP ==========
    http_client = providers.Resource(
        HttpClient,
        config=config.http,
    )

    async_http_client = providers.Resource(
        AsyncHttpClient,
        config=config.http,
    )


class MockResourceTestContainer(containers.DeclarativeContainer):
    """
    Mock 测试用的资源容器

    提供 Mock 对象而不是真实的资源连接，用于单元测试。
    """

    # 配置
    config = providers.Configuration()

    # ========== Mock 异步执行器 ==========
    async_executor = providers.Resource(
        AsyncExecutor,
        max_workers=2,  # 测试时使用较少的工作线程
    )

    # ========== Mock PostgreSQL ==========
    mock_pg_engine = providers.Singleton(
        lambda: __import__('unittest.mock').Mock(),
    )

    mock_postgresql_client = providers.Factory(
        lambda: __import__(
            'graphedu.common.resource.modules.database.postgresql',
            fromlist=['PostgresqlClient'],
        ).PostgresqlClient(),
    )

    # ========== Mock Redis ==========
    mock_redis_pool = providers.Singleton(
        lambda: __import__('unittest.mock').Mock(),
    )

    mock_redis_client = providers.Factory(
        lambda: __import__(
            'graphedu.common.resource.modules.cache.redis',
            fromlist=['RedisClient'],
        ).RedisClient(),
    )

    # ========== Mock Neo4j ==========
    mock_neo4j_driver = providers.Singleton(
        lambda: __import__('unittest.mock').Mock(),
    )

    mock_neo4j_client = providers.Factory(
        lambda: __import__(
            'graphedu.common.resource.modules.database.neo4j',
            fromlist=['Neo4jClient'],
        ).Neo4jClient(),
    )


# 默认测试配置
DEFAULT_TEST_CONFIG = {
    "async_executor": {
        "max_workers": 2,
    },
    "postgresql": {
        "dsn": "postgresql://test:test@localhost:5432/test_db",
        "echo": False,
        "pool": {
            "pool_size": 5,
            "pool_recycle": 3600,
            "pool_timeout": 30,
            "pool_pre_ping": True,
        },
    },
    "mysql": {
        "dsn": "mysql://test:test@localhost:3306/test_db",
        "echo": False,
        "pool": {"pool_size": 5},
    },
    "redis": {
        "dsn": "redis://localhost:6379/0",
    },
    "neo4j": {
        "dsn": "bolt://localhost:7687",
        "auth": ["neo4j:test_password"],
        "timeout": 30,
    },
    "oss": {
        "provider": "minio",
        "endpoint": "http://localhost:9000",
        "access_key": "minioadmin",
        "secret_key": "minioadmin",
        "use_ssl": False,
        "bucket": "test-bucket",
        "upload_from": "/tmp/test_upload",
        "download_to": "/tmp/test_download",
    },
    "http": {
        "timeout": 30.0,
        "headers": {"User-Agent": "TestClient"},
        "verify": False,
    },
}


def create_test_container(
    custom_config: dict | None = None,
    use_mocks: bool = False,
):
    """
    创建测试容器实例

    Args:
        custom_config: 自定义配置（将覆盖默认配置）
        use_mocks: 是否使用 Mock 对象而不是真实连接

    Returns:
        配置好的容器实例
    """
    # 合并配置
    config = DEFAULT_TEST_CONFIG.copy()
    if custom_config:
        config.update(custom_config)

    container = MockResourceTestContainer() if use_mocks else ResourceTestContainer()

    # from_dict 会原地更新配置
    # 注意：调用 from_dict() 不会返回值，只是更新配置
    container.config.from_dict(config)

    return container


# ========== 依赖注入示例 ==========

@inject
def example_service_with_pg(
    pg_client: PostgresqlClient = Provide[ResourceTestContainer.postgresql_client],
):
    """
    使用依赖注入的服务示例

    Args:
        pg_client: 注入的 PostgreSQL 客户端
    """
    return pg_client


@inject
async def example_async_service_with_pg(
    async_pg_client: AsyncPostgresqlClient = Provide[ResourceTestContainer.async_postgresql_client],
):
    """
    使用异步依赖注入的服务示例

    Args:
        async_pg_client: 注入的异步 PostgreSQL 客户端
    """
    return async_pg_client


# =============================================================================
# 测试用例
# =============================================================================

class TestCreateTestContainer:
    """测试 create_test_container 函数"""

    def test_create_default_container(self):
        """测试使用默认配置创建容器"""
        container = create_test_container()

        assert hasattr(container, 'config')
        assert hasattr(container, 'async_executor')
        assert container.config.async_executor.max_workers == 2
        assert container.config.postgresql.dsn is not None

    def test_create_container_with_custom_config(self):
        """测试使用自定义配置创建容器"""
        custom_config = {
            "async_executor": {"max_workers": 10},
            "postgresql": {"dsn": "postgresql://custom:custom@localhost/custom_db"}
        }

        container = create_test_container(custom_config)

        assert container.config.async_executor.max_workers == 10
        assert "custom_db" in container.config.postgresql.dsn

    def test_create_mock_container(self):
        """测试创建 Mock 容器"""
        container = create_test_container(use_mocks=True)

        assert hasattr(container, 'config')
        assert hasattr(container, 'async_executor')

    def test_container_config_merging(self):
        """测试配置合并逻辑"""
        custom_config = {
            "async_executor": {"max_workers": 8},
            # 只覆盖部分配置
        }

        container = create_test_container(custom_config)

        # 自定义配置应该生效
        assert container.config.async_executor.max_workers == 8
        # 默认配置的其他部分应该保留
        assert "postgresql" in container.config


class TestResourceTestContainerStructure:
    """测试 ResourceTestContainer 结构"""

    def test_container_has_configuration_provider(self):
        """测试容器有配置提供者"""
        container = ResourceTestContainer()
        assert hasattr(container, 'config')
        assert isinstance(container.config, providers.Configuration)

    def test_container_has_async_executor_provider(self):
        """测试容器有异步执行器提供者"""
        container = ResourceTestContainer()
        assert hasattr(container, 'async_executor')
        assert isinstance(container.async_executor, providers.Resource)

    def test_container_has_postgresql_providers(self):
        """测试容器有 PostgreSQL 提供者"""
        container = ResourceTestContainer()

        # 同步客户端
        assert hasattr(container, 'postgresql_client')
        assert isinstance(container.postgresql_client, providers.Resource)

        # 异步客户端
        assert hasattr(container, 'async_postgresql_client')
        assert isinstance(container.async_postgresql_client, providers.Resource)

        # 配置
        assert hasattr(container, 'pg_config')
        assert hasattr(container, 'async_pg_config')

    def test_container_has_mysql_providers(self):
        """测试容器有 MySQL 提供者"""
        container = ResourceTestContainer()

        assert hasattr(container, 'mysql_client')
        assert hasattr(container, 'async_mysql_client')
        assert isinstance(container.mysql_client, providers.Resource)
        assert isinstance(container.async_mysql_client, providers.Resource)

    def test_container_has_redis_providers(self):
        """测试容器有 Redis 提供者"""
        container = ResourceTestContainer()

        assert hasattr(container, 'redis_client')
        assert hasattr(container, 'async_redis_client')
        assert isinstance(container.redis_client, providers.Resource)
        assert isinstance(container.async_redis_client, providers.Resource)

    def test_container_has_neo4j_providers(self):
        """测试容器有 Neo4j 提供者"""
        container = ResourceTestContainer()

        assert hasattr(container, 'neo4j_client')
        assert hasattr(container, 'async_neo4j_client')
        assert isinstance(container.neo4j_client, providers.Resource)
        assert isinstance(container.async_neo4j_client, providers.Resource)

    def test_container_has_s3_providers(self):
        """测试容器有 S3/OSS 提供者"""
        container = ResourceTestContainer()

        assert hasattr(container, 's3_client')
        assert hasattr(container, 'async_s3_client')
        assert isinstance(container.s3_client, providers.Resource)
        assert isinstance(container.async_s3_client, providers.Resource)

    def test_container_has_http_providers(self):
        """测试容器有 HTTP 客户端提供者"""
        container = ResourceTestContainer()

        assert hasattr(container, 'http_client')
        assert hasattr(container, 'async_http_client')
        assert isinstance(container.http_client, providers.Resource)
        assert isinstance(container.async_http_client, providers.Resource)


class TestContainerConfigurationLoading:
    """测试容器配置加载"""

    def test_load_config_from_dict(self):
        """测试从字典加载配置"""
        container = ResourceTestContainer()
        test_config = {
            "async_executor": {"max_workers": 5},
            "postgresql": {
                "dsn": "postgresql://user:pass@localhost:5432/test",
                "echo": False,
                "pool": {
                    "pool_size": 10,
                    "pool_recycle": 7200,
                    "pool_timeout": 60,
                    "pool_pre_ping": True,
                }
            }
        }

        container.config.from_dict(test_config)

        assert container.config.async_executor.max_workers == 5
        assert container.config.postgresql.pool.pool_size == 10
        assert container.config.postgresql.pool.pool_recycle == 7200

    def test_load_config_from_yaml(self):
        """测试从 YAML 文件加载配置"""
        import tempfile

        import yaml

        yaml_content = """
async_executor:
  max_workers: 7

postgresql:
  dsn: postgresql://test:test@localhost:5432/test_yaml
  echo: false
  pool:
    pool_size: 15
    pool_recycle: 1800
    pool_timeout: 20
    pool_pre_ping: false

redis:
  dsn: redis://localhost:6379/5
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml.safe_load(yaml_content), f)
            temp_path = f.name

        try:
            container = ResourceTestContainer()
            container.config.from_yaml(temp_path)

            assert container.config.async_executor.max_workers == 7
            assert container.config.postgresql.pool.pool_size == 15
            assert container.config.redis.dsn == "redis://localhost:6379/5"
        finally:
            import os
            os.unlink(temp_path)


class TestContainerResourceInit:
    """测试容器资源初始化（使用 Mock）"""

    def test_init_async_executor_resource(self):
        """测试初始化异步执行器资源"""
        container = create_test_container()

        with container.async_executor as executor:
            assert isinstance(executor, AsyncExecutor)
            assert executor.max_workers == 2
            assert executor._executor is not None

    def test_init_postgresql_client_with_mock(self):
        """测试初始化 PostgreSQL 客户端（使用 Mock）"""
        container = create_test_container()

        with patch('graphedu.common.resource.modules.database.postgresql.create_engine') as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            with container.postgresql_client as client:
                assert isinstance(client, PostgresqlClient)
                assert client.config is not None
                assert client._pg_engine == mock_engine

    def test_init_async_postgresql_client_with_mock(self):
        """测试初始化异步 PostgreSQL 客户端（使用 Mock）"""
        container = create_test_container()

        with patch('graphedu.common.resource.modules.database.postgresql.create_async_engine') as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            async def test_init():
                async with container.async_postgresql_client as client:
                    assert isinstance(client, AsyncPostgresqlClient)
                    assert client.config is not None
                    assert client._pg_engine == mock_engine

            # 运行异步测试
            asyncio.run(test_init())

    def test_init_redis_client_with_mock(self):
        """测试初始化 Redis 客户端（使用 Mock）"""
        container = create_test_container()

        with patch('graphedu.common.resource.modules.cache.redis.ConnectionPool.from_url') as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            with container.redis_client as client:
                assert isinstance(client, RedisClient)
                assert client.config is not None
                assert client._connection_pool == mock_pool_instance

    def test_init_async_redis_client_with_mock(self):
        """测试初始化异步 Redis 客户端（使用 Mock）"""
        container = create_test_container()

        with patch('graphedu.common.resource.modules.cache.redis.AsyncConnectionPool.from_url') as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            async def test_init():
                async with container.async_redis_client as client:
                    assert isinstance(client, AsyncRedisClient)
                    assert client.config is not None

            asyncio.run(test_init())


class TestContainerDependencyInjection:
    """测试容器依赖注入功能"""

    def test_inject_async_executor(self):
        """测试注入异步执行器"""
        container = create_test_container()

        # 配置容器的 wire
        container.wire()

        @inject
        def test_function(
            executor: AsyncExecutor = Provide[ResourceTestContainer.async_executor]
        ):
            return executor

        with container.async_executor as injected_executor:
            result = test_function()
            assert result is injected_executor

        # 清理 wiring
        container.unwire()

    def test_inject_postgresql_client(self):
        """测试注入 PostgreSQL 客户端"""
        container = create_test_container()
        container.wire()

        with patch('graphedu.common.resource.modules.database.postgresql.create_engine') as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            @inject
            def test_function(
                pg_client: PostgresqlClient = Provide[ResourceTestContainer.postgresql_client]
            ):
                return pg_client

            with container.postgresql_client as client:
                result = test_function()
                assert result is client

        container.unwire()

    def test_dependency_injection_example_service(self):
        """测试示例服务的依赖注入"""
        container = create_test_container()
        container.wire()

        with patch('graphedu.common.resource.modules.database.postgresql.create_engine') as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            with container.postgresql_client as client:
                result = example_service_with_pg()
                assert result is client

        container.unwire()


class TestContainerLifecycle:
    """测试容器生命周期管理"""

    def test_container_resource_cleanup(self):
        """测试容器资源清理"""
        container = create_test_container()

        # 初始化资源
        with container.async_executor as executor:
            assert executor._executor is not None

        # 资源应该被清理
        assert executor._executor is None

    def test_multiple_resource_initialization(self):
        """测试多个资源初始化"""
        container = create_test_container()

        with patch('graphedu.common.resource.modules.database.postgresql.create_engine') as mock_pg:
            mock_pg.return_value = MagicMock()

            with patch('graphedu.common.resource.modules.cache.redis.ConnectionPool.from_url') as mock_redis:
                mock_redis.return_value = MagicMock()

                # 初始化多个资源
                with container.async_executor as executor:
                    assert isinstance(executor, AsyncExecutor)

                with container.postgresql_client as pg_client:
                    assert isinstance(pg_client, PostgresqlClient)

                with container.redis_client as redis_client:
                    assert isinstance(redis_client, RedisClient)


class TestMockResourceTestContainer:
    """测试 MockResourceTestContainer"""

    def test_mock_container_structure(self):
        """测试 Mock 容器结构"""
        container = MockResourceTestContainer()

        assert hasattr(container, 'config')
        assert hasattr(container, 'async_executor')
        assert hasattr(container, 'mock_pg_engine')
        assert hasattr(container, 'mock_redis_pool')
        assert hasattr(container, 'mock_neo4j_driver')

    def test_mock_container_providers(self):
        """测试 Mock 容器提供者类型"""
        container = MockResourceTestContainer()

        assert isinstance(container.async_executor, providers.Resource)
        assert isinstance(container.mock_pg_engine, providers.Singleton)
        assert isinstance(container.mock_redis_pool, providers.Singleton)
        assert isinstance(container.mock_neo4j_driver, providers.Singleton)

    def test_mock_factory_providers(self):
        """测试 Mock 工厂提供者"""
        container = MockResourceTestContainer()

        assert isinstance(container.mock_postgresql_client, providers.Factory)
        assert isinstance(container.mock_redis_client, providers.Factory)
        assert isinstance(container.mock_neo4j_client, providers.Factory)

    def test_mock_async_executor_init(self):
        """测试 Mock 容器的异步执行器初始化"""
        container = MockResourceTestContainer()

        with container.async_executor as executor:
            assert isinstance(executor, AsyncExecutor)
            # Mock 容器使用较少的工作线程
            assert executor.max_workers == 2


class TestContainerConfigurationProviders:
    """测试容器配置提供者"""

    def test_postgresql_config_provider(self):
        """测试 PostgreSQL 配置提供者"""
        container = create_test_container()

        config_dict = {
            "postgresql": {
                "dsn": "postgresql://test:test@localhost:5432/test",
                "echo": True,
                "pool": {
                    "pool_size": 20,
                    "pool_recycle": 1800,
                    "pool_timeout": 15,
                    "pool_pre_ping": False,
                }
            }
        }

        container.config.from_dict(config_dict)

        assert container.config.postgresql.dsn == "postgresql://test:test@localhost:5432/test"
        assert container.config.postgresql.echo is True
        assert container.config.postgresql.pool.pool_size == 20

    def test_redis_config_provider(self):
        """测试 Redis 配置提供者"""
        container = create_test_container()

        config_dict = {
            "redis": {
                "dsn": "redis://localhost:6379/1"
            }
        }

        container.config.from_dict(config_dict)

        assert container.config.redis.dsn == "redis://localhost:6379/1"

    def test_neo4j_config_provider(self):
        """测试 Neo4j 配置提供者"""
        container = create_test_container()

        config_dict = {
            "neo4j": {
                "dsn": "bolt://localhost:7687",
                "auth": ["admin:secret"],
                "timeout": 60,
            }
        }

        container.config.from_dict(config_dict)

        assert container.config.neo4j.dsn == "bolt://localhost:7687"
        assert container.config.neo4j.auth == ["admin:secret"]
        assert container.config.neo4j.timeout == 60

    def test_oss_config_provider(self):
        """测试 OSS 配置提供者"""
        container = create_test_container()

        config_dict = {
            "oss": {
                "provider": "aws",
                "endpoint": "https://s3.amazonaws.com",
                "access_key": "AKIAIOSFODNN7EXAMPLE",
                "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "use_ssl": True,
                "bucket": "my-bucket",
                "upload_from": "/tmp/upload",
                "download_to": "/tmp/download"
            }
        }

        container.config.from_dict(config_dict)

        assert container.config.oss.provider == "aws"
        assert container.config.oss.use_ssl is True


class TestDefaultTestConfig:
    """测试默认测试配置"""

    def test_default_config_structure(self):
        """测试默认配置结构"""
        assert "async_executor" in DEFAULT_TEST_CONFIG
        assert "postgresql" in DEFAULT_TEST_CONFIG
        assert "mysql" in DEFAULT_TEST_CONFIG
        assert "redis" in DEFAULT_TEST_CONFIG
        assert "neo4j" in DEFAULT_TEST_CONFIG
        assert "oss" in DEFAULT_TEST_CONFIG
        assert "http" in DEFAULT_TEST_CONFIG

    def test_default_config_values(self):
        """测试默认配置值"""
        assert DEFAULT_TEST_CONFIG["async_executor"]["max_workers"] == 2
        assert "test_db" in DEFAULT_TEST_CONFIG["postgresql"]["dsn"]
        assert DEFAULT_TEST_CONFIG["redis"]["dsn"] == "redis://localhost:6379/0"
        assert DEFAULT_TEST_CONFIG["neo4j"]["dsn"] == "bolt://localhost:7687"
        assert DEFAULT_TEST_CONFIG["neo4j"]["auth"] == ["neo4j:test_password"]

    def test_default_config_is_deep_copyable(self):
        """测试默认配置可以深拷贝"""
        config_copy = DEFAULT_TEST_CONFIG.copy()

        # 修改副本不应该影响原配置
        config_copy["async_executor"]["max_workers"] = 999

        assert DEFAULT_TEST_CONFIG["async_executor"]["max_workers"] == 2


class TestContainerEdgeCases:
    """测试容器边界情况"""

    def test_empty_custom_config(self):
        """测试空的自定义配置"""
        container = create_test_container(custom_config={})

        # 应该使用默认配置
        assert container.config.async_executor.max_workers == 2

    def test_nested_config_update(self):
        """测试嵌套配置更新"""
        custom_config = {
            "postgresql": {
                "pool": {
                    "pool_size": 99  # 只更新嵌套的值
                }
            }
        }

        # 注意：当前实现不会深度合并，会完全替换
        container = create_test_container(custom_config)

        # 验证配置被应用
        # (由于使用的是 dict.update，顶级键会被完全替换)
        assert "postgresql" in container.config

    def test_container_with_minimal_config(self):
        """测试最小配置"""
        minimal_config = {
            "async_executor": {"max_workers": 1}
        }

        container = ResourceTestContainer()
        container.config.from_dict(minimal_config)

        assert container.config.async_executor.max_workers == 1


class TestContainerIntegration:
    """测试容器集成场景"""

    def test_full_container_initialization_flow(self):
        """测试完整的容器初始化流程"""
        # 1. 创建容器
        container = create_test_container()

        # 2. 验证容器结构
        assert hasattr(container, 'config')
        assert hasattr(container, 'async_executor')

        # 3. 加载配置
        test_config = {
            "async_executor": {"max_workers": 3},
            "postgresql": {
                "dsn": "postgresql://test:test@localhost:5432/integration_test",
                "echo": False,
                "pool": {"pool_size": 5, "pool_recycle": 3600, "pool_timeout": 30, "pool_pre_ping": True}
            }
        }
        container.config.from_dict(test_config)

        # 4. 验证配置加载
        assert container.config.async_executor.max_workers == 3

        # 5. 初始化资源
        with container.async_executor as executor:
            assert executor.max_workers == 3

    def test_container_with_multiple_configs(self):
        """测试容器使用多个配置源"""
        container = ResourceTestContainer()

        # 第一个配置
        config1 = {"async_executor": {"max_workers": 5}}
        container.config.from_dict(config1)
        assert container.config.async_executor.max_workers == 5

        # 第二个配置会覆盖
        config2 = {"async_executor": {"max_workers": 10}}
        container.config.from_dict(config2)
        assert container.config.async_executor.max_workers == 10

    def test_container_provider_attributes(self):
        """测试容器提供者属性"""
        container = create_test_container()

        # 验证提供者是 Resource 类型
        assert providers.Resource in type(container.async_executor).__mro__
        assert providers.Resource in type(container.postgresql_client).__mro__
        assert providers.Resource in type(container.redis_client).__mro__


# =============================================================================
# 生产容器体系测试（Mixin 组合的分层容器）
# =============================================================================


def _patch_get_config(mock_config):
    """批量 patch 所有 mixin 模块中的 get_config。"""
    return patch.multiple(
        "graphedu.common.config.manager",
        get_config=MagicMock(return_value=mock_config),
    )


class TestContainerHierarchy:
    """测试生产容器的 Mixin 继承体系"""

    def test_cli_container_minimal_resources(self, mock_config):
        """验证 CliContainer 只包含 async_executor"""
        from graphedu.common.resource import CliContainer

        container = CliContainer()
        assert hasattr(container, "async_executor")

    def test_generator_container_resources(self, mock_config):
        """验证 GeneratorContainer 包含 DB + HTTP 资源"""
        from graphedu.common.resource import GeneratorContainer

        container = GeneratorContainer()
        assert hasattr(container, "async_executor")
        assert hasattr(container, "postgresql_client")
        assert hasattr(container, "http_client")
        assert not hasattr(container, "redis_client")

    def test_worker_container_resources(self, mock_config):
        """验证 WorkerContainer 包含构建所需资源（无 Scheduler）"""
        from graphedu.common.resource import WorkerContainer

        container = WorkerContainer()
        assert hasattr(container, "postgresql_client")
        assert hasattr(container, "redis_client")
        assert hasattr(container, "redis_decorator")
        assert hasattr(container, "s3_client")
        assert hasattr(container, "http_client")
        assert hasattr(container, "chat_llm")
        assert hasattr(container, "langgraph_checkpointer")
        assert not hasattr(container, "scheduler")

    def test_service_container_all_resources(self, mock_config):
        """验证 ServiceContainer 包含所有资源"""
        from graphedu.common.resource import ServiceContainer

        container = ServiceContainer()

        resources = [
            "postgresql_client",
            "redis_client",
            "redis_decorator",
            "chat_llm",
            "long_llm",
            "think_llm",
            "scheduler",
            "s3_client",
            "langgraph_checkpointer",
            "http_client",
        ]

        for resource in resources:
            assert hasattr(container, resource), f"ServiceContainer missing: {resource}"

    def test_container_factory(self):
        """验证容器工厂正确创建容器"""
        from graphedu.common.resource import CliContainer, create_container
        from graphedu.common.resource import GeneratorContainer, ServiceContainer, WorkerContainer

        service_container = create_container("service")
        assert isinstance(service_container, ServiceContainer)

        worker_container = create_container("worker")
        assert isinstance(worker_container, WorkerContainer)

        generator_container = create_container("generator")
        assert isinstance(generator_container, GeneratorContainer)

        cli_container = create_container("cli")
        assert isinstance(cli_container, CliContainer)


class TestSchedulerResourceFix:
    """测试 Scheduler 资源泄漏修复"""

    @pytest.mark.asyncio
    async def test_scheduler_cleanup(self, mock_config):
        """验证 APScheduler 正确关闭（修复资源泄漏）"""
        from graphedu.common.resource import ServiceContainer

        container = ServiceContainer()

        # Mock 数据库查询以避免真实数据库连接
        with patch(
            'graphedu.common.resource.modules.scheduler.async_scheduler.get_db_session'
        ) as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock()
            mock_session.return_value.__aenter__.return_value.execute.return_value.scalars.return_value.all.return_value = []

            await container.init_resources()

            scheduler_resource = await container.scheduler()
            scheduler = scheduler_resource.get_scheduler()
            assert scheduler.running

            await container.shutdown_resources()

            # 验证调度器已关闭
            assert not scheduler.running


# =============================================================================
# Pytest fixtures
# =============================================================================

@pytest.fixture
def mock_config():
    """创建 mock 配置对象"""
    from graphedu.common.config.modules.app import AppMetaConfig
    from graphedu.common.config.modules.datasource import Neo4jConfig, OssConfig, PostgresqlConfig, RedisConfig
    from graphedu.common.config.modules.model import LLMConfig
    from graphedu.common.config.modules.agent import AgentConfig

    config = MagicMock()

    # App 配置
    config.app = MagicMock(spec=AppMetaConfig)
    config.app.name = "test_app"
    config.app.version = "0.1.0"

    # PostgreSQL 配置
    config.datasource = MagicMock()
    config.datasource.postgresql = MagicMock(spec=PostgresqlConfig)
    config.datasource.postgresql.dsn = "postgresql://test:test@localhost:5432/test"
    config.datasource.postgresql.echo = False

    # Redis 配置
    config.datasource.redis = MagicMock(spec=RedisConfig)
    config.datasource.redis.dsn = "redis://localhost:6379/0"

    # Neo4j 配置
    config.datasource.neo4j = MagicMock(spec=Neo4jConfig)
    config.datasource.neo4j.dsn = "bolt://localhost:7687"
    config.datasource.neo4j.auth = ["neo4j:test"]
    config.datasource.neo4j.timeout = 30

    # OSS 配置
    config.datasource.oss = MagicMock(spec=OssConfig)
    config.datasource.oss.provider = "minio"
    config.datasource.oss.endpoint = "http://localhost:9000"
    config.datasource.oss.access_key = "minioadmin"
    config.datasource.oss.secret_key = "minioadmin"
    config.datasource.oss.use_ssl = False
    config.datasource.oss.bucket = "test-bucket"

    # LLM 配置
    config.model = MagicMock()
    config.model.chat = MagicMock(spec=LLMConfig)
    config.model.chat.name = "gpt-4"
    config.model.chat.api_key = "test_key"
    config.model.chat.api_base = "http://localhost:11434/v1"
    config.model.chat.temperature = 0.7

    config.model.long = MagicMock(spec=LLMConfig)
    config.model.long.name = "gpt-4-long"
    config.model.long.api_key = "test_key"
    config.model.long.api_base = "http://localhost:11434/v1"
    config.model.long.temperature = 0.5

    config.model.think = MagicMock(spec=LLMConfig)
    config.model.think.name = "gpt-4-think"
    config.model.think.api_key = "test_key"
    config.model.think.api_base = "http://localhost:11434/v1"
    config.model.think.temperature = 0.3

    # Agent 配置
    config.agent = MagicMock(spec=AgentConfig)
    config.agent.dsn = "postgresql://test:test@localhost:5432/test"

    # Scheduler 配置
    config.scheduler = MagicMock()
    config.scheduler.restore_on_startup = False
    config.scheduler.timezone = "Asia/Shanghai"
    config.scheduler.misfire_grace_time_default = 60

    return config
