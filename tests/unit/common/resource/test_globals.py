"""
全局资源函数测试

测试日志初始化功能。
"""

import logging
from unittest.mock import patch

import pytest

from graphedu.common.utils.logger import initialize_logging

# =============================================================================
# initialize_logging 测试
# =============================================================================

class TestInitializeLogging:
    """测试根日志记录器初始化"""

    @pytest.fixture
    def log_config(self):
        """日志配置字典"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                }
            },
            'root': {
                'level': 'INFO',
                'handlers': ['console']
            }
        }

    def test_initialize_with_valid_config(self, log_config):
        """测试使用有效配置初始化日志"""
        with patch('logging.config.dictConfig') as mock_dict_config:
            initialize_logging(log_config)
            mock_dict_config.assert_called_once_with(log_config)

    def test_initialize_with_invalid_config(self, log_config):
        """测试 dictConfig 抛出异常时重新抛出"""
        with patch('logging.config.dictConfig') as mock_dict_config:
            mock_dict_config.side_effect = ValueError("Invalid config")

            with pytest.raises(ValueError) as exc_info:
                initialize_logging(log_config)

            assert "Invalid config" in str(exc_info.value)

    def test_initialize_fallback_to_basic_config(self, log_config):
        """测试 dictConfig 失败时回退到 basicConfig"""
        with patch('logging.config.dictConfig') as mock_dict_config:
            with patch('logging.basicConfig') as mock_basic_config:
                mock_dict_config.side_effect = Exception("Load failed")

                with pytest.raises(Exception):
                    initialize_logging(log_config)

                mock_basic_config.assert_called_once_with(level=logging.INFO)
