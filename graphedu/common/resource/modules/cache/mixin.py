"""Cache Mixin：RedisMixin。"""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from dependency_injector import containers, providers

from graphedu.common.config.manager import get_config
from graphedu.common.resource.modules.cache.redis import AsyncRedisClient

if TYPE_CHECKING:
    from cashews import Cache


async def init_redis_decorator(redis_client: AsyncRedisClient) -> AsyncGenerator["Cache", Any]:
    """初始化 Redis 装饰器（cashews Cache）。

    Args:
        redis_client: AsyncRedisClient 实例。

    Yields:
        Cache: Cashews 缓存装饰器实例。
    """
    yield redis_client.get_decorator()


class RedisMixin(containers.DeclarativeContainer):
    """提供 Redis 客户端和 cashews 装饰器资源。

    Attributes:
        redis_client: Redis 异步客户端实例，用于缓存操作。
        redis_decorator: Cashews 缓存装饰器实例，用于函数级别的缓存注解。
    """

    redis_client = providers.Resource(AsyncRedisClient, config=get_config().datasource.redis)
    redis_decorator = providers.Resource(init_redis_decorator, redis_client=redis_client)
