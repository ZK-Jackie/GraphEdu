"""Resource 模块

提供项目中的各种资源类和容器管理，包括数据库、缓存、存储、HTTP 客户端等。
所有资源类都继承自 BaseSyncResource 或 BaseAsyncResource，支持依赖注入。

使用示例:
    # 同步资源
    from graphedu.common.resource import PostgresqlClient, RedisClient

    pg_client = PostgresqlClient()
    pg_client.init(config)

    # 异步资源
    from graphedu.common.resource import AsyncPostgresqlClient, AsyncRedisClient

    async_pg_client = AsyncPostgresqlClient()
    await async_pg_client.init(config)

    # 使用依赖注入
    from dependency_injector import containers, providers

    class Container(containers.DeclarativeContainer):
        postgresql = providers.Resource(PostgresqlClient, config=...)
        redis = providers.Resource(RedisClient, config=...)

    # 使用容器工厂
    from graphedu.common.resource import create_container, ContainerMode

    container = create_container(ContainerMode.SERVICE)
    await container.init_resources()
"""

from graphedu.common.resource.container import (
    CliContainer,
    GeneratorContainer,
    ServiceContainer,
    WorkerContainer,
)
from graphedu.common.resource.core.base import BaseAsyncResource, BaseSyncResource
from graphedu.common.resource.manager import (
    ContainerMode,
    ContainerType,
    create_container,
    get_container,
    set_container,
    shutdown_container,
    try_get_container,
)
from graphedu.common.resource.modules.cache.redis import AsyncRedisClient, RedisClient
from graphedu.common.resource.modules.database.mysql import AsyncMysqlClient, MysqlClient
from graphedu.common.resource.modules.database.neo4j import AsyncNeo4jClient, Neo4jClient
from graphedu.common.resource.modules.database.oss import AioS3Client, S3Client
from graphedu.common.resource.modules.database.postgresql import AsyncPostgresqlClient, PostgresqlClient
from graphedu.common.resource.modules.database.s3_adaptation.s3_config import (
    ProviderTypes,
    S3Provider,
    S3ProviderConfig,
    get_provider_config,
)
from graphedu.common.resource.modules.infrastructure.async_executor import AsyncExecutor
from graphedu.common.resource.modules.infrastructure.request import AsyncHttpClient, HttpClient
from graphedu.common.resource.modules.scheduler.async_scheduler import AsyncSchedulerResource
from graphedu.common.utils.logger import initialize_logging

__all__ = [
    "AioS3Client",
    "AsyncExecutor",
    "AsyncHttpClient",
    "AsyncMysqlClient",
    "AsyncNeo4jClient",
    "AsyncPostgresqlClient",
    "AsyncRedisClient",
    "AsyncSchedulerResource",
    "BaseAsyncResource",
    "BaseSyncResource",
    "CliContainer",
    "ContainerMode",
    "ContainerType",
    "GeneratorContainer",
    "HttpClient",
    "MysqlClient",
    "Neo4jClient",
    "PostgresqlClient",
    "ProviderTypes",
    "RedisClient",
    "S3Client",
    "S3Provider",
    "S3ProviderConfig",
    "ServiceContainer",
    "WorkerContainer",
    "create_container",
    "get_container",
    "get_provider_config",
    "initialize_logging",
    "set_container",
    "shutdown_container",
    "try_get_container",
]
