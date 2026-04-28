"""测试 Embeddings 模型配置。"""

from unittest.mock import patch

import pytest
from pydantic import ValidationError


class TestEmbeddingsConfig:
    """测试 EmbeddingsConfig 配置类。"""

    def test_default_values(self):
        """测试默认值。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig()

        assert config.name == "embedding-2"
        assert config.api_key == ""
        assert config.api_base == "https://open.bigmodel.cn/api/paas/v4"
        assert config.concur_limit == 1
        assert config.dimensions == 2048
        assert config.max_tokens == 4095
        assert config.batch_size == 16
        assert config.batch_max_tokens == 8000

    def test_custom_name(self):
        """测试自定义模型名称。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(name="bge-m3")

        assert config.name == "bge-m3"

    def test_custom_api_key(self):
        """测试自定义 API 密钥。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(api_key="sk-test-key")

        assert config.api_key == "sk-test-key"

    def test_custom_api_base(self):
        """测试自定义 API 基础 URL。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(api_base="https://api.openai.com/v1")

        assert config.api_base == "https://api.openai.com/v1"

    def test_custom_concur_limit(self):
        """测试自定义并发限制。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(concur_limit=5)

        assert config.concur_limit == 5

    def test_custom_dimensions(self):
        """测试自定义向量维度。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(dimensions=1536)

        assert config.dimensions == 1536

    def test_custom_max_tokens(self):
        """测试自定义最大 token 数。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(max_tokens=8192)

        assert config.max_tokens == 8192

    def test_custom_batch_size(self):
        """测试自定义批处理大小。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(batch_size=32)

        assert config.batch_size == 32

    def test_custom_batch_max_tokens(self):
        """测试自定义批处理最大 token 数。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(batch_max_tokens=16000)

        assert config.batch_max_tokens == 16000

    def test_concur_limit_validation_positive(self):
        """测试并发限制验证（正数）。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(concur_limit=1)

        assert config.concur_limit == 1

    def test_concur_limit_validation_zero(self):
        """测试并发限制验证（零应失败）。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        with pytest.raises(ValidationError):
            EmbeddingsConfig(concur_limit=0)

    def test_concur_limit_validation_negative(self):
        """测试并发限制验证（负数应失败）。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        with pytest.raises(ValidationError):
            EmbeddingsConfig(concur_limit=-1)

    def test_dimensions_validation_positive(self):
        """测试维度验证（正数）。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(dimensions=100)

        assert config.dimensions == 100

    def test_dimensions_validation_zero(self):
        """测试维度验证（零应失败）。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        with pytest.raises(ValidationError):
            EmbeddingsConfig(dimensions=0)

    def test_max_tokens_validation_positive(self):
        """测试最大 token 数验证（正数）。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(max_tokens=100)

        assert config.max_tokens == 100

    def test_max_tokens_validation_zero(self):
        """测试最大 token 数验证（零应失败）。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        with pytest.raises(ValidationError):
            EmbeddingsConfig(max_tokens=0)

    def test_batch_size_validation_positive(self):
        """测试批处理大小验证（正数）。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(batch_size=1)

        assert config.batch_size == 1

    def test_batch_size_validation_zero(self):
        """测试批处理大小验证（零应失败）。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        with pytest.raises(ValidationError):
            EmbeddingsConfig(batch_size=0)

    def test_batch_max_tokens_validation_positive(self):
        """测试批处理最大 token 数验证（正数）。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(batch_max_tokens=100)

        assert config.batch_max_tokens == 100

    def test_batch_max_tokens_validation_zero(self):
        """测试批处理最大 token 数验证（零应失败）。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        with pytest.raises(ValidationError):
            EmbeddingsConfig(batch_max_tokens=0)

    def test_get_lc_attr_default(self):
        """测试获取 LangChain 兼容属性（默认）。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig()

        lc_attr = config.get_lc_attr()

        assert lc_attr["model"] == "embedding-2"
        assert lc_attr["api_key"] == ""
        assert lc_attr["base_url"] == "https://open.bigmodel.cn/api/paas/v4"
        assert lc_attr["dimensions"] == 2048

    def test_get_lc_attr_custom(self):
        """测试获取自定义 LangChain 兼容属性。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(
            name="bge-m3",
            api_key="sk-test",
            api_base="https://api.example.com",
            dimensions=1024
        )

        lc_attr = config.get_lc_attr()

        assert lc_attr["model"] == "bge-m3"
        assert lc_attr["api_key"] == "sk-test"
        assert lc_attr["base_url"] == "https://api.example.com"
        assert lc_attr["dimensions"] == 1024

    def test_get_lc_attr_merge(self):
        """测试合并现有属性。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(name="embedding-2")

        existing_attr = {"custom_key": "custom_value"}
        lc_attr = config.get_lc_attr(lc_attr=existing_attr)

        # 应该包含原有属性
        assert lc_attr["custom_key"] == "custom_value"
        # 应该包含新属性
        assert lc_attr["model"] == "embedding-2"

    def test_get_lc_attr_override(self):
        """测试属性覆盖。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(name="new-model")

        existing_attr = {"model": "old-model", "dimensions": 100}
        lc_attr = config.get_lc_attr(lc_attr=existing_attr)

        # 新值应覆盖旧值
        assert lc_attr["model"] == "new-model"
        assert lc_attr["dimensions"] == 2048

    def test_config_serialization(self):
        """测试配置序列化。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(
            name="bge-m3",
            api_key="sk-test",
            dimensions=1024
        )

        config_dict = config.model_dump()

        assert config_dict["name"] == "bge-m3"
        assert config_dict["api_key"] == "sk-test"
        assert config_dict["dimensions"] == 1024

    def test_config_json(self):
        """测试 JSON 序列化。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        config = EmbeddingsConfig(name="test-model")

        json_str = config.model_dump_json()

        assert "test-model" in json_str

    def test_common_embedding_models(self):
        """测试常见嵌入模型。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        models = [
            "text-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large",
            "bge-m3",
            "bge-large-zh-v1.5",
            "embedding-2"
        ]

        for model in models:
            config = EmbeddingsConfig(name=model)
            assert config.name == model

    def test_different_dimensions_for_models(self):
        """测试不同模型的维度。"""
        from graphedu.common.config.modules.model import EmbeddingsConfig

        # OpenAI ada-002
        config = EmbeddingsConfig(name="text-embedding-ada-002", dimensions=1536)
        assert config.dimensions == 1536

        # BGE-M3
        config = EmbeddingsConfig(name="bge-m3", dimensions=1024)
        assert config.dimensions == 1024

        # 智谱 embedding-2
        config = EmbeddingsConfig(name="embedding-2", dimensions=2048)
        assert config.dimensions == 2048
