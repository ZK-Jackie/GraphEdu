"""PostgreSQL database resource management module.

This module provides synchronous and asynchronous PostgreSQL client implementations
with support for connection pooling, session management, and transaction handling.

Classes:
    PostgresqlClient: Synchronous PostgreSQL client
    AsyncPostgresqlClient: Asynchronous PostgreSQL client
"""

from collections.abc import AsyncGenerator, Generator
from contextlib import contextmanager, suppress
import logging
import re
import traceback
from typing import Any, Self

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from graphedu.common.config.modules.datasource import PostgresqlConfig
from graphedu.common.exceptions.common.resource import (
    DatabaseConnectionException,
    DatabaseEngineException,
    DatabaseSessionException,
    DatabaseTransactionException,
    InvalidGraphNameException,
    InvalidIdentifierException,
)
from graphedu.common.resource.core.base import BaseAsyncResource, BaseSyncResource

logger = logging.getLogger(__name__)

# AGE (Apache AGE) 内部函数依赖 ag_catalog 在 search_path 中，
# 在执行 Cypher 查询前需要设置此搜索路径。
# "$user" 对应当前连接用户的同名 schema（与 PostgreSQL 默认行为一致）。
AGE_SEARCH_PATH_SQL = 'SET LOCAL search_path = ag_catalog, "$user", public'


class PostgresqlClient(BaseSyncResource):
    """Synchronous PostgreSQL client for database operations.

    This client provides a synchronous interface to PostgreSQL databases with
    support for connection pooling, session management, and automatic transaction
    handling.

    Attributes:
        config: PostgreSQL configuration object (set during initialization)
        _pg_engine: SQLAlchemy synchronous engine instance
        _pg_session: SQLAlchemy session factory for creating database sessions

    Examples:
        >>> client = PostgresqlClient()
        >>> client.init(config)
        >>> with client.session() as session:
        ...     # Perform database operations
        ...     pass
        >>> client.shutdown()
    """

    config: PostgresqlConfig | None = None
    _pg_engine: Engine | None = None
    _pg_session: sessionmaker[Session] | None = None

    @property
    def engine(self) -> Engine | None:
        """Get the underlying SQLAlchemy engine.

        Returns:
            The SQLAlchemy Engine instance if initialized, None otherwise
        """
        return self._pg_engine

    @contextmanager
    def session(self) -> Generator[Session]:
        """Create a PostgreSQL database session context manager.

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
        if not self._pg_session:
            logger.debug("Attempted to access uninitialized PostgreSQL session factory")
            raise DatabaseSessionException(
                operation="create",
                reason="PostgreSQL session factory not initialized. Call init() first.",
            )

        session = self._pg_session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"PostgreSQL transaction failed, rolled back. Error: {e}", exc_info=True)
            raise DatabaseTransactionException(
                reason=f"Database operation failed: {type(e).__name__}",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error during PostgreSQL transaction. Error: {e}", exc_info=True)
            raise DatabaseTransactionException(
                reason=f"Unexpected error: {type(e).__name__}",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                },
            ) from e
        finally:
            session.close()

    def init(self, config: PostgresqlConfig) -> Self:
        """Initialize the PostgreSQL synchronous client with configuration.

        This method creates the database engine and session factory based on
        the provided configuration. It normalizes the DSN to ensure proper
        driver usage for synchronous connections.

        Args:
            config: PostgreSQL configuration containing connection details,
                pool settings, and other database parameters

        Returns:
            Self: Returns the client instance for method chaining

        Raises:
            DatabaseConnectionException: If connection to database fails
            DatabaseEngineException: If engine creation fails
        """
        self.config = config
        try:
            # Normalize DSN for synchronous psycopg driver
            dsn = self.config.get_sa_sync_dsn()
            self._pg_engine = create_engine(
                dsn,
                echo=self.config.echo,
                **self.config.pool.model_dump(),
            )
            self._pg_session = sessionmaker(bind=self._pg_engine, expire_on_commit=False)
            logger.info(f"PostgreSQL sync engine connected to {config.dsn.hosts()}")
            return self
        except SQLAlchemyError as e:
            logger.error(f"PostgreSQL sync connection failed. Error: {e}", exc_info=True)
            raise DatabaseConnectionException(
                reason=f"{type(e).__name__}: {e}",
                db_type="PostgreSQL",
                details={
                    "url": self.config.dsn.hosts(),
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during PostgreSQL sync initialization. Error: {e}", exc_info=True)
            raise DatabaseConnectionException(
                reason=f"{type(e).__name__}: {e}",
                db_type="PostgreSQL",
                details={
                    "url": self.config.dsn.hosts(),
                    "error_type": type(e).__name__,
                },
            ) from e

    def shutdown(self, _: Self = None) -> None:
        """Shutdown the PostgreSQL synchronous client and release resources.

        This method disposes of the database engine and closes all connections
        in the connection pool. It should be called when the client is no
        longer needed.

        Args:
            _: Optional parameter for compatibility with resource lifecycle

        Raises:
            DatabaseEngineException: If engine disposal fails
        """
        if self._pg_engine:
            try:
                self._pg_engine.dispose()
                self._pg_session = None
                logger.info("PostgreSQL sync engine released")
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL sync engine shutdown failed. Error: {e}", exc_info=True)
                raise DatabaseEngineException(
                    operation="shutdown",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error during PostgreSQL sync shutdown. Error: {e}", exc_info=True)
                raise DatabaseEngineException(
                    operation="shutdown",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e


class _RetrySessionContext:
    """Async context manager that retries session creation on transient connection errors.

    Retries are applied during the connection checkout phase in ``__aenter__``.
    Errors that occur during query execution (inside the ``async with`` body)
    are propagated to the caller without retry — callers at higher levels
    (e.g., Celery tasks) should implement their own retry logic if needed.
    """

    __slots__ = ("_begin_ctx", "_retry_count", "_session_factory")

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], retry_count: int):
        self._session_factory = session_factory
        self._retry_count = retry_count
        self._begin_ctx: Any = None

    async def __aenter__(self) -> AsyncSession:
        for attempt in range(self._retry_count + 1):
            ctx = self._session_factory.begin()
            try:
                session = await ctx.__aenter__()
                # Force connection checkout to detect stale/broken connections early
                await session.connection()
                self._begin_ctx = ctx
                return session
            except OperationalError as exc:
                with suppress(Exception):
                    await ctx.__aexit__(None, None, None)
                if attempt < self._retry_count:
                    logger.warning(
                        "[PostgreSQL] 连接异常 (第 %d/%d 次重试): %s",
                        attempt + 1,
                        self._retry_count,
                        exc,
                    )
                    continue
                raise DatabaseTransactionException(
                    reason=f"Database connection failed after {self._retry_count + 1} attempts: {type(exc).__name__}",
                    details={
                        "original_error": str(exc),
                        "error_type": type(exc).__name__,
                        "attempts": attempt + 1,
                    },
                ) from exc
            except SQLAlchemyError as e:
                with suppress(Exception):
                    await ctx.__aexit__(None, None, None)
                raise DatabaseTransactionException(
                    reason=f"Database operation failed: {type(e).__name__}",
                    details={
                        "original_error": str(e),
                        "error_type": type(e).__name__,
                    },
                ) from e
        return None  # unreachable: for-loop always returns or raises

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._begin_ctx is None:
            return False
        try:
            return await self._begin_ctx.__aexit__(exc_type, exc_val, exc_tb)
        except OperationalError as exc:
            raise DatabaseTransactionException(
                reason=f"Database operation failed: {type(exc).__name__}",
                details={
                    "original_error": str(exc),
                    "error_type": type(exc).__name__,
                },
            ) from exc
        except SQLAlchemyError as e:
            logger.debug(
                "PostgreSQL async transaction failed. "
                "Error: %s: %s\nTraceback:\n%s",
                type(e).__name__,
                e,
                traceback.format_exc(),
            )
            raise DatabaseTransactionException(
                reason=f"Database operation failed: {type(e).__name__}",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                },
            ) from e


class AsyncPostgresqlClient(BaseAsyncResource):
    """Asynchronous PostgreSQL client for database operations.

    This client provides an asynchronous interface to PostgreSQL databases with
    support for connection pooling, session management, and automatic transaction
    handling. It uses SQLAlchemy's async API with asyncio.

    Attributes:
        config: PostgreSQL configuration object (set during initialization)
        _pg_engine: SQLAlchemy asynchronous engine instance
        _pg_session: SQLAlchemy async session factory for creating database sessions
    """

    config: PostgresqlConfig | None = None
    _pg_engine: AsyncEngine | None = None
    _pg_session: async_sessionmaker[AsyncSession] | None = None
    _connection_retry_count: int = 2

    @property
    def engine(self) -> AsyncEngine | None:
        """Get the underlying SQLAlchemy async engine.

        Returns:
            The SQLAlchemy AsyncEngine instance if initialized, None otherwise
        """
        return self._pg_engine

    @property
    def session(self) -> async_sessionmaker[AsyncSession]:
        """Get the async session factory.

        Returns:
            The async session factory for creating database sessions

        Raises:
            DatabaseSessionException: If the session factory is not initialized
        """
        if not self._pg_session:
            logger.debug("Attempted to access uninitialized PostgreSQL async session factory")
            raise DatabaseSessionException(
                operation="access",
                reason="PostgreSQL async session factory not initialized. Call init() first.",
            )
        return self._pg_session

    async def init(self, config: PostgresqlConfig | dict) -> Self:
        """Initialize the PostgreSQL asynchronous client with configuration.

        This method creates the async database engine and session factory based on
        the provided configuration. It accepts either a PostgresqlConfig object
        or a dictionary that will be validated into a PostgresqlConfig.

        Args:
            config: PostgreSQL configuration containing connection details,
                pool settings, and other database parameters. Can be either
                a PostgresqlConfig instance or a dictionary.

        Returns:
            Self: Returns the client instance for method chaining

        Raises:
            DatabaseConnectionException: If connection to database fails
            DatabaseEngineException: If engine creation fails
        """
        if isinstance(config, dict):
            config = PostgresqlConfig.model_validate(config)
        self.config = config
        try:
            # get DSN for asynchronous psycopg driver
            dsn = self.config.get_sa_async_dsn()

            self._pg_engine = create_async_engine(
                dsn,
                echo=self.config.echo,
                **self.config.pool.model_dump(),
            )
            self._pg_session = async_sessionmaker(bind=self._pg_engine, expire_on_commit=False)
            logger.debug(f"PostgreSQL async engine connected to {config.dsn.hosts()}")
            logger.info("PostgreSQL async engine connected")
            return self
        except SQLAlchemyError as e:
            logger.error(f"PostgreSQL async connection failed. Error: {e}", exc_info=True)
            raise DatabaseConnectionException(
                reason=f"{type(e).__name__}: {e}",
                db_type="PostgreSQL (Async)",
                details={
                    "url": self.config.dsn.hosts(),
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during PostgreSQL async initialization. Error: {e}", exc_info=True)
            raise DatabaseConnectionException(
                reason=f"{type(e).__name__}: {e}",
                db_type="PostgreSQL (Async)",
                details={
                    "url": self.config.dsn.hosts(),
                    "error_type": type(e).__name__,
                },
            ) from e

    async def shutdown(self, _: Self = None) -> None:
        """Shutdown the PostgreSQL asynchronous client and release resources.

        This method disposes of the async database engine and closes all connections
        in the connection pool. It should be called when the client is no
        longer needed.

        Args:
            _: Optional parameter for compatibility with resource lifecycle

        Raises:
            DatabaseEngineException: If engine disposal fails
        """
        if self._pg_engine:
            try:
                await self._pg_engine.dispose()
                self._pg_session = None
                logger.info("PostgreSQL async engine released")
            except SQLAlchemyError as e:
                logger.error(f"PostgreSQL async engine shutdown failed. Error: {e}", exc_info=True)
                raise DatabaseEngineException(
                    operation="shutdown",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error during PostgreSQL async shutdown. Error: {e}", exc_info=True)
                raise DatabaseEngineException(
                    operation="shutdown",
                    reason=f"{type(e).__name__}: {e}",
                    details={
                        "error_type": type(e).__name__,
                        "original_error": str(e),
                    },
                ) from e

    async def session_generator(self) -> AsyncGenerator["AsyncSession"]:
        """Generate an async PostgreSQL database session as an async generator.

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
            >>> async def use_pg_session(pg_client: AsyncPostgresqlClient):
            ...     session_generator = pg_client.session_generator()
            ...     auto_session = await __anext__(session_generator)
            ...     # Use session for database operations
            ...     auto_session.add(some_model)
            ...     # Automatic commit on success, rollback on exception
            ...     await auto_session.commit()
        """
        if not self._pg_session:
            logger.debug("Attempted to access uninitialized PostgreSQL async session factory")
            raise DatabaseSessionException(
                operation="create",
                reason="PostgreSQL async session factory not initialized. Call init() first.",
            )
        session = self._pg_session
        try:
            async with session.begin() as auto_session:
                yield auto_session
        except SQLAlchemyError as e:
            logger.error(f"PostgreSQL async transaction failed. Error: {e}", exc_info=True)
            raise DatabaseTransactionException(
                reason=f"Database operation failed: {type(e).__name__}",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                },
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during PostgreSQL async transaction. Error: {e}", exc_info=True)
            raise DatabaseTransactionException(
                reason=f"Unexpected error: {type(e).__name__}",
                details={
                    "original_error": str(e),
                    "error_type": type(e).__name__,
                },
            ) from e

    def session_context(self):
        """Create an async PostgreSQL database session context manager.

        This method provides an async context manager that automatically handles
        transaction commit/rollback and session cleanup. Sessions are automatically
        committed upon successful completion and rolled back on exceptions.
        This is the recommended way to work with async database sessions.

        For transient connection errors (``OperationalError``), the connection
        establishment is retried up to ``_connection_retry_count`` times before
        propagating the exception.

        Returns:
            An async context manager yielding an AsyncSession.

        Raises:
            DatabaseSessionException: If the session factory is not initialized
            DatabaseTransactionException: If database operation fails and
                transaction rollback is necessary
        """
        if not self._pg_session:
            logger.debug("Attempted to access uninitialized PostgreSQL async session factory")
            raise DatabaseSessionException(
                operation="create",
                reason="PostgreSQL async session factory not initialized. Call init() first.",
            )
        return _RetrySessionContext(self._pg_session, self._connection_retry_count)

    async def ensure_graph_created(self, graph_name: str) -> None:
        """确保 AGE 图数据库已创建（幂等操作）。

        查询 ``ag_catalog.ag_graph`` 表，若图不存在则调用 ``create_graph`` 创建。
        此方法可安全多次调用，图已存在时无操作。

        Args:
            graph_name: 图的名称，需满足 AGE 图名称规范

        Raises:
            InvalidGraphNameException: 图名称不合法时抛出
            DatabaseTransactionException: 数据库操作失败时抛出
        """
        _validate_graph_name(graph_name)
        async with self.session_context() as session:
            await session.execute(text(AGE_SEARCH_PATH_SQL))
            result = await session.execute(
                text("SELECT count(*) FROM ag_catalog.ag_graph WHERE name = :name"),
                {"name": graph_name},
            )
            count = result.scalar()
            if count == 0:
                await session.execute(
                    text("SELECT * FROM ag_catalog.create_graph(:name)"),
                    {"name": graph_name},
                )

    async def execute_cypher(
        self,
        graph_name: str,
        cypher_stmt: str,
        cols: list[str] | None = None,
        params: dict | None = None,
    ) -> list[dict]:
        """Execute a Cypher query against the PostgreSQL database.

        This method allows executing raw Cypher queries using the SQLAlchemy engine.
        It is intended for use with PostgreSQL extensions that support Cypher, such
        as Apache AGE. The method returns results in a structured format based on
        the specified columns.

        Note:
            Apache AGE does not support server-side parameterized Cypher. When
            ``params`` is provided, SQLAlchemy's ``literal_binds`` compilation is
            used to safely inline values into the Cypher string on the Python side
            before sending to AGE. Use ``:name`` placeholders in ``cypher_stmt``
            and pass corresponding values in ``params``.

            The Cypher statement is embedded into the SQL as a PostgreSQL
            dollar-quoted literal (e.g. ``$agecy$...stmt...$agecy$``) and passed
            directly to ``ag_catalog.cypher(graph_name, stmt)``. This avoids the
            fragile ``age_prepare_cypher`` + ``cypher(NULL, NULL)`` two-step
            pattern used by the official psycopg SDK.

        Args:
            graph_name: The name of the graph database to target
            cypher_stmt: The Cypher query string to execute. Use ``:name`` style
                placeholders for parameters.
            cols: Optional list of column names to extract from the result set.
                If not provided, all columns will be returned.
            params: Optional dictionary of parameter values to inline into the
                Cypher statement via SQLAlchemy literal compilation.

        Returns:
            A list of dictionaries representing the query results, where each
            dictionary corresponds to a row and keys are column names.

        Raises:
            DatabaseSessionException: If the session factory is not initialized
            DatabaseTransactionException: If database operation fails and
                transaction rollback is necessary
            InvalidGraphNameException: If the graph name is invalid
            InvalidIdentifierException: If any column identifier is invalid
        """
        # Clean up Cypher statement — AGE requires single-line statements
        cypher_stmt = cypher_stmt.replace("\n", " ").replace("\t", " ").strip()

        # Inline params using safe manual replacement.
        # AGE does not support server-side parameterized Cypher, so values must
        # be embedded into the statement string on the Python side.
        # IMPORTANT: We cannot use SQLAlchemy's text() because it would interpret
        # Cypher relationship types (e.g., [:RELATED_TO]) as parameter placeholders.
        if params:
            cypher_stmt = _inline_cypher_params(cypher_stmt, params)

        async with self.session_context() as session:
            await session.execute(text(AGE_SEARCH_PATH_SQL))
            # Build and execute the cypher query directly
            query_stmt = _build_cypher(graph_name, cypher_stmt, cols)
            result = await session.execute(text(query_stmt))

            # Fetch all results
            rows = result.fetchall()
            if cols:
                return [dict(zip(cols, row, strict=True)) for row in rows]
            return [dict(row._mapping) for row in rows]


# ============================================================================
# Cypher query utilities
# ============================================================================

# Valid graph name pattern aligned with Apache AGE's internal validation
# and Neo4j/openCypher naming conventions.
# Start: letter or underscore
# Middle: letter, digit, underscore, dot, or hyphen
# End: letter, digit, or underscore
VALID_GRAPH_NAME = re.compile(r"^[_A-Za-z][-_A-Za-z0-9.]*[_A-Za-z0-9]$")
MIN_GRAPH_NAME_LENGTH = 3
MAX_IDENTIFIER_LENGTH = 63

# Valid SQL identifier for labels, column names, and types.
# Stricter than graph names — no dots or hyphens.
VALID_IDENTIFIER = re.compile(r"^[_A-Za-z][_A-Za-z0-9]*$")
WHITESPACE = re.compile(r"\s")


def _validate_graph_name(graph_name: str) -> None:
    """Validate that a graph name conforms to Apache AGE's naming rules.

    Graph names must:
    - Be at least 3 characters and at most 63 characters
    - Start with a letter or underscore
    - Contain only letters, digits, underscores, dots, and hyphens
    - End with a letter, digit, or underscore

    Args:
        graph_name: The graph name to validate

    Raises:
        InvalidGraphNameException: If the graph name is invalid
    """
    if not graph_name or not isinstance(graph_name, str):
        raise InvalidGraphNameException(graph_name=str(graph_name), reason="Graph name must be a non-empty string")

    if len(graph_name) < MIN_GRAPH_NAME_LENGTH:
        raise InvalidGraphNameException(
            graph_name=graph_name,
            reason=f"Must be at least {MIN_GRAPH_NAME_LENGTH} characters",
        )

    if len(graph_name) > MAX_IDENTIFIER_LENGTH:
        raise InvalidGraphNameException(
            graph_name=graph_name,
            reason=f"Must not exceed {MAX_IDENTIFIER_LENGTH} characters",
        )

    if not VALID_GRAPH_NAME.match(graph_name):
        raise InvalidGraphNameException(
            graph_name=graph_name,
            reason="Must start with letter/underscore, contain only letters/digits/underscore/dot/hyphen, "
            "and end with letter/digit/underscore",
        )


def _validate_identifier(name: str, context: str = "identifier") -> str:
    """Validate that a name is a safe SQL identifier.

    This follows stricter rules than graph names — only letters, digits,
    and underscores are permitted (no dots or hyphens).

    Args:
        name: The identifier to validate
        context: What the identifier represents (for error messages)

    Returns:
        The validated identifier name

    Raises:
        InvalidIdentifierException: If the identifier is invalid
    """
    if not name or not isinstance(name, str):
        raise InvalidIdentifierException(
            identifier=str(name), context=context, reason=f"{context} must be a non-empty string"
        )

    if len(name) > MAX_IDENTIFIER_LENGTH:
        raise InvalidIdentifierException(
            identifier=name, context=context, reason=f"Must not exceed {MAX_IDENTIFIER_LENGTH} characters"
        )

    if not VALID_IDENTIFIER.match(name):
        raise InvalidIdentifierException(
            identifier=name,
            context=context,
            reason="Must start with letter/underscore and contain only letters/digits/underscore",
        )

    return name


def _validate_column(col: str) -> str:
    """Validate and normalize a column specification for use in SQL.

    Accepts either a plain column name (e.g. 'v') or a name with type
    (e.g. 'v agtype'). Validates each component to prevent SQL injection.

    Args:
        col: Column specification string

    Returns:
        Normalized column specification, or empty string if blank

    Raises:
        InvalidIdentifierException: If any component is invalid
    """
    col = col.strip()
    if not col:
        return ""

    if WHITESPACE.search(col):
        parts = col.split()
        if len(parts) != 2:
            raise InvalidIdentifierException(
                identifier=col, context="column", reason="Column specification must be 'name' or 'name type'"
            )
        name, type_name = parts
        validated_name = _validate_identifier(name, "Column name")
        validated_type = _validate_identifier(type_name, "Column type")
        return f"{validated_name} {validated_type}"

    validated_name = _validate_identifier(col, "Column name")
    return f"{validated_name} ag_catalog.agtype"


def _inline_cypher_params(cypher_stmt: str, params: dict) -> str:
    """Safely inline parameter values into a Cypher statement.

    This function replaces parameter placeholders (e.g., :param_name) with their
    corresponding values, properly handling different data types (strings, numbers,
    booleans, None). It uses word boundary matching to avoid replacing Cypher
    relationship types like [:RELATED_TO].

    Args:
        cypher_stmt: The Cypher statement with parameter placeholders
        params: Dictionary of parameter names to values

    Returns:
        The Cypher statement with parameters inlined

    Example:
        >>> _inline_cypher_params(
        ...     "MATCH (n {id: :id}) WHERE n.name = :name RETURN n",
        ...     {"id": 1, "name": "Alice"}
        ... )
        "MATCH (n {id: 1}) WHERE n.name = 'Alice' RETURN n"
    """
    import re

    result = cypher_stmt

    for param_name, param_value in params.items():
        # Use word boundary to match only complete parameter names
        # This prevents matching :RELATED_TO inside [:RELATED_TO]
        pattern = rf":{re.escape(param_name)}\b"

        replacement = _format_cypher_value(param_value)
        result = re.sub(pattern, replacement, result)

    return result


def _format_cypher_value(value: Any) -> str:
    """Format a Python value for inclusion in a Cypher statement.

    Args:
        value: The Python value to format

    Returns:
        A string representation suitable for Cypher

    Raises:
        ValueError: If the value type is not supported
    """
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        # Escape single quotes by doubling them (Cypher standard)
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    if isinstance(value, (list, tuple)):
        # Format as Cypher array
        items = ", ".join(_format_cypher_value(item) for item in value)
        return f"[{items}]"
    raise ValueError(f"Unsupported parameter type for Cypher: {type(value).__name__}")


def _build_cypher(graph_name: str, cypher_stmt: str, columns: list[str] | None = None) -> str:
    """Build a SQL query that executes a Cypher statement via Apache AGE.

    Constructs a ``SELECT * FROM ag_catalog.cypher(graph, stmt) AS (...)``
    query by embedding the graph name as a single-quoted literal and the
    Cypher statement as a PostgreSQL dollar-quoted literal.  Dollar quoting
    avoids any need to escape the Cypher content.

    Args:
        graph_name: The name of the graph database to target
        cypher_stmt: The fully-inlined Cypher statement to execute (no
            unresolved ``:name`` placeholders)
        columns: Optional list of column specifications. Each can be either
            a column name (e.g., 'v') or a name with type (e.g., 'v agtype').

    Returns:
        A SQL query string ready for execution

    Raises:
        InvalidGraphNameException: If the graph name is invalid
        InvalidIdentifierException: If any column identifier is invalid
    """
    _validate_graph_name(graph_name)

    column_exp: list[str] = []
    if columns:
        for col in columns:
            validated = _validate_column(col)
            if validated:
                column_exp.append(validated)
    else:
        column_exp.append("v agtype")

    # Embed the Cypher statement using PostgreSQL dollar quoting so that
    # single quotes, backslashes, and other special characters inside the
    # Cypher query do not need escaping.  Choose a tag that is absent from
    # the statement; extend with underscores until unique.
    tag = "agecy"
    while f"${tag}$" in cypher_stmt:
        tag += "_"
    quoted_cypher = f"${tag}${cypher_stmt}${tag}$"

    # graph_name is validated above: only letters, digits, underscores,
    # dots, and hyphens — safe to embed as a single-quoted SQL literal.
    stmt_arr: list[str] = [
        f"SELECT * FROM ag_catalog.cypher('{graph_name}', {quoted_cypher}) AS (",
        ",".join(column_exp),
        ");",
    ]
    return "".join(stmt_arr)
