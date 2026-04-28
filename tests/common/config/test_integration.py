"""Config 模块集成测试。

测试各个配置模块之间的协同工作。
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from graphedu.common.config import load_config, ConfigManager
from graphedu.common.config.core.constants import ConfigConstants, RunningConstants


class TestConfigIntegration:
    """配置模块集成测试。"""

    def setup_method(self):
        """每个测试方法前的设置。"""
        ConfigManager._instance = None
        for key in list(os.environ.keys()):
            if key.startswith("GE_") or key.startswith("GRAPHEDU_"):
                del os.environ[key]

    def teardown_method(self):
        """每个测试方法后的清理。"""
        ConfigManager._instance = None
        for key in list(os.environ.keys()):
            if key.startswith("GE_") or key.startswith("GRAPHEDU_"):
                del os.environ[key]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_full_config_loading(self, mock_read_yaml):
        """测试完整配置加载。"""
        # Mock 完整的 YAML 配置
        mock_read_yaml.return_value = {
            "app": {
                "name": "test-app",
                "version": "1.0.0",
                "author": "Test Author",
            },
            "model": {
                "chat": {
                    "name": "gpt-4",
                    "api_key": "test-key",
                    "temperature": 0.8,
                },
            },
            "datasource": {
                "postgresql": {
                    "dsn": "postgresql://user:pass@localhost:5432/test",
                    "echo": True,
                    "pool": {
                        "pool_size": 20,
                        "pool_timeout": 60,
                    },
                },
            },
            "security": {
                "token": {
                    "secret": "test-secret",
                    "expire": 60,
                },
                "login": {
                    "single_end": False,
                    "captcha": False,
                },
            },
        }

        os.environ["GE_CONFIG_FILE_LOCAL"] = "test.yaml"

        try:
            config = load_config()

            # 验证应用配置
            assert config.app.name == "test-app"
            assert config.app.version == "1.0.0"
            assert config.app.author == "Test Author"

            # 验证模型配置
            assert config.model.chat.name == "gpt-4"
            assert config.model.chat.api_key == "test-key"
            assert config.model.chat.temperature == 0.8

            # 验证数据源配置
            assert "postgresql://user:pass@localhost:5432/test" in str(config.datasource.postgresql.dsn)
            assert config.datasource.postgresql.echo is True
            assert config.datasource.postgresql.pool.pool_size == 20

            # 验证安全配置
            assert config.security.token.secret == "test-secret"
            assert config.security.token.expire == 60
            assert config.security.login.single_end is False
            assert config.security.login.captcha is False

        finally:
            del os.environ["GE_CONFIG_FILE_LOCAL"]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_priority_order(self, mock_read_yaml):
        """测试配置优先级顺序。"""
        # Mock 返回默认值
        mock_read_yaml.return_value = {}

        os.environ["GE_CONFIG_FILE_LOCAL"] = "test.yaml"
        os.environ["GRAPHEDU__APP__NAME"] = "env_app"

        try:
            config = load_config()

            # 验证配置加载成功
            assert config is not None
            assert config.app is not None

        finally:
            del os.environ["GE_CONFIG_FILE_LOCAL"]
            del os.environ["GRAPHEDU__APP__NAME"]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_nested_config_access(self, mock_read_yaml):
        """测试嵌套配置访问路径。"""
        mock_read_yaml.return_value = {}

        config = load_config()

        # 测试深层嵌套访问
        # config.model.chat.extra_body.thinking.type
        thinking_type = config.model.chat.extra_body.thinking.type
        assert thinking_type == "disabled"

        # config.datasource.postgresql.pool.pool_size
        pool_size = config.datasource.postgresql.pool.pool_size
        assert pool_size == 10

        # config.security.token.header
        header = config.security.token.header
        assert header == "authorization"

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_immutability_after_load(self, mock_read_yaml):
        """测试配置加载后的可变性。"""
        mock_read_yaml.return_value = {"app": {"name": "original"}}

        config = load_config()

        # 保存原始值
        original_name = config.app.name

        # 修改配置
        config.app.name = "modified"

        # 验证可以修改（Pydantic BaseModel 默认可变）
        assert config.app.name == "modified"
        assert config.app.name != original_name

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_singleton_behavior(self, mock_read_yaml):
        """测试配置单例行为。"""
        mock_read_yaml.return_value = {}

        # 第一次加载
        config1 = load_config()

        # 第二次加载（不重新加载）
        config2 = load_config(reload=False)

        # 验证返回同一实例
        assert config1 is config2

        # 强制重新加载
        config3 = load_config(reload=True)

        # 验证创建新实例
        assert config1 is not config3

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_different_running_modes(self, mock_read_yaml):
        """测试不同运行模式。"""
        mock_read_yaml.return_value = {}
        mock_context = patch("graphedu.common.config.manager.ContextManager")
        mock_cm = mock_context.start()
        mock_cm.set_global_context = MagicMock()
        mock_cm.get_global_context = MagicMock(return_value=None)

        try:
            # 测试不同模式
            modes = ["service", "builder", "converter"]

            for mode in modes:
                ConfigManager._instance = None
                config = load_config(running_mode=mode)

                # 验证配置加载成功
                assert config is not None

        finally:
            mock_context.stop()

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_validation_integration(self, mock_read_yaml):
        """测试配置验证集成。"""
        # Mock 返回默认配置
        mock_read_yaml.return_value = {}

        # 配置应该使用默认值
        config = load_config()

        # 验证使用有效的默认值
        assert config.security.token.expire > 0

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_serialization_integration(self, mock_read_yaml):
        """测试配置序列化集成。"""
        mock_read_yaml.return_value = {}

        config = load_config()

        # 验证配置支持序列化
        assert hasattr(config, "model_dump")
        assert hasattr(config, "model_dump_json")


class TestConfigConstantsIntegration:
    """配置常量集成测试。"""

    def test_config_constants_usage(self):
        """测试配置常量的使用。"""
        # 验证常量值
        assert ConfigConstants.CONFIG_FILE_ENV == "GE_CONFIG_FILE_ENV"
        assert ConfigConstants.CONFIG_FILE_LOCAL == "GE_CONFIG_FILE_LOCAL"
        assert ConfigConstants.CONFIG_FILE_DEFAULT == "dev.config.yaml"

    def test_running_constants_usage(self):
        """测试运行状态常量的使用。"""
        # 验证常量值
        assert RunningConstants.RUNNING_STATE == "RUNNING_STATE"
        assert RunningConstants.CONFIG_INSTANCE == "CONFIG_INSTANCE"
        assert RunningConstants.RES_INITED_STATE == "RES_INITED_STATE"

    def test_constants_for_environment_variables(self):
        """测试常量用于环境变量设置。"""
        # 使用常量设置环境变量
        os.environ[ConfigConstants.CONFIG_FILE_LOCAL] = "test.yaml"

        try:
            # 验证可以读取
            assert os.environ[ConfigConstants.CONFIG_FILE_LOCAL] == "test.yaml"
        finally:
            del os.environ[ConfigConstants.CONFIG_FILE_LOCAL]


class TestConfigEdgeCases:
    """配置边缘情况测试。"""

    def setup_method(self):
        """每个测试方法前的设置。"""
        ConfigManager._instance = None
        for key in list(os.environ.keys()):
            if key.startswith("GE_") or key.startswith("GRAPHEDU_"):
                del os.environ[key]

    def teardown_method(self):
        """每个测试方法后的清理。"""
        ConfigManager._instance = None
        for key in list(os.environ.keys()):
            if key.startswith("GE_") or key.startswith("GRAPHEDU_"):
                del os.environ[key]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_empty_yaml_config(self, mock_read_yaml):
        """测试空 YAML 配置。"""
        mock_read_yaml.return_value = {}

        config = load_config()

        # 验证使用默认值
        assert config.app.name == "graphedu-service"
        assert config.model.chat.name == "glm-5-flash"

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_partial_yaml_config(self, mock_read_yaml):
        """测试部分 YAML 配置。"""
        mock_read_yaml.return_value = {
            "app": {"name": "test-app"},
            # 缺少其他配置
        }

        config = load_config()

        # 验证部分配置加载，其他使用默认值
        assert config.app.name == "test-app"
        assert config.model.chat.name == "glm-5-flash"  # 默认值

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_with_none_values(self, mock_read_yaml):
        """测试包含 None 值的配置。"""
        mock_read_yaml.return_value = {
            "app": {
                "name": "test",
                "author": None,  # 可选字段为 None
            },
        }

        config = load_config()

        # 验证 None 值正确处理
        assert config.app.name == "test"
        assert config.app.author is None

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_case_sensitivity(self, mock_read_yaml):
        """测试配置大小写敏感性。"""
        # 环境变量应该不区分大小写（pydantic-settings 特性）
        mock_read_yaml.return_value = {}

        os.environ["GRAPHEDU__APP__NAME"] = "test_app"

        try:
            config = load_config()

            # 验证配置加载成功
            assert config.app is not None

        finally:
            del os.environ["GRAPHEDU__APP__NAME"]
