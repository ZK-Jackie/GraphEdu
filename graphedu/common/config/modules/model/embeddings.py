"""Embeddings 模型配置。"""

from pydantic import BaseModel, Field


class EmbeddingsConfig(BaseModel):
    """文本嵌入模型配置。"""

    description: str | None = Field(default=None, description="模型描述信息（仅用于文档说明）")

    name: str = Field(default="embedding-2", description="嵌入模型名称（如 bge-m3、text-embedding-ada-002 等）")

    api_key: str = Field(default="", description="嵌入服务提供商的 API 密钥（敏感信息）")

    api_base: str = Field(default="https://open.bigmodel.cn/api/paas/v4", description="嵌入服务的 API 基础 URL")

    concur_limit: int = Field(default=1, gt=0, description="并发限制，每秒最大请求数")

    dimensions: int = Field(default=2048, gt=0, description="嵌入向量的维度数")

    max_tokens: int = Field(default=4095, gt=0, description="单次文本处理的最大 token 数")

    batch_size: int = Field(default=16, gt=0, description="单次批量处理的最大文本数量")

    batch_max_tokens: int = Field(default=8000, gt=0, description="单次批量处理的最大 token 总数")

    def get_lc_attr(self, *, lc_attr: dict | None = None) -> dict:
        """获取 LangChain 兼容的属性。"""
        lc_attr = lc_attr or {}
        lc_attr.update(
            {
                "model": self.name,
                "api_key": self.api_key,
                "base_url": self.api_base,
                "dimensions": self.dimensions,
            }
        )
        return lc_attr
