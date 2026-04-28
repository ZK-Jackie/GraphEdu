"""对象存储服务配置（S3 兼容）。"""

import logging
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)

ProviderTypes = Literal["aws", "aliyun", "minio", "rustfs", "cloudflare", "tencent", "generic"]


class OssConfig(BaseModel):
    """对象存储服务配置（S3 兼容）。"""

    provider: ProviderTypes = Field(default="minio", description="OSS 服务提供商类型")
    endpoint: AnyHttpUrl = Field(default="http://localhost:9000", description="OSS 服务器地址（包含协议和端口）")
    access_key: str = Field(default="minioadmin", description="OSS 访问密钥 ID（敏感信息）")
    secret_key: str = Field(default="minioadmin", description="OSS 访问密钥 Secret（敏感信息）")
    use_ssl: bool = Field(default=False, description="是否使用 SSL/TLS 加密连接")
    bucket: str = Field(default="test", description="默认存储桶名称")
    upload_from: str = Field(default="/tmp/graphedu", description="本地上传文件的临时目录路径")
    download_to: str = Field(default="/tmp/graphedu", description="下载文件的本地目标目录路径")

    model_config = ConfigDict(url_preserve_empty_path=True, validate_default=True)

    @field_validator("download_to", "upload_from")
    @classmethod
    def validate_path(cls, value: str) -> str:
        """验证并规范化路径。"""
        ret = value
        if ret.endswith("/"):
            logger.debug("The path should not end with `/`, has removed it")
            ret = ret[:-1]
        logger.debug(f"Validate path: {ret}")
        return ret
