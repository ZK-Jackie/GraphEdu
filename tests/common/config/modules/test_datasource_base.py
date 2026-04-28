"""测试数据源配置聚合类。"""

import pytest

from graphedu.common.config.modules.datasource import (
    DatasourceConfig,
    MongodbConfig,
    MysqlConfig,
    Neo4jConfig,
    OssConfig,
    PostgresqlConfig,
    RedisConfig,
)


class TestDatasourceConfig:
    """测试 DatasourceConfig 配置聚合类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = DatasourceConfig()

        # 验证所有数据源都有默认配置
        assert isinstance(config.postgresql, PostgresqlConfig)
        assert isinstance(config.mysql, MysqlConfig)
        assert isinstance(config.mongodb, MongodbConfig)
        assert isinstance(config.redis, RedisConfig)
        assert isinstance(config.neo4j, Neo4jConfig)
        assert isinstance(config.oss, OssConfig)

    def test_postgresql_config(self):
        """测试 PostgreSQL 配置。"""
        config = DatasourceConfig()

        assert str(config.postgresql.dsn) == "postgresql://postgres:postgres@localhost:5432/graphedu"
        assert config.postgresql.echo is False
        assert config.postgresql.pool.pool_size == 10

    def test_mysql_config(self):
        """测试 MySQL 配置。"""
        config = DatasourceConfig()

        assert str(config.mysql.dsn) == "mysql://user:password@localhost:3306/graphedu"
        assert config.mysql.timeout == 30
        assert config.mysql.retry == 3

    def test_mongodb_config(self):
        """测试 MongoDB 配置。"""
        config = DatasourceConfig()

        assert str(config.mongodb.url) == "mongodb://localhost:27017"
        assert config.mongodb.db_name == "graphedu"

    def test_redis_config(self):
        """测试 Redis 配置。"""
        config = DatasourceConfig()

        assert str(config.redis.dsn) == "redis://:password@localhost:6379/0"

    def test_neo4j_config(self):
        """测试 Neo4j 配置。"""
        config = DatasourceConfig()

        assert str(config.neo4j.dsn) == "bolt://localhost:7687"
        assert config.neo4j.auth == ["neo4j:password"]
        assert config.neo4j.timeout == 30

    def test_oss_config(self):
        """测试 OSS 配置。"""
        config = DatasourceConfig()

        assert config.oss.provider == "minio"
        assert str(config.oss.endpoint) == "http://localhost:9000"
        assert config.oss.bucket == "test"

    def test_custom_postgresql_config(self):
        """测试自定义 PostgreSQL 配置。"""
        from pydantic import PostgresDsn

        custom_postgres = PostgresqlConfig(dsn=PostgresDsn("postgresql://user:pass@host:5432/db"))
        config = DatasourceConfig(postgresql=custom_postgres)

        assert str(config.postgresql.dsn) == "postgresql://user:pass@host:5432/db"

    def test_custom_redis_config(self):
        """测试自定义 Redis 配置。"""
        from pydantic import RedisDsn

        custom_redis = RedisConfig(dsn=RedisDsn("redis://:secret@localhost:6379/1"))
        config = DatasourceConfig(redis=custom_redis)

        assert str(config.redis.dsn) == "redis://:secret@localhost:6379/1"

    def test_config_serialization(self):
        """测试配置序列化。"""
        import warnings

        config = DatasourceConfig()

        # 忽略 Pydantic 序列化警告
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            config_dict = config.model_dump(mode='json')

        assert "postgresql" in config_dict
        assert "mysql" in config_dict
        assert "mongodb" in config_dict
        assert "redis" in config_dict
        assert "neo4j" in config_dict
        assert "oss" in config_dict

    def test_config_json(self):
        """测试 JSON 序列化。"""
        import warnings

        config = DatasourceConfig()

        # 忽略 Pydantic 序列化警告
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            json_str = config.model_dump_json()

        assert "postgresql" in json_str
        assert "redis" in json_str
        assert "neo4j" in json_str

    def test_all_datasources_have_default_factories(self):
        """测试所有数据源都使用 default_factory。"""
        # 验证每个实例都是独立的
        config1 = DatasourceConfig()
        config2 = DatasourceConfig()

        # 修改 config1 不应影响 config2
        config1.postgresql.echo = True
        assert config2.postgresql.echo is False
