"""学习路径推荐 MCP 工具。

当学生表达学习目标时，根据关键词匹配知识点并回溯先修链，
生成学习路径子图并在 AGE 图中持久化。
"""

import logging

from langchain_core.messages import ToolMessage
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
from graphedu.services.education.learning_path import LearningPathService

logger = logging.getLogger(__name__)


def _build_map_content(
    nodes,
    relations,
    plan_id: str | None = None,
) -> MapContent:
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
                    **({"uuid": node.uuid} if hasattr(node, "uuid") else {}),
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
        additional_kwargs={"plan_id": plan_id} if plan_id else {},
    )


learning_path_description = (
    "学习路径推荐工具：当学生表达学习目标或想学习某个知识点时，"
    "传入主题名称和关键词列表生成单一主题的学习路径。\n\n"
    "何时使用：\n"
    '- 学生说"我想学XXX"、"帮我规划学习"、"我想掌握XXX"等表达学习目标时\n'
    "- 学生想要了解某个知识的前置知识体系时\n"
    "❗重要提示：如果你需要为学生生成多个不相关主题的学习路径（例如同时规划“二叉树”和“排序算法”），"
    "请**分别、多次**调用本工具，每次只传入一个主题及其相关的关键词。切勿将不同主题的关键词混在一次调用中。\n\n"
    '输入：该路径的主题名称（如"二叉树遍历"），'
    '以及从学生消息中提炼的一个或多个相关知识关键词（如 ["二叉树", "前序遍历"]）。'
)


class LearningPathArgsSchema(BaseModel):
    """学习路径生成工具的输入参数。"""

    theme: str = Field(
        description="学习路径的主题名称，用于命名生成的学习计划。如'二叉树遍历'、'排序算法'等概括性精简短语。",
        min_length=1,
        max_length=50,
    )
    keywords: list[str] = Field(
        description=("与该主题相关的一个或多个具体的知识关键词列表，1-5个词。"),
        min_length=1,
        max_length=5,
    )


@tool(
    "generate_learning_path",
    description=learning_path_description,
    args_schema=LearningPathArgsSchema,
)
async def generate_learning_path(
    theme: str,
    keywords: list[str],
    runtime: ToolRuntime[ChatContext, ChatState],
) -> Command:
    """学习路径推荐工具：根据关键词匹配知识点并回溯先修链生成学习路径。"""
    tool_call_id = runtime.tool_call_id

    try:
        # 1. 解析课程 ID
        course_id = runtime.context.course_id
        if course_id is None:
            return Command(
                update={
                    "lc_messages": [
                        ToolMessage(
                            content="当前会话未关联课程，无法生成学习路径。",
                            tool_call_id=tool_call_id,
                        )
                    ]
                }
            )

        pg_client = await get_db_client()

        # 2. 生成学习路径
        plan_record, nodes, relationships = await LearningPathService.generate_path(
            pg_client=pg_client,
            student_id=runtime.context.user_id,
            course_id=course_id,
            keywords=keywords,
            title=theme,
            session_id=runtime.context.conv_id,
        )

        if not nodes:
            return Command(
                update={
                    "lc_messages": [
                        ToolMessage(
                            content=f"未在课程知识图谱中找到与「{'、'.join(keywords)}」相关的知识点，无法生成学习路径。请尝试其他关键词。",
                            tool_call_id=tool_call_id,
                        )
                    ]
                }
            )

        # 3. 构建 MapContent 返回前端展示
        map_content = _build_map_content(nodes, relationships, plan_id=plan_record.plan_id)
        map_msg = ChatMessage.auto_new_message(
            role=RoleEnum.TOOL,
            content_type=ContentTypeEnum.MAP,
            content=map_content,
            user_id=runtime.context.user_id,
            conv_id=runtime.context.conv_id,
        )

        if relationships:
            summary = (
                f"成功为主题【{theme}】创建学习路径（计划ID: {plan_record.plan_id}）。\n"
                f"该路径包含 {len(nodes)} 个知识点和 {len(relationships)} 条先修关系。\n"
                f"系统要求：请向用户输出一段自然的文字说明，告知他们此专属学习路径推荐已被创建并保存在系统内，同时简单概括其中涉及的知识点数量和先修结构。"
            )
        else:
            summary = (
                f"成功为主题【{theme}】创建学习计划（计划ID: {plan_record.plan_id}）。\n"
                f"包含 {len(nodes)} 个独立知识点（无先修依赖，可直接开启学习）。\n"
                f"系统要求：请向用户输出一段自然的文字说明，告知他们已将该学习目标收录为系统计划，随时开启学习。"
            )
        return Command(
            update={
                "gm_messages": [map_msg],
                "lc_messages": [ToolMessage(content=summary, tool_call_id=tool_call_id)],
            }
        )

    except Exception as e:
        logger.error("学习路径生成失败: %s", e)
        return Command(
            update={
                "lc_messages": [
                    ToolMessage(content=f"学习路径生成失败：{e}", tool_call_id=tool_call_id),
                ],
            }
        )
