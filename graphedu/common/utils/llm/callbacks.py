"""LangChain callback utilities for streaming responses.

This module provides utilities for handling AI streaming responses,
including dispatching custom events and streaming responses to clients.
"""

from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Literal, Optional

from langchain_core.callbacks import adispatch_custom_event as lc_adispatch_custom_event
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage, ToolMessageChunk, merge_message_runs
from langchain_core.runnables import RunnableConfig

from ..strings import get_timestamp_ms

if TYPE_CHECKING:
    from graphedu.common.models.dto.educationv2.agent import ChatMessage


async def adispatch_custom_event(name: str, message: "ChatMessage", config: RunnableConfig | None = None) -> None:
    """用于发送自定义事件，这里会根据不同的事件名进行不同的处理

    :param name: 事件名
    :param message: gm 类型消息
    :param config: 事件配置
    :return: None
    """
    # ChatEventData 转换为 ChatMessage
    await lc_adispatch_custom_event(name, message, config=config)


async def async_ai_astream_respond(
    chain_returns: AsyncIterable[AIMessageChunk],
    config: RunnableConfig,
    event_name: str = "ai_response_token_stream",
    message_id: str = None,
    content_type: str = None,
) -> tuple[AIMessage, Optional["ChatMessage"]]:
    """实现自定义的 AI 流式数据返回，这里**会负责**消息的托管、迭代、组装，最终返回完整的信息对象

    :param chain_returns: chain.astream 返回的异步迭代器
    :param config: 运行时配置，需包含 `thread_id`、`user_id`、`conv_id`
    :param event_name: 数据返回时的 name，便于 astream_event 定位
    :param message_id: 有时可能需要特定的 message id 用于特定的情况，则提供，否则默认是进入函数时的毫秒时间戳值
    :param content_type: 消息内容类型，默认为 TEXT
    :return: AIMessage LangChain 类型消息；ChatMessage GM 类型消息
    """
    from graphedu.common.models.dto.educationv2.agent import ChatMessage, ContentTypeEnum, RoleEnum
    content_type = content_type or ContentTypeEnum.TEXT
    # 1 创建模板消息
    gm_ret = ChatMessage.auto_new_message(
        role=RoleEnum.AI,
        content="",
        content_type=content_type,
        user_id=config.get("configurable", {}).get("user_id", ''),
        conv_id=config.get("configurable", {}).get("conv_id", ''),
        message_id=message_id or get_timestamp_ms(),
    )
    # 2 迭代、发送消息块
    is_toolcall = False
    lc_message_buffer: list[AIMessage | AIMessageChunk] = []
    async for chunk in chain_returns:
        lc_message_buffer.append(chunk)
        if len(lc_message_buffer) < 2 or is_toolcall:
            if chunk.tool_calls:
                is_toolcall = True
            continue
        if len(lc_message_buffer) == 2:
            # 这个信息块文本内容需要加入先前错过的消息块中的内容
            gm_ret.auto_set_contents(ContentTypeEnum.TEXT, "".join([c.content for c in lc_message_buffer]))
        else:
            gm_ret.auto_set_contents(ContentTypeEnum.TEXT, chunk.content)
        await adispatch_custom_event(
            name=event_name,
            message=gm_ret,
            config=RunnableConfig(tags=["graphmind:response"], configurable=config.get("configurable")),
        )
    # 3 补全、组装最终信息
    lc_message_buffer = merge_message_runs(lc_message_buffer, chunk_separator="")
    lc_message_buffer[0].id = gm_ret.message_id
    gm_ret.auto_set_contents(content_type, lc_message_buffer[0].content)
    return lc_message_buffer[0], gm_ret


async def async_ai_chunk_respond(
    chunk: AIMessage | AIMessageChunk,
    config: RunnableConfig,
    thinking: bool = False,
    name: str = "ai_response_token_stream",
    content_type: str = None,
) -> None:
    """实现自定义的 AI 流式数据返回，这里**不提供**消息的托管、迭代、组装，**必须提供消息 id**

    :param chunk: AI 半成品，帮助将信息返回给用户，**必须提供消息 id**
    :param thinking: 是否为 Thinking 类型的消息
    :param name: 数据返回时的 name，便于 astream_event 定位，默认为 `ai_response_token_stream`
    :param content_type: 消息内容类型，默认为 TEXT
    :param config: 运行时配置，需包含 `thread_id`、`user_id`、`conv_id`
    :return: None
    """
    from graphedu.common.models.dto.educationv2.agent import ChatMessage, ContentTypeEnum

    content_type = content_type or ContentTypeEnum.TEXT
    if thinking:
        name = name or "ai_thinking_token_stream"
    await adispatch_custom_event(
        name=name,
        message=ChatMessage.from_lc_message(
            lc_message=chunk,
            thinking=thinking,
            user_id=config.get("configurable", {}).get("user_id", ''),
            conv_id=config.get("configurable", {}).get("conv_id", ''),
        ),
        config=RunnableConfig(tags=["graphmind:thinking"], configurable=config.get("configurable", {})),
    )


async def async_tool_chunk_respond(
    chunk: ToolMessage | ToolMessageChunk,
    config: RunnableConfig,
    name: str = "tool_call_token_stream",
    content_type: str = None,
) -> None:
    """实现自定义的 Tool 流式数据返回，这里不提供消息的托管、迭代、组装，**必须提供消息 id**

    :param chunk: tool 半成品，帮助将信息返回给用户，**必须提供消息 id**
    :param config: 运行时配置
    :param name: 数据返回时的 name，便于 astream_event 定位，默认为 `tool_call_token_stream`
    :param content_type: 消息内容类型，默认为 TEXT
    :return: None
    """
    from graphedu.common.models.dto.educationv2.agent import ChatMessage

    await adispatch_custom_event(
        name=name,
        message=ChatMessage.from_lc_message(
            lc_message=chunk,
            user_id=config.get("configurable", {}).get("user_id", ''),
            conv_id=config.get("configurable", {}).get("conv_id", ''),
        ),
        config=RunnableConfig(tags=["graphmind:response"], configurable=config.get("configurable", {})),
    )


async def async_gm_respond(
    message: "ChatMessage",
    config: RunnableConfig,
    name: str = "gm_token_stream",
) -> None:
    """实现自定义的 Thinking 流式数据返回，这里不提供消息的托管、迭代、组装，**必须提供消息 id**

    :param message: Thinking 消息，**必须提供消息 id**
    :param config: 运行时配置
    :param name: 数据返回时的 name，便于 astream_event 定位，默认为 `gm_thinking_token_stream`
    :return: None
    """
    await adispatch_custom_event(
        name=name,
        message=message,
        config=RunnableConfig(tags=["graphmind:response"], configurable=config.get("configurable")),
    )


async def async_system_respond(
    message: str,
    config: RunnableConfig,
    name: str = "system_message_stream",
    level: str | Literal["info", "error"] = "info",
) -> None:
    """实现自定义的系统消息流式数据返回，这里不提供消息的托管、迭代、组装

    :param message: 实时系统消息
    :param config: 运行时配置
    :param name: 数据返回时的 name，便于 astream_event 定位，默认为 `system_message_stream`
    :param level: 消息级别，默认为 info
    :return: None
    """
    from graphedu.common.models.dto.educationv2.agent import ChatMessage, ContentTypeEnum, RoleEnum

    await adispatch_custom_event(
        name=name,
        message=ChatMessage.auto_new_message(
            role=RoleEnum.SYSTEM,
            content=f"<{level}> {message} </{level}>",
            content_type=ContentTypeEnum.TEXT,
            user_id=config.get("configurable", {}).get("user_id", ''),
            conv_id=config.get("configurable", {}).get("conv_id", ''),
            message_id=get_timestamp_ms(),
        ),
        config=RunnableConfig(tags=["graphmind:response"], configurable=config.get("configurable", {})),
    )
