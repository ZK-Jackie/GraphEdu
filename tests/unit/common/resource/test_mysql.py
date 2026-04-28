"""
MySQL 客户端测试模块

测试同步和异步 MySQL 客户端的功能，包括：
- 引擎和会话管理
- 事务处理
- 驱动规范化（aiomysql <-> pymysql）
- 异常处理

注意：init 和 shutdown 的正常流程已在容器 fixture 中测试。
"""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from dependency_injector import containers, providers
import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import Session

from graphedu.common.config.modules.datasource.base import PoolConfig
from graphedu.common.config.modules.datasource.mysql import MysqlConfig
from graphedu.common.exceptions.common.resource import (
    DatabaseConnectionException,
    DatabaseEngineException,
    DatabaseSessionException,
    DatabaseTransactionException,
)
from graphedu.common.resource import AsyncMysqlClient, MysqlClient

# =============================================================================
# 主容器 Fixture：测试 init 和 shutdown
# =============================================================================

@pytest.fixture
def mysql_sync_container() -> Generator[MysqlClient]:
    """初始化同步 MySQL 客户端容器，测试 init 和 shutdown 流程。

    已测试：
    - init 成功并返回 self
    - config 属性正确设置
    - engine 属性正确创建
    - session 工厂正确创建
    - shutdown 成功并清空资源

    Yields:
        MysqlClient: 已初始化的同步 MySQL 客户端实例
    """
    config = MysqlConfig(
        dsn="mysql+pymysql://test_user:test_pass@localhost:3306/test_db",
        pool=PoolConfig(pool_size=5),
    )

    class SyncMysqlContainer(containers.DeclarativeContainer):
        """同步 MySQL 客户端容器。"""

        mysql_client: providers.Provider[MysqlClient] = providers.Resource(MysqlClient, config=config)

    # Mock create_engine 避免真实连接
    with patch("graphedu.common.resource.modules.database.mysql.create_engine") as mock_create:
        mock_engine = MagicMock(spec=Engine)
        mock_create.return_value = mock_engine

        # 调用 init
        container = SyncMysqlContainer()
        container.init_resources()
        client: MysqlClient = container.mysql_client()

        # 验证初始化成功（这些就是测试）
        assert client.config == config
        assert client._mysql_engine == mock_engine
        assert client._mysql_session is not None

        # Mock dispose 用于 shutdown
        mock_engine.dispose = MagicMock()

        yield client

        # 测试 shutdown
        client.shutdown()
        assert client._mysql_session is None


@pytest.fixture
async def mysql_async_container() -> AsyncGenerator[AsyncMysqlClient, None]:
    """初始化异步 MySQL 客户端容器，测试 init 和 shutdown 流程。

    已测试：
    - init 成功并返回 self
    - config 属性正确设置
    - engine 属性正确创建
    - session 工厂正确创建
    - shutdown 成功并清空资源

    Yields:
        AsyncMysqlClient: 已初始化的异步 MySQL 客户端实例
    """
    config = MysqlConfig(
        dsn="mysql+pymysql://test_user:test_pass@localhost:3306/test_db",
        pool=PoolConfig(pool_size=5),
    )

    class AsyncMysqlContainer(containers.DeclarativeContainer):
        """异步 MySQL 客户端容器。"""

        mysql_client: providers.Provider[AsyncMysqlClient] = providers.Resource(
            AsyncMysqlClient, config=config
        )

    # Mock create_async_engine 避免真实连接
    with patch("graphedu.common.resource.modules.database.mysql.create_async_engine") as mock_create:
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create.return_value = mock_engine

        # 调用 init
        container = AsyncMysqlContainer()
        await container.init_resources()
        client: AsyncMysqlClient = await container.mysql_client()

        # 验证初始化成功（这些就是测试）
        assert client.config == config
        assert client._mysql_engine == mock_engine
        assert client._mysql_session is not None

        # Mock dispose 用于 shutdown
        async_mock = AsyncMock()
        mock_engine.dispose = async_mock

        yield client

        # 测试 shutdown
        await client.shutdown()
        assert client._mysql_session is None


# =============================================================================
# 未初始化的客户端 Fixtures（用于测试边界情况）
# =============================================================================

@pytest.fixture
def mysql_sync_client_uninit() -> MysqlClient:
    """提供未初始化的同步 MySQL 客户端实例。"""
    return MysqlClient()


@pytest.fixture
def mysql_async_client_uninit() -> AsyncMysqlClient:
    """提供未初始化的异步 MySQL 客户端实例。"""
    return AsyncMysqlClient()


# =============================================================================
# 配置 Fixtures
# =============================================================================

@pytest.fixture
def mysql_config_aiomysql() -> MysqlConfig:
    """提供使用 aiomysql 驱动的配置（用于测试驱动规范化）。"""
    return MysqlConfig(
        dsn="mysql+aiomysql://user:pass@localhost:3306/graphedu",
        pool=PoolConfig(pool_size=5),
    )


@pytest.fixture
def mysql_config_pymysql() -> MysqlConfig:
    """提供使用 pymysql 驱动的配置。"""
    return MysqlConfig(
        dsn="mysql+pymysql://user:pass@localhost:3306/graphedu",
        pool=PoolConfig(pool_size=5),
    )


# =============================================================================
# Mock 对象 Fixtures
# =============================================================================

@pytest.fixture
def mock_sync_session() -> MagicMock:
    """提供 Mock 的同步会话。"""
    session = MagicMock(spec=Session)
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def mock_async_session() -> AsyncMock:
    """提供 Mock 的异步会话。"""
    session = AsyncMock(spec=AsyncSession)
    session.close = AsyncMock()

    # Mock async context manager for session.begin()
    mock_begin = MagicMock()
    mock_begin.__aenter__ = AsyncMock(return_value=session)
    mock_begin.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=mock_begin)

    return session


# =============================================================================
# 测试类：使用已初始化的容器进行功能测试
# =============================================================================

class TestMysqlClientWithContainer:
    """使用已初始化的同步 MySQL 客户端容器进行功能测试。"""

    def test_session_context_manager_success(self, mysql_sync_container, mock_sync_session):
        """测试会话上下文管理器的成功场景。

        验证：
        - 可以正确获取会话
        - 成功时自动 commit
        - 成功时自动 close
        """
        # Mock 会话工厂返回我们的 mock session
        mysql_sync_container._mysql_session = MagicMock(return_value=mock_sync_session)

        # 使用会话上下文管理器
        with mysql_sync_container.session() as session:
            assert session == mock_sync_session

        # 验证 commit 被调用
        mock_sync_session.commit.assert_called_once()

        # 验证 close 被调用
        mock_sync_session.close.assert_called_once()

    def test_session_context_manager_rollback_on_error(self, mysql_sync_container):
        """测试会话上下文管理器在错误时回滚。

        验证：
        - 失败时自动 rollback
        - 失败时仍然 close
        - 抛出 DatabaseTransactionException
        """
        # 创建会话并在 commit 时抛出错误
        mock_session = MagicMock(spec=Session)
        mock_session.commit.side_effect = SQLAlchemyError("Transaction failed")
        mysql_sync_container._mysql_session = MagicMock(return_value=mock_session)

        # 使用会话时应该抛出异常并回滚
        with pytest.raises(DatabaseTransactionException):
            with mysql_sync_container.session():
                pass

        # 验证 rollback 被调用
        mock_session.rollback.assert_called_once()

        # 验证 close 仍被调用
        mock_session.close.assert_called_once()


class TestAsyncMysqlClientWithContainer:
    """使用已初始化的异步 MySQL 客户端容器进行功能测试。"""

    @pytest.mark.asyncio
    async def test_session_context_manager_success(self, mysql_async_container, mock_async_session):
        """测试异步会话上下文管理器的成功场景。

        验证：
        - 可以正确获取异步会话
        - 成功时自动 close
        """
        # Mock 会话工厂返回我们的 mock session
        mysql_async_container._mysql_session = MagicMock(return_value=mock_async_session)

        # 使用会话上下文管理器
        async with mysql_async_container.session() as session:
            assert session == mock_async_session

        # 验证 close 被调用
        mock_async_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_context_manager_rollback_on_error(self, mysql_async_container):
        """测试异步会话上下文管理器在错误时回滚。

        验证：
        - 失败时自动 close
        - 抛出 DatabaseTransactionException
        """
        # 创建会话并在 begin 时抛出错误
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.close = AsyncMock()

        mock_begin = MagicMock()
        mock_begin.__aenter__.side_effect = SQLAlchemyError("Transaction failed")
        mock_begin.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin = MagicMock(return_value=mock_begin)

        mysql_async_container._mysql_session = MagicMock(return_value=mock_session)

        # 使用会话时应该抛出异常
        with pytest.raises(DatabaseTransactionException):
            async with mysql_async_container.session():
                pass

        # 验证 close 仍被调用
        mock_session.close.assert_called_once()

    def test_session_generator_classmethod(self, mysql_async_container, mock_async_session):
        """测试 session_generator 类方法（用于依赖注入）。

        验证：
        - 类方法返回异步上下文管理器
        - 上下文管理器具有正确的接口
        """
        # 设置会话工厂
        mysql_async_container._mysql_session = MagicMock(return_value=mock_async_session)

        # 使用类方法获取会话上下文管理器
        context_manager = AsyncMysqlClient.session_generator(mysql_async_container)

        # 验证返回的是会话上下文管理器
        assert context_manager is not None
        assert hasattr(context_manager, "__aenter__")
        assert hasattr(context_manager, "__aexit__")


# =============================================================================
# 测试类：初始化边界情况
# =============================================================================

class TestMysqlClientInitEdgeCases:
    """测试 MysqlClient 初始化的边界情况。"""

    def test_init_normalizes_aiomysql_to_pymysql(self, mysql_sync_client_uninit, mysql_config_aiomysql):
        """测试驱动规范化：同步客户端应将 aiomysql 替换为 pymysql。"""
        with patch("graphedu.common.resource.modules.database.mysql.create_engine") as mock_create:
            mock_engine = MagicMock(spec=Engine)
            mock_create.return_value = mock_engine

            mysql_sync_client_uninit.init(mysql_config_aiomysql)

            # 验证 create_engine 被调用时使用的是 pymysql
            call_args = mock_create.call_args
            url = call_args[0][0]
            assert "pymysql" in url
            assert "aiomysql" not in url

    def test_init_with_connection_error(self, mysql_sync_client_uninit, mysql_config_pymysql):
        """测试连接失败时抛出 DatabaseConnectionException。"""
        with patch("graphedu.common.resource.modules.database.mysql.create_engine") as mock_create:
            mock_create.side_effect = SQLAlchemyError("Connection refused")

            with pytest.raises(DatabaseConnectionException) as exc_info:
                mysql_sync_client_uninit.init(mysql_config_pymysql)

            assert exc_info.value.kwargs.get("db_type") == "MySQL"
            assert "Connection refused" in exc_info.value.message

    def test_init_with_unexpected_error(self, mysql_sync_client_uninit, mysql_config_pymysql):
        """测试初始化时的意外错误。"""
        with patch("graphedu.common.resource.modules.database.mysql.create_engine") as mock_create:
            mock_create.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(DatabaseConnectionException) as exc_info:
                mysql_sync_client_uninit.init(mysql_config_pymysql)

            assert exc_info.value.kwargs.get("db_type") == "MySQL"
            assert "Unexpected error" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_async_init_with_dict_config(self, mysql_async_client_uninit):
        """测试异步客户端支持字典配置初始化。"""
        config_dict = {"dsn": "mysql+pymysql://user:pass@localhost/db"}

        with patch("graphedu.common.resource.modules.database.mysql.create_async_engine") as mock_create:
            mock_engine = MagicMock(spec=AsyncEngine)
            mock_create.return_value = mock_engine

            await mysql_async_client_uninit.init(config_dict)

            # 验证配置被正确转换
            assert isinstance(mysql_async_client_uninit.config, MysqlConfig)
            assert mysql_async_client_uninit.config.dsn == config_dict["dsn"]

    @pytest.mark.asyncio
    async def test_async_init_with_connection_error(self, mysql_async_client_uninit, mysql_config_pymysql):
        """测试异步连接失败时抛出 DatabaseConnectionException。"""
        with patch("graphedu.common.resource.modules.database.mysql.create_async_engine") as mock_create:
            mock_create.side_effect = SQLAlchemyError("Connection refused")

            with pytest.raises(DatabaseConnectionException) as exc_info:
                await mysql_async_client_uninit.init(mysql_config_pymysql)

            assert exc_info.value.kwargs.get("db_type") == "MySQL (Async)"
            assert "Connection refused" in exc_info.value.message




# =============================================================================
# 测试类：关闭边界情况
# =============================================================================

class TestMysqlClientShutdownEdgeCases:
    """测试 MysqlClient 关闭的边界情况。"""

    def test_shutdown_with_dispose_error(self, mysql_sync_client_uninit, mysql_config_pymysql):
        """测试关闭时 dispose 失败的情况。"""
        faulty_engine = MagicMock(spec=Engine)
        faulty_engine.dispose.side_effect = SQLAlchemyError("Dispose failed")

        with patch("graphedu.common.resource.modules.database.mysql.create_engine", return_value=faulty_engine):
            mysql_sync_client_uninit.init(mysql_config_pymysql)

            with pytest.raises(DatabaseEngineException) as exc_info:
                mysql_sync_client_uninit.shutdown()

            assert exc_info.value.kwargs.get("operation") == "dispose"
            assert "Dispose failed" in exc_info.value.message


class TestAsyncMysqlClientShutdownEdgeCases:
    """测试 AsyncMysqlClient 关闭的边界情况。"""

    @pytest.mark.asyncio
    async def test_shutdown_with_dispose_error(self, mysql_async_client_uninit, mysql_config_pymysql):
        """测试关闭时 dispose 失败的情况。"""
        faulty_engine = MagicMock(spec=AsyncEngine)
        faulty_engine.dispose = AsyncMock(side_effect=SQLAlchemyError("Dispose failed"))

        with patch("graphedu.common.resource.modules.database.mysql.create_async_engine", return_value=faulty_engine):
            await mysql_async_client_uninit.init(mysql_config_pymysql)

            with pytest.raises(DatabaseEngineException) as exc_info:
                await mysql_async_client_uninit.shutdown()

            assert exc_info.value.kwargs.get("operation") == "dispose"
            assert "Dispose failed" in exc_info.value.message


# =============================================================================
# 测试类：属性访问
# =============================================================================

class TestMysqlClientProperties:
    """测试 MysqlClient 的属性访问。"""

    def test_config_property_returns_mysql_config(self, mysql_sync_container):
        """测试 config 属性返回 MysqlConfig 对象。"""
        assert isinstance(mysql_sync_container.config, MysqlConfig)
        assert str(mysql_sync_container.config.dsn).startswith("mysql+")

    def test_engine_property_returns_engine(self, mysql_sync_container):
        """测试 engine 属性返回 Engine 对象。"""
        assert mysql_sync_container.engine is not None
        # 注意：由于我们 mock 了 engine，它不是真正的 Engine 实例
        # 但我们可以验证它不是 None


class TestAsyncMysqlClientProperties:
    """测试 AsyncMysqlClient 的属性访问。"""

    @pytest.mark.asyncio
    async def test_config_property_returns_mysql_config(self, mysql_async_container):
        """测试 config 属性返回 MysqlConfig 对象。"""
        assert isinstance(mysql_async_container.config, MysqlConfig)
        assert str(mysql_async_container.config.dsn).startswith("mysql+")

    @pytest.mark.asyncio
    async def test_engine_property_returns_async_engine(self, mysql_async_container):
        """测试 engine 属性返回 AsyncEngine 对象。"""
        assert mysql_async_container.engine is not None
        # 注意：由于我们 mock 了 engine，它不是真正的 AsyncEngine 实例
        # 但我们可以验证它不是 None


# =============================================================================
# 测试类：会话错误情况
# =============================================================================

class TestMysqlClientSessionErrors:
    """测试未初始化时的会话错误。"""

    def test_session_without_init(self, mysql_sync_client_uninit):
        """测试未初始化时创建会话抛出异常。"""
        with pytest.raises(DatabaseSessionException) as exc_info:  # noqa: SIM117
            with mysql_sync_client_uninit.session():
                pass

        assert "not initialized" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_async_session_without_init(self, mysql_async_client_uninit):
        """测试未初始化时创建异步会话抛出异常。"""
        with pytest.raises(DatabaseSessionException) as exc_info:
            async with mysql_async_client_uninit.session():
                pass

        assert "not initialized" in exc_info.value.message.lower()
