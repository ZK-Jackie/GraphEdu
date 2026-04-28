"""Custom logging handlers and utilities.

This module provides custom logging handlers including:
- TimeLoggerRolloverHandler: Timed rotating file handler with custom naming
- FeishuWebhookHandler: Webhook handler for sending logs to Feishu
"""

from .feishu import FeishuWebhookHandler
from .time_handler import TimeLoggerRolloverHandler


def initialize_logging(logging_config: dict) -> None:
    """初始化根日志记录器"""
    import logging.config

    # 读取YAML配置文件
    try:
        logging.config.dictConfig(logging_config)
        logging.info("Logging configuration loaded successfully.")
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logging.error(f"Failed to load logging configuration: {e}.")
        raise e from e


__all__ = ["FeishuWebhookHandler", "TimeLoggerRolloverHandler", "initialize_logging"]
