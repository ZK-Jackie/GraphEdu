"""测试 BaseAppSettings 基类。"""

import os

import pytest

from graphedu.common.config import BaseAppSettings, load_config, get_config, ServiceConfig


class DummySettings(BaseAppSettings):
    """测试用的配置类。"""

    name: str = "default"
    value: int = 10


class TestBaseAppSettings:
    """测试 BaseAppSettings 基类功能。"""

    def test_default_values(self):
        """测试默认值加载。"""
        config = DummySettings()
        assert config.name == "default"
        assert config.value == 10

    def test_init_values(self):
        """测试初始化值覆盖默认值。"""
        config = DummySettings(name="test", value=20)
        assert config.name == "test"
        assert config.value == 20

    def test_env_override(self):
        """测试环境变量覆盖。"""
        # 临时清除配置文件环境变量，确保只测试环境变量覆盖
        old_config_file = os.environ.pop("GE_CONFIG_FILE_LOCAL", None)
        try:
            os.environ["GRAPHEDU_NAME"] = "env_name"
            os.environ["GRAPHEDU_VALUE"] = "30"
            config = DummySettings()
            assert config.name == "env_name"
            assert config.value == 30
            del os.environ["GRAPHEDU_NAME"]
            del os.environ["GRAPHEDU_VALUE"]
        finally:
            if old_config_file:
                os.environ["GE_CONFIG_FILE_LOCAL"] = old_config_file


class TestConfigManager:
    """测试配置管理器功能。"""

    def test_load_config(self):
        """测试配置加载。"""
        config = load_config("dev.config.yaml")
        assert isinstance(config, ServiceConfig)
        assert config.name == "GraphEdu Dev Environment"
        assert config.version == "0.0.1"

    def test_get_config_singleton(self):
        """测试 get_config 返回单例。"""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_database_config(self):
        """测试数据库配置加载。"""
        config = load_config("dev.config.yaml")
        assert config.database.postgresql.dsn is not None
        assert config.database.redis.url is not None
        assert config.database.neo4j.uri is not None

    def test_llm_config(self):
        """测试 LLM 配置加载。"""
        config = load_config("dev.config.yaml")
        assert config.chat.name is not None
        assert config.think.name is not None
        assert config.long.name is not None
        assert config.embeddings.name is not None

    def test_token_config(self):
        """测试 Token 配置加载。"""
        config = load_config("dev.config.yaml")
        assert config.token.algorithm == "HS512"
        assert config.token.expire == 1440
        assert config.token.header == "authorization"

    def test_login_config(self):
        """测试登录配置加载。"""
        config = load_config("dev.config.yaml")
        assert config.login.captcha is True
        assert config.login.single_end is True

    def test_oss_config(self):
        """测试 OSS 配置加载。"""
        config = load_config("dev.config.yaml")
        assert config.oss.bucket == "test"
        assert config.oss.endpoint == "http://localhost:9000"

    def test_system_config(self):
        """测试系统配置加载。"""
        config = load_config("dev.config.yaml")
        assert config.system.timezone == "UTC"
        assert config.system.location_query is True

    def test_log_config(self):
        """测试日志配置加载。"""
        config = load_config("dev.config.yaml")
        assert config.log.version == 1
        log_dict = config.log.get_dict_config()
        assert "formatters" in log_dict
        assert "handlers" in log_dict

    def test_postgresql_async_dsn(self):
        """测试 PostgreSQL 异步 DSN 生成。"""
        config = load_config("dev.config.yaml")
        async_dsn = config.database.postgresql.get_async_dsn()
        assert async_dsn.startswith("postgresql+asyncpg://")

    def test_llm_get_lc_attr(self):
        """测试 LLM 配置获取 LangChain 属性。"""
        config = load_config("dev.config.yaml")
        lc_attr = config.chat.get_lc_attr()
        assert "model_name" in lc_attr
        assert "api_key" in lc_attr
        assert "base_url" in lc_attr
        assert "rate_limiter" in lc_attr
        assert lc_attr["model_name"] == config.chat.name

    def test_embeddings_get_lc_attr(self):
        """测试 Embeddings 配置获取 LangChain 属性。"""
        config = load_config("dev.config.yaml")
        lc_attr = config.embeddings.get_lc_attr()
        assert "model" in lc_attr
        assert "api_key" in lc_attr
        assert "base_url" in lc_attr
        assert "dimensions" in lc_attr
        assert lc_attr["model"] == config.embeddings.name
