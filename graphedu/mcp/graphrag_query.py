"""语义知识图谱检索工具"""

import logging
from typing import Literal

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime
from langgraph.types import Command
from pydantic import BaseModel, Field

from graphedu.common.models.bo import ChatState
from graphedu.common.models.bo.agent import ChatContext
from graphedu.common.models.dto.educationv2.agent import ChatMessage, ContentTypeEnum, RoleEnum
from graphedu.common.resource.deps import get_db_client
from graphedu.mapper.education.learning_event import LearningEventMapper
from graphedu.services.external.graphrag import GraphRAGService

logger = logging.getLogger(__name__)


def _extract_user_question(runtime) -> str | None:
    """从运行时状态中提取用户最近的原始问题文本。"""
    lc_messages = runtime.state.get("lc_messages", [])
    for msg in reversed(lc_messages):
        if isinstance(msg, HumanMessage):
            content = msg.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                # 多模态消息，提取文本部分
                texts = [
                    part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"
                ]
                return " ".join(texts) if texts else None
    return None


graphrag_query_description = (
    "教学文档检索工具：直接调用 GraphRAG 服务检索课程知识。\n\n"
    "何时使用：\n"
    "- 用户询问课程知识点、概念解释、解题思路。\n"
    "- 需要结合课程资料进行专业回答，而不是通用常识回答。"
)


class GraphQueryArgsSchema(BaseModel):
    """Input for graph query."""

    query: str = Field(description="要检索的问题，建议重写为完整明确的问题")
    search_type: Literal["local", "global", "drift", "basic"] = Field(
        default="local", description="检索模式，local（默认，精准）、global（综合）、drift（混合）、basic（简易）"
    )


@tool("teaching_document_retrieval", description=graphrag_query_description, args_schema=GraphQueryArgsSchema)
async def graphrag_query(
    query: str,
    runtime: ToolRuntime[ChatContext, ChatState],
    search_type: Literal["local", "global", "drift", "basic"] = "local",
) -> Command:
    """GraphRAG 检索工具"""
    tool_call_id = runtime.tool_call_id

    try:
        # 准备 id
        graphrag_task_id = runtime.context.graphrag_task_id
        # 准备历史记录
        graphrag_history = [{"role": lm.type, "content": lm.content} for lm in runtime.state.lc_messages]
        if search_type == "global":
            result = await GraphRAGService.global_search(
                query=query, graphrag_task_id=graphrag_task_id, conversation_history=graphrag_history
            )
        elif search_type == "drift":
            result = await GraphRAGService.drift_search(
                query=query, graphrag_task_id=graphrag_task_id, conversation_history=graphrag_history
            )
        elif search_type == "basic":
            result = await GraphRAGService.basic_search(
                query=query, graphrag_task_id=graphrag_task_id, conversation_history=graphrag_history
            )
        else:
            result = await GraphRAGService.local_search(
                query=query, graphrag_task_id=graphrag_task_id, conversation_history=graphrag_history
            )

        # 记录学习事件
        course_id = runtime.context.course_id
        if course_id:
            user_question = _extract_user_question(runtime)
            pg_client = await get_db_client()
            async with pg_client.session_context() as db_session:
                from graphedu.common.models.dto.educationv2.event import LearningEventCreateDTO

                event_dto = LearningEventCreateDTO(
                    student_id=runtime.context.user_id,
                    course_id=course_id,
                    session_id=runtime.context.conv_id,
                    node_uuid=None,  # GraphRAG检索通常不针对特定知识点
                    event_type="question",
                    event_content=user_question or query,
                )
                await LearningEventMapper.create_event(
                    obj=event_dto,
                    db_session=db_session,
                )

    except Exception as e:
        logger.error("GraphRAG 检索失败: %s", e)
        return Command(
            update={
                "lc_messages": [ToolMessage(content=f"文档检索失败：{e}", tool_call_id=tool_call_id)],
            }
        )

    msg = ChatMessage.auto_new_message(
        role=RoleEnum.TOOL,
        content_type=ContentTypeEnum.TEXT,
        content=result.answer,
        user_id=runtime.context.user_id,
        conv_id=runtime.context.conv_id,
    )

    return Command(
        update={
            "gm_messages": [msg],
            "lc_messages": [ToolMessage(content=result.answer, tool_call_id=tool_call_id)],
        }
    )
