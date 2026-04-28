"""数据源配置（Spring Boot 风格：datasource）。"""

from pydantic import BaseModel, Field

from .mongodb import MongodbConfig
from .mysql import MysqlConfig
from .neo4j import Neo4jConfig
from .oss import OssConfig
from .postgresql import AgeConfig, PoolConfig, PostgresqlConfig
from .redis import RedisConfig


class DatasourceConfig(BaseModel):
    """数据源配置聚合类（Spring Boot 风格：datasource）。

    包含所有数据存储相关配置：
    - PostgreSQL（关系型数据库）
    - AGE（图数据库 - PostgreSQL 扩展）
    - MySQL（已废弃，保留兼容）
    - MongoDB（文档数据库）
    - Redis（缓存）
    - Neo4j（图数据库）
    - OSS（对象存储）
    """

    postgresql: PostgresqlConfig = Field(default_factory=PostgresqlConfig)
    """PostgreSQL 配置"""

    age: AgeConfig = Field(default_factory=AgeConfig)
    """Apache AGE 图数据库配置"""

    mysql: MysqlConfig = Field(default_factory=MysqlConfig)
    """MySQL 配置（已废弃）"""

    mongodb: MongodbConfig = Field(default_factory=MongodbConfig)
    """MongoDB 配置"""

    redis: RedisConfig = Field(default_factory=RedisConfig)
    """Redis 配置"""

    neo4j: Neo4jConfig = Field(default_factory=Neo4jConfig)
    """Neo4j 配置"""

    oss: OssConfig = Field(default_factory=OssConfig)
    """对象存储配置（S3 兼容）"""


__all__ = [
    "AgeConfig",
    "DatasourceConfig",
    "MongodbConfig",
    "MysqlConfig",
    "Neo4jConfig",
    "OssConfig",
    "PoolConfig",
    "PostgresqlConfig",
    "RedisConfig",
]
