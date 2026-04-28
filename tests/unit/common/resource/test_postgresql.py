"""PostgreSQL resource module unit tests.

This module contains comprehensive tests for the synchronous and asynchronous
PostgreSQL client implementations, covering initialization, session management,
transaction handling, error scenarios, DSN normalization, and AGE graph query
functions.

Test Structure:
    - TestPostgresqlClientInit: Initialization and configuration tests
    - TestPostgresqlClientLifecycle: Lifecycle management (shutdown)
    - TestPostgresqlClientSession: Session context manager and transaction handling
    - TestAsyncPostgresqlClientInit: Async client initialization
    - TestAsyncPostgresqlClientLifecycle: Async client lifecycle
    - TestAsyncPostgresqlClientSession: Async session management
    - TestGraphNameValidation: Graph name validation (_validate_graph_name)
    - TestIdentifierValidation: Identifier validation (_validate_identifier, _validate_column)
    - TestCypherValueFormatting: Cypher value formatting (_format_cypher_value)
    - TestCypherParamInlining: Cypher parameter inlining (_inline_cypher_params)
    - TestBuildCypher: SQL query building (_build_cypher)
    - TestEnsureGraphCreated: ensure_graph_created async method
    - TestExecuteCypher: execute_cypher async method
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from graphedu.common.config.modules.datasource.base import PoolConfig
from graphedu.common.config.modules.datasource.postgresql import PostgresqlConfig
from graphedu.common.exceptions.common.resource import (
    DatabaseConnectionException,
    DatabaseEngineException,
    DatabaseSessionException,
    DatabaseTransactionException,
    InvalidGraphNameException,
    InvalidIdentifierException,
)
from graphedu.common.resource.modules.database.postgresql import (
    AsyncPostgresqlClient,
    PostgresqlClient,
    _build_cypher,
    _format_cypher_value,
    _inline_cypher_params,
    _validate_column,
    _validate_graph_name,
    _validate_identifier,
)

# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def pg_config() -> PostgresqlConfig:
    """Create a PostgreSQL configuration for testing.

    Returns:
        PostgresqlConfig: A valid configuration instance
    """
    return PostgresqlConfig(
        dsn="postgresql://user:pass@localhost:5432/testdb",
        echo=False,
        pool=PoolConfig(
            pool_size=5,
            pool_timeout=30,
            pool_recycle=3600,
        ),
    )


@pytest.fixture
def pg_config_asyncpg() -> PostgresqlConfig:
    """Create a PostgreSQL config with asyncpg driver for DSN normalization tests.

    Returns:
        PostgresqlConfig: Configuration with asyncpg driver
    """
    return PostgresqlConfig(
        dsn="postgresql+asyncpg://user:pass@localhost:5432/testdb",
        echo=False,
        pool=PoolConfig(pool_size=5),
    )


@pytest.fixture
def pg_config_psycopg2() -> PostgresqlConfig:
    """Create a PostgreSQL config with psycopg2 driver for DSN normalization tests.

    Returns:
        PostgresqlConfig: Configuration with psycopg2 driver
    """
    return PostgresqlConfig(
        dsn="postgresql+psycopg2://user:pass@localhost:5432/testdb",
        echo=False,
        pool=PoolConfig(pool_size=5),
    )


@pytest.fixture
def pg_config_no_driver() -> PostgresqlConfig:
    """Create a PostgreSQL config without driver specification.

    Returns:
        PostgresqlConfig: Configuration without explicit driver
    """
    return PostgresqlConfig(
        dsn="postgresql://user:pass@localhost:5432/testdb",
        echo=False,
        pool=PoolConfig(pool_size=5),
    )


@pytest.fixture
def initialized_sync_client(pg_config: PostgresqlConfig) -> PostgresqlClient:
    """Create an initialized synchronous PostgreSQL client.

    Args:
        pg_config: PostgreSQL configuration

    Returns:
        PostgresqlClient: Initialized client with mocked engine
    """
    client = PostgresqlClient()

    with patch("graphedu.common.resource.modules.database.postgresql.create_engine") as mock_create:
        mock_engine = MagicMock(spec=Engine)
        mock_create.return_value = mock_engine

        client.init(pg_config)

    return client


@pytest.fixture
def initialized_async_client(pg_config: PostgresqlConfig) -> AsyncPostgresqlClient:
    """Create an initialized asynchronous PostgreSQL client.

    Args:
        pg_config: PostgreSQL configuration

    Returns:
        AsyncPostgresqlClient: Initialized client with mocked engine
    """
    client = AsyncPostgresqlClient()

    with patch("graphedu.common.resource.modules.database.postgresql.create_async_engine") as mock_create:
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create.return_value = mock_engine

        client.init(pg_config)

    return client


# =============================================================================
# PostgresqlClient Initialization Tests
# =============================================================================

class TestPostgresqlClientInit:
    """Test suite for PostgresqlClient initialization and configuration."""

    def test_init_returns_self_for_chaining(self, pg_config: PostgresqlConfig):
        """Test that init() returns self for method chaining."""
        client = PostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_engine") as mock_create:
            mock_engine = MagicMock(spec=Engine)
            mock_create.return_value = mock_engine

            result = client.init(pg_config)

            assert result is client, "init() should return self for method chaining"

    def test_init_sets_config_attribute(self, pg_config: PostgresqlConfig):
        """Test that init() sets the config attribute."""
        client = PostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_engine"):
            client.init(pg_config)

            assert client.config == pg_config, "config attribute should be set"

    def test_init_creates_engine_with_correct_dsn(self, pg_config: PostgresqlConfig):
        """Test that init() creates engine with normalized DSN."""
        client = PostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_engine") as mock_create:
            mock_engine = MagicMock(spec=Engine)
            mock_create.return_value = mock_engine

            client.init(pg_config)

            mock_create.assert_called_once()
            call_args = mock_create.call_args

            # Verify DSN contains psycopg driver
            assert "psycopg" in call_args[0][0], "DSN should contain psycopg driver"

            # Verify echo parameter
            assert call_args[1]["echo"] == pg_config.echo, "echo parameter should match config"

            # Verify pool parameters are passed
            pool_args = call_args[1]
            assert "pool_size" in pool_args, "pool_size should be passed"

    def test_init_creates_session_factory(self, pg_config: PostgresqlConfig):
        """Test that init() creates a session factory."""
        client = PostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_engine"):
            client.init(pg_config)

            assert client._pg_session is not None, "session factory should be created"

    def test_init_normalizes_dsn_psycopg2_to_psycopg(self, pg_config_psycopg2: PostgresqlConfig):
        """Test DSN normalization from psycopg2 to psycopg."""
        client = PostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_engine") as mock_create:
            mock_engine = MagicMock(spec=Engine)
            mock_create.return_value = mock_engine

            client.init(pg_config_psycopg2)

            call_args = mock_create.call_args
            dsn = call_args[0][0]

            assert "psycopg" in dsn, "DSN should contain psycopg"
            assert "psycopg2" not in dsn, "DSN should not contain psycopg2"

    def test_init_normalizes_dsn_asyncpg_to_psycopg(self, pg_config_asyncpg: PostgresqlConfig):
        """Test DSN normalization from asyncpg to psycopg."""
        client = PostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_engine") as mock_create:
            mock_engine = MagicMock(spec=Engine)
            mock_create.return_value = mock_engine

            client.init(pg_config_asyncpg)

            call_args = mock_create.call_args
            dsn = call_args[0][0]

            assert "psycopg" in dsn, "DSN should contain psycopg"
            assert "asyncpg" not in dsn, "DSN should not contain asyncpg"

    def test_init_adds_driver_when_missing(self, pg_config_no_driver: PostgresqlConfig):
        """Test that init() adds psycopg driver when not specified."""
        client = PostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_engine") as mock_create:
            mock_engine = MagicMock(spec=Engine)
            mock_create.return_value = mock_engine

            client.init(pg_config_no_driver)

            call_args = mock_create.call_args
            dsn = call_args[0][0]

            assert "postgresql+psycopg://" in dsn, "Driver should be added to DSN"

    def test_init_raises_connection_exception_on_sqlalchemy_error(self, pg_config: PostgresqlConfig):
        """Test that DatabaseConnectionException is raised on SQLAlchemy error."""
        client = PostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_engine") as mock_create:
            mock_create.side_effect = SQLAlchemyError("Connection failed")

            with pytest.raises(DatabaseConnectionException) as exc_info:
                client.init(pg_config)

            assert exc_info.value.db_type == "PostgreSQL"
            assert "Connection failed" in exc_info.value.reason
            assert exc_info.value.details["error_type"] == "SQLAlchemyError"

    def test_init_raises_connection_exception_on_unexpected_error(self, pg_config: PostgresqlConfig):
        """Test that DatabaseConnectionException is raised on unexpected errors."""
        client = PostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_engine") as mock_create:
            mock_create.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(DatabaseConnectionException) as exc_info:
                client.init(pg_config)

            assert exc_info.value.db_type == "PostgreSQL"
            assert "RuntimeError" in exc_info.value.details["error_type"]


# =============================================================================
# PostgresqlClient Lifecycle Tests
# =============================================================================

class TestPostgresqlClientLifecycle:
    """Test suite for PostgresqlClient lifecycle management."""

    def test_engine_property_returns_engine(self, initialized_sync_client: PostgresqlClient):
        """Test that engine property returns the underlying engine."""
        assert initialized_sync_client.engine is not None, "engine property should return engine"

    def test_engine_property_returns_none_when_not_initialized(self):
        """Test that engine property returns None when not initialized."""
        client = PostgresqlClient()

        assert client.engine is None, "engine should be None before initialization"

    def test_shutdown_disposes_engine(self, initialized_sync_client: PostgresqlClient):
        """Test that shutdown() disposes the engine."""
        initialized_sync_client._pg_engine.dispose = MagicMock()

        initialized_sync_client.shutdown()

        initialized_sync_client._pg_engine.dispose.assert_called_once()

    def test_shutdown_clears_session_factory(self, initialized_sync_client: PostgresqlClient):
        """Test that shutdown() clears the session factory."""
        initialized_sync_client.shutdown()

        assert initialized_sync_client._pg_session is None, "session factory should be cleared"

    def test_shutdown_raises_engine_exception_on_dispose_error(self, initialized_sync_client: PostgresqlClient):
        """Test that shutdown() raises DatabaseEngineException on dispose error."""
        initialized_sync_client._pg_engine.dispose.side_effect = SQLAlchemyError("Dispose failed")

        with pytest.raises(DatabaseEngineException) as exc_info:
            initialized_sync_client.shutdown()

        assert exc_info.value.operation == "shutdown"
        assert "Dispose failed" in exc_info.value.reason

    def test_shutdown_handles_none_engine_gracefully(self):
        """Test that shutdown() handles None engine without error."""
        client = PostgresqlClient()

        client.shutdown()

        assert client._pg_session is None


# =============================================================================
# PostgresqlClient Session Tests
# =============================================================================

class TestPostgresqlClientSession:
    """Test suite for PostgresqlClient session management."""

    def test_session_yields_session_instance(self, initialized_sync_client: PostgresqlClient):
        """Test that session context manager yields a session instance."""
        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)
        initialized_sync_client._pg_session = mock_session_factory

        with initialized_sync_client.session() as session:
            assert session == mock_session, "session should yield the session instance"

    def test_session_commits_on_success(self, initialized_sync_client: PostgresqlClient):
        """Test that session is committed on successful completion."""
        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)
        initialized_sync_client._pg_session = mock_session_factory

        with initialized_sync_client.session():
            pass

        mock_session.commit.assert_called_once()

    def test_session_closes_on_completion(self, initialized_sync_client: PostgresqlClient):
        """Test that session is closed after completion."""
        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)
        initialized_sync_client._pg_session = mock_session_factory

        with initialized_sync_client.session():
            pass

        mock_session.close.assert_called_once()

    def test_session_rollbacks_on_sqlalchemy_error(self, initialized_sync_client: PostgresqlClient):
        """Test that session is rolled back on SQLAlchemy error."""
        mock_session = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("Transaction failed")
        mock_session_factory = MagicMock(return_value=mock_session)
        initialized_sync_client._pg_session = mock_session_factory

        with pytest.raises(DatabaseTransactionException) as exc_info:
            with initialized_sync_client.session():
                pass

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        assert "Transaction failed" in exc_info.value.reason

    def test_session_rollbacks_on_generic_error(self, initialized_sync_client: PostgresqlClient):
        """Test that session is rolled back on generic errors."""
        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)
        initialized_sync_client._pg_session = mock_session_factory

        with pytest.raises(DatabaseTransactionException):
            with initialized_sync_client.session():
                raise ValueError("Some error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    def test_session_raises_exception_when_not_initialized(self):
        """Test that session raises DatabaseSessionException when not initialized."""
        client = PostgresqlClient()

        with pytest.raises(DatabaseSessionException) as exc_info:
            with client.session():
                pass

        assert "not initialized" in exc_info.value.reason


# =============================================================================
# AsyncPostgresqlClient Initialization Tests
# =============================================================================

class TestAsyncPostgresqlClientInit:
    """Test suite for AsyncPostgresqlClient initialization and configuration."""

    @pytest.mark.asyncio
    async def test_init_returns_self_for_chaining(self, pg_config: PostgresqlConfig):
        """Test that init() returns self for method chaining."""
        client = AsyncPostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_async_engine") as mock_create:
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_create.return_value = mock_engine

            result = await client.init(pg_config)

            assert result is client, "init() should return self for method chaining"

    @pytest.mark.asyncio
    async def test_init_sets_config_attribute(self, pg_config: PostgresqlConfig):
        """Test that init() sets the config attribute."""
        client = AsyncPostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_async_engine"):
            await client.init(pg_config)

            assert client.config == pg_config, "config attribute should be set"

    @pytest.mark.asyncio
    async def test_init_creates_engine_with_correct_dsn(self, pg_config: PostgresqlConfig):
        """Test that init() creates engine with normalized DSN."""
        client = AsyncPostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_async_engine") as mock_create:
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_create.return_value = mock_engine

            await client.init(pg_config)

            mock_create.assert_called_once()
            call_args = mock_create.call_args

            assert "psycopg" in call_args[0][0], "DSN should contain psycopg driver"
            assert call_args[1]["echo"] == pg_config.echo, "echo parameter should match"

    @pytest.mark.asyncio
    async def test_init_creates_session_factory(self, pg_config: PostgresqlConfig):
        """Test that init() creates an async session factory."""
        client = AsyncPostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_async_engine"):
            await client.init(pg_config)

            assert client._pg_session is not None, "async session factory should be created"

    @pytest.mark.asyncio
    async def test_init_accepts_dict_config(self):
        """Test that init() accepts dictionary configuration."""
        client = AsyncPostgresqlClient()
        config_dict = {
            "dsn": "postgresql://user:pass@localhost/db",
            "echo": False,
            "pool": {"pool_size": 5},
        }

        with patch("graphedu.common.resource.modules.database.postgresql.create_async_engine"):
            await client.init(config_dict)

            assert isinstance(client.config, PostgresqlConfig)

    @pytest.mark.asyncio
    async def test_init_normalizes_dsn_asyncpg_to_psycopg(self, pg_config_asyncpg: PostgresqlConfig):
        """Test DSN normalization from asyncpg to psycopg."""
        client = AsyncPostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_async_engine") as mock_create:
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_create.return_value = mock_engine

            await client.init(pg_config_asyncpg)

            call_args = mock_create.call_args
            dsn = call_args[0][0]

            assert "psycopg" in dsn, "DSN should contain psycopg"
            assert "asyncpg" not in dsn, "DSN should not contain asyncpg"

    @pytest.mark.asyncio
    async def test_init_raises_connection_exception_on_sqlalchemy_error(self, pg_config: PostgresqlConfig):
        """Test that DatabaseConnectionException is raised on SQLAlchemy error."""
        client = AsyncPostgresqlClient()

        with patch("graphedu.common.resource.modules.database.postgresql.create_async_engine") as mock_create:
            mock_create.side_effect = SQLAlchemyError("Connection failed")

            with pytest.raises(DatabaseConnectionException) as exc_info:
                await client.init(pg_config)

            assert exc_info.value.db_type == "PostgreSQL (Async)"
            assert "Connection failed" in exc_info.value.reason


# =============================================================================
# AsyncPostgresqlClient Lifecycle Tests
# =============================================================================

class TestAsyncPostgresqlClientLifecycle:
    """Test suite for AsyncPostgresqlClient lifecycle management."""

    def test_engine_property_returns_engine(self, initialized_async_client: AsyncPostgresqlClient):
        """Test that engine property returns the underlying async engine."""
        assert initialized_async_client.engine is not None, "engine property should return engine"

    def test_engine_property_returns_none_when_not_initialized(self):
        """Test that engine property returns None when not initialized."""
        client = AsyncPostgresqlClient()

        assert client.engine is None, "engine should be None before initialization"

    def test_session_property_returns_session_factory(self, initialized_async_client: AsyncPostgresqlClient):
        """Test that session property returns the session factory."""
        assert initialized_async_client.session is not None, "session property should return factory"

    def test_session_property_raises_exception_when_not_initialized(self):
        """Test that session property raises DatabaseSessionException when not initialized."""
        client = AsyncPostgresqlClient()

        with pytest.raises(DatabaseSessionException) as exc_info:
            _ = client.session

        assert "not initialized" in exc_info.value.reason

    @pytest.mark.asyncio
    async def test_shutdown_disposes_engine(self, initialized_async_client: AsyncPostgresqlClient):
        """Test that shutdown() disposes the async engine."""
        async_mock = AsyncMock()
        initialized_async_client._pg_engine.dispose = async_mock

        await initialized_async_client.shutdown()

        async_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_clears_session_factory(self, initialized_async_client: AsyncPostgresqlClient):
        """Test that shutdown() clears the session factory."""
        await initialized_async_client.shutdown()

        assert initialized_async_client._pg_session is None, "session factory should be cleared"

    @pytest.mark.asyncio
    async def test_shutdown_raises_engine_exception_on_dispose_error(self, initialized_async_client: AsyncPostgresqlClient):
        """Test that shutdown() raises DatabaseEngineException on dispose error."""
        async def mock_dispose_error():
            raise SQLAlchemyError("Dispose failed")

        initialized_async_client._pg_engine.dispose = mock_dispose_error

        with pytest.raises(DatabaseEngineException) as exc_info:
            await initialized_async_client.shutdown()

        assert exc_info.value.operation == "shutdown"
        assert "Dispose failed" in exc_info.value.reason

    @pytest.mark.asyncio
    async def test_shutdown_handles_none_engine_gracefully(self):
        """Test that shutdown() handles None engine without error."""
        client = AsyncPostgresqlClient()

        await client.shutdown()

        assert client._pg_session is None


# =============================================================================
# AsyncPostgresqlClient Session Tests
# =============================================================================

class TestAsyncPostgresqlClientSession:
    """Test suite for AsyncPostgresqlClient session management."""

    @pytest.mark.asyncio
    async def test_session_context_yields_session(self, initialized_async_client: AsyncPostgresqlClient):
        """Test that session_context yields an async session."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_begin = MagicMock()
        mock_begin.__aenter__ = AsyncMock(return_value=mock_session)
        mock_begin.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin = MagicMock(return_value=mock_begin)

        mock_session_factory = MagicMock(return_value=mock_session)
        initialized_async_client._pg_session = mock_session_factory

        async with initialized_async_client.session_context() as session:
            assert session == mock_session

    @pytest.mark.asyncio
    async def test_session_context_raises_exception_when_not_initialized(self):
        """Test that session_context raises DatabaseSessionException when not initialized."""
        client = AsyncPostgresqlClient()

        with pytest.raises(DatabaseSessionException) as exc_info:
            async with client.session_context():
                pass

        assert "not initialized" in exc_info.value.reason

    @pytest.mark.asyncio
    async def test_session_generator_yields_session(self, initialized_async_client: AsyncPostgresqlClient):
        """Test that session_generator yields an async session."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_begin = MagicMock()
        mock_auto_session = MagicMock()
        mock_begin.__aenter__ = AsyncMock(return_value=mock_auto_session)
        mock_begin.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin = MagicMock(return_value=mock_begin)

        mock_session_factory = MagicMock(return_value=mock_session)
        initialized_async_client._pg_session = mock_session_factory

        session_gen = initialized_async_client.session_generator()
        result = await anext(session_gen)

        assert result == mock_auto_session

    @pytest.mark.asyncio
    async def test_session_generator_raises_exception_when_not_initialized(self):
        """Test that session_generator raises DatabaseSessionException when not initialized."""
        client = AsyncPostgresqlClient()

        with pytest.raises(DatabaseSessionException) as exc_info:
            session_gen = client.session_generator()
            await anext(session_gen)

        assert "not initialized" in exc_info.value.reason


# =============================================================================
# Graph Name Validation Tests
# =============================================================================

class TestGraphNameValidation:
    """Test suite for _validate_graph_name."""

    def test_valid_graph_names(self):
        """Test that valid graph names pass validation."""
        valid_names = [
            "abc",
            "my_graph",
            "test-graph",
            "graph.v2",
            "_private",
            "A1",
            "a" * 63,
            "x_y-z.w",
        ]
        for name in valid_names:
            _validate_graph_name(name)  # should not raise

    def test_empty_string_raises(self):
        """Test that empty string raises InvalidGraphNameException."""
        with pytest.raises(InvalidGraphNameException):
            _validate_graph_name("")

    def test_none_raises(self):
        """Test that None raises InvalidGraphNameException."""
        with pytest.raises(InvalidGraphNameException):
            _validate_graph_name(None)

    def test_too_short_raises(self):
        """Test that names shorter than 3 characters raise exception."""
        with pytest.raises(InvalidGraphNameException) as exc_info:
            _validate_graph_name("ab")
        assert "at least 3" in exc_info.value.reason.lower() or "3" in exc_info.value.reason

    def test_too_long_raises(self):
        """Test that names exceeding 63 characters raise exception."""
        with pytest.raises(InvalidGraphNameException) as exc_info:
            _validate_graph_name("a" * 64)
        assert "63" in exc_info.value.reason

    def test_starts_with_digit_raises(self):
        """Test that names starting with a digit raise exception."""
        with pytest.raises(InvalidGraphNameException):
            _validate_graph_name("1graph")

    def test_starts_with_hyphen_raises(self):
        """Test that names starting with a hyphen raise exception."""
        with pytest.raises(InvalidGraphNameException):
            _validate_graph_name("-graph")

    def test_contains_spaces_raises(self):
        """Test that names containing spaces raise exception."""
        with pytest.raises(InvalidGraphNameException):
            _validate_graph_name("my graph")

    def test_ends_with_hyphen_raises(self):
        """Test that names ending with a hyphen raise exception."""
        with pytest.raises(InvalidGraphNameException):
            _validate_graph_name("graph-")

    def test_ends_with_dot_raises(self):
        """Test that names ending with a dot raise exception."""
        with pytest.raises(InvalidGraphNameException):
            _validate_graph_name("graph.")


# =============================================================================
# Identifier Validation Tests
# =============================================================================

class TestIdentifierValidation:
    """Test suite for _validate_identifier and _validate_column."""

    def test_valid_identifiers(self):
        """Test that valid identifiers pass validation."""
        valid = ["col", "_col", "col_name", "Col1", "agtype"]
        for ident in valid:
            assert _validate_identifier(ident) == ident

    def test_empty_identifier_raises(self):
        """Test that empty string raises InvalidIdentifierException."""
        with pytest.raises(InvalidIdentifierException):
            _validate_identifier("")

    def test_none_identifier_raises(self):
        """Test that None raises InvalidIdentifierException."""
        with pytest.raises(InvalidIdentifierException):
            _validate_identifier(None)

    def test_starts_with_digit_raises(self):
        """Test that identifiers starting with digit raise exception."""
        with pytest.raises(InvalidIdentifierException):
            _validate_identifier("1col")

    def test_contains_hyphen_raises(self):
        """Test that identifiers with hyphens raise exception."""
        with pytest.raises(InvalidIdentifierException):
            _validate_identifier("col-name")

    def test_too_long_raises(self):
        """Test that identifiers exceeding 63 characters raise exception."""
        with pytest.raises(InvalidIdentifierException):
            _validate_identifier("a" * 64)

    # -- _validate_column tests --

    def test_column_plain_name(self):
        """Test plain column name returns name with agtype."""
        result = _validate_column("v")
        assert result == "v ag_catalog.agtype"

    def test_column_name_with_type(self):
        """Test column with explicit type returns as-is if both valid."""
        result = _validate_column("v agtype")
        assert result == "v agtype"

    def test_column_blank_returns_empty(self):
        """Test blank column returns empty string."""
        assert _validate_column("") == ""
        assert _validate_column("  ") == ""

    def test_column_invalid_name_raises(self):
        """Test invalid column name raises InvalidIdentifierException."""
        with pytest.raises(InvalidIdentifierException):
            _validate_column("1bad")

    def test_column_too_many_parts_raises(self):
        """Test column with too many parts raises InvalidIdentifierException."""
        with pytest.raises(InvalidIdentifierException):
            _validate_column("a b c")


# =============================================================================
# Cypher Value Formatting Tests
# =============================================================================

class TestCypherValueFormatting:
    """Test suite for _format_cypher_value."""

    def test_none(self):
        assert _format_cypher_value(None) == "NULL"

    def test_bool_true(self):
        assert _format_cypher_value(True) == "true"

    def test_bool_false(self):
        assert _format_cypher_value(False) == "false"

    def test_integer(self):
        assert _format_cypher_value(42) == "42"

    def test_float(self):
        assert _format_cypher_value(3.14) == "3.14"

    def test_string(self):
        assert _format_cypher_value("hello") == "'hello'"

    def test_string_with_quotes(self):
        """Test that single quotes are escaped by doubling."""
        assert _format_cypher_value("it's") == "'it''s'"

    def test_list(self):
        assert _format_cypher_value([1, 2, 3]) == "[1, 2, 3]"

    def test_tuple(self):
        assert _format_cypher_value(("a", "b")) == "['a', 'b']"

    def test_nested_list(self):
        assert _format_cypher_value([[1, 2], [3, 4]]) == "[[1, 2], [3, 4]]"

    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported parameter type"):
            _format_cypher_value({"key": "value"})


# =============================================================================
# Cypher Parameter Inlining Tests
# =============================================================================

class TestCypherParamInlining:
    """Test suite for _inline_cypher_params."""

    def test_single_param(self):
        result = _inline_cypher_params(
            "MATCH (n {id: :id}) RETURN n",
            {"id": 1},
        )
        assert result == "MATCH (n {id: 1}) RETURN n"

    def test_multiple_params(self):
        result = _inline_cypher_params(
            "MATCH (n {id: :id, name: :name}) RETURN n",
            {"id": 1, "name": "Alice"},
        )
        assert ":id" not in result
        assert ":name" not in result
        assert "1" in result
        assert "'Alice'" in result

    def test_preserves_relationship_types(self):
        """Test that relationship types like [:RELATED_TO] are NOT replaced."""
        result = _inline_cypher_params(
            "MATCH (n)-[:RELATED_TO]->(m {id: :id}) RETURN n",
            {"id": 42},
        )
        assert "[:RELATED_TO]" in result
        assert ":id" not in result
        assert "42" in result

    def test_none_param(self):
        result = _inline_cypher_params("SET n.val = :val", {"val": None})
        assert result == "SET n.val = NULL"

    def test_bool_param(self):
        result = _inline_cypher_params("SET n.active = :active", {"active": True})
        assert result == "SET n.active = true"

    def test_no_params_is_noop(self):
        stmt = "MATCH (n) RETURN n"
        assert _inline_cypher_params(stmt, {}) == stmt


# =============================================================================
# Build Cypher Query Tests
# =============================================================================

class TestBuildCypher:
    """Test suite for _build_cypher."""

    def test_basic_query_without_columns(self):
        """Test building query without explicit columns defaults to 'v agtype'."""
        result = _build_cypher("my_graph", "MATCH (n) RETURN n")
        assert "ag_catalog.cypher('my_graph'" in result
        assert "$agecy$" in result
        assert "v ag_catalog.agtype" in result
        assert result.endswith(";")

    def test_query_with_custom_columns(self):
        """Test building query with explicit columns."""
        result = _build_cypher("my_graph", "MATCH (n) RETURN n", cols=["n agtype", "m agtype"])
        assert "n ag_catalog.agtype" in result
        assert "m ag_catalog.agtype" in result

    def test_invalid_graph_name_raises(self):
        """Test that invalid graph name raises InvalidGraphNameException."""
        with pytest.raises(InvalidGraphNameException):
            _build_cypher("ab", "MATCH (n) RETURN n")  # too short

    def test_invalid_column_raises(self):
        """Test that invalid column raises InvalidIdentifierException."""
        with pytest.raises(InvalidIdentifierException):
            _build_cypher("graph", "MATCH (n) RETURN n", cols=["1bad"])

    def test_dollar_quoting_tag_uniqueness(self):
        """Test that dollar quoting tag is unique when statement contains $agecy$."""
        stmt = "RETURN '$agecy$ something'"
        result = _build_cypher("test_graph", stmt)
        # tag should be extended to avoid conflict
        assert "$agecy_$" in result or "$agecy__$" in result or "agecy_" in result


# =============================================================================
# ensure_graph_created Tests
# =============================================================================

class TestEnsureGraphCreated:
    """Test suite for AsyncPostgresqlClient.ensure_graph_created."""

    @pytest.mark.asyncio
    async def test_creates_graph_when_not_exists(self, initialized_async_client):
        """Test that graph is created when it doesn't exist."""
        mock_auto_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0  # graph doesn't exist
        mock_auto_session.execute = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_begin = MagicMock()
        mock_begin.__aenter__ = AsyncMock(return_value=mock_auto_session)
        mock_begin.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin = MagicMock(return_value=mock_begin)
        initialized_async_client._pg_session = MagicMock(return_value=mock_session)

        await initialized_async_client.ensure_graph_created("my_graph")

        # Should have called execute twice: check + create
        assert mock_auto_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_skips_creation_when_exists(self, initialized_async_client):
        """Test that no graph creation occurs when it already exists."""
        mock_auto_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1  # graph already exists
        mock_auto_session.execute = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_begin = MagicMock()
        mock_begin.__aenter__ = AsyncMock(return_value=mock_auto_session)
        mock_begin.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin = MagicMock(return_value=mock_begin)
        initialized_async_client._pg_session = MagicMock(return_value=mock_session)

        await initialized_async_client.ensure_graph_created("my_graph")

        # Should have called execute only once: check only
        mock_auto_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_name_raises(self, initialized_async_client):
        """Test that invalid graph name raises InvalidGraphNameException."""
        with pytest.raises(InvalidGraphNameException):
            await initialized_async_client.ensure_graph_created("ab")  # too short


# =============================================================================
# execute_cypher Tests
# =============================================================================

class TestExecuteCypher:
    """Test suite for AsyncPostgresqlClient.execute_cypher."""

    @pytest.mark.asyncio
    async def test_basic_query_returns_dicts(self, initialized_async_client):
        """Test that execute_cypher returns list of dicts from raw rows."""
        mock_auto_session = AsyncMock()
        mock_row = MagicMock()
        mock_row._mapping = {"v": '{"name": "Alice"}'}
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_auto_session.execute = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_begin = MagicMock()
        mock_begin.__aenter__ = AsyncMock(return_value=mock_auto_session)
        mock_begin.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin = MagicMock(return_value=mock_begin)
        initialized_async_client._pg_session = MagicMock(return_value=mock_session)

        result = await initialized_async_client.execute_cypher(
            "test_graph", "MATCH (n) RETURN n",
        )

        assert len(result) == 1
        assert result[0] == {"v": '{"name": "Alice"}'}

    @pytest.mark.asyncio
    async def test_query_with_columns(self, initialized_async_client):
        """Test execute_cypher with explicit column names."""
        mock_auto_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("Alice", 30)]
        mock_auto_session.execute = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_begin = MagicMock()
        mock_begin.__aenter__ = AsyncMock(return_value=mock_auto_session)
        mock_begin.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin = MagicMock(return_value=mock_begin)
        initialized_async_client._pg_session = MagicMock(return_value=mock_session)

        result = await initialized_async_client.execute_cypher(
            "test_graph",
            "MATCH (n) RETURN n.name, n.age",
            cols=["name agtype", "age agtype"],
        )

        assert len(result) == 1
        assert result[0] == {"name": "Alice", "age": 30}

    @pytest.mark.asyncio
    async def test_query_with_params(self, initialized_async_client):
        """Test execute_cypher with parameter inlining."""
        mock_auto_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_auto_session.execute = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_begin = MagicMock()
        mock_begin.__aenter__ = AsyncMock(return_value=mock_auto_session)
        mock_begin.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin = MagicMock(return_value=mock_begin)
        initialized_async_client._pg_session = MagicMock(return_value=mock_session)

        await initialized_async_client.execute_cypher(
            "test_graph",
            "MATCH (n {id: :id}) RETURN n",
            params={"id": 42},
        )

        # Verify the executed SQL contains the inlined param
        call_args = mock_auto_session.execute.call_args
        sql_text = str(call_args[0][0])
        assert "42" in sql_text

    @pytest.mark.asyncio
    async def test_cleans_whitespace_in_statement(self, initialized_async_client):
        """Test that newlines and tabs are cleaned from Cypher statement."""
        mock_auto_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_auto_session.execute = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_begin = MagicMock()
        mock_begin.__aenter__ = AsyncMock(return_value=mock_auto_session)
        mock_begin.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin = MagicMock(return_value=mock_begin)
        initialized_async_client._pg_session = MagicMock(return_value=mock_session)

        messy_stmt = "MATCH (n)\n\tWHERE n.active\nRETURN n"
        await initialized_async_client.execute_cypher("test_graph", messy_stmt)

        call_args = mock_auto_session.execute.call_args
        sql_text = str(call_args[0][0])
        assert "\n" not in sql_text.split("$agecy$")[1]
        assert "\t" not in sql_text.split("$agecy$")[1]

    @pytest.mark.asyncio
    async def test_invalid_graph_name_raises(self, initialized_async_client):
        """Test that invalid graph name raises InvalidGraphNameException."""
        with pytest.raises(InvalidGraphNameException):
            await initialized_async_client.execute_cypher("ab", "MATCH (n) RETURN n")

    @pytest.mark.asyncio
    async def test_invalid_column_raises(self, initialized_async_client):
        """Test that invalid column raises InvalidIdentifierException."""
        with pytest.raises(InvalidIdentifierException):
            await initialized_async_client.execute_cypher(
                "test_graph", "MATCH (n) RETURN n", cols=["1bad"],
            )
