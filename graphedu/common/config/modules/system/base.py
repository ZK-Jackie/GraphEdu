"""系统级配置（对应 system 命名空间）。"""

from pydantic import BaseModel, Field


class SystemConfig(BaseModel):
    """系统级配置（Spring Boot 风格）。"""

    timezone: str = Field(default="UTC", description="系统默认时区（如 UTC、Asia/Shanghai）")

    location_query: bool = Field(default=True, description="是否启用 IP 地址位置查询功能")
