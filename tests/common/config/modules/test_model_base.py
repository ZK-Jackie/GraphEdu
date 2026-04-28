"""测试 AI 模型配置聚合类。"""

import pytest

from graphedu.common.config.modules.model import (
    EmbeddingsConfig,
    LLMConfig,
    ModelConfig,
)


class TestModelConfig:
    """测试 ModelConfig 配置聚合类。"""

    def test_default_values(self):
        """测试默认值。"""
        config = ModelConfig()

        # 验证所有模型配置都有默认值
        assert isinstance(config.chat, LLMConfig)
        assert isinstance(config.think, LLMConfig)
        assert isinstance(config.long, LLMConfig)
        assert isinstance(config.embeddings, EmbeddingsConfig)

    def test_chat_config_defaults(self):
        """测试聊天模型默认配置。"""
        config = ModelConfig()

        assert config.chat.name == "glm-5-flash"
        assert config.chat.api_key == ""
        assert config.chat.api_base == "https://open.bigmodel.cn/api/paas/v4"
        assert config.chat.temperature == 0.7
        assert config.chat.max_tokens == 4096
        assert config.chat.top_p == 0.9
        assert config.chat.concur_limit == 2

    def test_think_config_defaults(self):
        """测试思考模型默认配置。"""
        config = ModelConfig()

        assert config.think.name == "glm-5-flash"
        assert config.think.temperature == 0.7

    def test_long_config_defaults(self):
        """测试长文本模型默认配置。"""
        config = ModelConfig()

        assert config.long.name == "glm-5-flash"
        assert config.long.max_tokens == 4096

    def test_embeddings_config_defaults(self):
        """测试嵌入模型默认配置。"""
        config = ModelConfig()

        assert config.embeddings.name == "embedding-2"
        assert config.embeddings.api_key == ""
        assert config.embeddings.api_base == "https://open.bigmodel.cn/api/paas/v4"
        assert config.embeddings.concur_limit == 1
        assert config.embeddings.dimensions == 2048
        assert config.embeddings.max_tokens == 4095
        assert config.embeddings.batch_size == 16
        assert config.embeddings.batch_max_tokens == 8000

    def test_custom_chat_config(self):
        """测试自定义聊天模型配置。"""
        custom_chat = LLMConfig(
            name="gpt-4",
            api_key="sk-test",
            api_base="https://api.openai.com/v1",
            temperature=0.5,
            max_tokens=8192
        )
        config = ModelConfig(chat=custom_chat)

        assert config.chat.name == "gpt-4"
        assert config.chat.api_base == "https://api.openai.com/v1"
        assert config.chat.temperature == 0.5

    def test_custom_think_config(self):
        """测试自定义思考模型配置。"""
        custom_think = LLMConfig(
            name="gpt-4-turbo",
            temperature=0.2
        )
        config = ModelConfig(think=custom_think)

        assert config.think.name == "gpt-4-turbo"
        assert config.think.temperature == 0.2

    def test_custom_long_config(self):
        """测试自定义长文本模型配置。"""
        custom_long = LLMConfig(
            name="claude-3-opus-200k",
            max_tokens=4096
        )
        config = ModelConfig(long=custom_long)

        assert config.long.name == "claude-3-opus-200k"
        assert config.long.max_tokens == 4096

    def test_custom_embeddings_config(self):
        """测试自定义嵌入模型配置。"""
        custom_embeddings = EmbeddingsConfig(
            name="bge-m3",
            dimensions=1024,
            max_tokens=8192
        )
        config = ModelConfig(embeddings=custom_embeddings)

        assert config.embeddings.name == "bge-m3"
        assert config.embeddings.dimensions == 1024

    def test_different_models_for_different_purposes(self):
        """测试不同用途使用不同模型。"""
        config = ModelConfig(
            chat=LLMConfig(name="gpt-4"),
            think=LLMConfig(name="gpt-4-turbo"),
            long=LLMConfig(name="claude-3-opus-200k"),
            embeddings=EmbeddingsConfig(name="bge-m3")
        )

        assert config.chat.name == "gpt-4"
        assert config.think.name == "gpt-4-turbo"
        assert config.long.name == "claude-3-opus-200k"
        assert config.embeddings.name == "bge-m3"

    def test_config_serialization(self):
        """测试配置序列化。"""
        config = ModelConfig()

        config_dict = config.model_dump()

        assert "chat" in config_dict
        assert "think" in config_dict
        assert "long" in config_dict
        assert "embeddings" in config_dict

    def test_config_json(self):
        """测试 JSON 序列化。"""
        config = ModelConfig()

        json_str = config.model_dump_json()

        assert "chat" in json_str
        assert "embeddings" in json_str

    def test_llm_config_validation_temperature_bounds(self):
        """测试 LLM 温度参数边界验证。"""
        from pydantic import ValidationError

        # 有效范围 0.0-2.0
        ModelConfig(chat=LLMConfig(temperature=0.0))
        ModelConfig(chat=LLMConfig(temperature=1.0))
        ModelConfig(chat=LLMConfig(temperature=2.0))

        # 超出范围应失败
        with pytest.raises(ValidationError):
            ModelConfig(chat=LLMConfig(temperature=-0.1))

        with pytest.raises(ValidationError):
            ModelConfig(chat=LLMConfig(temperature=2.1))

    def test_llm_config_validation_top_p_bounds(self):
        """测试 LLM top_p 参数边界验证。"""
        from pydantic import ValidationError

        # 有效范围 0.0-1.0
        ModelConfig(chat=LLMConfig(top_p=0.0))
        ModelConfig(chat=LLMConfig(top_p=0.5))
        ModelConfig(chat=LLMConfig(top_p=1.0))

        # 超出范围应失败
        with pytest.raises(ValidationError):
            ModelConfig(chat=LLMConfig(top_p=-0.1))

        with pytest.raises(ValidationError):
            ModelConfig(chat=LLMConfig(top_p=1.1))

    def test_llm_config_validation_positive_values(self):
        """测试 LLM 正数值验证。"""
        from pydantic import ValidationError

        # 正数应有效
        ModelConfig(
            chat=LLMConfig(
                max_tokens=100,
                concur_limit=1
            )
        )

        # 零应失败
        with pytest.raises(ValidationError):
            ModelConfig(chat=LLMConfig(max_tokens=0))

        with pytest.raises(ValidationError):
            ModelConfig(chat=LLMConfig(concur_limit=0))

    def test_embeddings_config_validation_positive_values(self):
        """测试嵌入模型正数值验证。"""
        from pydantic import ValidationError

        # 正数应有效
        ModelConfig(
            embeddings=EmbeddingsConfig(
                dimensions=100,
                concur_limit=1,
                max_tokens=100,
                batch_size=1,
                batch_max_tokens=100
            )
        )

        # 零应失败
        with pytest.raises(ValidationError):
            ModelConfig(embeddings=EmbeddingsConfig(dimensions=0))

        with pytest.raises(ValidationError):
            ModelConfig(embeddings=EmbeddingsConfig(concur_limit=0))

    def test_all_models_use_same_api_provider(self):
        """测试所有模型使用同一 API 提供商（智谱）。"""
        config = ModelConfig()

        # 所有模型默认使用智谱 API
        assert "bigmodel.cn" in config.chat.api_base
        assert "bigmodel.cn" in config.think.api_base
        assert "bigmodel.cn" in config.long.api_base
        assert "bigmodel.cn" in config.embeddings.api_base

    def test_models_with_different_api_keys(self):
        """测试不同模型使用不同 API 密钥。"""
        config = ModelConfig(
            chat=LLMConfig(api_key="key-chat"),
            think=LLMConfig(api_key="key-think"),
            long=LLMConfig(api_key="key-long"),
            embeddings=EmbeddingsConfig(api_key="key-embeddings")
        )

        assert config.chat.api_key == "key-chat"
        assert config.think.api_key == "key-think"
        assert config.long.api_key == "key-long"
        assert config.embeddings.api_key == "key-embeddings"
