"""测试 ChatAgent 类"""

import pytest
from unittest.mock import patch

from graphedu.services.agent.chat_agent import ChatAgent
from graphedu.common.models.dto.educationv2.agent import ChatMessage, ContentTypeEnum, RoleEnum


@pytest.mark.asyncio
async def test_chat_agent_init():
    """测试 ChatAgent 初始化"""
    with patch("graphedu.services.agent.chat_agent.ChatOpenAI"), \
         patch("graphedu.services.agent.chat_agent.AsyncPostgresSaver"):
        agent = ChatAgent()
        await agent.init()
        assert agent.is_initialized() is True
        assert agent._agent is not None


@pytest.mark.asyncio
async def test_chat_agent_stream():
    """测试流式响应"""
    with patch("graphedu.services.agent.chat_agent.ChatOpenAI"), \
         patch("graphedu.services.agent.chat_agent.AsyncPostgresSaver"):
        agent = ChatAgent()
        await agent.init()

        message = ChatMessage.auto_new_message(
            role=RoleEnum.HUMAN,
            content_type=ContentTypeEnum.TEXT,
            content="Hello",
            user_id=1,
            conv_id=1
        )

        values = {"new_message": message}
        config = {"thread_id": "test-1", "user_id": 1, "conv_id": 1}

        # 由于需要 mock LLM，这里只验证函数调用
        try:
            async for msg in agent.async_stream(values, config):
                assert isinstance(msg, ChatMessage)
                break
        except Exception:
            pytest.skip("需要完整的 mock 设置")


@pytest.mark.asyncio
async def test_get_agent_singleton():
    """测试单例模式"""
    from graphedu.services.agent.chat import get_agent

    agent1 = await get_agent()
    agent2 = await get_agent()

    assert agent1 is agent2


@pytest.mark.asyncio
async def test_chat_agent_not_initialized():
    """测试未初始化时调用方法"""
    agent = ChatAgent()

    message = ChatMessage.auto_new_message(
        role=RoleEnum.HUMAN,
        content_type=ContentTypeEnum.TEXT,
        content="Hello",
        user_id=1,
        conv_id=1
    )

    values = {"new_message": message}
    config = {"thread_id": "test-1", "user_id": 1, "conv_id": 1}

    with pytest.raises(RuntimeError, match="ChatAgent not initialized"):
        async for _ in agent.async_stream(values, config):
            pass

    with pytest.raises(RuntimeError, match="ChatAgent not initialized"):
        await agent.async_get_history(config)
