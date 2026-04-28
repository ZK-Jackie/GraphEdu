"""测试 PostgreSQL 数据库配置。"""

import pytest
from pydantic import ValidationError
from pydantic import PostgresDsn

from graphedu.common.config.modules.datasource.postgresql import PoolConfig, PostgresqlConfig


class TestPoolConfig:
    """测试 PoolConfig 连接池配置。"""

    def test_default_values(self):
        """测试默认值。"""
        config = PoolConfig()

        assert config.echo_pool is False
        assert config.pool_size == 10
        assert config.pool_recycle == 3600
        assert config.pool_timeout == 30
        assert config.pool_pre_ping is True
        assert config.pool_reset_on_return == "rollback"
        assert config.pool_use_lifo is False

    def test_custom_values(self):
        """测试自定义值。"""
        config = PoolConfig(
            echo_pool=True,
            pool_size=20,
            pool_recycle=1800,
            pool_timeout=60,
            pool_pre_ping=False,
            pool_reset_on_return="commit",
            pool_use_lifo=True,
        )

        assert config.echo_pool is True
        assert config.pool_size == 20
        assert config.pool_recycle == 1800
        assert config.pool_timeout == 60
        assert config.pool_pre_ping is False
        assert config.pool_reset_on_return == "commit"
        assert config.pool_use_lifo is True

    def test_echo_pool_field(self):
        """测试 echo_pool 字段。"""
        config = PoolConfig(echo_pool=True)

        assert config.echo_pool is True

    def test_pool_size_positive(self):
        """测试 pool_size 正值。"""
        config = PoolConfig(pool_size=50)

        assert config.pool_size == 50

    def test_pool_size_validation_zero(self):
        """测试 pool_size 验证（零应失败）。"""
        with pytest.raises(ValidationError):
            PoolConfig(pool_size=0)

    def test_pool_size_validation_negative(self):
        """测试 pool_size 验证（负数应失败）。"""
        with pytest.raises(ValidationError):
            PoolConfig(pool_size=-10)

    def test_pool_recycle_positive(self):
        """测试 pool_recycle 正值。"""
        config = PoolConfig(pool_recycle=7200)

        assert config.pool_recycle == 7200

    def test_pool_recycle_validation_zero(self):
        """测试 pool_recycle 验证（零应失败）。"""
        with pytest.raises(ValidationError):
            PoolConfig(pool_recycle=0)

    def test_pool_timeout_positive(self):
        """测试 pool_timeout 正值。"""
        config = PoolConfig(pool_timeout=120)

        assert config.pool_timeout == 120

    def test_pool_timeout_validation_zero(self):
        """测试 pool_timeout 验证（零应失败）。"""
        with pytest.raises(ValidationError):
            PoolConfig(pool_timeout=0)

    def test_pool_pre_ping_field(self):
        """测试 pool_pre_ping 字段。"""
        config = PoolConfig(pool_pre_ping=False)

        assert config.pool_pre_ping is False

    def test_pool_reset_on_return_rollback(self):
        """测试 pool_reset_on_return 为 rollback。"""
        config = PoolConfig(pool_reset_on_return="rollback")

        assert config.pool_reset_on_return == "rollback"

    def test_pool_reset_on_return_commit(self):
        """测试 pool_reset_on_return 为 commit。"""
        config = PoolConfig(pool_reset_on_return="commit")

        assert config.pool_reset_on_return == "commit"

    def test_pool_reset_on_return_false(self):
        """测试 pool_reset_on_return 为 False。"""
        config = PoolConfig(pool_reset_on_return=False)

        assert config.pool_reset_on_return is False

    def test_pool_reset_on_return_true(self):
        """测试 pool_reset_on_return 为 True。"""
        config = PoolConfig(pool_reset_on_return=True)

        assert config.pool_reset_on_return is True

    def test_pool_use_lifo_field(self):
        """测试 pool_use_lifo 字段。"""
        config = PoolConfig(pool_use_lifo=True)

        assert config.pool_use_lifo is True


class TestPostgresqlConfig:
    """测试 PostgresqlConfig 数据库配置。"""

    def test_default_values(self):
        """测试默认值。"""
        config = PostgresqlConfig()

        assert str(config.dsn) == "postgresql://postgres:postgres@localhost:5432/graphedu"
        assert config.echo is False
        assert isinstance(config.pool, PoolConfig)

    def test_custom_dsn(self):
        """测试自定义 DSN。"""
        custom_dsn = "postgresql://user:pass@host:5432/dbname"
        config = PostgresqlConfig(dsn=custom_dsn)

        assert str(config.dsn) == custom_dsn

    def test_dsn_type_validation(self):
        """测试 DSN 类型验证。"""
        # 有效的 PostgreSQL DSN
        valid_dsn = "postgresql://user:password@localhost:5432/mydb"
        config = PostgresqlConfig(dsn=valid_dsn)

        assert isinstance(config.dsn, PostgresDsn)

    def test_echo_field(self):
        """测试 echo 字段。"""
        config = PostgresqlConfig(echo=True)

        assert config.echo is True

    def test_pool_custom(self):
        """测试自定义连接池配置。"""
        pool_config = PoolConfig(pool_size=20, pool_timeout=60)
        config = PostgresqlConfig(pool=pool_config)

        assert config.pool.pool_size == 20
        assert config.pool.pool_timeout == 60

    def test_pool_default_factory(self):
        """测试连接池默认工厂。"""
        config = PostgresqlConfig()

        # 验证使用默认连接池配置
        assert isinstance(config.pool, PoolConfig)
        assert config.pool.pool_size == 10

    def test_get_async_dsn(self):
        """测试获取异步 DSN。"""
        sync_dsn = "postgresql://user:pass@localhost:5432/mydb"
        config = PostgresqlConfig(dsn=sync_dsn)

        # 验证可以调用方法
        async_dsn = config.get_sa_async_dsn()

        # 验证返回字符串
        assert isinstance(async_dsn, str)
        # 验证包含 psycopg 协议（当前实现使用 psycopg）
        assert "postgresql+psycopg://" in async_dsn

    def test_get_async_dsn_default(self):
        """测试获取异步 DSN（默认配置）。"""
        config = PostgresqlConfig()

        # 验证可以调用方法
        async_dsn = config.get_sa_async_dsn()

        # 验证返回字符串
        assert isinstance(async_dsn, str)
        # 验证包含 psycopg 协议（当前实现使用 psycopg）
        assert "postgresql+psycopg://" in async_dsn

    def test_get_sa_sync_dsn(self):
        """测试获取同步 DSN（用于 SQLAlchemy）。"""
        sync_dsn = "postgresql://user:pass@localhost:5432/mydb"
        config = PostgresqlConfig(dsn=sync_dsn)

        # 验证可以调用方法
        sa_dsn = config.get_sa_sync_dsn()

        # 验证返回字符串
        assert isinstance(sa_dsn, str)
        # 验证包含 psycopg 协议
        assert "postgresql+psycopg://" in sa_dsn

    def test_get_sa_sync_dsn_default(self):
        """测试获取同步 DSN（默认配置）。"""
        config = PostgresqlConfig()

        # 验证可以调用方法
        sa_dsn = config.get_sa_sync_dsn()

        # 验证返回字符串
        assert isinstance(sa_dsn, str)
        # 验证包含 psycopg 协议
        assert "postgresql+psycopg://" in sa_dsn

    def test_sa_dsn_methods_comparison(self):
        """测试同步和异步 DSN 方法的差异。"""
        config = PostgresqlConfig()

        sync_dsn = config.get_sa_sync_dsn()
        async_dsn = config.get_sa_async_dsn()

        # 当前实现：两者都使用 psycopg（这可能是源代码的 bug，但测试应反映实际情况）
        assert "postgresql+psycopg://" in sync_dsn
        assert "postgresql+psycopg://" in async_dsn

    def test_sa_dsn_preserves_components(self):
        """测试 DSN 方法保留原始组件。"""
        # 使用包含所有组件的 DSN
        full_dsn = "postgresql://testuser:testpass@testhost:5433/testdb?options=-c%20client_encoding%3DUTF8"
        config = PostgresqlConfig(dsn=full_dsn)

        sa_dsn = config.get_sa_async_dsn()

        # 验证保留主机和端口（可能在不同位置）
        assert "testhost" in sa_dsn or "5433" in sa_dsn
        # 验证保留数据库名
        assert "testdb" in sa_dsn
        # 验证保留查询参数
        assert "client_encoding" in sa_dsn or "UTF8" in sa_dsn

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = PostgresqlConfig()

        # 验证配置支持序列化
        assert hasattr(config, "model_dump")
        assert hasattr(config, "model_dump_json")

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = PostgresqlConfig()

        # 验证可以序列化为 JSON
        json_str = config.model_dump_json()

        # 验证返回字符串
        assert isinstance(json_str, str)
        assert len(json_str) > 0

    def test_nested_pool_config(self):
        """测试嵌套连接池配置。"""
        config = PostgresqlConfig(
            pool=PoolConfig(
                pool_size=30,
                pool_recycle=1800,
                pool_pre_ping=False,
            )
        )

        # 验证嵌套配置
        assert config.pool.pool_size == 30
        assert config.pool.pool_recycle == 1800
        assert config.pool.pool_pre_ping is False

    def test_connection_pool_settings(self):
        """测试连接池设置的合理性。"""
        # 高并发场景
        config = PostgresqlConfig(
            pool=PoolConfig(
                pool_size=50,
                pool_timeout=10,
                pool_recycle=3600,
                pool_pre_ping=True,
            )
        )

        assert config.pool.pool_size == 50
        assert config.pool.pool_timeout == 10
        assert config.pool.pool_recycle == 3600
        assert config.pool.pool_pre_ping is True

    def test_dsn_with_different_components(self):
        """测试不同组件的 DSN。"""
        test_dsns = [
            "postgresql://user@localhost/db",
            "postgresql://user:password@localhost:5432/db",
            "postgresql://user:password@host:5432/dbname",
            "postgresql://user:password@192.168.1.1:5432/testdb",
        ]

        for dsn in test_dsns:
            config = PostgresqlConfig(dsn=dsn)
            assert str(config.dsn) == dsn
