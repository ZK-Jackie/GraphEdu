"""Webhook payload generators for logging handlers.

This module provides payload generators that convert LogRecord objects
to webhook-compatible JSON payloads, including:
- TemplatePayloadGenerator: Template-based payload generation
- FeishuPayloadGenerator: Feishu-specific payload with signature support
"""

from collections.abc import Callable
import json
import logging
from typing import Any


class PayloadGenerator:
    """Base class for payload generators.

    Responsible for converting LogRecord objects to webhook-compatible payloads.
    Subclasses must implement the __call__ method.
    """

    def __call__(self, record: logging.LogRecord) -> dict[str, Any]:
        """Generate payload from log record. Subclasses must implement this method.

        Args:
            record: Log record to convert.

        Returns:
            Payload dictionary.
        """
        raise NotImplementedError


class TemplatePayloadGenerator(PayloadGenerator):
    """Template-based payload generator.

    Supports string templates or callable objects for payload generation.
    """

    def __init__(self, template: str | Callable[[logging.LogRecord], dict[str, Any]]):
        """Initialize template payload generator.

        Args:
            template: String template supporting LogRecord attributes, or callable object.
        """
        self.template = template
        self.is_callable = callable(template)

    def __call__(self, record: logging.LogRecord) -> dict[str, Any]:
        """将日志记录转换为 webhook payload。

        Args:
            record: 日志记录对象

        Returns:
            包含日志数据的字典

        Raises:
            ValueError: 模板无效或函数返回非字典值
        """
        if self.is_callable:
            # 如果是可调用对象，直接调用
            result = self.template(record)
            if isinstance(result, dict):
                return result
            raise ValueError("Payload 函数必须返回字典")

        # 字符串模板支持
        # 支持 {message}, {levelname}, {pathname}, {lineno}, {asctime} 等 LogRecord 属性
        try:
            formatted = self.template.format(**record.__dict__)
            return json.loads(formatted)
        except (KeyError, AttributeError, json.JSONDecodeError) as e:
            raise ValueError(f"无效的 payload 模板: {e}") from None


__all__ = [
    "PayloadGenerator",
    "TemplatePayloadGenerator",
]
