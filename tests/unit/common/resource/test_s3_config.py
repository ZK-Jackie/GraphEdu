"""
S3 配置模块单元测试

测试 S3 服务提供商配置的各个组件：
- S3Provider 枚举
- S3ProviderConfig dataclass 及其方法
- PROVIDER_CONFIGS 预定义配置
- get_provider_config() 工厂函数
- ProviderTypes 类型定义

测试覆盖：
- 正常场景
- 边界条件
- 错误处理
- Mock 外部依赖（botocore, logging）
"""

from typing import get_args
from unittest.mock import MagicMock, patch

import pytest

from graphedu.common.resource.modules.database.s3_adaptation.s3_config import (
    PROVIDER_CONFIGS,
    ProviderTypes,
    S3Provider,
    S3ProviderConfig,
    get_provider_config,
)


# =============================================================================
# S3ProviderConfig 测试
# =============================================================================

class TestS3ProviderConfig:
    """测试 S3 服务商配置 dataclass"""

    def test_default_config_values(self):
        """测试默认配置的所有字段值"""
        config = S3ProviderConfig()

        assert config.addressing_style == "path"
        assert config.signature_version == "s3v4"
        assert config.url_template == "{endpoint}/{bucket}/{object}"
        assert config.force_path_style is True

    def test_custom_config_values(self):
        """测试自定义配置值"""
        config = S3ProviderConfig(
            addressing_style="virtual",
            signature_version="v2",
            url_template="{bucket}.{endpoint}/{object}",
            force_path_style=False,
        )

        assert config.addressing_style == "virtual"
        assert config.signature_version == "v2"
        assert config.url_template == "{bucket}.{endpoint}/{object}"
        assert config.force_path_style is False

    def test_config_is_frozen(self):
        """测试配置对象是不可变的"""
        config = S3ProviderConfig()

        with pytest.raises(AttributeError):
            config.addressing_style = "virtual"

    def test_config_equality(self):
        """测试配置对象相等性"""
        config1 = S3ProviderConfig()
        config2 = S3ProviderConfig()

        assert config1 == config2

    def test_config_with_different_values_not_equal(self):
        """测试不同配置不相等"""
        config1 = S3ProviderConfig(addressing_style="path")
        config2 = S3ProviderConfig(addressing_style="virtual")

        assert config1 != config2


class TestS3ProviderConfigGetBotoConfig:
    """测试 S3ProviderConfig.get_boto_config() 方法"""

    @patch("botocore.config.Config")
    def test_get_boto_config_with_default_settings(self, mock_config_class):
        """测试使用默认设置生成 boto 配置"""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        config = S3ProviderConfig()
        result = config.get_boto_config()

        # 验证 Config 被正确调用
        mock_config_class.assert_called_once_with(signature_version="s3v4")
        assert result == mock_config

    @patch("botocore.config.Config")
    def test_get_boto_config_with_virtual_addressing(self, mock_config_class):
        """测试 virtual 地址风格生成 boto 配置"""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        config = S3ProviderConfig(
            addressing_style="virtual",
            signature_version="s3v4"
        )
        result = config.get_boto_config()

        # 验证包含 s3 addressing_style 配置
        expected_config = {
            "signature_version": "s3v4",
            "s3": {"addressing_style": "virtual"}
        }
        mock_config_class.assert_called_once_with(**expected_config)
        assert result == mock_config

    @patch("botocore.config.Config")
    def test_get_boto_config_with_path_addressing(self, mock_config_class):
        """测试 path 地址风格生成 boto 配置"""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        config = S3ProviderConfig(
            addressing_style="path",
            signature_version="v2"
        )
        result = config.get_boto_config()

        # path 风格不包含 s3 配置
        mock_config_class.assert_called_once_with(signature_version="v2")
        assert result == mock_config

    @patch("botocore.config.Config")
    def test_get_boto_config_with_different_signature_versions(self, mock_config_class):
        """测试不同签名版本"""
        test_cases = ["s3v4", "v4", "v2"]

        for signature_version in test_cases:
            mock_config_class.reset_mock()
            config = S3ProviderConfig(signature_version=signature_version)
            config.get_boto_config()

            mock_config_class.assert_called_once()
            call_kwargs = mock_config_class.call_args[1]
            assert call_kwargs["signature_version"] == signature_version


class TestS3ProviderConfigBuildObjectUrl:
    """测试 S3ProviderConfig.build_object_url() 方法"""

    def test_build_url_with_http(self):
        """测试构建 HTTP URL"""
        config = S3ProviderConfig(
            url_template="{endpoint}/{bucket}/{object}"
        )

        url = config.build_object_url(
            endpoint="localhost:9000",
            bucket="test-bucket",
            object_name="test-file.txt",
            use_ssl=False
        )

        assert url == "http://localhost:9000/test-bucket/test-file.txt"

    def test_build_url_with_https(self):
        """测试构建 HTTPS URL"""
        config = S3ProviderConfig(
            url_template="{endpoint}/{bucket}/{object}"
        )

        url = config.build_object_url(
            endpoint="s3.amazonaws.com",
            bucket="my-bucket",
            object_name="my-file.txt",
            use_ssl=True
        )

        assert url == "https://s3.amazonaws.com/my-bucket/my-file.txt"

    def test_build_url_cleans_endpoint_protocol(self):
        """测试清理 endpoint 的协议前缀"""
        config = S3ProviderConfig(
            url_template="{endpoint}/{bucket}/{object}"
        )

        # 即使传入带 https:// 的 endpoint
        url = config.build_object_url(
            endpoint="https://s3.amazonaws.com/",
            bucket="my-bucket",
            object_name="my-file.txt",
            use_ssl=True
        )

        # 应该不包含重复的协议
        assert url == "https://s3.amazonaws.com/my-bucket/my-file.txt"

    def test_build_url_with_http_in_endpoint(self):
        """测试清理 endpoint 的 http 协议"""
        config = S3ProviderConfig(
            url_template="{endpoint}/{bucket}/{object}"
        )

        url = config.build_object_url(
            endpoint="http://localhost:9000",
            bucket="test-bucket",
            object_name="test.txt",
            use_ssl=False
        )

        assert url == "http://localhost:9000/test-bucket/test.txt"

    def test_build_url_virtual_hosted_style(self):
        """测试虚拟主机风格的 URL"""
        config = S3ProviderConfig(
            url_template="{bucket}.s3.amazonaws.com/{object}"
        )

        url = config.build_object_url(
            endpoint="s3.amazonaws.com",
            bucket="my-bucket",
            object_name="my-file.txt",
            use_ssl=True
        )

        assert url == "https://my-bucket.s3.amazonaws.com/my-file.txt"

    def test_build_url_with_nested_object_path(self):
        """测试构建带多级路径的对象 URL"""
        config = S3ProviderConfig(
            url_template="{endpoint}/{bucket}/{object}"
        )

        url = config.build_object_url(
            endpoint="s3.amazonaws.com",
            bucket="my-bucket",
            object_name="path/to/nested/file.txt",
            use_ssl=True
        )

        assert url == "https://s3.amazonaws.com/my-bucket/path/to/nested/file.txt"

    def test_build_url_with_special_characters(self):
        """测试构建包含特殊字符的对象 URL"""
        config = S3ProviderConfig(
            url_template="{endpoint}/{bucket}/{object}"
        )

        url = config.build_object_url(
            endpoint="s3.amazonaws.com",
            bucket="my-bucket",
            object_name="file with spaces & special-chars_@#.txt",
            use_ssl=True
        )

        assert url == "https://s3.amazonaws.com/my-bucket/file with spaces & special-chars_@#.txt"

    def test_build_url_trailing_slash_in_endpoint(self):
        """测试清理 endpoint 末尾斜杠"""
        config = S3ProviderConfig(
            url_template="{endpoint}/{bucket}/{object}"
        )

        url = config.build_object_url(
            endpoint="https://s3.amazonaws.com/",
            bucket="my-bucket",
            object_name="test.txt",
            use_ssl=True
        )

        assert url == "https://s3.amazonaws.com/my-bucket/test.txt"
        assert not url.endswith("my-bucket//test.txt")

    def test_build_url_aliyun_style(self):
        """测试阿里云 OSS 风格 URL"""
        config = S3ProviderConfig(
            url_template="{bucket}.{endpoint}/{object}"
        )

        url = config.build_object_url(
            endpoint="oss-cn-hangzhou.aliyuncs.com",
            bucket="my-bucket",
            object_name="test.txt",
            use_ssl=True
        )

        assert url == "https://my-bucket.oss-cn-hangzhou.aliyuncs.com/test.txt"


# =============================================================================
# S3Provider 测试
# =============================================================================

class TestS3Provider:
    """测试 S3 服务商枚举"""

    def test_all_provider_values(self):
        """测试所有服务商枚举值"""
        assert S3Provider.AWS.value == "aws"
        assert S3Provider.ALIYUN.value == "aliyun"
        assert S3Provider.MINIO.value == "minio"
        assert S3Provider.RUSTFS.value == "rustfs"
        assert S3Provider.CLOUDFLARE.value == "cloudflare"
        assert S3Provider.TENCENT.value == "tencent"
        assert S3Provider.GENERIC.value == "generic"

    def test_provider_is_string(self):
        """测试服务商枚举继承自 str"""
        provider = S3Provider.AWS

        assert isinstance(provider, str)
        assert str(provider) == "aws"

    def test_provider_comparison(self):
        """测试服务商枚举比较"""
        assert S3Provider.AWS == "aws"
        assert S3Provider.AWS == S3Provider.AWS
        assert S3Provider.AWS != S3Provider.ALIYUN

    def test_provider_from_string(self):
        """测试从字符串创建服务商枚举"""
        provider = S3Provider("aws")
        assert provider == S3Provider.AWS

    def test_provider_from_invalid_string_raises_error(self):
        """测试从无效字符串创建服务商枚举抛出错误"""
        with pytest.raises(ValueError, match="is not a valid S3Provider"):
            S3Provider("invalid_provider")

    def test_all_providers_are_unique(self):
        """测试所有服务商枚举值唯一"""
        values = [p.value for p in S3Provider]
        assert len(values) == len(set(values))


# =============================================================================
# PROVIDER_CONFIGS 测试
# =============================================================================

class TestProviderConfigs:
    """测试预定义服务商配置字典"""

    def test_aws_config_properties(self):
        """测试 AWS 配置属性"""
        config = PROVIDER_CONFIGS[S3Provider.AWS]

        assert config.addressing_style == "virtual"
        assert config.signature_version == "s3v4"
        assert config.url_template == "{bucket}.s3.amazonaws.com/{object}"
        assert config.force_path_style is False

    def test_aliyun_config_properties(self):
        """测试阿里云配置属性"""
        config = PROVIDER_CONFIGS[S3Provider.ALIYUN]

        assert config.addressing_style == "virtual"
        assert config.signature_version == "s3"
        assert config.url_template == "{bucket}.{endpoint}/{object}"
        assert config.force_path_style is False

    def test_minio_config_properties(self):
        """测试 MinIO 配置属性"""
        config = PROVIDER_CONFIGS[S3Provider.MINIO]

        assert config.addressing_style == "path"
        assert config.signature_version == "s3v4"
        assert config.url_template == "{endpoint}/{bucket}/{object}"
        assert config.force_path_style is True

    def test_rustfs_config_properties(self):
        """测试 RustFS 配置属性"""
        config = PROVIDER_CONFIGS[S3Provider.RUSTFS]

        assert config.addressing_style == "path"
        assert config.signature_version == "s3v4"
        assert config.url_template == "{endpoint}/{bucket}/{object}"
        assert config.force_path_style is True

    def test_tencent_config_properties(self):
        """测试腾讯云配置属性"""
        config = PROVIDER_CONFIGS[S3Provider.TENCENT]

        assert config.addressing_style == "virtual"
        assert config.signature_version == "s3v4"
        assert config.url_template == "{bucket}.{endpoint}/{object}"
        assert config.force_path_style is False

    def test_cloudflare_config_properties(self):
        """测试 Cloudflare 配置属性"""
        config = PROVIDER_CONFIGS[S3Provider.CLOUDFLARE]

        assert config.addressing_style == "virtual"
        assert config.signature_version == "s3v4"
        assert config.url_template == "{endpoint}/{bucket}/{object}"
        assert config.force_path_style is False

    def test_generic_config_properties(self):
        """测试通用配置属性"""
        config = PROVIDER_CONFIGS[S3Provider.GENERIC]

        assert config.addressing_style == "path"
        assert config.signature_version == "s3v4"
        assert config.url_template == "{endpoint}/{bucket}/{object}"
        assert config.force_path_style is True

    def test_all_providers_have_config(self):
        """测试所有服务商都有对应配置"""
        for provider in S3Provider:
            assert provider in PROVIDER_CONFIGS
            assert isinstance(PROVIDER_CONFIGS[provider], S3ProviderConfig)

    def test_configs_are_frozen(self):
        """测试所有预定义配置都是不可变的"""
        for provider in S3Provider:
            config = PROVIDER_CONFIGS[provider]

            with pytest.raises(AttributeError):
                config.addressing_style = "path"


# =============================================================================
# get_provider_config 测试
# =============================================================================

class TestGetProviderConfig:
    """测试 get_provider_config() 工厂函数"""

    def test_get_with_lowercase_string(self):
        """测试使用小写字符串获取配置"""
        config = get_provider_config("aws")

        assert isinstance(config, S3ProviderConfig)
        assert config.addressing_style == "virtual"
        assert config.url_template == "{bucket}.s3.amazonaws.com/{object}"

    def test_get_with_uppercase_string(self):
        """测试使用大写字符串获取配置（会转为小写）"""
        config = get_provider_config("AWS")

        assert isinstance(config, S3ProviderConfig)
        assert config.addressing_style == "virtual"

    def test_get_with_mixed_case_string(self):
        """测试使用混合大小写字符串获取配置"""
        config = get_provider_config("MiNiO")

        assert isinstance(config, S3ProviderConfig)
        assert config.addressing_style == "path"
        assert config.force_path_style is True

    def test_get_with_enum(self):
        """测试使用枚举获取配置"""
        config = get_provider_config(S3Provider.MINIO)

        assert isinstance(config, S3ProviderConfig)
        assert config.addressing_style == "path"
        assert config.force_path_style is True

    def test_get_with_unknown_provider_returns_generic(self):
        """测试使用未知服务商返回 GENERIC 配置"""
        config = get_provider_config("unknown_provider_xyz")

        assert isinstance(config, S3ProviderConfig)
        assert config.addressing_style == "path"
        assert config.force_path_style is True

    @patch("graphedu.common.resource.modules.database.s3_adaptation.s3_config.logger")
    def test_unknown_provider_logs_warning(self, mock_logger):
        """测试未知服务商记录警告日志"""
        get_provider_config("unknown_provider")

        mock_logger.warning.assert_called_once()
        args = mock_logger.warning.call_args[0]
        assert "unknown_provider" in args[0]

    def test_get_all_supported_providers(self):
        """测试所有支持的服务商字符串"""
        providers = ["aws", "aliyun", "minio", "rustfs", "cloudflare", "tencent", "generic"]

        for provider_str in providers:
            config = get_provider_config(provider_str)
            assert config is not None
            assert isinstance(config, S3ProviderConfig)

    def test_get_provider_returns_correct_config_type(self):
        """测试返回的配置类型正确"""
        # virtual 风格
        aws_config = get_provider_config("aws")
        assert aws_config.addressing_style == "virtual"

        # path 风格
        minio_config = get_provider_config("minio")
        assert minio_config.addressing_style == "path"

    def test_get_provider_is_case_insensitive(self):
        """测试服务商名称不区分大小写"""
        config1 = get_provider_config("aws")
        config2 = get_provider_config("AWS")
        config3 = get_provider_config("Aws")
        config4 = get_provider_config(S3Provider.AWS)

        # 所有方式应该返回相同的配置
        assert config1.addressing_style == config2.addressing_style
        assert config2.addressing_style == config3.addressing_style
        assert config3.addressing_style == config4.addressing_style


# =============================================================================
# ProviderTypes 测试
# =============================================================================

class TestProviderTypes:
    """测试 ProviderTypes 类型定义"""

    def test_provider_types_contains_all_providers(self):
        """测试 ProviderTypes 包含所有服务商"""
        args = get_args(ProviderTypes)
        expected_providers = ["aws", "aliyun", "minio", "rustfs", "cloudflare", "tencent", "generic"]

        for provider in expected_providers:
            assert provider in args

    def test_provider_types_is_literal(self):
        """测试 ProviderTypes 是 Literal 类型"""
        from typing import get_origin

        origin = get_origin(ProviderTypes)
        # Literal 类型的 origin 是 Literal
        assert origin.__name__ == "Literal"

    def test_provider_types_values_match_enum(self):
        """测试 ProviderTypes 值与 S3Provider 枚举匹配"""
        type_args = get_args(ProviderTypes)
        enum_values = [p.value for p in S3Provider]

        for enum_value in enum_values:
            assert enum_value in type_args


# =============================================================================
# 集成测试场景
# =============================================================================

class TestS3ConfigIntegration:
    """S3 配置集成测试场景"""

    def test_build_real_world_aws_url(self):
        """测试构建真实世界的 AWS S3 URL"""
        config = get_provider_config("aws")
        url = config.build_object_url(
            endpoint="s3.amazonaws.com",
            bucket="my-production-bucket",
            object_name="images/2024/photo.jpg",
            use_ssl=True
        )

        assert url == "https://my-production-bucket.s3.amazonaws.com/images/2024/photo.jpg"

    def test_build_real_world_minio_url(self):
        """测试构建真实世界的 MinIO URL"""
        config = get_provider_config("minio")
        url = config.build_object_url(
            endpoint="localhost:9000",
            bucket="test-bucket",
            object_name="documents/report.pdf",
            use_ssl=False
        )

        assert url == "http://localhost:9000/test-bucket/documents/report.pdf"

    def test_build_real_world_aliyun_oss_url(self):
        """测试构建真实世界的阿里云 OSS URL"""
        config = get_provider_config("aliyun")
        url = config.build_object_url(
            endpoint="oss-cn-hangzhou.aliyuncs.com",
            bucket="my-oss-bucket",
            object_name="app/data.json",
            use_ssl=True
        )

        assert url == "https://my-oss-bucket.oss-cn-hangzhou.aliyuncs.com/app/data.json"

    def test_build_real_world_tencent_cos_url(self):
        """测试构建真实世界的腾讯云 COS URL"""
        config = get_provider_config("tencent")
        url = config.build_object_url(
            endpoint="cos.ap-guangzhou.myqcloud.com",
            bucket="my-cos-bucket",
            object_name="videos/sample.mp4",
            use_ssl=True
        )

        assert url == "https://my-cos-bucket.cos.ap-guangzhou.myqcloud.com/videos/sample.mp4"

    @patch("botocore.config.Config")
    def test_get_boto_config_for_all_providers(self, mock_config_class):
        """测试所有服务商的 boto 配置生成"""
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        for provider in S3Provider:
            mock_config_class.reset_mock()
            config = PROVIDER_CONFIGS[provider]
            boto_config = config.get_boto_config()

            assert boto_config is not None
            mock_config_class.assert_called_once()

    def test_unknown_provider_fallback_to_generic(self):
        """测试未知服务商降级到 GENERIC 配置的完整流程"""
        # 获取未知服务商配置
        config = get_provider_config("unknown_s3_provider")

        # 验证是 GENERIC 配置
        assert config.addressing_style == "path"
        assert config.force_path_style is True

        # 验证可以正常使用
        url = config.build_object_url(
            endpoint="custom-endpoint.com",
            bucket="custom-bucket",
            object_name="file.txt",
            use_ssl=True
        )

        assert url == "https://custom-endpoint.com/custom-bucket/file.txt"
