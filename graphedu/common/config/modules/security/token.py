"""Token 配置。"""

import logging

from pydantic import BaseModel, Field, field_validator

from graphedu.common.config.core.validators import validate_header_lowercase

logger = logging.getLogger(__name__)


class TokenConfig(BaseModel):
    """JWT Token 配置。"""

    description: str | None = Field(default=None, description="Token 配置描述信息（仅用于文档说明）")

    header: str = Field(default="authorization", description="HTTP 请求头字段名（必须小写）")

    secret: str = Field(default="secret", description="JWT 签名密钥（敏感信息，生产环境必须修改）")

    algorithm: str = Field(default="HS512", description="JWT 加密算法（支持 HS256、HS384、HS512 等）")

    expire: int = Field(default=120, gt=0, description="Token 过期时间（分钟）")

    @field_validator("header", mode="before")
    @classmethod
    def check_header_lowercase(cls, value: str) -> str:
        """验证并转换 header 为小写。"""
        return validate_header_lowercase(value)
