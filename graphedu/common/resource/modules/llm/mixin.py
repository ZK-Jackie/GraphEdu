"""LLM Mixin：LLMMixin。"""

from dependency_injector import containers, providers
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from graphedu.common.config.manager import get_config
from graphedu.common.config.modules.model import EmbeddingsConfig, LLMConfig


async def init_llm(config: LLMConfig):
    """初始化 LLM 实例"""
    yield ChatOpenAI(**config.get_lc_attr())


async def init_embeddings(config: EmbeddingsConfig):
    """初始化 Embeddings 实例"""
    yield OpenAIEmbeddings(**config.get_lc_attr())


class ModelsMixin(containers.DeclarativeContainer):
    """三种 LLM 模型资源：对话、长文本、思考。

    Attributes:
        chat_llm: 对话型 LLM 实例，用于日常对话和短文本处理。
        long_llm: 长文本 LLM 实例，用于处理长文档和大上下文。
        think_llm: 思考型 LLM 实例，用于需要深度推理的复杂任务。
    """

    chat_llm = providers.Resource(init_llm, config=get_config().model.chat)
    long_llm = providers.Resource(init_llm, config=get_config().model.long)
    think_llm = providers.Resource(init_llm, config=get_config().model.think)
    embeddings = providers.Resource(init_embeddings, config=get_config().model.embeddings)
