"""部署配置的 Pydantic 模型定义。"""

from typing import Literal

from pydantic import BaseModel, Field

_SupportedProfiles = Literal["postgres", "redis", "neo4j", "backend", "frontend"] | str


class DeployImages(BaseModel):
    """Docker 镜像版本配置。

    每个字段对应一个服务的镜像标签（tag），用于 .env 和 docker-compose.yaml。
    默认值与项目当前使用的镜像版本保持一致。
    """

    postgres: str = Field(default="18.3.0", description="PostgreSQL 镜像版本（含 pgvector、AGE 扩展）")
    redis: str = Field(default="8.6.2-alpine", description="Redis 镜像版本")
    backend: str = Field(default="latest", description="后端服务镜像版本")
    frontend: str = Field(default="latest", description="前端服务镜像版本")


class DeployConfig(BaseModel):
    """部署配置（Docker Compose Profiles + 镜像版本）。"""

    profiles: list[_SupportedProfiles] = Field(default_factory=list, description="Docker Compose profiles 列表")
    images: DeployImages = Field(default_factory=DeployImages, description="Docker 镜像版本配置")
