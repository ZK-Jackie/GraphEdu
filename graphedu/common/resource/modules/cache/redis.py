"""Redis cache resource management module.

This module provides synchronous and asynchronous Redis client implementations
with support for connection pooling, client creation, and resource lifecycle
management.

Classes:
    RedisClient: Synchronous Redis client
    AsyncRedisClient: Asynchronous Redis client
"""

import logging
from typing import TYPE_CHECKING, Self

from redis import ConnectionPool, Redis
from redis.asyncio import ConnectionPool as AsyncConnectionPool, Redis as AsyncRedis
from redis.exceptions import RedisError

from graphedu.common.config.modules.datasource import RedisConfig
from graphedu.common.exceptions.common.resource import (
    CacheConnectionException,
    CachePoolException,
)
from graphedu.common.resource.core.base import BaseAsyncResource, BaseSyncResource

logger = logging.getLogger(__name__)


class RedisClient(BaseSyncResource):
    """Synchronous Redis client for cache operations.

    This client provides a synchronous interface to Redis with support for
    connection pooling and resource lifecycle management. It manages the
    connection pool and provides methods to create Redis client instances.

    Attributes:
        config: Redis configuration object (set during initialization)
        mode: Client mode identifier ("sync")
        _connection_pool: Redis connection pool for managing connections

    Examples:
        >>> client = RedisClient()
        >>> client.init(config)
        >>> redis = client.get_redis()
        >>> redis.set('key', 'value')
        >>> client.shutdown()
    """

    config: RedisConfig | None = None
    mode = "sync"
    _connection_pool: ConnectionPool | None = None

    @property
    def pool(self) -> ConnectionPool | None:
        """Get the underlying Redis connection pool.

        Returns:
            The Redis ConnectionPool instance if initialized, None otherwise
        """
        return self._connection_pool

    def init(self, config: RedisConfig) -> Self:
        """Initialize the Redis synchronous client with configuration.

        This method creates a Redis connection pool based on the provided
        configuration. The pool manages connections to Redis server and
        enables efficient connection reuse. `decode_responses` is set to
        True here for convenience.

        Warnings:
            Any redis configuration options should be written to the
            connection URL used during initialization, as this method does
            not accept additional parameters.

            Such as setting `decode_responses=True`, the url should be like:
            `redis://localhost:6379/0?decode_responses=true`

        Args:
            config: Redis configuration containing connection URL and
                other connection parameters

        Returns:
            Self: Returns the client instance for method chaining

        Raises:
            CacheConnectionException: If connection to Redis fails
        """
        self.config = config
        try:
            self._connection_pool = ConnectionPool.from_url(str(self.config.dsn))
            logger.debug(f"Sync Redis connection pool created: {self._connection_pool}")
            logger.info(f"Redis sync connection pool created to {self.config.dsn.host}")
            return self
        except RedisError as e:
            logger.error(f"Redis sync connection failed. Error: {type(e).__name__}: {e}", exc_info=True)
            raise CacheConnectionException(
                reason=f"{type(e).__name__}: {e}",
                cache_type="Redis",
                details={
                    "url": self.config.dsn.host,
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during Redis sync initialization. Error: {e}", exc_info=True)
            raise CacheConnectionException(
                reason=f"{type(e).__name__}: {e}",
                cache_type="Redis",
                details={
                    "url": self.config.dsn.host,
                    "error_type": type(e).__name__,
                },
            ) from e

    def get_redis(self) -> Redis:
        """Create a Redis client instance from the connection pool.

        This method creates a new Redis client using the managed connection pool.
        The client can be used to perform Redis operations.

        Returns:
            Redis: A Redis client instance connected to the server

        Raises:
            CachePoolException: If connection pool is not initialized

        Examples:
            >>> from dependency_injector import containers, providers
            >>> from dependency_injector.wiring import inject, Provide  # noqa: F401
            ...
            >>> class Container(containers.DeclarativeContainer):
            ...     redis_client = providers.Resource(RedisClient, config=...)
            ...
            >>> @inject
            >>> async def some_function(client: RedisClient = Provide[Container.redis_client]):
            ...     redis = client.get_redis()
            ...     await redis.set('key', 'value', ex=60)
            ...     value = await redis.get('key')
        """
        if not self._connection_pool:
            logger.error("Attempted to access uninitialized Redis connection pool")
            raise CachePoolException(
                operation="create",
                reason="Redis connection pool not initialized. Call init() first.",
            )

        logger.debug(f"Creating Redis sync client with connection pool: {self._connection_pool}")
        redis_client = Redis(connection_pool=self._connection_pool, decode_responses=True)
        logger.info("Redis sync client created")
        return redis_client

    def shutdown(self, _: Self = None) -> None:
        """Shutdown the Redis synchronous client and release resources.

        This method disconnects all connections in the connection pool and
        releases resources. It should be called when the client is no
        longer needed.

        Args:
            _: Optional parameter for compatibility with resource lifecycle

        Raises:
            CachePoolException: If pool disconnection fails
        """
        if self._connection_pool:
            try:
                self._connection_pool.disconnect()
                self._connection_pool = None
                logger.info("Redis sync connection pool released")
            except RedisError as e:
                logger.error(f"Redis sync pool shutdown failed. Error: {e}", exc_info=True)
                raise CachePoolException(
                    operation="disconnect",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error during Redis sync shutdown. Error: {e}", exc_info=True)
                raise CachePoolException(
                    operation="disconnect",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e


if TYPE_CHECKING:
    from cashews import Cache


class AsyncRedisClient(BaseAsyncResource):
    """Asynchronous Redis client for cache operations.

    This client provides an asynchronous interface to Redis with support for
    connection pooling and resource lifecycle management. It uses asyncio
    and redis-py's async API for non-blocking operations.

    Warnings:
        Any redis configuration options should be written to the
        connection URL used during initialization, as this method does
        not accept additional parameters.

        Such as setting `decode_responses=True`, the url should be like:
        `redis://localhost:6379/0?decode_responses=true`

    Attributes:
        config: Redis configuration object (set during initialization)
        mode: Client mode identifier ("async")
        _connection_pool: Async Redis connection pool for managing connections
    """

    config: RedisConfig | None = None
    mode = "async"
    _cashews_instance: "Cache | None" = None
    _connection_pool: AsyncConnectionPool | None = None

    @property
    def pool(self) -> AsyncConnectionPool | None:
        """Get the underlying async Redis connection pool.

        Returns:
            The AsyncConnectionPool instance if initialized, None otherwise
        """
        return self._connection_pool

    async def init(self, config: RedisConfig | dict) -> Self:
        """Initialize the Redis asynchronous client with configuration.

        This method creates an async Redis connection pool based on the provided
        configuration. The pool manages connections to Redis server and enables
        efficient connection reuse for async operations.

        Args:
            config: Redis configuration containing connection URL and
                other connection parameters. Can be either a RedisConfig
                instance or a dictionary that will be validated.

        Returns:
            Self: Returns the client instance for method chaining

        Raises:
            CacheConnectionException: If connection to Redis fails
        """
        if isinstance(config, dict):
            config = RedisConfig.model_validate(config)
        self.config = config
        # Initialize redis-py async connection pool
        try:
            self._connection_pool = AsyncConnectionPool.from_url(str(self.config.dsn))
            logger.debug(f"Async Redis connection pool created: {self._connection_pool}")
            logger.info("Redis async connection pool created.")
        except RedisError as e:
            logger.error(f"Redis async connection failed. Error: {e}\n", exc_info=True)
            raise CacheConnectionException(
                reason=f"{type(e).__name__}: {e}",
                cache_type="Redis (Async)",
                details={
                    "url": self.config.dsn.host,
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during Redis async initialization. Error: {e}", exc_info=True)
            raise CacheConnectionException(
                reason=f"{type(e).__name__}: {e}",
                cache_type="Redis (Async)",
                details={
                    "url": self.config.dsn.host,
                    "error_type": type(e).__name__,
                },
            ) from e
        # Initialize Cashews cache instance if installed
        try:
            from cashews import Cache

            # https://github.com/Krukov/cashews?tab=readme-ov-file#configuration
            self._cashews_instance = Cache()
            self._cashews_instance.setup(str(self.config.dsn))
            logger.debug("Cashews cache instance created for Redis async client")
        except ImportError:
            logger.debug("Cashews not installed, skipping cache instance creation for Redis async client")
        except Exception as e:
            logger.error(f"Unexpected error during Cashews cache instance creation. Error: {e}", exc_info=True)
            raise CacheConnectionException(
                reason=f"{type(e).__name__}: {e}",
                cache_type="Redis (Async)",
                details={
                    "url": self.config.dsn.host,
                    "error_type": type(e).__name__,
                },
            ) from e
        return self

    async def shutdown(self, _: Self = None) -> None:
        """Shutdown the Redis asynchronous client and release resources.

        This method disconnects all connections in the async connection pool
        and releases resources. It should be called when the client is no
        longer needed.

        Args:
            _: Optional parameter for compatibility with resource lifecycle

        Raises:
            CachePoolException: If pool disconnection fails
        """
        if self._connection_pool:
            try:
                await self._connection_pool.disconnect()
                self._connection_pool = None
                logger.info("Redis async connection pool released")
            except RedisError as e:
                logger.error(f"Redis async pool shutdown failed. Error: {e}", exc_info=True)
                raise CachePoolException(
                    operation="disconnect",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e
            except Exception as e:
                logger.debug(
                    f"Unexpected error during Redis async shutdown. Error: {type(e).__name__}: {e}\n", exc_info=True
                )
                raise CachePoolException(
                    operation="disconnect",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e
        if self._cashews_instance:
            try:
                await self._cashews_instance.close()
                self._cashews_instance = None
                logger.info("Cashews cache instance for Redis async client released")
            except Exception as e:
                logger.error(f"Error during Cashews cache instance shutdown. Error: {e}", exc_info=True)
                raise CachePoolException(
                    operation="close",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e

    def get_redis(self) -> AsyncRedis:
        """Create an async Redis client instance from the connection pool.

        This method creates a new async Redis client using the managed
        connection pool. The client can be used to perform async Redis
        operations.

        Returns:
            AsyncRedis: An async Redis client instance connected to the server

        Raises:
            CachePoolException: If connection pool is not initialized

        Examples:
            >>> from dependency_injector import containers, providers
            >>> from dependency_injector.wiring import inject, Provide  # noqa: F401
            ...
            >>> class Container(containers.DeclarativeContainer):
            ...     redis_client = providers.Resource(AsyncRedisClient, config=...)
            ...
            >>> @inject
            >>> async def some_function(client: AsyncRedisClient = Provide[Container.redis_client]):
            ...     redis = client.get_redis()
            ...     await redis.set('key', 'value', ex=60)
            ...     value = await redis.get('key')
        """
        if not self._connection_pool:
            logger.debug("Attempted to access uninitialized Redis async connection pool")
            raise CachePoolException(
                operation="create",
                reason="Redis async connection pool not initialized. Call init() first.",
            )

        logger.debug(f"Creating Redis async client with connection pool: {self._connection_pool}")
        redis_client = AsyncRedis(connection_pool=self._connection_pool)
        logger.info("Redis async client created")
        return redis_client

    def get_decorator(self) -> "Cache":
        """Get a decorator for caching functions using the async Redis client.

        This method returns a decorator that can be used to cache the results
        of asynchronous functions using the managed async Redis client. It
        requires Cashews to be installed and properly initialized.

        Returns:
            Callable: A decorator function for caching async function results
        """
        if not self._cashews_instance:
            logger.error("Cashews is not installed or cache instance not initialized, cannot provide decorator")
            raise CacheConnectionException(
                reason="Cashews library is required for caching decorator but is not available",
                cache_type="Redis (Async)",
                details={
                    "url": self.config.dsn.host if self.config else "unknown",
                    "error_type": "CashewsNotAvailable",
                },
            )
        return self._cashews_instance

    @classmethod
    def redis_generator(cls, instance: "AsyncRedisClient") -> AsyncRedis:
        """Generate a Redis client from an AsyncRedisClient instance, useful when using DI.

        This is a convenience method that delegates to get_redis().

        Args:
            instance: The AsyncRedisClient instance to create client from

        Returns:
            AsyncRedis: An async Redis client instance

        Examples:
            >>> from dependency_injector import containers, providers
            >>> from dependency_injector.wiring import inject, Provide  # noqa: F401
            ...
            >>> class Container(containers.DeclarativeContainer):
            ...     redis_client = providers.Resource(AsyncRedisClient, config=...)
            ...     redis_session = providers.Factory(AsyncRedisClient.redis_generator, instance=redis_client)
            ...
            >>> @inject
            >>> async def some_function(redis: AsyncRedis = Provide[Container.redis_session]):
            ...     await redis.set('key', 'value')

        """
        return instance.get_redis()
