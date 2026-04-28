from dependency_injector.wiring import Provide, inject
from langchain_openai import OpenAIEmbeddings


@inject
async def get_embeddings(embeddings: OpenAIEmbeddings = Provide["embeddings"]) -> OpenAIEmbeddings:
    """为模块获取嵌入对象"""
    return await embeddings
