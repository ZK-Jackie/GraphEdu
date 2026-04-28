"""验证码 DTO 模型。"""
from pydantic import Field

from graphedu.common.models.dto.base import DTO


class CaptchaDTO(DTO):
    """验证码响应模型

    用于返回验证码相关信息

    Attributes:
        uuid: 会话 ID，用于验证码校验
        img: 验证码图片的 base64 编码
        code: 验证码答案，仅用于测试环境
        captcha_enabled: 是否启用验证码
    """

    uuid: str = Field(description="会话ID")
    img: str = Field(description="验证码图片的base64编码")
    code: int | str | None = Field(default=None, description="验证码答案，仅用于测试环境")
    captcha_enabled: bool | None = Field(default=True, description="是否启用验证码")


class TurnstileValidateDTO(DTO):
    """Cloudflare Turnstile 验证请求模型

    用于接收前端提交的 Turnstile 验证 token

    Attributes:
        token: Turnstile 验证 token（用户端返回的 response token）
        remote_ip: 可选的用户 IP 地址
    """

    token: str = Field(description="Turnstile 验证 token")
    remote_ip: str | None = Field(default=None, description="用户 IP 地址（可选）")
