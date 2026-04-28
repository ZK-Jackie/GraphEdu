"""题库查询工具"""

import logging
from uuid import UUID

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime
from langgraph.types import Command
from pydantic import BaseModel, Field

from graphedu.common.models.bo import ChatState
from graphedu.common.models.bo.agent import ChatContext
from graphedu.common.models.dto.educationv2.agent import ChatMessage, ContentTypeEnum, RoleEnum
from graphedu.common.models.shared import QuestionOptionContent
from graphedu.common.resource.deps import get_db_client
from graphedu.mapper.education.exercise_knowledge_point import ExerciseKnowledgePointMapper
from graphedu.mapper.education.exercise_query import ExerciseQueryMapper
from graphedu.mapper.education.knowledge_point_embedding import KnowledgePointEmbeddingMapper
from graphedu.mapper.education.syllabus_graph import SyllabusGraphMapper

from ._deps import get_embeddings

logger = logging.getLogger(__name__)

query_exercise_description = (
    "从课程题库中查询已有的练习题。\n"
    "何时使用：\n"
    "- 用户需要做题练习、复习知识点时，优先调用此工具查询题库中是否已有相关题目。\n"
    "- 此工具支持根据自然语言描述（topic 关键词）在整个课程范围内进行语义检索。\n"
    "- 如果此工具返回没有匹配题目，再使用 set_a_question 工具生成新题目。\n"
)


class QueryExerciseArgsSchema(BaseModel):
    """题库查询工具的输入参数（章节ID从上下文获取）"""

    topic: str | None = Field(
        default=None,
        description="需要练习的知识点关键词、主题或概念描述。提供此字段会优先通过语义匹配搜寻相关题目（支持跨章节）。如果不确定知识点，可留空",
    )
    difficulty: int | None = Field(default=None, description="预留字段：希望练习的难度(1简单, 2中等, 3困难)")


@tool("query_exercise", description=query_exercise_description, args_schema=QueryExerciseArgsSchema)
async def query_exercise(
    topic: str | None,
    difficulty: int | None,
    runtime: ToolRuntime[ChatContext, ChatState],
) -> Command:
    """从课程题库中查询匹配的练习题"""
    tool_call_id = runtime.tool_call_id
    course_id = runtime.context.course_id
    chapter_id = runtime.context.chapter_id
    user_id = runtime.context.user_id

    # 1. 检查必要参数
    if not course_id:
        return Command(
            update={
                "lc_messages": [
                    ToolMessage(
                        content="上下文缺失课程信息，无法跨知识点组题。请检查当前会话关联的课程。",
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )

    # 2. 从知识图谱/章节取题
    exercises = []
    try:
        db_client = await get_db_client()
        async with db_client.session_context() as session:
            node_uuids = set()
            # 2.1 若提供了 topic，则通过向量和图谱检索相关节点
            if topic:
                # 语义匹配
                embeddings = await get_embeddings()
                embedded_topic = await embeddings.aembed_query(topic)
                kp_records = await KnowledgePointEmbeddingMapper.search_by_embedding(
                    course_id=course_id, query_embedding=embedded_topic, top_k=5, db_session=session
                )
                node_uuids.update(kp.node_uuid for kp in kp_records)

                # 文本精确匹配
                nodes = await SyllabusGraphMapper.search_nodes(pg_client=db_client, course_id=course_id, keyword=topic)
                for n in nodes:
                    if n.uuid:
                        try:
                            node_uuids.add(UUID(n.uuid) if isinstance(n.uuid, str) else n.uuid)
                        except ValueError:
                            continue

            # 2.2 从关联表中找题目
            if node_uuids:
                exercise_ids = await ExerciseKnowledgePointMapper.get_exercises_by_node_uuids(
                    db_session=session,
                    node_uuids=list(node_uuids),
                    course_id=course_id,
                    student_id=user_id,
                    limit=3,
                )
                if exercise_ids:
                    # 也可以在这里加上根据难度过滤：目前留空难度逻辑，只随缘抽第一条符合的
                    exercises = await ExerciseQueryMapper.get_exercises_by_ids(
                        pg_client=db_client, exercise_ids=exercise_ids
                    )

            # 2.3 降级逻辑：如果没有 topic 或没找到，依然走随机查询章节题库
            if not exercises and chapter_id:
                exercises = await ExerciseQueryMapper.get_random_exercise(
                    pg_client=db_client,
                    chapter_id=chapter_id,
                    limit=1,
                )
    except Exception as e:
        logger.error("题库查询失败: %s", e)
        return Command(
            update={
                "lc_messages": [
                    ToolMessage(
                        content=f"题库查询失败：{e}。请使用 set_a_question 工具生成新题目。",
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )

    # 3. 无题目 → 提示 LLM 调用 set_question
    if not exercises:
        return Command(
            update={
                "lc_messages": [
                    ToolMessage(
                        content="该章节下暂无题目，请使用 set_a_question 工具为学生生成新题目。",
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )

    # 4. 返回题目
    exercise = exercises[0]
    question_content = QuestionOptionContent.model_validate(exercise.exercise)
    question_content.exercise_id = exercise.exercise_id
    question_msg = ChatMessage.auto_new_message(
        role=RoleEnum.TOOL,
        content_type=ContentTypeEnum.QUESTION_OPTION,
        content=question_content,
        user_id=runtime.context.user_id,
        conv_id=runtime.context.conv_id,
    )
    return Command(
        update={
            "gm_messages": [question_msg],
            "lc_messages": [
                ToolMessage(
                    content=f"从题库中找到匹配题目并已展示给学生。题目ID: {exercise.exercise_id}",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )
