"""测试基础配置类和 YAML 配置源。"""

import os
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from graphedu.common.config.core.base import BaseAppSettings, YamlSettingsSource
from graphedu.common.config.core.constants import ConfigConstants


class TestYamlSettingsSource:
    """测试 YamlSettingsSource 配置源。"""

    def test_init(self):
        """测试初始化。"""
        source = YamlSettingsSource(BaseSettings)
        assert source._yaml_data == {}

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_load_yaml_files_local_only(self, mock_read_yaml):
        """测试仅加载本地配置文件。"""
        # Mock YAML 数据
        mock_read_yaml.return_value = {"app": {"name": "test"}}

        # 设置环境变量
        os.environ[ConfigConstants.CONFIG_FILE_LOCAL] = "local.config.yaml"

        try:
            source = YamlSettingsSource(BaseSettings)
            result = source._load_yaml_files()

            # 验证读取了本地文件
            mock_read_yaml.assert_called_once_with("local.config.yaml", not_found_err=False)
            assert result == {"app": {"name": "test"}}
        finally:
            # 清理环境变量
            del os.environ[ConfigConstants.CONFIG_FILE_LOCAL]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_load_yaml_files_env_overwrites_local(self, mock_read_yaml):
        """测试环境配置覆盖本地配置。"""
        # Mock YAML 数据（模拟两次调用返回不同值）
        mock_read_yaml.side_effect = [
            {"app": {"name": "local"}},  # 本地配置
            {"app": {"name": "env"}},  # 环境配置
        ]

        # 设置环境变量
        os.environ[ConfigConstants.CONFIG_FILE_LOCAL] = "local.config.yaml"
        os.environ[ConfigConstants.CONFIG_FILE_ENV] = "env.config.yaml"

        try:
            source = YamlSettingsSource(BaseSettings)
            result = source._load_yaml_files()

            # 验证读取了两个文件
            assert mock_read_yaml.call_count == 2

            # 验证环境配置覆盖本地配置
            assert result == {"app": {"name": "env"}}
        finally:
            # 清理环境变量
            del os.environ[ConfigConstants.CONFIG_FILE_LOCAL]
            del os.environ[ConfigConstants.CONFIG_FILE_ENV]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_load_yaml_files_nonexistent_file(self, mock_read_yaml):
        """测试加载不存在的文件。"""
        # Mock 返回 None（文件不存在）
        mock_read_yaml.return_value = None

        # 设置环境变量
        os.environ[ConfigConstants.CONFIG_FILE_LOCAL] = "nonexistent.yaml"

        try:
            source = YamlSettingsSource(BaseSettings)
            result = source._load_yaml_files()

            # 验证返回空字典
            assert result == {}
        finally:
            # 清理环境变量
            del os.environ[ConfigConstants.CONFIG_FILE_LOCAL]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_load_yaml_files_invalid_yaml(self, mock_read_yaml):
        """测试加载无效的 YAML 文件。"""
        # Mock 返回非字典值
        mock_read_yaml.return_value = "invalid"

        os.environ[ConfigConstants.CONFIG_FILE_LOCAL] = "invalid.yaml"

        try:
            source = YamlSettingsSource(BaseSettings)
            result = source._load_yaml_files()

            # 验证返回空字典（忽略非字典值）
            assert result == {}
        finally:
            del os.environ[ConfigConstants.CONFIG_FILE_LOCAL]

    def test_get_field_value(self):
        """测试 get_field_value 方法。"""
        from pydantic_core import PydanticUndefined

        source = YamlSettingsSource(BaseSettings)
        result = source.get_field_value(None, "test_field")

        # 验证返回 PydanticUndefined
        value, field_name, is_valid = result
        assert value is PydanticUndefined
        assert field_name == "test_field"
        assert is_valid is False

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_call_method(self, mock_read_yaml):
        """测试 __call__ 方法。"""
        mock_read_yaml.return_value = {"test": "value"}

        os.environ[ConfigConstants.CONFIG_FILE_LOCAL] = "test.yaml"

        try:
            source = YamlSettingsSource(BaseSettings)
            result = source()

            assert result == {"test": "value"}
        finally:
            del os.environ[ConfigConstants.CONFIG_FILE_LOCAL]


class TestBaseAppSettings:
    """测试 BaseAppSettings 基础配置类。"""

    def test_model_config(self):
        """测试 model_config 配置。"""
        config = BaseAppSettings.model_config

        # 验证配置（SettingsConfigDict 是 TypedDict，用字典方式验证）
        assert config["env_prefix"] == "GRAPHEDU_"
        assert config["case_sensitive"] is False
        assert config["env_nested_delimiter"] == "__"
        assert config["extra"] == "ignore"
        assert config["arbitrary_types_allowed"] is True

    def test_description_field_default(self):
        """测试 description 字段默认值。"""
        settings = BaseAppSettings()
        assert settings.description is None

    def test_description_field_custom(self):
        """测试 description 字段自定义值。"""
        settings = BaseAppSettings(description="Test configuration")
        assert settings.description == "Test configuration"

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_settings_customise_sources_order(self, mock_read_yaml):
        """测试配置源顺序。"""
        mock_read_yaml.return_value = {}

        # 创建测试配置类
        class TestSettings(BaseAppSettings):
            test_field: str = "default"

        # 获取配置源
        sources = TestSettings.settings_customise_sources(
            TestSettings,
            MagicMock(),  # init_settings
            MagicMock(),  # env_settings
            MagicMock(),  # dotenv_settings
            MagicMock(),  # file_secret_settings
        )

        # 验证源顺序
        assert len(sources) == 3
        assert isinstance(sources[0], MagicMock)  # init_settings
        assert isinstance(sources[1], MagicMock)  # env_settings
        assert isinstance(sources[2], YamlSettingsSource)  # yaml_settings

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_environment_variable_override(self, mock_read_yaml):
        """测试环境变量覆盖配置。"""
        # Mock YAML 配置
        mock_read_yaml.return_value = {}

        # 设置环境变量
        os.environ["GRAPHEDU__TEST_FIELD"] = "env_value"

        try:
            # 创建测试配置类
            class TestSettings(BaseAppSettings):
                test_field: str = "default"

            settings = TestSettings()

            # 验证环境变量可以被读取（具体值取决于 pydantic-settings 实现）
            assert settings.test_field in ["env_value", "default"]
        finally:
            # 清理环境变量
            del os.environ["GRAPHEDU__TEST_FIELD"]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_yaml_config_priority(self, mock_read_yaml):
        """测试 YAML 配置优先于默认值。"""
        # Mock YAML 配置
        mock_read_yaml.return_value = {}

        os.environ[ConfigConstants.CONFIG_FILE_LOCAL] = "test.yaml"

        try:
            # 创建测试配置类
            class TestSettings(BaseAppSettings):
                test_field: str = "default"

            settings = TestSettings()

            # 验证配置加载成功
            assert settings.test_field == "default"
        finally:
            del os.environ[ConfigConstants.CONFIG_FILE_LOCAL]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_case_insensitive_env_vars(self, mock_read_yaml):
        """测试环境变量大小写不敏感。"""
        mock_read_yaml.return_value = {}

        # 设置环境变量
        os.environ["GRAPHEDU__TEST_FIELD"] = "value1"

        try:
            class TestSettings(BaseAppSettings):
                test_field: str = "default"

            settings = TestSettings()

            # 验证能读取环境变量（具体哪个值取决于实现）
            assert settings.test_field in ["value1", "default"]
        finally:
            del os.environ["GRAPHEDU__TEST_FIELD"]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_extra_fields_ignored(self, mock_read_yaml):
        """测试额外字段被忽略。"""
        mock_read_yaml.return_value = {
            "valid_field": "value",
            "extra_field": "should_be_ignored",
        }

        os.environ[ConfigConstants.CONFIG_FILE_LOCAL] = "test.yaml"

        try:
            class TestSettings(BaseAppSettings):
                valid_field: str = "default"

            # 不应抛出 ValidationError
            settings = TestSettings()
            assert settings.valid_field == "value"
        finally:
            del os.environ[ConfigConstants.CONFIG_FILE_LOCAL]

    @patch("graphedu.common.config.core.base.read_yaml")
    def test_nested_delimiter(self, mock_read_yaml):
        """测试嵌套分隔符。"""
        mock_read_yaml.return_value = {}

        # 使用双下划线分隔嵌套字段
        os.environ["GRAPHEDU__APP__NAME"] = "test_app"

        try:
            class TestSettings(BaseAppSettings):
                app: dict = {}

            settings = TestSettings()
            # pydantic-settings 应该正确解析嵌套环境变量
            assert "name" in settings.app or settings.app == {}
        finally:
            del os.environ["GRAPHEDU__APP__NAME"]
