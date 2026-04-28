from ..webhook_handler import WebhookLoggerHandler
from ._payload import FeishuPayloadGenerator


class FeishuWebhookHandler(WebhookLoggerHandler):
    """Feishu-specific Webhook logging handler.

    Pre-configured with FeishuPayloadGenerator.

    Args:
        url: Feishu webhook URL.
        sign_secret: Feishu webhook signature secret (optional).
        template_path: Path to the JSON template file (optional).
        template_mapping: Additional template variable mappings (optional).
        timeout: Request timeout in seconds (default: 5).
        retries: Number of retries on failure (default: 3).
    """

    headers = {"Content-Type": "application/json"}

    def __init__(
        self,
        url: str,
        sign_secret: str | None = None,
        template_path: str | None = None,
        template_mapping: dict[str, str] | None = None,
        timeout: int = 5,
        retries: int = 3,
    ):
        payload_generator = FeishuPayloadGenerator(sign_secret=sign_secret, template_path=template_path)
        super().__init__(
            url=url, payload_generator=payload_generator, headers=self.headers, timeout=timeout, retries=retries
        )
