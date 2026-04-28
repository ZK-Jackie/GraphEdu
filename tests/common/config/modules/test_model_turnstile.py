"""测试 Cloudflare Turnstile 验证码配置。"""

import pytest
from pydantic import ValidationError


class TestTurnstileConfig:
    """测试 TurnstileConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig()

        assert config.secret == ""
        assert config.verify_url == "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        assert config.timeout == 10.0

    def test_custom_secret(self):
        """测试自定义密钥。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(secret="1x0000000000000000000000000000000AA")

        assert config.secret == "1x0000000000000000000000000000000AA"

    def test_custom_verify_url(self):
        """测试自定义验证 URL。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(
            verify_url="https://challenges.cloudflare.com/turnstile/v0/siteverify"
        )

        assert config.verify_url == "https://challenges.cloudflare.com/turnstile/v0/siteverify"

    def test_custom_timeout(self):
        """测试自定义超时时间。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(timeout=30.0)

        assert config.timeout == 30.0

    def test_timeout_validation_positive(self):
        """测试超时时间验证（正数）。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(timeout=0.1)

        assert config.timeout == 0.1

    def test_timeout_validation_zero(self):
        """测试超时时间验证（零应失败）。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        with pytest.raises(ValidationError):
            TurnstileConfig(timeout=0)

    def test_timeout_validation_negative(self):
        """测试超时时间验证（负数应失败）。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        with pytest.raises(ValidationError):
            TurnstileConfig(timeout=-10.0)

    def test_timeout_fractional(self):
        """测试小数超时时间。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(timeout=5.5)

        assert config.timeout == 5.5

    def test_secret_empty_string(self):
        """测试空密钥（有效，虽然不推荐）。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(secret="")

        assert config.secret == ""

    def test_secret_with_special_chars(self):
        """测试包含特殊字符的密钥。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        secret = "0xABCDEF-1234567890abcdef"
        config = TurnstileConfig(secret=secret)

        assert config.secret == secret

    def test_verify_url_default_value(self):
        """测试默认验证 URL 是官方端点。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig()

        assert "challenges.cloudflare.com" in config.verify_url
        assert "siteverify" in config.verify_url

    def test_config_serialization(self):
        """测试配置序列化。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(
            secret="test-secret",
            timeout=15.0
        )

        config_dict = config.model_dump()

        assert config_dict["secret"] == "test-secret"
        assert config_dict["timeout"] == 15.0

    def test_config_json(self):
        """测试 JSON 序列化。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(secret="test-secret")

        json_str = config.model_dump_json()

        assert "test-secret" in json_str

    def test_production_config(self):
        """测试生产环境配置示例。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(
            secret="1xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
            timeout=10.0
        )

        assert config.secret.startswith("1x")
        assert config.timeout == 10.0

    def test_timeout_very_short(self):
        """测试非常短的超时时间。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(timeout=0.5)

        assert config.timeout == 0.5

    def test_timeout_very_long(self):
        """测试很长的超时时间。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(timeout=120.0)

        assert config.timeout == 120.0

    def test_description_field(self):
        """测试 description 字段（仅文档用途）。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(
            secret="test",
            description="Production Turnstile configuration"
        )

        assert config.description == "Production Turnstile configuration"

    def test_description_none(self):
        """测试 description 默认为 None。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(secret="test")

        assert config.description is None

    def test_config_with_all_fields(self):
        """测试配置所有字段。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        config = TurnstileConfig(
            description="Test configuration",
            secret="test-secret-key",
            verify_url="https://challenges.cloudflare.com/turnstile/v0/siteverify",
            timeout=20.0
        )

        config_dict = config.model_dump()

        assert config_dict["description"] == "Test configuration"
        assert config_dict["secret"] == "test-secret-key"
        assert config_dict["verify_url"] == "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        assert config_dict["timeout"] == 20.0
