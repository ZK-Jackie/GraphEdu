"""测试登录配置。"""

import pytest

from graphedu.common.config.modules.security.login import LoginConfig


class TestLoginConfig:
    """测试 LoginConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = LoginConfig()

        assert config.single_end is True
        assert config.captcha is True
        assert config.description is None

    def test_custom_values(self):
        """测试自定义值。"""
        config = LoginConfig(single_end=False, captcha=False)

        assert config.single_end is False
        assert config.captcha is False

    def test_single_end_true(self):
        """测试单点登录启用。"""
        config = LoginConfig(single_end=True)

        assert config.single_end is True

    def test_single_end_false(self):
        """测试单点登录禁用（允许多设备登录）。"""
        config = LoginConfig(single_end=False)

        assert config.single_end is False

    def test_captcha_true(self):
        """测试验证码启用。"""
        config = LoginConfig(captcha=True)

        assert config.captcha is True

    def test_captcha_false(self):
        """测试验证码禁用。"""
        config = LoginConfig(captcha=False)

        assert config.captcha is False

    def test_description_field(self):
        """测试 description 字段。"""
        desc = "Login security configuration"
        config = LoginConfig(description=desc)

        assert config.description == desc

    def test_description_field_optional(self):
        """测试 description 字段可选。"""
        config = LoginConfig()

        assert config.description is None

    def test_single_end_and_captcha_combinations(self):
        """测试 single_end 和 captcha 的组合。"""
        test_cases = [
            (True, True),
            (True, False),
            (False, True),
            (False, False),
        ]

        for single_end, captcha in test_cases:
            config = LoginConfig(single_end=single_end, captcha=captcha)
            assert config.single_end == single_end
            assert config.captcha == captcha

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = LoginConfig(single_end=True, captcha=True)

        config_dict = config.model_dump()

        assert config_dict["single_end"] is True
        assert config_dict["captcha"] is True

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = LoginConfig()

        json_str = config.model_dump_json()

        assert "single_end" in json_str
        assert "captcha" in json_str

    def test_bool_type_strict(self):
        """测试布尔类型严格性。"""
        # 应该只接受布尔值
        config = LoginConfig(single_end=True, captcha=False)

        assert isinstance(config.single_end, bool)
        assert isinstance(config.captcha, bool)
