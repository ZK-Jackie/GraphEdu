"""Neo4j 资源模块单元测试

测试覆盖范围：
- 同步客户端 (Neo4jClient) 的 init/shutdown 流程
- 异步客户端 (AsyncNeo4jClient) 的 init/shutdown 流程
- 查询和执行操作（query/execute）
- 边界情况：连接失败、未初始化调用、关闭失败
- 属性访问：driver、config
"""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from neo4j import AsyncDriver, Driver
import pytest

from graphedu.common.config.modules.datasource.neo4j import Neo4jConfig
from graphedu.common.exceptions.common.resource import (
    GraphDatabaseConnectionException,
    GraphDatabaseDriverException,
    GraphDatabaseQueryException,
)
from graphedu.common.resource.modules.database.neo4j import AsyncNeo4jClient, Neo4jClient

# =============================================================================
# Fixtures: 配置
# =============================================================================

@pytest.fixture
def neo4j_config_normal() -> Neo4jConfig:
    """提供正常的 Neo4j 配置。"""
    return Neo4jConfig(
        dsn="bolt://localhost:7687",
        auth=["neo4j:password"],
        timeout=30
    )


@pytest.fixture
def neo4j_config_custom_db() -> Neo4jConfig:
    """提供自定义数据库名称的 Neo4j 配置。"""
    return Neo4jConfig(
        dsn="bolt://localhost:7688",
        auth=["admin:admin123"]
    )


# =============================================================================
# Fixtures: 未初始化的客户端
# =============================================================================

@pytest.fixture
def neo4j_client_uninit() -> Neo4jClient:
    """提供未初始化的同步 Neo4j 客户端实例。"""
    return Neo4jClient()


@pytest.fixture
def neo4j_async_client_uninit() -> AsyncNeo4jClient:
    """提供未初始化的异步 Neo4j 客户端实例。"""
    return AsyncNeo4jClient()


# =============================================================================
# Fixtures: 已初始化的同步客户端（Container 模式）
# =============================================================================

@pytest.fixture
def neo4j_sync_client(neo4j_config_normal) -> Generator[Neo4jClient]:
    """初始化同步 Neo4j 客户端容器，测试 init 和 shutdown 流程。

    已测试：
    - init 成功并返回 self
    - config 属性正确设置
    - driver 属性正确创建
    - shutdown 成功并清空资源

    Yields:
        Neo4jClient: 已初始化的同步 Neo4j 客户端实例
    """
    client = Neo4jClient()

    # Mock GraphDatabase.driver 以避免真实连接
    with patch('graphedu.common.resource.modules.database.neo4j.GraphDatabase.driver') as mock_driver:
        mock_driver_instance = MagicMock(spec=Driver)
        mock_driver.return_value = mock_driver_instance

        # 初始化并验证
        result = client.init(neo4j_config_normal)

        # 验证初始化（这些就是测试的一部分）
        assert result is client
        assert client.config == neo4j_config_normal
        assert client._driver == mock_driver_instance

        yield client

        # 测试 shutdown
        mock_driver_instance.close = MagicMock()
        client.shutdown()
        assert client._driver is None


# =============================================================================
# Fixtures: 已初始化的异步客户端（Container 模式）
# =============================================================================

@pytest.fixture
async def neo4j_async_client(neo4j_config_normal) -> Generator[AsyncNeo4jClient, None, None]:
    """初始化异步 Neo4j 客户端容器，测试 init 和 shutdown 流程。

    已测试：
    - init 成功并返回 self
    - config 属性正确设置
    - driver 属性正确创建
    - shutdown 成功并清空资源

    Yields:
        AsyncNeo4jClient: 已初始化的异步 Neo4j 客户端实例
    """
    client = AsyncNeo4jClient()

    # Mock AsyncGraphDatabase.driver 以避免真实连接
    with patch('graphedu.common.resource.modules.database.neo4j.AsyncGraphDatabase.driver') as mock_driver:
        mock_driver_instance = MagicMock(spec=AsyncDriver)
        mock_driver.return_value = mock_driver_instance

        # 初始化并验证
        result = await client.init(neo4j_config_normal)

        # 验证初始化（这些就是测试的一部分）
        assert result is client
        assert client.config == neo4j_config_normal
        assert client._drive == mock_driver_instance

        yield client

        # 测试 shutdown
        mock_close = AsyncMock()
        mock_driver_instance.close = mock_close
        await client.shutdown()
        assert client._drive is None


# =============================================================================
# 测试类：同步客户端初始化边界情况
# =============================================================================

class TestNeo4jClientInitEdgeCases:
    """测试 Neo4jClient 初始化的边界情况。"""

    def test_init_with_connection_error(self, neo4j_client_uninit, neo4j_config_normal):
        """测试连接失败时抛出 GraphDatabaseConnectionException。"""
        with patch('graphedu.common.resource.modules.database.neo4j.GraphDatabase.driver') as mock_driver:
            mock_driver.side_effect = Exception("Connection refused")

            with pytest.raises(GraphDatabaseConnectionException) as exc_info:
                neo4j_client_uninit.init(neo4j_config_normal)

            assert exc_info.value.kwargs['db_type'] == "Neo4j"
            assert "Connection refused" in exc_info.value.kwargs['reason']

    def test_init_with_authentication_error(self, neo4j_client_uninit, neo4j_config_normal):
        """测试认证失败时的异常处理。"""
        with patch('graphedu.common.resource.modules.database.neo4j.GraphDatabase.driver') as mock_driver:
            mock_driver.side_effect = Exception("Authentication failed")

            with pytest.raises(GraphDatabaseConnectionException) as exc_info:
                neo4j_client_uninit.init(neo4j_config_normal)

            assert exc_info.value.kwargs['db_type'] == "Neo4j"
            assert "Authentication failed" in exc_info.value.kwargs['reason']

    def test_init_with_timeout_error(self, neo4j_client_uninit, neo4j_config_normal):
        """测试连接超时时的异常处理。"""
        with patch('graphedu.common.resource.modules.database.neo4j.GraphDatabase.driver') as mock_driver:
            mock_driver.side_effect = Exception("Connection timeout")

            with pytest.raises(GraphDatabaseConnectionException) as exc_info:
                neo4j_client_uninit.init(neo4j_config_normal)

            assert exc_info.value.kwargs['db_type'] == "Neo4j"
            assert "Connection timeout" in exc_info.value.kwargs['reason']


class TestAsyncNeo4jClientInitEdgeCases:
    """测试 AsyncNeo4jClient 初始化的边界情况。"""

    @pytest.mark.asyncio
    async def test_async_init_with_connection_error(self, neo4j_async_client_uninit, neo4j_config_normal):
        """测试异步连接失败时抛出 GraphDatabaseConnectionException。"""
        with patch('graphedu.common.resource.modules.database.neo4j.AsyncGraphDatabase.driver') as mock_driver:
            mock_driver.side_effect = Exception("Async connection failed")

            with pytest.raises(GraphDatabaseConnectionException) as exc_info:
                await neo4j_async_client_uninit.init(neo4j_config_normal)

            assert exc_info.value.kwargs['db_type'] == "Neo4j (Async)"
            assert "Async connection failed" in exc_info.value.kwargs['reason']

    @pytest.mark.asyncio
    async def test_async_init_with_dict_config(self, neo4j_async_client_uninit):
        """测试异步客户端支持字典配置初始化。"""
        config_dict = {
            'dsn': 'bolt://localhost:7687',
            'auth': ['neo4j:password']
        }

        with patch('graphedu.common.resource.modules.database.neo4j.AsyncGraphDatabase.driver') as mock_driver:
            mock_driver_instance = MagicMock(spec=AsyncDriver)
            mock_driver.return_value = mock_driver_instance

            await neo4j_async_client_uninit.init(config_dict)

            assert isinstance(neo4j_async_client_uninit.config, Neo4jConfig)
            assert str(neo4j_async_client_uninit.config.dsn) == "bolt://localhost:7687"


# =============================================================================
# 测试类：同步客户端关闭边界情况
# =============================================================================

class TestNeo4jClientShutdownEdgeCases:
    """测试 Neo4jClient 关闭的边界情况。"""

    def test_shutdown_with_close_error(self, neo4j_client_uninit, neo4j_config_normal):
        """测试关闭时 close 失败的情况。"""
        faulty_driver = MagicMock(spec=Driver)
        faulty_driver.close.side_effect = Exception("Close failed")

        with patch('graphedu.common.resource.modules.database.neo4j.GraphDatabase.driver', return_value=faulty_driver):
            neo4j_client_uninit.init(neo4j_config_normal)

            with pytest.raises(GraphDatabaseConnectionException) as exc_info:
                neo4j_client_uninit.shutdown()

            assert exc_info.value.kwargs['db_type'] == "Neo4j"
            assert "Close failed" in exc_info.value.kwargs['reason']

    def test_shutdown_without_init(self, neo4j_client_uninit):
        """测试未初始化时调用 shutdown（应该正常通过）。"""
        # 未初始化时 _driver 为 None，shutdown 应该正常通过
        neo4j_client_uninit.shutdown()
        assert neo4j_client_uninit._driver is None


class TestAsyncNeo4jClientShutdownEdgeCases:
    """测试 AsyncNeo4jClient 关闭的边界情况。"""

    @pytest.mark.asyncio
    async def test_async_shutdown_with_close_error(self, neo4j_async_client_uninit, neo4j_config_normal):
        """测试异步关闭时 close 失败的情况。"""
        faulty_driver = MagicMock(spec=AsyncDriver)
        faulty_driver.close.side_effect = Exception("Async close failed")

        with patch('graphedu.common.resource.modules.database.neo4j.AsyncGraphDatabase.driver', return_value=faulty_driver):
            await neo4j_async_client_uninit.init(neo4j_config_normal)

            with pytest.raises(GraphDatabaseConnectionException) as exc_info:
                await neo4j_async_client_uninit.shutdown()

            assert exc_info.value.kwargs['db_type'] == "Neo4j (Async)"
            assert "Async close failed" in exc_info.value.kwargs['reason']

    @pytest.mark.asyncio
    async def test_async_shutdown_without_init(self, neo4j_async_client_uninit):
        """测试未初始化时调用 async shutdown（应该正常通过）。"""
        # 未初始化时 _drive 为 None，shutdown 应该正常通过
        await neo4j_async_client_uninit.shutdown()
        assert neo4j_async_client_uninit._drive is None


# =============================================================================
# 测试类：同步客户端功能测试
# =============================================================================

class TestNeo4jClientWithContainer:
    """使用已初始化的同步 Neo4j 客户端进行功能测试。"""

    def test_query_success(self, neo4j_sync_client):
        """测试查询功能：成功场景。

        验证：
        - 查询正常执行
        - 返回值符合预期
        - 使用读路由 (routing="r")
        """
        # Arrange
        mock_records = [{"name": "Alice"}, {"name": "Bob"}]
        mock_summary = MagicMock()
        mock_summary.result_available_after = 10
        mock_keys = ["name"]

        neo4j_sync_client._driver.execute_query = MagicMock(
            return_value=(mock_records, mock_summary, mock_keys)
        )

        # Act
        records, summary, keys = neo4j_sync_client.query("MATCH (n:Person) RETURN n.name AS name")

        # Assert
        assert records == mock_records
        assert summary == mock_summary
        assert keys == mock_keys
        neo4j_sync_client._driver.execute_query.assert_called_once_with(
            "MATCH (n:Person) RETURN n.name AS name",
            database_="neo4j",
            routing_="r"
        )

    def test_query_with_custom_database(self, neo4j_sync_client):
        """测试查询功能：使用自定义数据库。"""
        # Arrange
        mock_records = []
        mock_summary = MagicMock()
        mock_keys = []

        neo4j_sync_client._driver.execute_query = MagicMock(
            return_value=(mock_records, mock_summary, mock_keys)
        )

        # Act
        records, summary, keys = neo4j_sync_client.query(
            "MATCH (n) RETURN n",
            database="custom_db"
        )

        # Assert
        neo4j_sync_client._driver.execute_query.assert_called_once_with(
            "MATCH (n) RETURN n",
            database_="custom_db",
            routing_="r"
        )

    def test_query_with_parameters(self, neo4j_sync_client):
        """测试查询功能：带参数的查询。"""
        # Arrange
        mock_records = [{"name": "Charlie"}]
        mock_summary = MagicMock()
        mock_keys = ["name"]

        neo4j_sync_client._driver.execute_query = MagicMock(
            return_value=(mock_records, mock_summary, mock_keys)
        )

        # Act
        records, _, _ = neo4j_sync_client.query(
            "MATCH (n:Person {name: $name}) RETURN n",
            name="Charlie"
        )

        # Assert
        assert records == mock_records
        neo4j_sync_client._driver.execute_query.assert_called_once()

    def test_query_without_init(self, neo4j_client_uninit):
        """测试未初始化时调用查询。"""
        with pytest.raises(GraphDatabaseDriverException) as exc_info:
            neo4j_client_uninit.query("MATCH (n) RETURN n")

        assert "not initialized" in exc_info.value.kwargs['reason']
        assert exc_info.value.kwargs['operation'] == "query"

    def test_query_with_execution_error(self, neo4j_sync_client):
        """测试查询执行失败时的异常处理。"""
        neo4j_sync_client._driver.execute_query.side_effect = Exception("Query syntax error")

        with pytest.raises(GraphDatabaseQueryException) as exc_info:
            neo4j_sync_client.query("INVALID CYPHER")

        assert exc_info.value.kwargs['db_type'] == "Neo4j"
        assert "Query syntax error" in exc_info.value.kwargs['reason']
        assert exc_info.value.kwargs['query'] == "INVALID CYPHER"

    def test_execute_success(self, neo4j_sync_client):
        """测试写操作功能：成功场景。

        验证：
        - 写操作正常执行
        - 返回值符合预期
        - 使用写路由 (routing="w")
        """
        # Arrange
        mock_result = MagicMock()
        mock_result.counters.nodes_created = 1
        mock_result.counters.relationships_created = 0

        neo4j_sync_client._driver.execute_query = MagicMock(return_value=mock_result)

        # Act
        result = neo4j_sync_client.execute("CREATE (n:Person {name: 'Alice'})")

        # Assert
        assert result == mock_result
        neo4j_sync_client._driver.execute_query.assert_called_once_with(
            "CREATE (n:Person {name: 'Alice'})",
            database_="neo4j",
            routing_="w"
        )

    def test_execute_with_custom_database(self, neo4j_sync_client):
        """测试写操作功能：使用自定义数据库。"""
        # Arrange
        mock_result = MagicMock()
        neo4j_sync_client._driver.execute_query = MagicMock(return_value=mock_result)

        # Act
        result = neo4j_sync_client.execute(
            "CREATE (n:Node)",
            database="test_db"
        )

        # Assert
        assert result == mock_result
        neo4j_sync_client._driver.execute_query.assert_called_once_with(
            "CREATE (n:Node)",
            database_="test_db",
            routing_="w"
        )

    def test_execute_with_parameters(self, neo4j_sync_client):
        """测试写操作功能：带参数的执行。"""
        # Arrange
        mock_result = MagicMock()
        neo4j_sync_client._driver.execute_query = MagicMock(return_value=mock_result)

        # Act
        result = neo4j_sync_client.execute(
            "CREATE (n:Person {name: $name, age: $age})",
            name="Bob",
            age=30
        )

        # Assert
        assert result == mock_result
        call_args = neo4j_sync_client._driver.execute_query.call_args
        assert call_args.kwargs["name"] == "Bob"
        assert call_args.kwargs["age"] == 30

    def test_execute_without_init(self, neo4j_client_uninit):
        """测试未初始化时调用写操作。"""
        with pytest.raises(GraphDatabaseDriverException) as exc_info:
            neo4j_client_uninit.execute("CREATE (n)")

        assert "not initialized" in exc_info.value.kwargs['reason']
        assert exc_info.value.kwargs['operation'] == "execute"

    def test_execute_with_execution_error(self, neo4j_sync_client):
        """测试写操作执行失败时的异常处理。"""
        neo4j_sync_client._driver.execute_query.side_effect = Exception("Constraint validation failed")

        with pytest.raises(GraphDatabaseQueryException) as exc_info:
            neo4j_sync_client.execute("CREATE (n:Person {id: 'duplicate'})")

        assert exc_info.value.kwargs['db_type'] == "Neo4j"
        assert "Constraint validation failed" in exc_info.value.kwargs['reason']
        assert exc_info.value.kwargs['query'] == "CREATE (n:Person {id: 'duplicate'})"


# =============================================================================
# 测试类：异步客户端功能测试
# =============================================================================

class TestAsyncNeo4jClientWithContainer:
    """使用已初始化的异步 Neo4j 客户端进行功能测试。"""

    @pytest.mark.asyncio
    async def test_async_query_success(self, neo4j_async_client):
        """测试异步查询功能：成功场景。

        验证：
        - 查询正常执行
        - 返回值符合预期
        - 使用读路由 (routing="r")
        """
        # Arrange
        mock_records = [{"name": "Alice"}, {"name": "Bob"}]
        mock_summary = MagicMock()
        mock_summary.result_available_after = 10
        mock_keys = ["name"]

        async_mock = AsyncMock(return_value=(mock_records, mock_summary, mock_keys))
        neo4j_async_client._drive.execute_query = async_mock

        # Act
        records, summary, keys = await neo4j_async_client.query("MATCH (n:Person) RETURN n.name AS name")

        # Assert
        assert records == mock_records
        assert summary == mock_summary
        assert keys == mock_keys

    @pytest.mark.asyncio
    async def test_async_query_with_custom_database(self, neo4j_async_client):
        """测试异步查询功能：使用自定义数据库。"""
        # Arrange
        mock_records = []
        mock_summary = MagicMock()
        mock_keys = []

        async_mock = AsyncMock(return_value=(mock_records, mock_summary, mock_keys))
        neo4j_async_client._drive.execute_query = async_mock

        # Act
        records, summary, keys = await neo4j_async_client.query(
            "MATCH (n) RETURN n",
            database="custom_db"
        )

        # Assert
        assert records == mock_records
        assert summary == mock_summary
        assert keys == mock_keys

    @pytest.mark.asyncio
    async def test_async_query_with_parameters(self, neo4j_async_client):
        """测试异步查询功能：带参数的查询。"""
        # Arrange
        mock_records = [{"name": "Charlie"}]
        mock_summary = MagicMock()
        mock_keys = ["name"]

        async_mock = AsyncMock(return_value=(mock_records, mock_summary, mock_keys))
        neo4j_async_client._drive.execute_query = async_mock

        # Act
        records, _, _ = await neo4j_async_client.query(
            "MATCH (n:Person {name: $name}) RETURN n",
            name="Charlie"
        )

        # Assert
        assert records == mock_records
        async_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_query_without_init(self, neo4j_async_client_uninit):
        """测试未初始化时调用异步查询。"""
        with pytest.raises(GraphDatabaseDriverException) as exc_info:
            await neo4j_async_client_uninit.query("MATCH (n) RETURN n")

        assert "not initialized" in exc_info.value.kwargs['reason']
        assert exc_info.value.kwargs['operation'] == "query"

    @pytest.mark.asyncio
    async def test_async_query_with_execution_error(self, neo4j_async_client):
        """测试异步查询执行失败时的异常处理。"""
        async_mock = AsyncMock(side_effect=Exception("Async query failed"))
        neo4j_async_client._drive.execute_query = async_mock

        with pytest.raises(GraphDatabaseQueryException) as exc_info:
            await neo4j_async_client.query("INVALID ASYNC CYPHER")

        assert exc_info.value.kwargs['db_type'] == "Neo4j (Async)"
        assert "Async query failed" in exc_info.value.kwargs['reason']
        assert exc_info.value.kwargs['query'] == "INVALID ASYNC CYPHER"

    @pytest.mark.asyncio
    async def test_async_execute_success(self, neo4j_async_client):
        """测试异步写操作功能：成功场景。

        验证：
        - 写操作正常执行
        - 返回值符合预期
        - 使用写路由 (routing="w")
        """
        # Arrange
        mock_result = MagicMock()
        mock_result.counters.nodes_created = 1

        async_mock = AsyncMock(return_value=mock_result)
        neo4j_async_client._drive.execute_query = async_mock

        # Act
        result = await neo4j_async_client.execute("CREATE (n:Person {name: 'Alice'})")

        # Assert
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_async_execute_with_custom_database(self, neo4j_async_client):
        """测试异步写操作功能：使用自定义数据库。"""
        # Arrange
        mock_result = MagicMock()

        async_mock = AsyncMock(return_value=mock_result)
        neo4j_async_client._drive.execute_query = async_mock

        # Act
        result = await neo4j_async_client.execute(
            "CREATE (n:Node)",
            database="test_db"
        )

        # Assert
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_async_execute_with_parameters(self, neo4j_async_client):
        """测试异步写操作功能：带参数的执行。"""
        # Arrange
        mock_result = MagicMock()

        async_mock = AsyncMock(return_value=mock_result)
        neo4j_async_client._drive.execute_query = async_mock

        # Act
        result = await neo4j_async_client.execute(
            "CREATE (n:Person {name: $name, age: $age})",
            name="Bob",
            age=30
        )

        # Assert
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_async_execute_without_init(self, neo4j_async_client_uninit):
        """测试未初始化时调用异步写操作。"""
        with pytest.raises(GraphDatabaseDriverException) as exc_info:
            await neo4j_async_client_uninit.execute("CREATE (n)")

        assert "not initialized" in exc_info.value.kwargs['reason']
        assert exc_info.value.kwargs['operation'] == "execute"

    @pytest.mark.asyncio
    async def test_async_execute_with_execution_error(self, neo4j_async_client):
        """测试异步写操作执行失败时的异常处理。"""
        async_mock = AsyncMock(side_effect=Exception("Async constraint validation failed"))
        neo4j_async_client._drive.execute_query = async_mock

        with pytest.raises(GraphDatabaseQueryException) as exc_info:
            await neo4j_async_client.execute("CREATE (n:Person {id: 'duplicate'})")

        assert exc_info.value.kwargs['db_type'] == "Neo4j (Async)"
        assert "Async constraint validation failed" in exc_info.value.kwargs['reason']
        assert exc_info.value.kwargs['query'] == "CREATE (n:Person {id: 'duplicate'})"


# =============================================================================
# 测试类：属性访问
# =============================================================================

class TestNeo4jClientProperties:
    """测试 Neo4jClient 的属性访问。"""

    def test_config_property_returns_config(self, neo4j_sync_client, neo4j_config_normal):
        """测试 config 属性返回正确的配置对象。"""
        assert isinstance(neo4j_sync_client.config, Neo4jConfig)
        assert str(neo4j_sync_client.config.dsn) == str(neo4j_config_normal.dsn)
        assert neo4j_sync_client.config.auth == neo4j_config_normal.auth

    def test_driver_property_returns_driver(self, neo4j_sync_client):
        """测试 driver 属性返回驱动对象。"""
        assert neo4j_sync_client.driver is not None
        assert neo4j_sync_client.driver == neo4j_sync_client._driver

    def test_driver_property_when_uninitialized(self, neo4j_client_uninit):
        """测试未初始化时 driver 属性返回 None。"""
        assert neo4j_client_uninit.driver is None

    def test_mode_attribute(self, neo4j_client_uninit):
        """测试 mode 属性值为 'sync'。"""
        assert neo4j_client_uninit.mode == "sync"


class TestAsyncNeo4jClientProperties:
    """测试 AsyncNeo4jClient 的属性访问。"""

    @pytest.mark.asyncio
    async def test_config_property_returns_config(self, neo4j_async_client, neo4j_config_normal):
        """测试 config 属性返回正确的配置对象。"""
        assert isinstance(neo4j_async_client.config, Neo4jConfig)
        assert str(neo4j_async_client.config.dsn) == str(neo4j_config_normal.dsn)
        assert neo4j_async_client.config.auth == neo4j_config_normal.auth

    @pytest.mark.asyncio
    async def test_driver_property_returns_driver(self, neo4j_async_client):
        """测试 driver 属性返回异步驱动对象。"""
        assert neo4j_async_client.driver is not None
        assert neo4j_async_client.driver == neo4j_async_client._drive

    @pytest.mark.asyncio
    async def test_driver_property_when_uninitialized(self, neo4j_async_client_uninit):
        """测试未初始化时 driver 属性返回 None。"""
        assert neo4j_async_client_uninit.driver is None


# =============================================================================
# 测试类：完整生命周期
# =============================================================================

class TestNeo4jClientLifecycle:
    """测试 Neo4jClient 的完整生命周期。"""

    def test_full_lifecycle_with_mock(self, neo4j_config_normal):
        """测试完整的生命周期：初始化 -> 查询 -> 写操作 -> 关闭。"""
        client = Neo4jClient()

        with patch('graphedu.common.resource.modules.database.neo4j.GraphDatabase.driver') as mock_driver:
            mock_driver_instance = MagicMock(spec=Driver)
            mock_driver.return_value = mock_driver_instance

            # 1. 初始化
            client.init(neo4j_config_normal)
            assert client._driver is not None
            assert client.config == neo4j_config_normal

            # 2. 执行查询
            mock_records = [{"name": "Alice"}]
            mock_summary = MagicMock()
            mock_keys = ["name"]

            mock_driver_instance.execute_query = MagicMock(
                return_value=(mock_records, mock_summary, mock_keys)
            )

            records, summary, keys = client.query("MATCH (n) RETURN n")
            assert records == mock_records

            # 3. 执行写操作
            mock_result = MagicMock()
            mock_driver_instance.execute_query = MagicMock(return_value=mock_result)

            result = client.execute("CREATE (n)")
            assert result == mock_result

            # 4. 关闭
            mock_driver_instance.close = MagicMock()
            client.shutdown()
            assert client._driver is None

            # 验证 close 被调用
            mock_driver_instance.close.assert_called_once()


class TestAsyncNeo4jClientLifecycle:
    """测试 AsyncNeo4jClient 的完整生命周期。"""

    @pytest.mark.asyncio
    async def test_async_full_lifecycle_with_mock(self, neo4j_config_normal):
        """测试异步客户端的完整生命周期。"""
        client = AsyncNeo4jClient()

        with patch('graphedu.common.resource.modules.database.neo4j.AsyncGraphDatabase.driver') as mock_driver:
            mock_driver_instance = MagicMock(spec=AsyncDriver)
            mock_driver.return_value = mock_driver_instance

            # 1. 初始化
            await client.init(neo4j_config_normal)
            assert client._drive is not None
            assert client.config == neo4j_config_normal

            # 2. 执行查询
            mock_records = [{"name": "Alice"}]
            mock_summary = MagicMock()
            mock_keys = ["name"]

            async_mock = AsyncMock(return_value=(mock_records, mock_summary, mock_keys))
            mock_driver_instance.execute_query = async_mock

            records, summary, keys = await client.query("MATCH (n) RETURN n")
            assert records == mock_records

            # 3. 关闭
            async_close_mock = AsyncMock()
            mock_driver_instance.close = async_close_mock
            await client.shutdown()
            assert client._drive is None

            # 验证 close 被调用
            async_close_mock.assert_called_once()
