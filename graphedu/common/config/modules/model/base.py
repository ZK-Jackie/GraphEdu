"""AI 模型配置聚合（对应 model 命名空间）。"""

from pydantic import BaseModel, Field

from .embeddings import EmbeddingsConfig
from .llm import LLMConfig


class ModelConfig(BaseModel):
    """AI 模型配置聚合（Spring Boot 风格）。"""

    chat: LLMConfig = Field(default_factory=LLMConfig)
    """聊天 LLM 配置"""

    think: LLMConfig = Field(default_factory=LLMConfig)
    """思考 LLM 配置"""

    long: LLMConfig = Field(default_factory=LLMConfig)
    """长文本 LLM 配置"""

    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    """嵌入模型配置"""
