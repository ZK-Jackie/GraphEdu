"""应用元数据配置（对应 app 命名空间，Spring Boot 风格）。"""

from pydantic import BaseModel, Field


class AppMetaConfig(BaseModel):
    """应用元数据配置（Spring Boot 风格）。"""

    name: str = Field(default="graphedu-service", description="应用程序名称")

    version: str = Field(default="0.0.1", description="应用程序版本号（语义化版本）")

    author: str | None = Field(default=None, description="应用程序作者")

    repository: str | None = Field(default=None, description="代码仓库地址（URL）")
