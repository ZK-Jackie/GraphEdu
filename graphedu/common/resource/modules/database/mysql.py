"""MySQL database resource management module.

This module provides synchronous and asynchronous MySQL client implementations
with support for connection pooling, session management, and transaction handling.

Classes:
    MysqlClient: Synchronous MySQL client
    AsyncMysqlClient: Asynchronous MySQL client
"""

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
import logging
from typing import Self

from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from graphedu.common.config.modules.datasource import MysqlConfig
from graphedu.common.exceptions.common.resource import (
    DatabaseConnectionException,
    DatabaseEngineException,
    DatabaseSessionException,
    DatabaseTransactionException,
)
from graphedu.common.resource.core.base import BaseAsyncResource, BaseSyncResource

logger = logging.getLogger(__name__)


class MysqlClient(BaseSyncResource):
    """Synchronous MySQL client for database operations.

    This client provides a synchronous interface to MySQL databases with
    support for connection pooling, session management, and automatic transaction
    handling.

    Attributes:
        config: MySQL configuration object (set during initialization)
        _mysql_engine: SQLAlchemy synchronous engine instance
        _mysql_session: SQLAlchemy session factory for creating database sessions

    Examples:
        >>> client = MysqlClient()
        >>> client.init(config)
        >>> with client.session() as session:
        ...     # Perform database operations
        ...     pass
        >>> client.shutdown()
    """

    config: MysqlConfig | None = None
    _mysql_engine: Engine | None = None
    _mysql_session: sessionmaker[Session] | None = None

    @property
    def engine(self) -> Engine | None:
        """Get the underlying SQLAlchemy engine.

        Returns:
            The SQLAlchemy Engine instance if initialized, None otherwise
        """
        return self._mysql_engine

    @contextmanager
    def session(self) -> Generator[Session]:
        """Create a MySQL database session context manager.

        This method provides a context manager that automatically handles
        transaction commit/rollback and session cleanup. Sessions are
        automatically committed upon successful completion and rolled
        back on exceptions.

        Yields:
            Session: A SQLAlchemy Session instance for database operations

        Raises:
            DatabaseSessionException: If the session factory is not initialized
            DatabaseTransactionException: If database operation fails and
                transaction rollback is necessary

        Examples:
            >>> with client.session() as session:
            ...     user = session.query(User).first()
            ...     user.name = "New Name"
            ...     # Automatic commit on success, rollback on exception
        """
        if not self._mysql_session:
            logger.debug("Attempted to access uninitialized MySQL session factory")
            raise DatabaseSessionException(
                operation="create",
                reason="MySQL session factory not initialized. Call init() first.",
            )

        session = self._mysql_session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"MySQL transaction failed, rolled back. Error: {e}", exc_info=True)
            raise DatabaseTransactionException(
                reason=f"Database operation failed: {type(e).__name__}",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error during MySQL transaction. Error: {e}", exc_info=True)
            raise DatabaseTransactionException(
                reason=f"Unexpected error: {type(e).__name__}",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                },
            ) from e
        finally:
            session.close()

    def init(self, config: MysqlConfig) -> Self:
        """Initialize the MySQL synchronous client with configuration.

        This method creates the database engine and session factory based on
        the provided configuration. It normalizes the DSN to ensure proper
        driver usage for synchronous connections.

        Args:
            config: MySQL configuration containing connection details,
                pool settings, and other database parameters

        Returns:
            Self: Returns the client instance for method chaining

        Raises:
            DatabaseConnectionException: If connection to database fails
            DatabaseEngineException: If engine creation fails
        """
        self.config = config
        try:
            # Normalize DSN for synchronous pymysql driver
            dsn = self.config.get_sa_sync_dsn()
            self._mysql_engine = create_engine(
                dsn,
                echo=self.config.echo,
                **self.config.pool.model_dump(),
            )
            self._mysql_session = sessionmaker(bind=self._mysql_engine, expire_on_commit=False)
            logger.info(f"MySQL sync engine connected to {config.dsn.host}")
            return self
        except SQLAlchemyError as e:
            logger.error(f"MySQL sync connection failed. Error: {e}", exc_info=True)
            raise DatabaseConnectionException(
                reason=f"{type(e).__name__}: {e}",
                db_type="MySQL",
                details={
                    "url": self.config.dsn.host,
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during MySQL sync initialization. Error: {e}", exc_info=True)
            raise DatabaseConnectionException(
                reason=f"{type(e).__name__}: {e}",
                db_type="MySQL",
                details={
                    "url": self.config.dsn.host,
                    "error_type": type(e).__name__,
                },
            ) from e

    def shutdown(self, _: Self = None) -> None:
        """Shutdown the MySQL synchronous client and release resources.

        This method disposes of the database engine and closes all connections
        in the connection pool. It should be called when the client is no
        longer needed.

        Args:
            _: Optional parameter for compatibility with resource lifecycle

        Raises:
            DatabaseEngineException: If engine disposal fails
        """
        if self._mysql_engine:
            try:
                self._mysql_engine.dispose()
                self._mysql_session = None
                logger.info("MySQL sync engine released")
            except SQLAlchemyError as e:
                logger.error(f"MySQL sync engine shutdown failed. Error: {e}", exc_info=True)
                raise DatabaseEngineException(
                    operation="shutdown",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error during MySQL sync shutdown. Error: {e}", exc_info=True)
                raise DatabaseEngineException(
                    operation="shutdown",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e


class AsyncMysqlClient(BaseAsyncResource):
    """Asynchronous MySQL client for database operations.

    This client provides an asynchronous interface to MySQL databases with
    support for connection pooling, session management, and automatic transaction
    handling. It uses SQLAlchemy's async API with asyncio.

    Attributes:
        config: MySQL configuration object (set during initialization)
        _mysql_engine: SQLAlchemy asynchronous engine instance
        _mysql_session: SQLAlchemy async session factory for creating database sessions
    """

    config: MysqlConfig | None = None
    _mysql_engine: AsyncEngine | None = None
    _mysql_session: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine | None:
        """Get the underlying SQLAlchemy async engine.

        Returns:
            The SQLAlchemy AsyncEngine instance if initialized, None otherwise
        """
        return self._mysql_engine

    @property
    def session(self) -> async_sessionmaker[AsyncSession]:
        """Get the async session factory.

        Returns:
            The async session factory for creating database sessions

        Raises:
            DatabaseSessionException: If the session factory is not initialized
        """
        if not self._mysql_session:
            logger.debug("Attempted to access uninitialized MySQL async session factory")
            raise DatabaseSessionException(
                operation="access",
                reason="MySQL async session factory not initialized. Call init() first.",
            )
        return self._mysql_session

    async def init(self, config: MysqlConfig | dict) -> Self:
        """Initialize the MySQL asynchronous client with configuration.

        This method creates the async database engine and session factory based on
        the provided configuration. It accepts either a MysqlConfig object
        or a dictionary that will be validated into a MysqlConfig.

        Args:
            config: MySQL configuration containing connection details,
                pool settings, and other database parameters. Can be either
                a MysqlConfig instance or a dictionary.

        Returns:
            Self: Returns the client instance for method chaining

        Raises:
            DatabaseConnectionException: If connection to database fails
            DatabaseEngineException: If engine creation fails
        """
        if isinstance(config, dict):
            config = MysqlConfig.model_validate(config)
        self.config = config
        try:
            # Get DSN for asynchronous aiomysql driver
            dsn = self.config.get_sa_async_dsn()

            self._mysql_engine = create_async_engine(
                dsn,
                echo=self.config.echo,
                **self.config.pool.model_dump(),
            )
            self._mysql_session = async_sessionmaker(bind=self._mysql_engine, expire_on_commit=False)
            logger.debug(f"MySQL async engine connected to {config.dsn.host}")
            logger.info("MySQL async engine connected")
            return self
        except SQLAlchemyError as e:
            logger.error(f"MySQL async connection failed. Error: {e}", exc_info=True)
            raise DatabaseConnectionException(
                reason=f"{type(e).__name__}: {e}",
                db_type="MySQL (Async)",
                details={
                    "url": self.config.dsn.host,
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during MySQL async initialization. Error: {e}", exc_info=True)
            raise DatabaseConnectionException(
                reason=f"{type(e).__name__}: {e}",
                db_type="MySQL (Async)",
                details={
                    "url": self.config.dsn.host,
                    "error_type": type(e).__name__,
                },
            ) from e

    async def shutdown(self, _: Self = None) -> None:
        """Shutdown the MySQL asynchronous client and release resources.

        This method disposes of the async database engine and closes all connections
        in the connection pool. It should be called when the client is no
        longer needed.

        Args:
            _: Optional parameter for compatibility with resource lifecycle

        Raises:
            DatabaseEngineException: If engine disposal fails
        """
        if self._mysql_engine:
            try:
                await self._mysql_engine.dispose()
                self._mysql_session = None
                logger.info("MySQL async engine released")
            except SQLAlchemyError as e:
                logger.error(f"MySQL async engine shutdown failed. Error: {e}", exc_info=True)
                raise DatabaseEngineException(
                    operation="shutdown",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error during MySQL async shutdown. Error: {e}", exc_info=True)
                raise DatabaseEngineException(
                    operation="shutdown",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e

    async def session_generator(self) -> AsyncGenerator[AsyncSession]:
        """Generate an async MySQL database session as an async generator.

        This method creates an async generator that yields a database session.
        The session is automatically committed on successful completion and
        rolled back on exceptions.

        Note:
            This is a lower-level method. For most use cases, consider using
            session_context() instead, which provides a more ergonomic async
            context manager interface.

        Yields:
            AsyncSession: A SQLAlchemy AsyncSession instance for database operations

        Raises:
            DatabaseSessionException: If the session factory is not initialized
            DatabaseTransactionException: If database operation fails and
                transaction rollback is necessary

        Examples:
            >>> async def use_mysql_session(mysql_client: AsyncMysqlClient):
            ...     session_generator = mysql_client.session_generator()
            ...     auto_session = await anext(session_generator)
            ...     # Use session for database operations
            ...     auto_session.add(some_model)
            ...     # Automatic commit on success, rollback on exception
        """
        if not self._mysql_session:
            logger.debug("Attempted to access uninitialized MySQL async session factory")
            raise DatabaseSessionException(
                operation="create",
                reason="MySQL async session factory not initialized. Call init() first.",
            )
        session = self._mysql_session
        try:
            async with session.begin() as auto_session:
                yield auto_session
        except SQLAlchemyError as e:
            logger.error(f"MySQL async transaction failed. Error: {e}", exc_info=True)
            raise DatabaseTransactionException(
                reason=f"Database operation failed: {type(e).__name__}",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during MySQL async transaction. Error: {e}", exc_info=True)
            raise DatabaseTransactionException(
                reason=f"Unexpected error: {type(e).__name__}",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                },
            ) from e

    @asynccontextmanager
    async def session_context(self) -> AsyncGenerator[AsyncSession]:
        """Create an async MySQL database session context manager.

        This method provides an async context manager that automatically handles
        transaction commit/rollback and session cleanup. Sessions are automatically
        committed upon successful completion and rolled back on exceptions.
        This is the recommended way to work with async database sessions.

        Yields:
            AsyncSession: A SQLAlchemy AsyncSession instance for database operations

        Raises:
            DatabaseSessionException: If the session factory is not initialized
            DatabaseTransactionException: If database operation fails and
                transaction rollback is necessary

        Examples:
            >>> from dependency_injector.wiring import inject, Provide
            >>> from graphedu.common.resource import ServiceContainer
            >>> @inject
            >>> async def use_context_session(
            ...    mysql_client: AsyncMysqlClient = Provide[ServiceContainer.mysql_client]
            ... ):
            ...     async with mysql_client.session_context() as auto_session:
            ...         # Use session for database operations
            ...         await auto_session.execute("SELECT 1")
            ...         # Automatic commit on success, rollback on exception
            ...         # Automatic session cleanup on exit
        """
        import traceback

        if not self._mysql_session:
            logger.debug("Attempted to access uninitialized MySQL async session factory")
            raise DatabaseSessionException(
                operation="create",
                reason="MySQL async session factory not initialized. Call init() first.",
            )
        session = self._mysql_session
        try:
            async with session.begin() as auto_session:
                yield auto_session
        except SQLAlchemyError as e:
            logger.debug(
                f"MySQL async transaction failed. Error: {type(e).__name__}: {e}\nTraceback:\n{traceback.format_exc()}"
            )
            raise DatabaseTransactionException(
                reason=f"Database operation failed: {type(e).__name__}",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                },
            ) from e
