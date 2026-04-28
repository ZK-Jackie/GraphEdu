"""通用视图对象模块。"""

from pydantic import Field

from graphedu.common.models.vo.base import VO


class TurnstileValidateVO(VO):
    """Cloudflare Turnstile 验证结果响应模型"""

    success: bool = Field(description="验证是否成功")
    challenge_ts: str | None = Field(default=None, description="验证时间戳（ISO 8601 格式）")
    hostname: str | None = Field(default=None, description="验证时使用的主机名")
    error_codes: list[str] | None = Field(default=None, description="错误码列表")
    action: str | None = Field(default=None, description="验证操作类型（仅 Managed 模式）")
    cdata: str | None = Field(default=None, description="客户数据（仅 Managed 模式）")
