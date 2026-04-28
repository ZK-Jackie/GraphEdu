"""Neo4j graph database resource module.

This module provides synchronous and asynchronous Neo4j graph database clients
with connection management, query execution, and proper error handling.
"""

import logging
from typing import Any, LiteralString, Self

from neo4j import AsyncDriver, AsyncGraphDatabase, Driver, GraphDatabase

from graphedu.common.config.modules.datasource import Neo4jConfig
from graphedu.common.exceptions import (
    GraphDatabaseConnectionException,
    GraphDatabaseDriverException,
    GraphDatabaseQueryException,
)
from graphedu.common.resource.core.base import BaseAsyncResource, BaseSyncResource

logger = logging.getLogger(__name__)


class Neo4jClient(BaseSyncResource):
    """Synchronous Neo4j graph database client.

    This client manages a Neo4j driver for synchronous graph database operations
    including queries, writes, and connection management.

    Attributes:
        config (Neo4jConfig | None): Neo4j connection configuration.
        mode (str): Operation mode indicator, set to "sync".
        _driver (Driver | None): Neo4j driver instance.

    Raises:
        GraphDatabaseConnectionException: If connection to Neo4j fails.
        GraphDatabaseDriverException: If driver operation fails.
        GraphDatabaseQueryException: If query execution fails.
    """

    config: Neo4jConfig | None = None
    mode = "sync"
    _driver: Driver | None = None

    @property
    def driver(self) -> Driver | None:
        """Get the Neo4j driver instance.

        Returns:
            Driver | None: The Neo4j driver or None if not initialized.
        """
        return self._driver

    def init(self, config: Neo4jConfig) -> Self:
        """Initialize the Neo4j client with a driver connection.

        Creates a Neo4j driver instance with the provided configuration
        for synchronous database operations.

        Args:
            config: Neo4j configuration containing URI and authentication credentials.

        Returns:
            Self: Returns self for method chaining.

        Raises:
            GraphDatabaseConnectionException: If connection to Neo4j fails.

        Examples:
            >>> config = Neo4jConfig(uri="bolt://localhost:7687", username="neo4j", password="pass")
            >>> client = Neo4jClient().init(config)
        """
        self.config = config
        try:
            self._driver = GraphDatabase.driver(uri=str(self.config.dsn), auth=self.config.get_auth_tuples())
            logger.debug(f"Neo4j sync driver connected: {self._driver}")
            logger.info(f"Neo4j synchronous driver has successfully connected to {self.config.dsn!s}")
            return self
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}", exc_info=True)
            raise GraphDatabaseConnectionException(reason=str(e), db_type="Neo4j") from e

    def query(self, query: LiteralString, database: str = "neo4j", **kwargs) -> tuple[list[dict], Any, list[str]]:
        """Execute a read query on the Neo4j database.

        Executes a Cypher query with read routing, typically used for
        queries that read data from the graph.

        Args:
            query: Cypher query string to execute (must be a literal string for security).
            database: Name of the Neo4j database to query. Defaults to "neo4j".
            **kwargs: Additional parameters to pass to the query.

        Returns:
            tuple[list[dict], Any, list[str]]: A tuple containing:
                - List of result records as dictionaries
                - Query summary metadata
                - List of result keys

        Raises:
            GraphDatabaseDriverException: If driver is not initialized.
            GraphDatabaseQueryException: If query execution fails.

        Examples:
            >>> records, summary, keys = client.query("MATCH (n:Person) RETURN n LIMIT 10")
            >>> for record in records:
            ...     print(record)
        """
        if not self._driver:
            raise GraphDatabaseDriverException(operation="query", reason="driver not initialized. Call init() first.")

        logger.debug(f"Neo4j sync query: {query}, using database: {database}, with kwargs: {kwargs}")
        try:
            records, summary, keys = self._driver.execute_query(query, database_=database, routing_="r", **kwargs)
            return records, summary, keys
        except Exception as e:
            logger.error(f"Neo4j query execution failed: {e}", exc_info=True)
            raise GraphDatabaseQueryException(reason=str(e), query=query, db_type="Neo4j") from e

    def execute(self, query: LiteralString, database: str = "neo4j", **kwargs) -> Any:
        """Execute a write query on the Neo4j database.

        Executes a Cypher query with write routing, typically used for
        queries that modify data in the graph.

        Args:
            query: Cypher query string to execute (must be a literal string for security).
            database: Name of the Neo4j database to execute on. Defaults to "neo4j".
            **kwargs: Additional parameters to pass to the query.

        Returns:
            Any: Query result, typically containing summary information.

        Raises:
            GraphDatabaseDriverException: If driver is not initialized.
            GraphDatabaseQueryException: If query execution fails.

        Examples:
            >>> result = client.execute("CREATE (n:Person {name: 'Alice'})")
            >>> print(f"Created {result.counters.nodes_created} nodes")
        """
        if not self._driver:
            raise GraphDatabaseDriverException(operation="execute", reason="driver not initialized. Call init() first.")

        logger.debug(f"Neo4j sync execute: {query}, with kwargs: {kwargs}")
        try:
            return self._driver.execute_query(query, database_=database, routing_="w", **kwargs)
        except Exception as e:
            logger.error(f"Neo4j execute operation failed: {e}", exc_info=True)
            raise GraphDatabaseQueryException(reason=str(e), query=query, db_type="Neo4j") from e

    def shutdown(self, _: Self = None) -> None:
        """Shutdown the Neo4j client and close the driver.

        Closes the Neo4j driver connection and cleans up resources.
        After shutdown, the client cannot be used for new operations.

        Args:
            _: Ignored parameter (required by BaseSyncResource interface).

        Raises:
            GraphDatabaseConnectionException: If driver closure fails.

        Examples:
            >>> neo4j_client.shutdown()
        """
        if self._driver:
            try:
                self._driver.close()
                self._driver = None
                logger.info("Neo4j synchronous driver closed successfully")
            except Exception as e:
                logger.error(f"Neo4j shutdown failed: {e}", exc_info=True)
                raise GraphDatabaseConnectionException(reason=str(e), db_type="Neo4j") from e


class AsyncNeo4jClient(BaseAsyncResource):
    """Asynchronous Neo4j graph database client.

    This client manages an async Neo4j driver for asynchronous graph database
    operations including queries, writes, and connection management.

    Attributes:
        config (Neo4jConfig | None): Neo4j connection configuration.
        _drive (AsyncDriver | None): Async Neo4j driver instance.

    Raises:
        GraphDatabaseConnectionException: If connection to Neo4j fails.
        GraphDatabaseDriverException: If driver operation fails.
        GraphDatabaseQueryException: If query execution fails.
    """

    config: Neo4jConfig | None = None
    _drive: AsyncDriver | None = None

    @property
    def driver(self) -> AsyncDriver | None:
        """Get the async Neo4j driver instance.

        Returns:
            AsyncDriver | None: The async Neo4j driver or None if not initialized.
        """
        return self._drive

    async def init(self, config: Neo4jConfig | dict) -> Self:
        """Initialize the async Neo4j client with a driver connection.

        Creates an async Neo4j driver instance with the provided configuration
        for asynchronous database operations. Accepts either a Neo4jConfig
        object or a dictionary that will be validated into one.

        Args:
            config: Neo4j configuration containing URI and authentication credentials.
                    Can be a Neo4jConfig object or a dict.

        Returns:
            Self: Returns self for method chaining.

        Raises:
            GraphDatabaseConnectionException: If connection to Neo4j fails.
        """
        if isinstance(config, dict):
            config = Neo4jConfig.model_validate(config)

        self.config = config
        try:
            self._drive = AsyncGraphDatabase.driver(uri=str(self.config.dsn), auth=self.config.get_auth_tuples())
            logger.debug(f"Neo4j async driver connected: {self._drive}")
            logger.info(f"Neo4j async driver connected has successfully connected to {self.config.dsn!s}")
            return self
        except Exception as e:
            logger.error(f"Neo4j async connection failed: {e}", exc_info=True)
            raise GraphDatabaseConnectionException(reason=str(e), db_type="Neo4j (Async)") from e

    async def query(self, query: LiteralString, database: str = "neo4j", **kwargs) -> tuple[list[dict], Any, list[str]]:
        """Execute an async read query on the Neo4j database.

        Executes a Cypher query with read routing asynchronously, typically
        used for queries that read data from the graph.

        Args:
            query: Cypher query string to execute (must be a literal string for security).
            database: Name of the Neo4j database to query. Defaults to "neo4j".
            **kwargs: Additional parameters to pass to the query.

        Returns:
            tuple[list[dict], Any, list[str]]: A tuple containing:
                - List of result records as dictionaries
                - Query summary metadata
                - List of result keys

        Raises:
            GraphDatabaseDriverException: If driver is not initialized.
            GraphDatabaseQueryException: If query execution fails.
        """
        if not self._drive:
            raise GraphDatabaseDriverException(
                operation="query", reason="async driver not initialized. Call init() first."
            )

        logger.debug(f"Neo4j async query: {query}, using database: {database}, with kwargs: {kwargs}")
        try:
            records, summary, keys = await self._drive.execute_query(query, database_=database, routing_="r", **kwargs)
            return records, summary, keys
        except Exception as e:
            logger.error(f"Neo4j async query execution failed: {e}", exc_info=True)
            raise GraphDatabaseQueryException(reason=str(e), query=query, db_type="Neo4j (Async)") from e

    async def execute(self, query: LiteralString, database: str = "neo4j", **kwargs) -> Any:
        """Execute an async write query on the Neo4j database.

        Executes a Cypher query with write routing asynchronously, typically
        used for queries that modify data in the graph.

        Args:
            query: Cypher query string to execute (must be a literal string for security).
            database: Name of the Neo4j database to execute on. Defaults to "neo4j".
            **kwargs: Additional parameters to pass to the query.

        Returns:
            Any: Query result, typically containing summary information.

        Raises:
            GraphDatabaseDriverException: If driver is not initialized.
            GraphDatabaseQueryException: If query execution fails.
        """
        if not self._drive:
            raise GraphDatabaseDriverException(
                operation="execute", reason="async driver not initialized. Call init() first."
            )

        logger.debug(f"Neo4j async execute: {query}, with kwargs: {kwargs}")
        try:
            return await self._drive.execute_query(query, database_=database, routing_="w", **kwargs)
        except Exception as e:
            logger.error(f"Neo4j async execute operation failed: {e}", exc_info=True)
            raise GraphDatabaseQueryException(reason=str(e), query=query, db_type="Neo4j (Async)") from e

    async def shutdown(self, _: Self = None) -> None:
        """Shutdown the async Neo4j client and close the driver.

        Closes the async Neo4j driver connection and cleans up resources.
        After shutdown, the client cannot be used for new operations.

        Args:
            _: Ignored parameter (required by BaseAsyncResource interface).

        Raises:
            GraphDatabaseConnectionException: If driver closure fails.
        """
        if self._drive:
            try:
                await self._drive.close()
                self._drive = None
                logger.info("Neo4j async driver closed successfully")
            except Exception as e:
                logger.error(f"Neo4j async shutdown failed: {e}", exc_info=True)
                raise GraphDatabaseConnectionException(reason=str(e), db_type="Neo4j (Async)") from e
