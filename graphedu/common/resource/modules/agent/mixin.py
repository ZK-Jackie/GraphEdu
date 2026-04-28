"""Agent Mixin：CheckpointMixin。"""

from dependency_injector import containers, providers

from graphedu.common.config.manager import get_config
from graphedu.common.resource.modules.agent.checkpoint import init_langgraph_checkpointer


class CheckpointMixin(containers.DeclarativeContainer):
    """提供 LangGraph PostgreSQL 检查点资源。

    Attributes:
        langgraph_checkpointer: LangGraph 检查点实例，用于持久化 Agent 状态。
    """

    langgraph_checkpointer = providers.Resource(init_langgraph_checkpointer, config=get_config().agent)
