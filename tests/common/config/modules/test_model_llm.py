"""测试 LLM 模型配置。"""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from graphedu.common.config.modules.model.llm import LLMConfig, ZaiConfigurable, _ZaiThinkingConfig


class TestZaiThinkingConfig:
    """测试 _ZaiThinkingConfig 思考配置。"""

    def test_default_values(self):
        """测试默认值。"""
        config = _ZaiThinkingConfig()

        assert config.type == "disabled"
        assert config.clear_thinking is True

    def test_custom_values(self):
        """测试自定义值。"""
        config = _ZaiThinkingConfig(type="enabled", clear_thinking=False)

        assert config.type == "enabled"
        assert config.clear_thinking is False

    def test_type_enabled(self):
        """测试启用思考功能。"""
        config = _ZaiThinkingConfig(type="enabled")

        assert config.type == "enabled"

    def test_type_disabled(self):
        """测试禁用思考功能。"""
        config = _ZaiThinkingConfig(type="disabled")

        assert config.type == "disabled"

    def test_clear_thinking_true(self):
        """测试清除思考内容。"""
        config = _ZaiThinkingConfig(clear_thinking=True)

        assert config.clear_thinking is True

    def test_clear_thinking_false(self):
        """测试保留思考内容。"""
        config = _ZaiThinkingConfig(clear_thinking=False)

        assert config.clear_thinking is False


class TestZaiConfigurable:
    """测试 ZaiConfigurable 额外请求体参数。"""

    def test_default_values(self):
        """测试默认值。"""
        config = ZaiConfigurable()

        assert isinstance(config.thinking, _ZaiThinkingConfig)
        assert config.thinking.type == "disabled"
        assert config.thinking.clear_thinking is True

    def test_custom_thinking_config(self):
        """测试自定义思考配置。"""
        thinking = _ZaiThinkingConfig(type="enabled", clear_thinking=False)
        config = ZaiConfigurable(thinking=thinking)

        assert config.thinking.type == "enabled"
        assert config.thinking.clear_thinking is False

    def test_thinking_default_factory(self):
        """测试 thinking 默认工厂。"""
        config = ZaiConfigurable()

        # 验证使用默认工厂创建
        assert isinstance(config.thinking, _ZaiThinkingConfig)


class TestLLMConfig:
    """测试 LLMConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = LLMConfig()

        assert config.name == "glm-5-flash"
        assert config.api_key == ""
        assert config.api_base == "https://open.bigmodel.cn/api/paas/v4"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.top_p == 0.9
        assert config.concur_limit == 2.0
        assert config.description is None

    def test_custom_values(self):
        """测试自定义值。"""
        config = LLMConfig(
            name="gpt-4",
            api_key="test-key",
            api_base="https://api.openai.com/v1",
            temperature=0.5,
            max_tokens=8192,
            top_p=0.8,
            concur_limit=10.0,
        )

        assert config.name == "gpt-4"
        assert config.api_key == "test-key"
        assert config.api_base == "https://api.openai.com/v1"
        assert config.temperature == 0.5
        assert config.max_tokens == 8192
        assert config.top_p == 0.8
        assert config.concur_limit == 10.0

    def test_name_field(self):
        """测试 name 字段。"""
        config = LLMConfig(name="gpt-4-turbo")

        assert config.name == "gpt-4-turbo"

    def test_api_key_field(self):
        """测试 api_key 字段。"""
        key = "sk-1234567890"
        config = LLMConfig(api_key=key)

        assert config.api_key == key

    def test_api_base_field(self):
        """测试 api_base 字段。"""
        base = "https://api.openai.com/v1"
        config = LLMConfig(api_base=base)

        assert config.api_base == base

    def test_temperature_validation(self):
        """测试 temperature 验证（0.0-2.0）。"""
        # 有效值
        LLMConfig(temperature=0.0)
        LLMConfig(temperature=1.0)
        LLMConfig(temperature=2.0)

        # 无效值
        with pytest.raises(ValidationError):
            LLMConfig(temperature=-0.1)

        with pytest.raises(ValidationError):
            LLMConfig(temperature=2.1)

    def test_max_tokens_positive(self):
        """测试 max_tokens 正值。"""
        config = LLMConfig(max_tokens=16384)

        assert config.max_tokens == 16384

    def test_max_tokens_validation_zero(self):
        """测试 max_tokens 验证（零应失败）。"""
        with pytest.raises(ValidationError):
            LLMConfig(max_tokens=0)

    def test_max_tokens_validation_negative(self):
        """测试 max_tokens 验证（负数应失败）。"""
        with pytest.raises(ValidationError):
            LLMConfig(max_tokens=-100)

    def test_top_p_validation(self):
        """测试 top_p 验证（0.0-1.0）。"""
        # 有效值
        LLMConfig(top_p=0.0)
        LLMConfig(top_p=0.5)
        LLMConfig(top_p=1.0)

        # 无效值
        with pytest.raises(ValidationError):
            LLMConfig(top_p=-0.1)

        with pytest.raises(ValidationError):
            LLMConfig(top_p=1.1)

    def test_concur_limit_positive(self):
        """测试 concur_limit 正值。"""
        config = LLMConfig(concur_limit=5.0)

        assert config.concur_limit == 5.0

    def test_concur_limit_validation_zero(self):
        """测试 concur_limit 验证（零应失败）。"""
        with pytest.raises(ValidationError):
            LLMConfig(concur_limit=0)

    def test_concur_limit_validation_negative(self):
        """测试 concur_limit 验证（负数应失败）。"""
        with pytest.raises(ValidationError):
            LLMConfig(concur_limit=-1.0)

    def test_extra_body_default(self):
        """测试 extra_body 默认值。"""
        config = LLMConfig()

        assert isinstance(config.extra_body, ZaiConfigurable)
        assert config.extra_body.thinking.type == "disabled"

    def test_extra_body_custom(self):
        """测试自定义 extra_body。"""
        extra = ZaiConfigurable(thinking=_ZaiThinkingConfig(type="enabled"))
        config = LLMConfig(extra_body=extra)

        assert config.extra_body.thinking.type == "enabled"

    @patch("langchain_core.rate_limiters.InMemoryRateLimiter")
    def test_get_lc_attr_default(self, mock_rate_limiter):
        """测试 get_lc_attr 默认行为。"""
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance

        config = LLMConfig()
        lc_attr = config.get_lc_attr()

        # 验证返回字典
        assert isinstance(lc_attr, dict)

        # 验证基本字段（验证字段存在且值正确）
        assert lc_attr["model_name"] == config.name
        assert lc_attr["api_key"] == config.api_key
        assert lc_attr["base_url"] == config.api_base
        assert lc_attr["temperature"] == config.temperature
        assert lc_attr["max_tokens"] == config.max_tokens
        assert lc_attr["top_p"] == config.top_p
        assert "rate_limiter" in lc_attr
        assert isinstance(lc_attr["extra_body"], dict)

    @patch("langchain_core.rate_limiters.InMemoryRateLimiter")
    def test_get_lc_attr_with_custom_dict(self, mock_rate_limiter):
        """测试 get_lc_attr 传入自定义字典。"""
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance

        config = LLMConfig()
        custom_attr = {"custom_key": "custom_value"}
        lc_attr = config.get_lc_attr(lc_attr=custom_attr)

        # 验证合并了自定义属性
        assert lc_attr["custom_key"] == "custom_value"
        assert lc_attr["model_name"] == config.name

    @patch("langchain_core.rate_limiters.InMemoryRateLimiter")
    def test_get_lc_attr_rate_limiter(self, mock_rate_limiter):
        """测试 get_lc_attr 创建 rate limiter。"""
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance

        config = LLMConfig(concur_limit=5.0)
        lc_attr = config.get_lc_attr()

        # 验证创建 rate limiter
        mock_rate_limiter.assert_called_once_with(requests_per_second=5.0)
        assert "rate_limiter" in lc_attr

    @patch("langchain_core.rate_limiters.InMemoryRateLimiter")
    def test_get_lc_attr_extra_body_serialization(self, mock_rate_limiter):
        """测试 get_lc_attr 序列化 extra_body。"""
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance

        config = LLMConfig()
        lc_attr = config.get_lc_attr()

        # 验证 extra_body 被序列化为字典
        assert isinstance(lc_attr["extra_body"], dict)
        assert "thinking" in lc_attr["extra_body"]

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = LLMConfig()

        config_dict = config.model_dump()

        assert "name" in config_dict
        assert "api_key" in config_dict
        assert "api_base" in config_dict
        assert "temperature" in config_dict
        assert "max_tokens" in config_dict
        assert "top_p" in config_dict
        assert "concur_limit" in config_dict
        assert "extra_body" in config_dict

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = LLMConfig()

        json_str = config.model_dump_json()

        assert "glm-5-flash" in json_str
        assert "temperature" in json_str
        assert "max_tokens" in json_str

    def test_common_llm_providers(self):
        """测试常见 LLM 提供商配置。"""
        providers = [
            {
                "name": "gpt-4",
                "api_base": "https://api.openai.com/v1",
            },
            {
                "name": "glm-4-turbo",
                "api_base": "https://open.bigmodel.cn/api/paas/v4",
            },
            {
                "name": "claude-3-sonnet",
                "api_base": "https://api.anthropic.com/v1",
            },
        ]

        for provider in providers:
            config = LLMConfig(**provider)
            assert config.name == provider["name"]
            assert config.api_base == provider["api_base"]

    def test_temperature_impact(self):
        """测试 temperature 对输出的影响。"""
        # 低温度 - 更确定
        config_low = LLMConfig(temperature=0.1)
        assert config_low.temperature == 0.1

        # 高温度 - 更随机
        config_high = LLMConfig(temperature=1.5)
        assert config_high.temperature == 1.5

    def test_description_field(self):
        """测试 description 字段。"""
        desc = "Chat model for conversations"
        config = LLMConfig(description=desc)

        assert config.description == desc

    def test_description_field_optional(self):
        """测试 description 字段可选。"""
        config = LLMConfig()

        assert config.description is None
