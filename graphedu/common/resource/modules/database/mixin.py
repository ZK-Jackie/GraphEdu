"""Graph DB Mixin：Neo4jMixin。"""

from dependency_injector import containers, providers

from graphedu.common.config.manager import get_config

from .mysql import AsyncMysqlClient
from .neo4j import AsyncNeo4jClient
from .oss import AioS3Client
from .postgresql import AsyncPostgresqlClient


class Neo4jMixin(containers.DeclarativeContainer):
    """提供 Neo4j 异步客户端资源。

    Attributes:
        neo4j_client: Neo4j 异步客户端实例，用于图数据库操作。
    """

    neo4j_client = providers.Resource(AsyncNeo4jClient, config=get_config().datasource.neo4j)


class PostgresqlMixin(containers.DeclarativeContainer):
    """提供 PostgreSQL 异步客户端资源。

    Attributes:
        postgresql_client: PostgreSQL 异步客户端实例，用于数据库连接和操作。
    """

    postgresql_client = providers.Resource(AsyncPostgresqlClient, config=get_config().datasource.postgresql)


class MysqlMixin(containers.DeclarativeContainer):
    """提供 MySQL 异步客户端资源。

    Attributes:
        mysql_client: MySQL 异步客户端实例，用于数据库连接和操作。
    """

    mysql_client = providers.Resource(AsyncMysqlClient, config=get_config().datasource.mysql)


class S3Mixin(containers.DeclarativeContainer):
    """提供 S3/OSS 异步客户端资源。

    Attributes:
        s3_client: S3/OSS 异步客户端实例，用于对象存储操作（上传、下载、删除等）。
    """

    s3_client = providers.Resource(AioS3Client, config=get_config().datasource.oss)
