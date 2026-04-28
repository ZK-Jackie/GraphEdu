"""登录配置。"""

from pydantic import BaseModel, Field


class LoginConfig(BaseModel):
    """用户登录配置。"""

    description: str | None = Field(default=None, description="登录配置描述信息（仅用于文档说明）")

    single_end: bool = Field(default=True, description="单一用户是否只允许一处登录（单点登录模式）")

    captcha: bool = Field(default=True, description="是否启用验证码校验")
