"""LangChain/LangGraph message utility functions.

This module provides utilities for working with LangChain and LangGraph messages,
including message reduction, ID generation, and message conversion.
"""

import random
from typing import TYPE_CHECKING, Any, Literal, TypeVar, Union

from langchain_core.messages import AIMessageChunk, BaseMessage, ToolCall, ToolMessageChunk
from langchain_core.runnables import RunnableConfig
from langgraph.graph import add_messages
from langgraph.graph.message import Messages as LangchainMessages
from pydantic import BaseModel

from graphedu.common.utils.uuids import uuid7_str

from ..strings import get_timestamp_ms
from .callbacks import async_gm_respond

_T_BaseModel = TypeVar("_T_BaseModel", bound=BaseModel)

if TYPE_CHECKING:
    from graphedu.common.models.dto.educationv2.agent import ChatMessage, T_ContentType

    _T_LC_Message = TypeVar("_T_LC_Message", bound=BaseMessage)
    _T_GM_Message = TypeVar("_T_GM_Message", bound=ChatMessage)
    ChatMessagesLike = _T_GM_Message | list[_T_GM_Message]


# Map-Reduce style message processing functions ###


def reduce_lc_messages(left: LangchainMessages, right: LangchainMessages) -> list:
    """合并 LangChain 消息列表

    使用 LangGraph 的 add_messages 函数合并两条消息列表。

    Args:
        left: 左侧消息列表
        right: 右侧消息列表

    Returns:
        list: 合并后的消息列表
    """
    return add_messages(left, right)


def reduce_gm_messages(left: "ChatMessagesLike", right: "ChatMessagesLike") -> list:
    """合并 GM（Graph Message）消息列表

    合并两个消息（或消息列表），去除空值和根据 message_id 去重。

    Args:
        left: 左侧消息或消息列表
        right: 右侧消息或消息列表

    Returns:
        list: 合并并去重后的消息列表
    """
    # coerce to list
    if isinstance(left, list):
        left = left[0]
    if not isinstance(left, list):
        left = [left]
    if isinstance(right, list):
        right = right[0]
    if not isinstance(right, list):
        right = [right]
    # merge
    merged = left + right
    # remove null values
    merged = [msg for msg in merged if msg is not None]
    # remove duplicates by message_id
    return list({msg.message_id: msg for msg in merged}.values())


def reduce_right(left: Any, right: Any) -> Any:
    """归约函数：仅返回右侧值

    用于 map-reduce 操作，丢弃左侧值，保留右侧值。

    Args:
        left: 左侧值（被忽略）
        right: 右侧值

    Returns:
        Any: 右侧值
    """
    return right


def reduce_merge(left: list, right: list) -> list:
    """归约函数：合并两个列表

    用于 map-reduce 操作，将两个列表连接在一起。

    Args:
        left: 左侧列表
        right: 右侧列表

    Returns:
        list: 合并后的列表
    """
    return left + right


# 生成消息 ID ###
def generate_call_id() -> str:
    """生成 AIMessage 调用工具的工具 ID，构成为 `call_xxxxxxxxxxxxxxxxxx`，`call_` 后接18位（0-9）数字
    Returns:
        str: 工具 ID
    """
    random_nums = [str(random.randint(0, 9)) for _ in range(18)]
    return f"call_{''.join(random_nums)}"


def generate_msg_id() -> str:
    """生成唯一的消息 ID

    Returns:
        str: UUID v4 格式的消息 ID
    """
    return uuid7_str()


# 创建 LangChain 消息对象 ###


def create_ai_message_chunk(id: str, reasoning_content: str = "", content: str = "") -> AIMessageChunk:
    """创建 AI 消息块对象

    Args:
        id: 消息 ID
        reasoning_content: 推理内容（存储在 additional_kwargs 中）
        content: 消息内容

    Returns:
        AIMessageChunk: AI 消息块对象
    """
    return AIMessageChunk(content=content, id=id, additional_kwargs={"reasoning_content": reasoning_content})


def create_tool_message_chunk(
    content: str, tool_call_id: str, message_id: str, reasoning_content: str
) -> ToolMessageChunk:
    """创建一个 ToolMessageChunk 对象

    :param content: 消息的 content 字段
    :param tool_call_id: 消息的 tool_call_id 字段
    :param message_id: 消息的 id 字段
    :param reasoning_content: 消息的 additional_kwargs["reasoning_content"] 字段
    :return: ToolMessageChunk 对象
    """
    return ToolMessageChunk(
        content=content,
        tool_call_id=tool_call_id,
        id=message_id,
        additional_kwargs={"reasoning_content": reasoning_content},
    )


def create_tool_call(response: str, args: dict[str, Any], default_tool: str, mapping: dict = None) -> ToolCall:
    """通过解析 AI 响应信息，创建对应的 ToolCall 对象

    :param response: AI 响应信息
    :param args: 工具请求需要传入的参数
    :param default_tool: 默认工具名
    :param mapping: AI 回答与真实工具名的映射，键为 AI 回答的关键词，值为真实的工具名
    :return: ToolCall 对象
    """
    if mapping is None:
        mapping = {"knowledge_qa": "knowledge_qa", "inquiry": "inquiry"}
    for key, value in mapping.items():
        if key in response:
            return {"name": value, "args": args, "id": generate_call_id()}
    return {"name": default_tool, "args": args, "id": generate_call_id()}


def item_in_content(content: str, items: list[str]) -> str | None:
    """检查内容中是否包含列表中的任一项

    Args:
        content: 待检查的内容字符串
        items: 候选项列表

    Returns:
        str | None: 第一个匹配到的项，如果没有匹配则返回 None
    """
    for item in items:
        if item in content:
            return item
    return None


def get_message_type(type_str: str) -> int:
    """将消息类型字符串转换为 RoleEnum 枚举值

    Args:
        type_str: 消息类型字符串，如 "AIMessage", "Human" 等

    Returns:
        int: 对应的 RoleEnum 枚举值

    Examples:
        >>> get_message_type("AIMessage")
        RoleEnum.AI
        >>> get_message_type("human")
        RoleEnum.HUMAN
    """
    from graphedu.common.models.dto.educationv2.agent import RoleEnum

    if type_str in ["AIMessage", "AIMessageChunk", "AI", "ai"]:
        return RoleEnum.AI
    if type_str in ["HumanMessage", "HumanMessageChunk", "Human", "human"]:
        return RoleEnum.HUMAN
    if type_str in ["SystemMessage", "System", "system"]:
        return RoleEnum.SYSTEM
    if type_str in ["ToolMessage", "Tool", "tool"]:
        return RoleEnum.TOOL
    return RoleEnum.UNKNOWN


# 创建/汇报 GM 消息对象 ###
def create_collapse(
    content: str, message_id: str, mode: Literal["start", "end"], config: RunnableConfig
) -> "ChatMessage":
    """快捷创建折叠消息"""
    from graphedu.common.models.dto.educationv2.agent import ChatMessage, ContentTypeEnum, RoleEnum

    return ChatMessage.auto_new_message(
        role=RoleEnum.SYSTEM,
        content_type=ContentTypeEnum.COLLAPSE_START if mode == "start" else ContentTypeEnum.COLLAPSE_END,
        content=content,
        message_id=message_id,
        user_id=config.get("configurable", {}).get("user_id", 0),
        conv_id=config.get("configurable", {}).get("conv_id", 0),
    )


async def create_report_collapse(
    content: str, mode: Literal["start", "end"], config: RunnableConfig, *, message_id: str = None
) -> "ChatMessage":
    """快捷创建折叠消息"""
    from graphedu.common.models.dto.educationv2.agent import ChatMessage, ContentTypeEnum, RoleEnum

    message_id = message_id or get_timestamp_ms()
    collapse_msg = ChatMessage.auto_new_message(
        role=RoleEnum.SYSTEM,
        content_type=ContentTypeEnum.COLLAPSE_START if mode == "start" else ContentTypeEnum.COLLAPSE_END,
        content=content,
        message_id=message_id,
        user_id=config.get("configurable", {}).get("user_id", 0),
        conv_id=config.get("configurable", {}).get("conv_id", 0),
    )
    await async_gm_respond(collapse_msg, config)
    return collapse_msg


async def auto_create_report(
    role: int,
    content_type: str,
    content: Union["T_ContentType", list["T_ContentType"]],
    config: RunnableConfig,
    message_id: str | None = None,
) -> "ChatMessage":
    """自动创建消息并汇报"""
    from graphedu.common.models.dto.educationv2.agent import ChatMessage

    if message_id is None:
        message_id = get_timestamp_ms()
    msg = ChatMessage.auto_new_message(
        role=role,
        content_type=content_type,
        content=content,
        message_id=message_id,
        user_id=config.get("configurable", {}).get("user_id", 0),
        conv_id=config.get("configurable", {}).get("conv_id", 0),
    )
    await async_gm_respond(msg, config)
    return msg


# 消息转换 ###


def prompt_prints(lc_messages: list["_T_LC_Message"]):
    """获取消息列表中所有的提示信息

    将 LangChain 消息列表格式化为可读的字符串。

    Args:
        lc_messages: LangChain 消息列表

    Returns:
        str: 格式化后的消息字符串，每条消息一行
    """
    return "\n".join([f"{m.type}: ```{m.content}```" for m in lc_messages])
