"""依赖注入模块，提供数据库、缓存、存储和 HTTP 客户端实例的获取函数。

本模块提供预定义的依赖函数，用于在 FastAPI 路由中方便地注入各种资源实例。
这些函数内部使用 dependency_injector.wiring 进行依赖注入，确保资源自动初始化和生命周期管理。

使用示例:
    from fastapi import APIRouter, Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from redis.asyncio import Redis as AsyncRedis
    from graphedu.common.resource.deps import get_db, get_redis, get_s3, get_httpx

    router = APIRouter()

    @router.post("/login")
    async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        # 使用预定义依赖函数
        query_db: AsyncSession = Depends(get_db),
        redis_session: AsyncRedis = Depends(get_redis),
    ):
        # 使用数据库会话
        result = await query_db.execute(select(User).where(User.username == form_data.username))
        user = result.scalar_one_or_none()

        # 使用 Redis
        await redis_session.set(f"token:{user.id}", token, ex=3600)

        return {"access_token": token}

注意:
    - 这些依赖函数主要在 API 层（Controller）使用
    - Service 层建议使用 @inject 装饰器 + Provide 字符串路径
    - 所有函数都支持异步调用，返回 AsyncGenerator 或直接返回资源实例
"""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.resource import (
    AioS3Client,
    AsyncHttpClient,
    AsyncMysqlClient,
    AsyncNeo4jClient,
    AsyncPostgresqlClient,
    AsyncRedisClient,
)


@inject
async def _get_db_client(db_client: AsyncPostgresqlClient = Provide["postgresql_client"]) -> AsyncPostgresqlClient:
    """获取 PostgreSQL 数据库客户端实例。不可用于 FastAPI 依赖注入

    Returns:
        AsyncPostgresqlClient: PostgreSQL 数据库客户端实例。
    """
    return db_client


@inject
async def get_scheduler(
    sched_resource=Provide["scheduler"],
) -> "AsyncSchedulerResource":
    """获取已初始化的 APScheduler 调度器资源实例（来自 DI 容器）。不可用于 FastAPI 依赖注入

    Returns:
        AsyncSchedulerResource: 调度器资源实例。

    Raises:
        RuntimeError: 调度器尚未初始化。
    """
    return sched_resource


@inject
async def get_mysql_client(mysql_client: AsyncMysqlClient = Provide["mysql_client"]) -> AsyncMysqlClient:
    """获取 MySQL 数据库客户端实例。不可用于 FastAPI 依赖注入

    Returns:
        AsyncMysqlClient: MySQL 数据库客户端实例。
    """
    return mysql_client


@inject
async def get_redis_client(redis: AsyncRedisClient = Provide["redis_client"]) -> AsyncRedisClient:
    """获取 Redis 客户端实例。不可用于 FastAPI 依赖注入

    Returns:
        AsyncRedisClient: Redis 客户端实例。
    """
    return redis


@inject
async def get_neo4j_client(neo4j_client: AsyncNeo4jClient = Provide["neo4j_client"]) -> AsyncNeo4jClient:
    """获取 Neo4j 客户端实例。不可用于 FastAPI 依赖注入

    Returns:
        AsyncNeo4jClient: Neo4j 客户端实例。
    """
    return neo4j_client


@inject
async def get_s3_client(s3_client: AioS3Client = Provide["s3_client"]) -> AioS3Client:
    """获取 S3 客户端实例。不可用于 FastAPI 依赖注入

    Returns:
        AioS3Client: S3 客户端实例。
    """
    return s3_client


@inject
async def get_http_client(http_client: AsyncHttpClient = Provide["http_client"]) -> AsyncHttpClient:
    """获取 HTTP 异步客户端实例。不可用于 FastAPI 依赖注入

    Returns:
        AsyncHttpClient: HTTP 异步客户端实例。
    """
    return http_client


async def get_db() -> AsyncGenerator[AsyncSession]:
    """获取 PostgreSQL 数据库会话，用于 FastAPI 依赖注入。

    Yields:
        AsyncSession: SQLAlchemy 异步会话实例。

    Examples:
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: int,
            session: AsyncSession = Depends(get_db),
        ):
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            return user
    """
    client = await _get_db_client()
    async with client.session_context() as session:
        yield session


async def get_db_client() -> AsyncPostgresqlClient:
    """获取 PostgreSQL 数据库客户端实例，用于 FastAPI 依赖注入。

    Returns:
        AsyncPostgresqlClient: PostgreSQL 数据库客户端实例。

    Examples:
        @router.get("/users")
        async def list_users(
            db_client: AsyncPostgresqlClient = Depends(get_db_client),
        ):
            result = await db_client.execute(select(User))
            users = result.scalars().all()
            return users
    """
    return await _get_db_client()


async def get_redis() -> AsyncRedis:
    """获取 Redis 客户端连接，用于 FastAPI 依赖注入。

    Returns:
        AsyncRedis: Redis 客户端连接实例。

    Examples:
        @router.post("/cache")
        async def cache_data(
            redis_session: AsyncRedis = Depends(get_redis),
        ):
            await redis_session.set("key", "value", ex=3600)
            return {"status": "cached"}
    """
    return (await get_redis_client()).get_redis()


async def get_s3() -> AioS3Client:
    """获取 S3 客户端实例，用于 FastAPI 依赖注入。

    Returns:
        AioS3Client: S3 客户端实例。

    Examples:
        @router.post("/upload")
        async def upload_file(
            file: UploadFile,
            s3: AioS3Client = Depends(get_s3),
        ):
            url = await s3.upload_file(file)
            return {"url": url}
    """
    return await get_s3_client()


async def get_httpx() -> AsyncHttpClient:
    """获取 HTTP 异步客户端实例，用于 FastAPI 依赖注入。

    Returns:
        AsyncHttpClient: HTTP 异步客户端实例。

    Examples:
        @router.get("/proxy")
        async def proxy_request(
            http_client: AsyncHttpClient = Depends(get_httpx),
        ):
            response = await http_client.get("https://api.example.com/data")
            return response.json()
    """
    return await get_http_client()


if TYPE_CHECKING:
    from cashews import Cache

    from graphedu.common.resource.modules.scheduler import AsyncSchedulerResource


async def get_redis_decorator() -> "Cache":
    """获取 Cashews Cache 实例，用于 FastAPI 依赖注入。

    Returns:
        Cache: Cashews 缓存装饰器实例。

    Examples:
        @router.get("/cached-data")
        async def get_cached_data(
            cache: Cache = Depends(get_redis_decorator),
        ):
            # 使用缓存装饰器
            @cache(ttl=60, key="data")
            async def fetch_data():
                return expensive_operation()

            return await fetch_data()
    """
    return (await get_redis_client()).get_decorator()
