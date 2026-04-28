"""验证码相关 Models 模块

本模块定义了与验证码业务逻辑相关的数据及传输对象，主要包括验证码服务端侧的返回结果。

"""
from pydantic import BaseModel, Field


class TurnstileValidateResult(BaseModel):
    """Turnstile 验证结果 BO 模型"""

    success: bool = Field(description="验证是否成功")
    challenge_ts: str | None = Field(default=None, description="验证时间戳（ISO 8601 格式）")
    hostname: str | None = Field(default=None, description="验证时使用的主机名")
    error_codes: list[str] | None = Field(default=None, description="错误码列表")
    action: str | None = Field(default=None, description="验证操作类型（仅 Managed 模式）")
    cdata: str | None = Field(default=None, description="客户数据（仅 Managed 模式）")
