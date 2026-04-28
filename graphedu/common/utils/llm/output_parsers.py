"""LLM output parser utilities.

This module provides custom output parsers for LangChain, including:
- ThinkingOutputParser: For parsing thinking model responses
- FixOutputParser: For modifying output messages
- WholeJsonOutputParser: For parsing JSON outputs
"""

from collections.abc import AsyncIterable, Callable, Iterable
import logging
from typing import Annotated, Any, Literal, TypeVar

from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.output_parsers import BaseGenerationOutputParser
from langchain_core.outputs import ChatGeneration, Generation
from langchain_core.runnables import RunnableConfig, RunnableGenerator
from pydantic import BaseModel, SkipValidation

from ..jsons import try_parse_json_object
from ..strings import extract_contents

logger = logging.getLogger(__name__)

_T_BaseModel = TypeVar("_T_BaseModel", bound=BaseModel)

glm_thinking_config = {"start_tag": "Thinking", "end_tag": "Response", "warning_tag": "###"}

ds_thinking_tag = {"start_tag": "<think>", "end_tag": "</think>"}


class ThinkingStateEnum:
    """思考状态枚举。"""

    NO_RESPOND = 0
    THINKING = 1
    RESPONSE = 2
    BOTH = 3


TSE = ThinkingStateEnum


def _process_ai_message_buffer(
    chunk: AIMessageChunk,
    buffer: str,
    tse: int,
    start_tag: str = "<think>",
    end_tag: str = "</think>",
    warning_tag: str | None = None,
    *,
    config: RunnableConfig,
) -> tuple[int, dict[str, str | None] | None]:
    """处理缓冲字符传数据，适用于不喜欢完整标注开始、末尾的 AI"""
    content = chunk.content
    # 1 没有开头和末尾标签时，默认为 thinking
    if start_tag not in buffer or end_tag not in buffer:  # 如果没有开头标签，则认为当前为 thinking
        return TSE.THINKING, {"reasoning_content": content, "content": None}
    if start_tag and end_tag in buffer:  # 如果有开头和末尾标签
        if buffer.endswith(end_tag):  # 如果末尾刚好是 </think>，则认为当前为 thinking
            return TSE.THINKING, {"reasoning_content": content, "content": None}
        if tse == TSE.THINKING:  # 如果末尾不是 </think> 而当前状态还没有从 thinking 转为 response，则说明在结束边界
            last_gt = content.rfind(end_tag[-1])
            return TSE.BOTH, {"reasoning_content": content[: last_gt + 1], "content": content[last_gt + 1 :]}
        return TSE.RESPONSE, {"reasoning_content": None, "content": content}  # 当前为 response
    logger.error(f"Unexpected state in ThinkingOutputParser! \nchunk: {chunk},\nbuffer: {buffer}")
    return TSE.NO_RESPOND, {"reasoning_content": content, "content": content}


def _process_ai_message_chunk(
    chunk: AIMessageChunk,
    _thinking: bool,
    start_tag: str = "Thinking",
    end_tag: str = "###Response",
    warning_tag: str | None = None,
    *,
    config: RunnableConfig,
) -> tuple[bool, dict[str, str | None] | None]:
    """处理当前块数据，适用于完整标注思考开始、末尾的 AI"""
    content = chunk.content
    # 遇到三个井号，跳过该 chunk
    if warning_tag and warning_tag in content:
        return _thinking, None
    # 标记 Thinking 或 Response
    if start_tag in content:
        return True, None
    if end_tag in content:
        return False, None
    # 根据当前标记返回不同结构的字典
    if _thinking:
        return _thinking, {"reasoning_content": content, "content": None}
    return _thinking, {"reasoning_content": None, "content": content}


def ThinkingOutputParser(  # noqa
    chunks: Iterable[AIMessageChunk], config: RunnableConfig
) -> Iterable[dict[str, str | None]]:
    """Thinking 模型的输出解析器，用于解析 Thinking 和 Response 的内容"""
    # 1 获取配置参数
    start_tag = _get_from_config(config, "start_tag", "<think>")
    end_tag = _get_from_config(config, "end_tag", "</think>")
    warning_tag = _get_from_config(config, "warning_tag", None)
    # 2 定义状态变量
    acc_respond = ""  # 累计响应，流式缓冲区
    _4state = TSE.NO_RESPOND
    _thinking = False  # True 为 thinking， False 为 response，是状态机变量，不是普通的 bool
    # 3 迭代处理数据
    for chunk in chunks:
        if isinstance(chunk, AIMessageChunk):
            # _thinking, result = _process_ai_message_chunk(
            #     chunk, _thinking, start_tag, end_tag, warning_tag, config=config
            # )
            # if result is not None:
            #     yield result
            acc_respond += chunk.content
            _4state, result = _process_ai_message_buffer(
                chunk, acc_respond, _4state, start_tag, end_tag, warning_tag, config=config
            )
            if result is not None:
                yield result
        elif isinstance(chunk, AIMessage):
            mid, after = extract_contents(chunk.content, start_tag, end_tag)
            yield {"reasoning_content": mid, "content": after}
        else:
            raise Exception("非法的输入类型，请检查输入内容")


async def AsyncThinkingOutputParser(  # noqa
    chunks: AsyncIterable[AIMessageChunk], config: RunnableConfig
) -> AsyncIterable[dict[str, Any]]:
    # 1 获取配置参数
    start_tag = _get_from_config(config, "start_tag", "<think>")
    end_tag = _get_from_config(config, "end_tag", "</think>")
    warning_tag = _get_from_config(config, "warning_tag", None)
    # 2 定义状态变量
    acc_respond = ""  # 累计响应，流式缓冲区
    _4state = TSE.NO_RESPOND
    _thinking = False  # True 为 thinking， False 为 response，是状态机变量，不是普通的 bool
    # 3 迭代处理数据
    async for chunk in chunks:
        if isinstance(chunk, AIMessageChunk):
            # _thinking, result = _process_ai_message_chunk(
            #     chunk, _thinking, start_tag, end_tag, warning_tag, config=config
            # )
            # if result is not None:
            #     yield result
            acc_respond += chunk.content
            _4state, result = _process_ai_message_buffer(
                chunk, acc_respond, _4state, start_tag, end_tag, warning_tag, config=config
            )
            if result is not None:
                yield result
        elif isinstance(chunk, AIMessage):
            mid, after = extract_contents(chunk.content, start_tag, end_tag)
            yield {"reasoning_content": mid, "content": after}
        else:
            raise Exception("非法的输入类型，请检查输入内容")


def FixOutputParser(  # noqa
    chunks: Iterable[AIMessageChunk], config: RunnableConfig
) -> Iterable[AIMessageChunk]:
    new_id = _get_from_config(config, "message_id", None)
    head_content = _get_from_config(config, "extra_head", "")
    tail_content = _get_from_config(config, "extra_tail", "")

    first_call = True
    for chunk in chunks:
        if isinstance(chunk, AIMessageChunk):
            if first_call:
                chunk.content = head_content + chunk.content
                first_call = False
            if chunk.response_metadata.get("finish_reason", False):
                chunk.id = new_id or chunk.id
                chunk.content += tail_content
            yield chunk
        elif isinstance(chunk, AIMessage):
            chunk.content = head_content + chunk.content
            yield chunk
        else:
            raise Exception("非法的输入类型，请检查输入内容")


async def AsyncFixOutputParser(  # noqa
    chunks: AsyncIterable[AIMessageChunk], config: RunnableConfig
) -> AsyncIterable[AIMessageChunk]:
    new_id = _get_from_config(config, "message_id", None)
    head_content = _get_from_config(config, "extra_head", "")
    tail_content = _get_from_config(config, "extra_tail", "")
    first_call = True
    async for chunk in chunks:
        if isinstance(chunk, AIMessageChunk):
            if first_call:
                chunk.content = head_content + chunk.content
                first_call = False
            if chunk.response_metadata.get("finish_reason", False):
                chunk.id = new_id or chunk.id
                chunk.content += tail_content
            yield chunk
        elif isinstance(chunk, AIMessage):
            chunk.content = head_content + chunk.content
            yield chunk
        else:
            raise Exception("非法的输入类型，请检查输入内容")


def _get_from_config(config: RunnableConfig, key: str, default: str = None) -> str | None:
    try:
        return config["configurable"][key]
    except KeyError:
        return default


# langchain_core.messages.utils._convert_to_message line 256 BaseMessage 中会被发送的内容

thinking_parser: Callable = RunnableGenerator(ThinkingOutputParser, AsyncThinkingOutputParser)
"""
深度思考 LLM 的输出解析器，可在 RunnableConfig.configurable 中配置思考模型的输出模板

配置项：
- start_tag: 思考内容的开始标记，默认为 "Thinking"
- end_tag: 思考内容的结束标记，默认为 "###Response"
- warning_tag: 思考内容的警告/忽略标记，默认为 "###"

配置格式：
RunnableConfig(configurable={"start_tag": "Thinking", "end_tag": "###Response", "warning_tag": "###"}) 或
{"configurable": {"start_tag": "Thinking", "end_tag": "###Response", "warning_tag": "###"}}

注意：
1. 不适用于 state 中的消息插入，最后还是需要自己修正并插入到 state 中
2. 尽量搭配 async_xx_astream_respond 函数使用，用于向前端返回思考的消息
3. 市面上：LLM 的消息记录基本上不带思考内容，只带最终内容，思考内容仅用于调试、分析、查阅

返回：
字典，格式为 {"reasoning_content": "思考内容"/None, "content": None/"最终内容"}
"""

fix_output_parser: Callable = RunnableGenerator(FixOutputParser, AsyncFixOutputParser)
"""
修正的输出解析器，用于 Runnable 中的 LLM 输出，在 RunnableConfig.configurable 中设置

可配置项：
- message_id: 输出消息的 ID
- extra_head: 为输出消息添加的头部内容
- extra_tail: 为输出消息添加的尾部内容

配置格式：
RunnableConfig(configurable={"message_id": "your_new_id", "extra_head": "头部内容", "extra_tail": "尾部内容"}) 或
{"configurable": {"message_id": "your_new_id", "extra_head": "头部内容", "extra_tail": "尾部内容"}}

注意：
1. 不适用于 state 中的 id 修改，最后还是需要自己修正并插入到 state 中
2. 尽量搭配 async_xx_astream_respond 函数使用，用于向前端返回修正的消息

返回：
AIMessageChunk 的迭代器
"""


class WholeJsonOutputParser(BaseGenerationOutputParser[_T_BaseModel | dict | list]):
    """自定义的 Langchain 输出解析器，用于解析实体提取的结果。"""

    expect_type: Literal["dict", "list"] = "dict"

    pydantic_object: Annotated[type[_T_BaseModel] | None, SkipValidation()] = None

    def parse_result(self, result: list[Generation], *, partial: bool = False) -> dict | list | pydantic_object:
        """解析 LLM 生成结果为 JSON 对象。

        Args:
            result: LLM 生成的结果列表
            partial: 是否允许部分解析（暂未实现）

        Returns:
            解析后的字典、列表或 Pydantic 对象

        Raises:
            NotImplementedError: 如果结果数量不为 1
            OutputParserException: 解析失败时
        """
        # Validate Generation
        if len(result) != 1:
            # 该输出解析器只能用于单一结果生成模型生成的内容
            raise NotImplementedError("This output parser can only be used with a single generation.")
        generation = result[0]
        if not isinstance(generation, ChatGeneration):
            # 该输出解析器只能用于聊天生成
            raise OutputParserException("This output parser can only be used with a chat generation.")
        # 使用自定义解析法
        try:
            _, result = try_parse_json_object(generation.message.content, expect_type=self.expect_type)
            if self.pydantic_object:
                result = self.pydantic_object.model_validate(result)
        except Exception as e:
            raise OutputParserException(f"Failed to parse the output: {e}") from e
        # 返回解析后的结果
        return result
