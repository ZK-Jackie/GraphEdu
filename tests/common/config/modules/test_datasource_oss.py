"""测试 OSS 配置。"""

import logging
from unittest.mock import patch

import pytest
from pydantic import AnyHttpUrl, ValidationError

from graphedu.common.config.modules.datasource.oss import OssConfig, ProviderTypes


class TestOssConfig:
    """测试 OssConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = OssConfig()

        assert config.provider == "minio"
        assert str(config.endpoint) == "http://localhost:9000"
        assert config.access_key == "minioadmin"
        assert config.secret_key == "minioadmin"
        assert config.use_ssl is False
        assert config.bucket == "test"
        assert config.upload_from == "/tmp/graphedu"
        assert config.download_to == "/tmp/graphedu"

    def test_custom_provider(self):
        """测试自定义提供商。"""
        providers: list[ProviderTypes] = ["aws", "aliyun", "minio", "rustfs",
                                          "cloudflare", "tencent", "generic"]

        for provider in providers:
            config = OssConfig(provider=provider)
            assert config.provider == provider

    def test_custom_endpoint(self):
        """测试自定义端点。"""
        config = OssConfig(endpoint="https://s3.amazonaws.com")

        assert str(config.endpoint) == "https://s3.amazonaws.com"

    def test_custom_access_key(self):
        """测试自定义访问密钥。"""
        config = OssConfig(access_key="AKIAIOSFODNN7EXAMPLE")

        assert config.access_key == "AKIAIOSFODNN7EXAMPLE"

    def test_custom_secret_key(self):
        """测试自定义密钥。"""
        config = OssConfig(secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")

        assert config.secret_key == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

    def test_use_ssl_true(self):
        """测试启用 SSL。"""
        config = OssConfig(use_ssl=True)

        assert config.use_ssl is True

    def test_custom_bucket(self):
        """测试自定义存储桶。"""
        config = OssConfig(bucket="my-bucket")

        assert config.bucket == "my-bucket"

    def test_custom_upload_from(self):
        """测试自定义上传目录。"""
        config = OssConfig(upload_from="/var/uploads")

        assert config.upload_from == "/var/uploads"

    def test_custom_download_to(self):
        """测试自定义下载目录。"""
        config = OssConfig(download_to="/var/downloads")

        assert config.download_to == "/var/downloads"

    def test_upload_from_trailing_slash(self):
        """测试上传目录路径末尾斜杠被移除。"""
        with patch("graphedu.common.config.modules.datasource.oss.logger") as mock_logger:
            config = OssConfig(upload_from="/tmp/uploads/")

            assert config.upload_from == "/tmp/uploads"

    def test_download_to_trailing_slash(self):
        """测试下载目录路径末尾斜杠被移除。"""
        with patch("graphedu.common.config.modules.datasource.oss.logger") as mock_logger:
            config = OssConfig(download_to="/tmp/downloads/")

            assert config.download_to == "/tmp/downloads"

    def test_path_validator_both_slashes(self):
        """测试两个路径都有末尾斜杠。"""
        with patch("graphedu.common.config.modules.datasource.oss.logger") as mock_logger:
            config = OssConfig(
                upload_from="/tmp/graphedu/",
                download_to="/tmp/graphedu/"
            )

            assert config.upload_from == "/tmp/graphedu"
            assert config.download_to == "/tmp/graphedu"

    def test_path_without_trailing_slash(self):
        """测试没有末尾斜杠的路径（不变）。"""
        config = OssConfig(
            upload_from="/tmp/graphedu",
            download_to="/tmp/graphedu"
        )

        assert config.upload_from == "/tmp/graphedu"
        assert config.download_to == "/tmp/graphedu"

    def test_windows_style_path(self):
        """测试 Windows 风格路径。"""
        config = OssConfig(upload_from="C:\\ uploads")

        assert "uploads" in config.upload_from

    def test_relative_path(self):
        """测试相对路径。"""
        config = OssConfig(upload_from="./uploads")

        assert config.upload_from == "./uploads"

    def test_endpoint_type_validation(self):
        """测试端点类型验证。"""
        config = OssConfig(endpoint="http://oss.example.com:9000")
        assert isinstance(config.endpoint, AnyHttpUrl)

    def test_invalid_endpoint(self):
        """测试无效的端点。"""
        with pytest.raises(ValidationError):
            OssConfig(endpoint="not-a-url")

    def test_aws_s3_config(self):
        """测试 AWS S3 配置。"""
        config = OssConfig(
            provider="aws",
            endpoint="https://s3.amazonaws.com",
            access_key="AKIAIOSFODNN7EXAMPLE",
            secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            bucket="my-s3-bucket",
            use_ssl=True
        )

        assert config.provider == "aws"
        assert "s3.amazonaws.com" in str(config.endpoint)
        assert config.use_ssl is True

    def test_aliyun_oss_config(self):
        """测试阿里云 OSS 配置。"""
        config = OssConfig(
            provider="aliyun",
            endpoint="https://oss-cn-hangzhou.aliyuncs.com",
            bucket="my-oss-bucket"
        )

        assert config.provider == "aliyun"
        assert "aliyuncs.com" in str(config.endpoint)

    def test_tencent_cos_config(self):
        """测试腾讯云 COS 配置。"""
        config = OssConfig(
            provider="tencent",
            endpoint="https://cos.ap-guangzhou.myqcloud.com",
            bucket="my-cos-bucket"
        )

        assert config.provider == "tencent"

    def test_minio_config(self):
        """测试 MinIO 配置。"""
        config = OssConfig(
            provider="minio",
            endpoint="http://localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket="test-bucket",
            use_ssl=False
        )

        assert config.provider == "minio"
        assert config.use_ssl is False
        assert config.bucket == "test-bucket"

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = OssConfig(
            provider="minio",
            endpoint="http://localhost:9000",
            bucket="test",
            access_key="key",
            secret_key="secret"
        )

        config_dict = config.model_dump(mode="json")

        assert config_dict["provider"] == "minio"
        assert config_dict["bucket"] == "test"
        assert config_dict["access_key"] == "key"
        assert config_dict["secret_key"] == "secret"

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = OssConfig(
            provider="aws",
            bucket="my-bucket"
        )

        json_str = config.model_dump_json()

        assert "aws" in json_str
        assert "my-bucket" in json_str

    def test_cloudflare_r2_config(self):
        """测试 Cloudflare R2 配置。"""
        config = OssConfig(
            provider="cloudflare",
            endpoint="https://abc123.r2.cloudflarestorage.com",
            bucket="my-r2-bucket"
        )

        assert config.provider == "cloudflare"
        assert "r2" in str(config.endpoint)

    def test_custom_port_endpoint(self):
        """测试自定义端口的端点。"""
        config = OssConfig(endpoint="http://minio.example.com:9000")

        assert "9000" in str(config.endpoint)

    def test_ip_address_endpoint(self):
        """测试 IP 地址端点。"""
        config = OssConfig(endpoint="http://192.168.1.100:9000")

        assert "192.168.1.100" in str(config.endpoint)

    def test_bucket_name_validation(self):
        """测试存储桶名称（DNS 兼容）。"""
        valid_buckets = [
            "my-bucket",
            "my.bucket",
            "my-bucket-123",
            "bucket"
        ]

        for bucket in valid_buckets:
            config = OssConfig(bucket=bucket)
            assert config.bucket == bucket

    def test_special_characters_in_keys(self):
        """测试密钥中的特殊字符。"""
        config = OssConfig(
            access_key="access-key-with-dashes",
            secret_key="secret/key/with/slashes"
        )

        assert "dashes" in config.access_key
        assert "slashes" in config.secret_key
