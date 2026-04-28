"""AI Agent 服务模块。

本包提供基于 LangChain/LangGraph 的 AI Agent 实现，包括：
- 知识图谱构建 Agent
- 对话管理 Agent
- 推理和决策 Agent
"""

from graphedu.services.agent.chat_agent import ChatAgent

_agent_instance = None


async def get_agent():
    """获取 AI Agent"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ChatAgent()
        await _agent_instance.init()
    return _agent_instance


__all__ = ["ChatAgent", "get_agent"]
