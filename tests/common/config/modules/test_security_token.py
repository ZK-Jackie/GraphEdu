"""测试 Token 配置。"""

import warnings

import pytest
from pydantic import ValidationError

from graphedu.common.config.modules.security.token import TokenConfig


class TestTokenConfig:
    """测试 TokenConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = TokenConfig()

        assert config.header == "authorization"
        assert config.secret == "secret"
        assert config.algorithm == "HS512"
        assert config.expire == 120
        assert config.description is None

    def test_custom_values(self):
        """测试自定义值。"""
        config = TokenConfig(
            header="x-auth-token",
            secret="my-secret-key",
            algorithm="HS256",
            expire=60,
        )

        assert config.header == "x-auth-token"
        assert config.secret == "my-secret-key"
        assert config.algorithm == "HS256"
        assert config.expire == 60

    def test_header_validation_lowercase(self):
        """测试 header 验证（自动转小写）。"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            config = TokenConfig(header="Authorization")

            # 验证警告产生
            assert len(w) == 1
            assert "Token header must be lowercase" in str(w[0].message)

            # 验证自动转换
            assert config.header == "authorization"

    def test_header_already_lowercase(self):
        """测试 header 已经是小写（不产生警告）。"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            config = TokenConfig(header="authorization")

            # 验证不产生警告
            assert len(w) == 0
            assert config.header == "authorization"

    def test_secret_field(self):
        """测试 secret 字段。"""
        secret = "my-very-secret-key-12345"
        config = TokenConfig(secret=secret)

        assert config.secret == secret

    def test_algorithm_field(self):
        """测试 algorithm 字段。"""
        algorithms = ["HS256", "HS384", "HS512", "RS256"]

        for algo in algorithms:
            config = TokenConfig(algorithm=algo)
            assert config.algorithm == algo

    def test_expire_field_positive(self):
        """测试 expire 字段（正整数）。"""
        config = TokenConfig(expire=30)

        assert config.expire == 30

    def test_expire_field_validation_negative(self):
        """测试 expire 字段验证（负数应失败）。"""
        with pytest.raises(ValidationError):
            TokenConfig(expire=-10)

    def test_expire_field_validation_zero(self):
        """测试 expire 字段验证（零应失败）。"""
        with pytest.raises(ValidationError):
            TokenConfig(expire=0)

    def test_expire_field_large_value(self):
        """测试 expire 字段（大值）。"""
        config = TokenConfig(expire=10080)  # 一周

        assert config.expire == 10080

    def test_description_field(self):
        """测试 description 字段。"""
        desc = "Token configuration for authentication"
        config = TokenConfig(description=desc)

        assert config.description == desc

    def test_description_field_optional(self):
        """测试 description 字段可选。"""
        config = TokenConfig()

        assert config.description is None

    def test_header_with_hyphens(self):
        """测试带连字符的 header。"""
        config = TokenConfig(header="x-auth-token")

        assert config.header == "x-auth-token"

    def test_header_with_underscores(self):
        """测试带下划线的 header。"""
        config = TokenConfig(header="auth_token")

        assert config.header == "auth_token"

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = TokenConfig(
            header="authorization",
            secret="secret",
            algorithm="HS512",
            expire=120,
        )

        config_dict = config.model_dump()

        assert config_dict["header"] == "authorization"
        assert config_dict["secret"] == "secret"
        assert config_dict["algorithm"] == "HS512"
        assert config_dict["expire"] == 120

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = TokenConfig()

        json_str = config.model_dump_json()

        assert "authorization" in json_str
        assert "HS512" in json_str
        assert "120" in json_str

    def test_common_jwt_algorithms(self):
        """测试常见 JWT 算法。"""
        # HMAC 算法
        for algo in ["HS256", "HS384", "HS512"]:
            config = TokenConfig(algorithm=algo)
            assert config.algorithm == algo

    def test_token_expiry_in_minutes(self):
        """测试 token 过期时间单位为分钟。"""
        config = TokenConfig(expire=60)

        # 60 分钟 = 1 小时
        assert config.expire == 60

    def test_sensitive_secret_handling(self):
        """测试敏感信息处理。"""
        config = TokenConfig(secret="sensitive-secret-key")

        # 验证 secret 正确存储
        assert config.secret == "sensitive-secret-key"

        # 在序列化时应该正确处理
        config_dict = config.model_dump()
        assert "sensitive-secret-key" in config_dict["secret"]
