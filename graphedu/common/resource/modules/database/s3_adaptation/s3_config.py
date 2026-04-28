"""S3 客户端配置模块

定义不同 S3 服务提供商的配置规范
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

# 供外部模块导入的类型定义
ProviderTypes = Literal["aws", "aliyun", "minio", "rustfs", "cloudflare", "tencent", "generic"]


class S3Provider(StrEnum):
    """S3 服务提供商枚举"""

    AWS = "aws"
    ALIYUN = "aliyun"
    MINIO = "minio"
    RUSTFS = "rustfs"
    CLOUDFLARE = "cloudflare"
    TENCENT = "tencent"
    GENERIC = "generic"


@dataclass(frozen=True)
class S3ProviderConfig:
    """S3 服务商配置

    Attributes:
        addressing_style: 地址风格，'virtual' 或 'path'
            - virtual: bucket_name.endpoint.com (阿里云、AWS)
            - path: endpoint.com/bucket_name (MinIO、RustFS)
        signature_version: 签名版本，'s3v4' 或 'v2'
        url_template: URL 生成模板，支持变量: {bucket}, {endpoint}, {object}
        force_path_style: 是否强制使用路径风格（boto3 参数）
    """

    addressing_style: Literal["virtual", "path"] = "path"
    signature_version: str = "s3v4"
    url_template: str = "{endpoint}/{bucket}/{object}"
    force_path_style: bool = True

    def get_boto_config(self):
        """获取 boto3 Config 对象"""
        from botocore.config import Config

        addressing_style = "virtual" if self.addressing_style == "virtual" else None

        config_params = {"signature_version": self.signature_version}
        if addressing_style:
            config_params["s3"] = {"addressing_style": addressing_style}

        return Config(**config_params) if config_params else None

    def build_object_url(self, endpoint: str, bucket: str, object_name: str, use_ssl: bool = True) -> str:
        """构建对象访问 URL

        Args:
            endpoint: OSS 端点
            bucket: 存储桶名称
            object_name: 对象名称
            use_ssl: 是否使用 SSL
        """
        # 移除 endpoint 的协议前缀
        clean_endpoint = endpoint.split("://")[-1].rstrip("/")
        protocol = "https" if use_ssl else "http"

        # 根据模板生成 URL
        url = self.url_template.format(endpoint=clean_endpoint, bucket=bucket, object=object_name)

        return f"{protocol}://{url}"


# 预定义服务商配置
PROVIDER_CONFIGS: dict[S3Provider, S3ProviderConfig] = {
    S3Provider.AWS: S3ProviderConfig(
        addressing_style="virtual",
        signature_version="s3v4",
        url_template="{bucket}.s3.amazonaws.com/{object}",
        force_path_style=False,
    ),
    S3Provider.ALIYUN: S3ProviderConfig(
        addressing_style="virtual",
        signature_version="s3",
        url_template="{bucket}.{endpoint}/{object}",
        force_path_style=False,
    ),
    S3Provider.MINIO: S3ProviderConfig(
        addressing_style="path",
        signature_version="s3v4",
        url_template="{endpoint}/{bucket}/{object}",
        force_path_style=True,
    ),
    S3Provider.RUSTFS: S3ProviderConfig(
        addressing_style="path",
        signature_version="s3v4",
        url_template="{endpoint}/{bucket}/{object}",
        force_path_style=True,
    ),
    S3Provider.TENCENT: S3ProviderConfig(
        addressing_style="virtual",
        signature_version="s3v4",
        url_template="{bucket}.{endpoint}/{object}",
        force_path_style=False,
    ),
    S3Provider.CLOUDFLARE: S3ProviderConfig(
        addressing_style="virtual",
        signature_version="s3v4",
        url_template="{endpoint}/{bucket}/{object}",
        force_path_style=False,
    ),
    S3Provider.GENERIC: S3ProviderConfig(
        addressing_style="path",
        signature_version="s3v4",
        url_template="{endpoint}/{bucket}/{object}",
        force_path_style=True,
    ),
}


def get_provider_config(provider: S3Provider | str) -> S3ProviderConfig:
    """获取服务商配置

    Args:
        provider: 服务商名称或枚举

    Returns:
        S3ProviderConfig: 服务商配置

    Raises:
        ValueError: 不支持的服务商
    """
    if isinstance(provider, str):
        try:
            provider = S3Provider(provider.lower())
        except ValueError:
            logger.warning(f"Unknown provider '{provider}', falling back to GENERIC")
            provider = S3Provider.GENERIC

    return PROVIDER_CONFIGS.get(provider, PROVIDER_CONFIGS[S3Provider.GENERIC])


# 导入 logger（避免循环导入）
import logging

logger = logging.getLogger(__name__)
