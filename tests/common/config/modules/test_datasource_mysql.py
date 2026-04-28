"""测试 MySQL 配置。"""

import pytest
from pydantic import MySQLDsn, ValidationError

from graphedu.common.config.modules.datasource import MysqlConfig, PoolConfig


class TestMysqlConfig:
    """测试 MysqlConfig 配置类（已废弃）。"""

    def test_default_values(self):
        """测试默认值。"""
        config = MysqlConfig()

        assert str(config.dsn) == "mysql://user:password@localhost:3306/graphedu"
        assert config.timeout == 30
        assert config.retry == 3
        assert isinstance(config.pool, PoolConfig)

    def test_custom_dsn(self):
        """测试自定义 DSN。"""
        custom_dsn = "mysql://root:secret@db.example.com:3307/mydb"
        config = MysqlConfig(dsn=custom_dsn)

        assert str(config.dsn) == custom_dsn

    def test_dsn_with_different_components(self):
        """测试不同组件的 DSN。"""
        config = MysqlConfig(
            dsn="mysql://admin:admin123@mysql-server:3306/production"
        )

        assert "admin" in str(config.dsn)
        assert "mysql-server" in str(config.dsn)
        assert "production" in str(config.dsn)

    def test_dsn_with_charset(self):
        """测试带字符集的 DSN。"""
        config = MysqlConfig(dsn="mysql://user:pass@localhost:3306/db?charset=utf8mb4")

        assert "utf8mb4" in str(config.dsn)

    def test_custom_timeout(self):
        """测试自定义超时时间。"""
        config = MysqlConfig(timeout=60)

        assert config.timeout == 60

    def test_timeout_validation_positive(self):
        """测试超时时间验证（正数）。"""
        config = MysqlConfig(timeout=10)

        assert config.timeout == 10

    def test_timeout_validation_zero(self):
        """测试超时时间验证（零应失败）。"""
        with pytest.raises(ValidationError):
            MysqlConfig(timeout=0)

    def test_timeout_validation_negative(self):
        """测试超时时间验证（负数应失败）。"""
        with pytest.raises(ValidationError):
            MysqlConfig(timeout=-10)

    def test_custom_retry(self):
        """测试自定义重试次数。"""
        config = MysqlConfig(retry=5)

        assert config.retry == 5

    def test_retry_validation_positive(self):
        """测试重试次数验证（正数）。"""
        config = MysqlConfig(retry=1)

        assert config.retry == 1

    def test_retry_validation_zero(self):
        """测试重试次数验证（零应失败）。"""
        with pytest.raises(ValidationError):
            MysqlConfig(retry=0)

    def test_default_pool_config(self):
        """测试默认连接池配置。"""
        config = MysqlConfig()

        assert config.pool.pool_size == 10
        assert config.pool.pool_recycle == 3600
        assert config.pool.pool_timeout == 30
        assert config.pool.pool_pre_ping is True

    def test_custom_pool_config(self):
        """测试自定义连接池配置。"""
        custom_pool = PoolConfig(pool_size=20, pool_recycle=1800)
        config = MysqlConfig(pool=custom_pool)

        assert config.pool.pool_size == 20
        assert config.pool.pool_recycle == 1800

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = MysqlConfig(
            dsn="mysql://root:pass@localhost:3306/db",
            timeout=45,
            retry=2,
        )

        config_dict = config.model_dump(mode="json")

        assert config_dict["dsn"] == "mysql://root:pass@localhost:3306/db"
        assert config_dict["timeout"] == 45
        assert config_dict["retry"] == 2

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = MysqlConfig(dsn="mysql://user:pass@localhost:3306/db")

        json_str = config.model_dump_json()

        assert "mysql" in json_str
        assert "3306" in json_str

    def test_dsn_type_validation(self):
        """测试 DSN 类型验证。"""
        config = MysqlConfig(dsn="mysql://user:pass@localhost:3306/db")
        assert isinstance(config.dsn, MySQLDsn)

    def test_deprecated_note(self):
        """测试废弃说明（文档目的）。"""
        # MySQL 配置类标记为已废弃，但仍可用
        config = MysqlConfig()
        assert config is not None

    def test_connection_string_with_ssl(self):
        """测试带 SSL 的连接字符串。"""
        config = MysqlConfig(dsn="mysql://user:pass@localhost:3306/db?ssl=true")

        assert "ssl" in str(config.dsn)
