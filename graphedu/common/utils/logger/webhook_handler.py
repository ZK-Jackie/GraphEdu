"""Optimized Webhook Logger design.

Supports dynamic payload generation and multiple webhook services.
"""

from collections.abc import Callable
import logging
import queue
from typing import Any

import httpx
from tenacity import Retrying, stop_after_attempt

from .webhook_payload import PayloadGenerator, TemplatePayloadGenerator


# ==================== Webhook Handler ====================
class _WebhookLoggerDispatcher(logging.Handler):
    """Internal handler running in a dedicated listener thread.

    Responsible for actually sending HTTP requests.
    """

    def __init__(
        self,
        url: str,
        payload_generator: PayloadGenerator,
        headers: dict = None,
        timeout: int = 5,
        retries: int = 3,
    ):
        super().__init__()
        self.url = url
        self.payload_generator = payload_generator
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout
        self.retries = retries
        self._client = httpx.Client(timeout=timeout)

    def emit(self, record):
        try:
            # Generate payload using payload_generator
            payload = self.payload_generator(record)

            # Send with retry mechanism
            try:
                for attempt in Retrying(stop=stop_after_attempt(self.retries)):
                    with attempt:
                        response = self._client.post(self.url, json=payload, headers=self.headers)
                        response.raise_for_status()
            except Exception as e:
                raise RuntimeError(f"Failed to send log to webhook (retried {self.retries} times): {e}") from None
        except Exception:
            self.handleError(record)


class WebhookLoggerHandler(logging.Handler):
    """Generic Webhook logging handler.

    Usage examples:
        # Method 1: Use predefined PayloadGenerator
        handler = WebhookLoggerHandler(
            url="https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
            payload_generator=FeishuPayloadGenerator(sign_secret="xxx")
        )

        # Method 2: Use custom template (supports all LogRecord attributes)
        template = json.dumps({
            "text": "[{levelname}] {asctime} - {message}"
        })
        handler = WebhookLoggerHandler(
            url="https://example.com/webhook",
            payload_generator=TemplatePayloadGenerator(template)
        )

        # Method 3: Use custom function (most flexible)
        def custom_generator(record):
            return {
                "level": record.levelname,
                "msg": record.getMessage(),
                "custom_field": "real-time computed value"
            }
        handler = WebhookLoggerHandler(
            url="https://example.com/webhook",
            payload_generator=custom_generator
        )
    """

    def __init__(
        self,
        url: str,
        payload_generator: PayloadGenerator | Callable[[logging.LogRecord], dict[str, Any]],
        headers: dict = None,
        timeout: int = 5,
        retries: int = 3,
    ):
        """Initialize webhook logger handler.

        Args:
            url: Webhook URL.
            payload_generator: Payload generator (PayloadGenerator instance or callable).
            headers: Request headers.
            timeout: Timeout in seconds.
            retries: Number of retries.
        """
        super().__init__()

        # 如果传入的是可调用对象但不是 PayloadGenerator 实例，包装一下
        if not isinstance(payload_generator, PayloadGenerator):
            payload_generator = TemplatePayloadGenerator(payload_generator)

        self.url = url
        self.headers = headers
        self.timeout = timeout
        self.retries = retries

        # 创建队列
        self.queue = queue.Queue(-1)

        # 创建实际的发送者
        self.dispatcher = _WebhookLoggerDispatcher(
            url=url, payload_generator=payload_generator, headers=headers, timeout=timeout, retries=retries
        )

        # 创建监听器
        self.listener = logging.handlers.QueueListener(self.queue, self.dispatcher, respect_handler_level=True)

        # 启动监听
        self.listener.start()

    def setFormatter(self, fmt):  # noqa: N802
        """Note: WebhookLoggerHandler typically doesn't need setFormatter.

        The formatting logic is handled in PayloadGenerator.
        """
        super().setFormatter(fmt)
        # Optionally pass formatter to dispatcher
        if self.dispatcher:
            self.dispatcher.setFormatter(fmt)

    def emit(self, record):
        """发送日志记录到队列。

        Args:
            record: 要发送的日志记录
        """
        try:
            self.queue.put(record)
        except Exception:
            self.handleError(record)

    def close(self):
        """关闭处理器并停止监听器。"""
        self.listener.stop()
        super().close()


__all__ = [
    "WebhookLoggerHandler",
]
