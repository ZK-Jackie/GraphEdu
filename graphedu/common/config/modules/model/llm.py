"""LLM 模型配置。"""

from typing import Literal

from pydantic import BaseModel, Field

_KeyOfChatOpenAI = Literal[
    "model_name", "api_key", "base_url", "temperature", "max_tokens", "top_p", "rate_limiter", "extra_body"
]


class _ZaiThinkingConfig(BaseModel):
    """Zai 模型的思考配置参数。"""

    type: Literal["enabled", "disabled"] = Field(default="disabled", description="思考功能开关")
    clear_thinking: bool = Field(default=True, description="是否在回答时忽略思考内容")


class _ZaiResponseFormatConfig(BaseModel):
    type: Literal["text", "json_object"] = Field(
        default="text", description="回答时的响应格式，一般在 invoke 方法调用时以函数参数形式传入"
    )


class ZaiConfigurable(BaseModel):
    """Zai 模型的额外请求体参数。"""

    thinking: _ZaiThinkingConfig = Field(default_factory=_ZaiThinkingConfig, description="思考配置参数")
    user_id: str | None = Field(
        default=None, description="用户 ID，用于 Zai 模型的个性化响应，一般情况下由请求时传入，不在配置中配置"
    )
    request_id: str | None = Field(
        default=None, description="请求 ID，若不提供则 Zai 会自动生成 UUID，一般情况下由请求时传入，不在配置中配置"
    )
    # response_format: _ZaiResponseFormatConfig = Field(
    #     default_factory=_ZaiResponseFormatConfig, description="响应格式配置参数"
    # )


class LLMConfig(BaseModel):
    """大语言模型配置。"""

    description: str | None = Field(default=None, description="模型描述信息（仅用于文档说明）")
    name: str = Field(default="glm-5-flash", description="LLM 模型名称（如 glm-4-flash、gpt-4 等）")
    api_key: str = Field(default="", description="LLM 服务提供商的 API 密钥（敏感信息）")
    api_base: str = Field(default="https://open.bigmodel.cn/api/paas/v4", description="LLM 服务的 API 基础 URL")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="采样温度，控制生成文本的随机性（0.0-2.0，越低越确定）"
    )
    max_tokens: int = Field(default=4096, gt=0, description="单次生成的最大令牌数")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p 采样参数，控制生成文本的多样性（0.0-1.0）")
    concur_limit: float = Field(
        default=2,
        gt=0,
        description="并发限制，每秒最大请求数，可参考 https://bigmodel.cn/usercenter/proj-mgmt/rate-limits",
    )
    extra_body: ZaiConfigurable = Field(
        default_factory=ZaiConfigurable, description="额外的请求体参数，直接传递给 LLM API"
    )

    def get_lc_attr(self, *, lc_attr: dict | None = None) -> dict:
        """获取 LangChain 兼容的属性。"""
        from langchain_core.rate_limiters import InMemoryRateLimiter

        lc_attr = lc_attr or {}
        lc_attr.update(
            {
                "model_name": self.name,
                "api_key": self.api_key,
                "base_url": self.api_base,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "rate_limiter": InMemoryRateLimiter(requests_per_second=self.concur_limit),
                "extra_body": self.extra_body.model_dump(),
            }
        )
        return lc_attr
