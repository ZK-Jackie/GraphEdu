"""聊天模块业务逻辑相关的模型"""

from typing import Annotated, NotRequired, TypedDict

from langchain_core.messages import AnyMessage
from pydantic import BaseModel, Field

from graphedu.common.models.dto.educationv2.agent import ChatFeature, ChatMessage
from graphedu.common.utils.llm.messages import reduce_gm_messages, reduce_lc_messages


class InvokableConfig(TypedDict):
    """调用聊天模块需要传入的配置"""

    thread_id: str
    user_id: int
    conv_id: int
    course_id: NotRequired[int | None]


class InvokableValues(TypedDict):
    """调用聊天模块需要传入的内容"""

    new_message: ChatMessage


class ChatContext(ChatFeature):
    """Agent 交互上下文"""

    user_id: int
    conv_id: int
    course_id: int | None = Field(default=None)
    graphrag_task_id: int | None = Field(default=None)


class ChatState(BaseModel):
    """Agent 状态管理"""

    lc_messages: Annotated[list[AnyMessage], reduce_lc_messages]
    """LangChain 类型消息列表"""

    gm_messages: Annotated[list[ChatMessage], reduce_gm_messages]
    """ChatMessage 类型消息列表"""
