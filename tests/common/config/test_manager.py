"""测试配置管理器单例。"""

import os
from unittest.mock import MagicMock, patch

import pytest

from graphedu.common.config import ConfigManager
from graphedu.common.config.core.constants import ConfigConstants, RunningConstants
from graphedu.common.config.modes.service import ServiceConfig


class TestConfigManager:
    """测试 ConfigManager 配置管理器。"""

    def setup_method(self):
        """每个测试方法前的设置。"""
        # 重置单例实例
        ConfigManager._instance = None

    def teardown_method(self):
        """每个测试方法后的清理。"""
        # 清理单例实例
        ConfigManager._instance = None
        # 清理环境变量
        for key in list(os.environ.keys()):
            if key.startswith("GE_") or key.startswith("GRAPHEDU_"):
                del os.environ[key]

    @patch("graphedu.common.config.manager.ContextManager")
    @patch.object(ServiceConfig, "__init__", return_value=None)
    def test_load_default_config(self, mock_service_init, mock_context):
        """测试加载默认配置。"""
        mock_context.get_global_context.return_value = None
        mock_context.set_global_context = MagicMock()

        # 加载默认配置
        config = ConfigManager.load()

        # 验证实例创建
        assert isinstance(config, ServiceConfig)
        assert ConfigManager._instance is config

        # 验证环境变量设置
        assert os.environ.get(ConfigConstants.CONFIG_FILE_LOCAL) == "dev.config.yaml"

        # 验证上下文设置
        assert mock_context.set_global_context.call_count == 3

    @patch("graphedu.common.config.manager.ContextManager")
    @patch.object(ServiceConfig, "__init__", return_value=None)
    def test_load_custom_config(self, mock_service_init, mock_context):
        """测试加载自定义配置文件。"""
        mock_context.get_global_context.return_value = None
        mock_context.set_global_context = MagicMock()

        # 加载自定义配置
        config = ConfigManager.load(filename="prod.config.yaml")

        # 验证环境变量设置
        assert os.environ.get(ConfigConstants.CONFIG_FILE_LOCAL) == "prod.config.yaml"

        # 验证实例创建
        assert isinstance(config, ServiceConfig)

    @patch("graphedu.common.config.manager.ContextManager")
    @patch.object(ServiceConfig, "__init__", return_value=None)
    def test_load_with_reload_false(self, mock_service_init, mock_context):
        """测试 reload=False 时复用已有实例。"""
        mock_context.get_global_context.return_value = None
        mock_context.set_global_context = MagicMock()

        # 第一次加载
        config1 = ConfigManager.load()

        # 第二次加载（reload=False）
        config2 = ConfigManager.load(reload=False)

        # 验证返回同一实例
        assert config1 is config2
        assert mock_service_init.call_count == 1

    @patch("graphedu.common.config.manager.ContextManager")
    @patch.object(ServiceConfig, "__init__", return_value=None)
    def test_load_with_reload_true(self, mock_service_init, mock_context):
        """测试 reload=True 时重新加载。"""
        mock_context.get_global_context.return_value = None
        mock_context.set_global_context = MagicMock()

        # 第一次加载
        config1 = ConfigManager.load()

        # 第二次加载（reload=True）
        config2 = ConfigManager.load(reload=True)

        # 验证创建新实例
        assert config1 is not config2
        assert mock_service_init.call_count == 2

    @patch("graphedu.common.config.manager.ContextManager")
    @patch.object(ServiceConfig, "__init__", return_value=None)
    def test_load_sets_running_mode(self, mock_service_init, mock_context):
        """测试加载时设置运行模式。"""
        mock_context.get_global_context.return_value = None
        mock_context.set_global_context = MagicMock()

        # 加载配置
        ConfigManager.load(running_mode="builder")

        # 验证运行模式设置
        mock_context.set_global_context.assert_any_call(RunningConstants.RUNNING_STATE, "BUILDER")

    @patch("graphedu.common.config.manager.ContextManager")
    @patch.object(ServiceConfig, "__init__", return_value=None)
    def test_load_sets_config_instance(self, mock_service_init, mock_context):
        """测试加载时设置配置实例。"""
        mock_context.get_global_context.return_value = None
        mock_context.set_global_context = MagicMock()

        # 加载配置
        config = ConfigManager.load()

        # 验证配置实例设置
        calls = mock_context.set_global_context.call_args_list
        config_call = [call for call in calls if call[0][0] == RunningConstants.CONFIG_INSTANCE]
        assert len(config_call) == 1
        assert config_call[0][0][1] is config

    @patch("graphedu.common.config.manager.ContextManager")
    @patch.object(ServiceConfig, "__init__", return_value=None)
    def test_load_sets_resource_inited(self, mock_service_init, mock_context):
        """测试加载时设置资源初始化状态。"""
        mock_context.get_global_context.return_value = None
        mock_context.set_global_context = MagicMock()

        # 加载配置
        ConfigManager.load()

        # 验证资源初始化状态设置
        calls = mock_context.set_global_context.call_args_list
        init_call = [call for call in calls if call[0][0] == RunningConstants.RES_INITED_STATE]
        assert len(init_call) == 1
        assert init_call[0][0][1] is True

    @patch("graphedu.common.config.manager.ContextManager")
    @patch.object(ServiceConfig, "__init__", return_value=None)
    def test_get_cached_instance(self, mock_service_init, mock_context):
        """测试获取缓存的实例。"""
        mock_context.get_global_context.return_value = None
        mock_context.set_global_context = MagicMock()

        # 加载配置
        config1 = ConfigManager.load()

        # 获取配置
        config2 = ConfigManager.get()

        # 验证返回同一实例
        assert config1 is config2
        assert mock_service_init.call_count == 1

    @patch("graphedu.common.config.manager.ContextManager")
    @patch.object(ServiceConfig, "__init__", return_value=None)
    def test_get_from_context(self, mock_service_init, mock_context):
        """测试从上下文获取配置。"""
        # Mock 上下文返回配置实例
        mock_config = MagicMock(spec=ServiceConfig)
        mock_context.get_global_context.return_value = mock_config
        mock_context.set_global_context = MagicMock()

        # 重置实例
        ConfigManager._instance = None

        # 获取配置
        config = ConfigManager.get()

        # 验证从上下文获取
        assert config is mock_config
        assert ConfigManager._instance is config

    @patch("graphedu.common.config.manager.ContextManager")
    @patch.object(ServiceConfig, "__init__", return_value=None)
    def test_get_auto_load_default(self, mock_service_init, mock_context):
        """测试自动加载默认配置。"""
        mock_context.get_global_context.return_value = None
        mock_context.set_global_context = MagicMock()

        # 重置实例
        ConfigManager._instance = None

        # 获取配置（未加载时自动加载）
        config = ConfigManager.get()

        # 验证自动加载
        assert isinstance(config, ServiceConfig)
        assert ConfigManager._instance is config

    @patch("graphedu.common.config.manager.ContextManager")
    @patch.object(ServiceConfig, "__init__", return_value=None)
    def test_multiple_running_modes(self, mock_service_init, mock_context):
        """测试不同运行模式的加载。"""
        mock_context.get_global_context.return_value = None
        mock_context.set_global_context = MagicMock()

        # 测试不同运行模式
        modes = ["service", "builder", "converter"]
        expected_states = ["SERVICE", "BUILDER", "CONVERTER"]

        for mode, expected_state in zip(modes, expected_states):
            ConfigManager._instance = None
            ConfigManager.load(running_mode=mode)

            # 验证运行模式设置
            calls = mock_context.set_global_context.call_args_list
            state_call = [call for call in calls if call[0][0] == RunningConstants.RUNNING_STATE]
            assert state_call[-1][0][1] == expected_state


class TestConfigManagerIntegration:
    """测试 ConfigManager 集成场景。"""

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

    @patch("graphedu.common.config.manager.ContextManager")
    def test_load_config_function(self, mock_context):
        """测试 load_config 包装函数。"""
        from graphedu.common.config import load_config

        mock_context.get_global_context.return_value = None
        mock_context.set_global_context = MagicMock()

        # 调用包装函数
        config = load_config(filename="test.config.yaml")

        # 验证环境变量设置
        assert os.environ.get(ConfigConstants.CONFIG_FILE_LOCAL) == "test.config.yaml"

    @patch("graphedu.common.config.manager.ContextManager")
    @patch.object(ServiceConfig, "__init__", return_value=None)
    def test_get_config_function(self, mock_service_init, mock_context):
        """测试 get_config 包装函数。"""
        from graphedu.common.config import get_config

        mock_context.get_global_context.return_value = None
        mock_context.set_global_context = MagicMock()

        # 调用包装函数
        config = get_config()

        # 验证返回配置实例
        assert config is not None
