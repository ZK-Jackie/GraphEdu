"""测试 Redis 配置。"""

import pytest
from pydantic import RedisDsn, ValidationError

from graphedu.common.config.modules.datasource import RedisConfig


class TestRedisConfig:
    """测试 RedisConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = RedisConfig()

        assert str(config.dsn) == "redis://:password@localhost:6379/0"

    def test_custom_dsn(self):
        """测试自定义 DSN。"""
        custom_dsn = "redis://:secret@localhost:6379/1"
        config = RedisConfig(dsn=custom_dsn)

        assert str(config.dsn) == custom_dsn

    def test_dsn_with_password(self):
        """测试带密码的 DSN。"""
        config = RedisConfig(dsn="redis://:my_password@redis.example.com:6380/2")

        assert str(config.dsn) == "redis://:my_password@redis.example.com:6380/2"

    def test_dsn_without_password(self):
        """测试不带密码的 DSN。"""
        config = RedisConfig(dsn="redis://localhost:6379/0")

        assert str(config.dsn) == "redis://localhost:6379/0"

    def test_dsn_with_username(self):
        """测试带用户名的 DSN。"""
        config = RedisConfig(dsn="redis://default:password@localhost:6379/0")

        assert "default" in str(config.dsn)

    def test_dsn_with_database_index(self):
        """测试不同数据库索引。"""
        for db_index in [0, 1, 2, 15]:
            config = RedisConfig(dsn=f"redis://:password@localhost:6379/{db_index}")
            assert f"/{db_index}" in str(config.dsn)

    def test_dsn_with_custom_port(self):
        """测试自定义端口。"""
        config = RedisConfig(dsn="redis://:password@localhost:6380/0")

        assert "6380" in str(config.dsn)

    def test_dsn_with_custom_host(self):
        """测试自定义主机。"""
        config = RedisConfig(dsn="redis://:password@redis.example.com:6379/0")

        assert "redis.example.com" in str(config.dsn)

    def test_dsn_with_socket(self):
        """测试 Unix socket 连接。"""
        # Pydantic RedisDsn 不支持 Unix socket 格式，跳过此测试
        # Unix socket 格式如 redis://:password@/var/run/redis/redis.sock 不被 RedisDsn 支持
        pytest.skip("Pydantic RedisDsn does not support Unix socket format")

    def test_dsn_type_validation(self):
        """测试 DSN 类型验证。"""
        # 应该接受有效的 Redis DSN
        config = RedisConfig(dsn="redis://:password@localhost:6379/0")
        assert isinstance(config.dsn, RedisDsn)

    def test_invalid_dsn(self):
        """测试无效的 DSN。"""
        # 无效的协议应该抛出 ValidationError
        with pytest.raises(ValidationError):
            RedisConfig(dsn="http://localhost:6379")

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = RedisConfig(dsn="redis://:secret@localhost:6379/1")

        config_dict = config.model_dump(mode='json')

        assert config_dict["dsn"] == "redis://:secret@localhost:6379/1"

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = RedisConfig(dsn="redis://:secret@localhost:6379/1")

        json_str = config.model_dump_json()

        assert "redis" in json_str
        assert "6379" in json_str

    def test_dsn_with_ssl(self):
        """测试 SSL 连接（rediss://）。"""
        config = RedisConfig(dsn="rediss://:password@localhost:6379/0")

        assert str(config.dsn).startswith("rediss://")

    def test_dsn_with_sentinel(self):
        """测试 Sentinel 模式。"""
        # Pydantic RedisDsn 不支持多主机 Sentinel 格式，跳过此测试
        # Sentinel 格式如 redis://:password@sentinel1:26379,sentinel2:26379/mymaster/0 不被 RedisDsn 支持
        pytest.skip("Pydantic RedisDsn does not support multi-host Sentinel format")

    def test_dsn_with_connection_params(self):
        """测试带连接参数的 DSN。"""
        config = RedisConfig(dsn="redis://:password@localhost:6379/0?decode_responses=true")

        assert "decode_responses" in str(config.dsn)
