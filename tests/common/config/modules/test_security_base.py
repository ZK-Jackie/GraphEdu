"""测试安全配置聚合类。"""

import pytest

from graphedu.common.config.modules.security import (
    LoginConfig,
    SecurityConfig,
    TokenConfig,
)
from graphedu.common.config.modules.model import TurnstileConfig


class TestSecurityConfig:
    """测试 SecurityConfig 配置聚合类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = SecurityConfig()

        # 验证所有安全配置都有默认值
        assert isinstance(config.login, LoginConfig)
        assert isinstance(config.token, TokenConfig)
        assert isinstance(config.turnstile, TurnstileConfig)

    def test_login_config_defaults(self):
        """测试登录配置默认值。"""
        config = SecurityConfig()

        assert config.login.single_end is True
        assert config.login.captcha is True

    def test_token_config_defaults(self):
        """测试 Token 配置默认值。"""
        config = SecurityConfig()

        assert config.token.header == "authorization"
        assert config.token.secret == "secret"
        assert config.token.algorithm == "HS512"
        assert config.token.expire == 120

    def test_turnstile_config_defaults(self):
        """测试 Turnstile 配置默认值。"""
        config = SecurityConfig()

        assert config.turnstile.secret == ""
        assert config.turnstile.verify_url == "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        assert config.turnstile.timeout == 10.0

    def test_custom_login_config(self):
        """测试自定义登录配置。"""
        custom_login = LoginConfig(single_end=False, captcha=False)
        config = SecurityConfig(login=custom_login)

        assert config.login.single_end is False
        assert config.login.captcha is False

    def test_custom_token_config(self):
        """测试自定义 Token 配置。"""
        custom_token = TokenConfig(
            header="x-auth-token",
            secret="my-secret-key",
            algorithm="HS256",
            expire=60
        )
        config = SecurityConfig(token=custom_token)

        assert config.token.header == "x-auth-token"
        assert config.token.secret == "my-secret-key"
        assert config.token.algorithm == "HS256"
        assert config.token.expire == 60

    def test_custom_turnstile_config(self):
        """测试自定义 Turnstile 配置。"""
        from graphedu.common.config.modules.model import TurnstileConfig

        custom_turnstile = TurnstileConfig(
            secret="0xabc123",
            timeout=30.0
        )
        config = SecurityConfig(turnstile=custom_turnstile)

        assert config.turnstile.secret == "0xabc123"
        assert config.turnstile.timeout == 30.0

    def test_all_security_components_present(self):
        """测试所有安全组件都存在。"""
        config = SecurityConfig()

        # 验证配置包含所有安全相关组件
        assert hasattr(config, "login")
        assert hasattr(config, "token")
        assert hasattr(config, "turnstile")

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = SecurityConfig()

        config_dict = config.model_dump()

        assert "login" in config_dict
        assert "token" in config_dict
        assert "turnstile" in config_dict

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = SecurityConfig()

        json_str = config.model_dump_json()

        assert "login" in json_str
        assert "token" in json_str
        assert "turnstile" in json_str

    def test_login_single_end_true(self):
        """测试单点登录启用。"""
        config = SecurityConfig(login=LoginConfig(single_end=True))

        assert config.login.single_end is True

    def test_login_single_end_false(self):
        """测试单点登录禁用（允许多处登录）。"""
        config = SecurityConfig(login=LoginConfig(single_end=False))

        assert config.login.single_end is False

    def test_login_captcha_enabled(self):
        """测试验证码启用。"""
        config = SecurityConfig(login=LoginConfig(captcha=True))

        assert config.login.captcha is True

    def test_login_captcha_disabled(self):
        """测试验证码禁用。"""
        config = SecurityConfig(login=LoginConfig(captcha=False))

        assert config.login.captcha is False

    def test_token_expire_validation(self):
        """测试 Token 过期时间验证。"""
        from pydantic import ValidationError

        # 正数应该有效
        config = SecurityConfig(token=TokenConfig(expire=30))
        assert config.token.expire == 30

        # 零应该失败
        with pytest.raises(ValidationError):
            SecurityConfig(token=TokenConfig(expire=0))

    def test_security_config_with_realistic_values(self):
        """测试使用真实值的配置。"""
        config = SecurityConfig(
            login=LoginConfig(
                single_end=True,
                captcha=True
            ),
            token=TokenConfig(
                header="authorization",
                secret="production-secret-key-change-me",
                algorithm="HS512",
                expire=120
            ),
            turnstile=TurnstileConfig(
                secret="1x0000000000000000000000000000000AA",
                timeout=10.0
            )
        )

        assert config.login.single_end is True
        assert config.token.secret == "production-secret-key-change-me"
        assert config.turnstile.secret == "1x0000000000000000000000000000000AA"
