"""测试配置常量。"""

import pytest

from graphedu.common.config.core.constants import CONFIG_PREFIX, ConfigConstants, RunningConstants


class TestConfigConstants:
    """测试 ConfigConstants 常量类。"""

    def test_config_file_env_constant(self):
        """测试 CONFIG_FILE_ENV 常量。"""
        assert ConfigConstants.CONFIG_FILE_ENV == "GE_CONFIG_FILE_ENV"

    def test_config_file_local_constant(self):
        """测试 CONFIG_FILE_LOCAL 常量。"""
        assert ConfigConstants.CONFIG_FILE_LOCAL == "GE_CONFIG_FILE_LOCAL"

    def test_config_file_default_constant(self):
        """测试 CONFIG_FILE_DEFAULT 常量。"""
        assert ConfigConstants.CONFIG_FILE_DEFAULT == "dev.config.yaml"


class TestRunningConstants:
    """测试 RunningConstants 常量类。"""

    def test_running_state_constant(self):
        """测试 RUNNING_STATE 常量。"""
        assert RunningConstants.RUNNING_STATE == "RUNNING_STATE"

    def test_config_instance_constant(self):
        """测试 CONFIG_INSTANCE 常量。"""
        assert RunningConstants.CONFIG_INSTANCE == "CONFIG_INSTANCE"

    def test_res_inited_state_constant(self):
        """测试 RES_INITED_STATE 常量。"""
        assert RunningConstants.RES_INITED_STATE == "RES_INITED_STATE"


class TestConfigPrefix:
    """测试 CONFIG_PREFIX 常量。"""

    def test_config_prefix_value(self):
        """测试环境变量前缀。"""
        assert CONFIG_PREFIX == "GRAPHEDU"

    def test_config_prefix_format(self):
        """测试前缀格式（全大写，无下划线）。"""
        assert CONFIG_PREFIX.isupper()
        assert "_" not in CONFIG_PREFIX
