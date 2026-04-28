"""安全配置聚合（对应 security 命名空间）。"""

from pydantic import BaseModel, Field

from .login import LoginConfig
from .token import TokenConfig
from .turnstile import TurnstileConfig


class SecurityConfig(BaseModel):
    """安全配置聚合（Spring Boot 风格）。"""

    login: LoginConfig = Field(default_factory=LoginConfig)
    """登录配置"""

    token: TokenConfig = Field(default_factory=TokenConfig)
    """JWT Token 配置"""

    turnstile: TurnstileConfig = Field(default_factory=TurnstileConfig)
    """Cloudflare Turnstile 验证码配置"""
