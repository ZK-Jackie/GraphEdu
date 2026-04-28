"""可视化知识图谱检索展示工具。"""

import logging

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime
from langgraph.types import Command
from pydantic import BaseModel, Field

from graphedu.common.models.bo import ChatState
from graphedu.common.models.bo.agent import ChatContext
from graphedu.common.models.dto.educationv2.agent import (
    ChatMessage,
    ContentTypeEnum,
    MapContent,
    MapNode,
    MapRelation,
    RoleEnum,
)
from graphedu.common.resource.deps import get_db_client
from graphedu.mapper.education.learning_event import LearningEventMapper
from graphedu.services.education.syllabus_graph import SyllabusGraphService

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


class VisualizeGraphQueryArgsSchema(BaseModel):
    """知识图谱查询工具参数。"""

    keyword: str = Field(description="用户问题中提炼出的知识点关键词")


def _build_map_content(nodes, relations, keyword: str) -> MapContent:
    """将图谱节点与关系转换为 MapContent。"""
    return MapContent(
        nodes=[
            MapNode(
                uid=node.id,
                name=node.title,
                labels=["KnowledgePoint"],
                properties={
                    "course_id": node.course_id,
                    "description": node.description,
                    "importance": node.importance,
                    "source": node.source,
                },
            )
            for node in nodes
        ],
        relations=[
            MapRelation(
                uid=relation.id,
                source=relation.from_node_id,
                target=relation.to_node_id,
                name=relation.type,
                properties={
                    "confidence": relation.confidence,
                    "description": relation.description,
                },
            )
            for relation in relations
        ],
        additional_kwargs={"keyword": keyword},
    )


@tool(
    "knowledge_point_query",
    description=(
        "知识图谱展示工具：当用户询问某个知识点、概念或实体时，"
        "传入关键词并返回对应知识图谱（关键词检索+向量检索混合）。"
    ),
    args_schema=VisualizeGraphQueryArgsSchema,
)
async def visualize_graph_query(
    keyword: str,
    runtime: ToolRuntime[ChatContext, ChatState],
) -> Command:
    """知识图谱可视化检索入口。"""
    tool_call_id = runtime.tool_call_id

    try:
        course_id = runtime.context.course_id
        if course_id is None:
            return Command(
                update={
                    "lc_messages": [
                        ToolMessage(
                            content="当前会话未关联课程，无法检索课程知识图谱。",
                            tool_call_id=tool_call_id,
                        )
                    ]
                }
            )

        pg_client = await get_db_client()
        merged_nodes, keyword_nodes, vector_nodes = await SyllabusGraphService.search_nodes_hybrid(
            pg_client=pg_client,
            course_id=course_id,
            keyword=keyword,
        )
        if not merged_nodes:
            return Command(
                update={
                    "lc_messages": [
                        ToolMessage(
                            content=f"未在知识图谱中找到与{keyword}相关的节点。",
                            tool_call_id=tool_call_id,
                        )
                    ]
                }
            )

        # 记录学习事件：用户对知识点的提问
        # 从状态中提取用户原始问题文本
        user_question = _extract_user_question(runtime)
        async with pg_client.session_context() as db_session:
            from graphedu.common.models.dto.educationv2.event import LearningEventCreateDTO

            for node in merged_nodes:
                event_dto = LearningEventCreateDTO(
                    student_id=runtime.context.user_id,
                    course_id=course_id,
                    session_id=runtime.context.conv_id,
                    node_uuid=node.uuid,
                    event_type="question",
                    event_content=user_question or keyword,
                )
                await LearningEventMapper.create_event(
                    obj=event_dto,
                    db_session=db_session,
                )

        graph_nodes, graph_relations = await SyllabusGraphService.get_two_hop_subgraph_from_seeds(
            pg_client=pg_client,
            seed_nodes=merged_nodes,
            node_limit=80,
            relation_limit=160,
        )
        map_content = _build_map_content(graph_nodes, graph_relations, keyword)

        map_msg = ChatMessage.auto_new_message(
            role=RoleEnum.TOOL,
            content_type=ContentTypeEnum.MAP,
            content=map_content,
            user_id=runtime.context.user_id,
            conv_id=runtime.context.conv_id,
        )

        summary = (
            f"图谱检索完成：关键词命中 {len(keyword_nodes)} 个，"
            f"向量命中 {len(vector_nodes)} 个，"
            f"合并后两跳子图节点 {len(graph_nodes)} 个、关系 {len(graph_relations)} 条。"
        )
        return Command(
            update={
                "gm_messages": [map_msg],
                "lc_messages": [ToolMessage(content=summary, tool_call_id=tool_call_id)],
            }
        )

    except Exception as e:
        logger.error("知识图谱可视化检索失败: %s", e)
        return Command(
            update={
                "lc_messages": [ToolMessage(content=f"知识图谱检索失败：{e}", tool_call_id=tool_call_id)],
            }
        )
