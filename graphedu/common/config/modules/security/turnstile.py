"""Cloudflare Turnstile 验证码配置。"""

from pydantic import BaseModel, Field


class TurnstileConfig(BaseModel):
    """Cloudflare Turnstile 验证码配置。

    References:
        https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
    """

    description: str | None = Field(default=None)

    secret: str = Field(default="")
    """Cloudflare Turnstile 密钥（敏感信息）"""

    verify_url: str = Field(default="https://challenges.cloudflare.com/turnstile/v0/siteverify")
    """Turnstile 验证 API 端点 URL"""

    timeout: float = Field(default=10.0, gt=0)
    """请求超时时间（秒）"""
