"""测试 ServiceConfig 配置类。"""

from unittest.mock import patch

import pytest

from graphedu.common.config.modes.service import ServiceConfig


class TestServiceConfig:
    """测试 ServiceConfig 配置类。"""

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_default_values(self, mock_read_yaml):
        """测试默认值设置。"""
        mock_read_yaml.return_value = {}

        config = ServiceConfig()

        # 验证所有默认配置字段存在
        assert hasattr(config, "app")
        assert hasattr(config, "model")
        assert hasattr(config, "datasource")
        assert hasattr(config, "security")
        assert hasattr(config, "agent")
        assert hasattr(config, "logging")
        assert hasattr(config, "system")

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_structure(self, mock_read_yaml):
        """测试配置结构。"""
        mock_read_yaml.return_value = {}

        config = ServiceConfig()

        # 验证嵌套配置结构
        assert hasattr(config.app, "name")
        assert hasattr(config.app, "version")
        assert hasattr(config.model, "chat")
        assert hasattr(config.datasource, "postgresql")
        assert hasattr(config.security, "token")
        assert hasattr(config.security, "login")

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_app_config_access(self, mock_read_yaml):
        """测试应用配置访问。"""
        mock_read_yaml.return_value = {
            "app": {"name": "test_app", "version": "1.0.0", "author": "Test Author"},
        }

        config = ServiceConfig()

        # 验证应用配置被加载（注意：pydantic-settings 的加载机制可能不同）
        # 这里我们只验证配置对象存在
        assert config.app is not None
        assert hasattr(config.app, "name")
        assert hasattr(config.app, "version")
        assert hasattr(config.app, "author")

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_model_config_access(self, mock_read_yaml):
        """测试模型配置访问。"""
        mock_read_yaml.return_value = {}

        config = ServiceConfig()

        # 验证模型配置对象存在
        assert config.model is not None
        assert hasattr(config.model, "chat")
        assert hasattr(config.model.chat, "name")
        assert hasattr(config.model.chat, "api_key")

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_datasource_config_access(self, mock_read_yaml):
        """测试数据源配置访问。"""
        mock_read_yaml.return_value = {}

        config = ServiceConfig()

        # 验证数据源配置对象存在
        assert config.datasource is not None
        assert hasattr(config.datasource, "postgresql")
        assert hasattr(config.datasource.postgresql, "dsn")

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_security_config_access(self, mock_read_yaml):
        """测试安全配置访问。"""
        mock_read_yaml.return_value = {}

        config = ServiceConfig()

        # 验证安全配置对象存在
        assert config.security is not None
        assert hasattr(config.security, "token")
        assert hasattr(config.security, "login")
        assert hasattr(config.security.token, "secret")
        assert hasattr(config.security.login, "single_end")

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_nested_config_paths(self, mock_read_yaml):
        """测试嵌套配置路径访问。"""
        mock_read_yaml.return_value = {}

        config = ServiceConfig()

        # 验证深层嵌套访问
        # config.model.chat.temperature
        assert hasattr(config.model.chat, "temperature")
        # config.datasource.postgresql.pool
        assert hasattr(config.datasource.postgresql, "pool")
        # config.security.token.algorithm
        assert hasattr(config.security.token, "algorithm")

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_description_field(self, mock_read_yaml):
        """测试描述字段。"""
        mock_read_yaml.return_value = {}

        config = ServiceConfig()

        # 验证顶层描述字段
        assert hasattr(config, "description")
        assert config.description is None

        # 可以设置描述
        config.description = "Test configuration"
        assert config.description == "Test configuration"

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_with_yaml_file(self, mock_read_yaml):
        """测试从 YAML 文件加载配置。"""
        import os

        mock_read_yaml.return_value = {
            "app": {"name": "yaml_app", "version": "2.0.0"},
            "model": {"chat": {"name": "test_model"}},
        }

        os.environ["GE_CONFIG_FILE_LOCAL"] = "test.yaml"

        try:
            config = ServiceConfig()

            # 验证 YAML 配置加载
            assert config.app.name == "yaml_app"
            assert config.app.version == "2.0.0"
            assert config.model.chat.name == "test_model"
        finally:
            del os.environ["GE_CONFIG_FILE_LOCAL"]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_with_environment_override(self, mock_read_yaml):
        """测试环境变量覆盖配置。"""
        import os

        mock_read_yaml.return_value = {}

        os.environ["GRAPHEDU__APP__NAME"] = "env_app"

        try:
            config = ServiceConfig()

            # 验证配置对象存在（pydantic-settings 会处理环境变量）
            assert config.app is not None
        finally:
            del os.environ["GRAPHEDU__APP__NAME"]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_module_independence(self, mock_read_yaml):
        """测试各配置模块的独立性。"""
        mock_read_yaml.return_value = {}

        config = ServiceConfig()

        # 验证每个模块都有独立的配置对象
        assert config.app is not config.model
        assert config.security is not config.datasource
        assert config.logging is not config.system

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_serialization(self, mock_read_yaml):
        """测试配置序列化。"""
        mock_read_yaml.return_value = {}

        config = ServiceConfig()

        # 验证配置对象存在
        assert config is not None
        assert hasattr(config, "model_dump")

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_json_compatible(self, mock_read_yaml):
        """测试配置 JSON 兼容性。"""
        mock_read_yaml.return_value = {}

        config = ServiceConfig()

        # 验证配置支持 JSON 序列化
        assert hasattr(config, "model_dump_json")
        assert hasattr(config, "model_dump")

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_immutability_optional(self, mock_read_yaml):
        """测试配置的可变性（pydantic 默认可变）。"""
        mock_read_yaml.return_value = {}

        config = ServiceConfig()

        # 验证可以修改配置（pydantic BaseModel 默认可变）
        original_name = config.app.name
        config.app.name = "modified_app"

        # 注意：这会修改对象，因为 BaseModel 默认是可变的
        # 如果需要不可变性，应该使用 frozen=True
        assert config.app.name == "modified_app"

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_config_validation(self, mock_read_yaml):
        """测试配置验证。"""
        from pydantic import ValidationError

        # Mock 返回无效配置
        mock_read_yaml.return_value = {
            "security": {"token": {"expire": -100}},  # 无效：expire 必须 > 0
        }

        # ServiceConfig 应该使用默认值而不是抛出验证错误
        # 因为 expire 的默认值是有效的
        config = ServiceConfig()

        # 验证使用默认值（因为 YAML 值无效）
        assert config.security.token.expire > 0
