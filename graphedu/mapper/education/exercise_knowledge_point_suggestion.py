"""习题-知识点候选推荐 Mapper 模块。

提供 AI 推荐候选知识点的数据访问。候选独立于已确认关联（edu_exercise_knowledge_point），
教师确认后才转入已确认表。消费端（query_exercise / assess）只读已确认关联，不受候选影响。
"""

import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.orm.education import EduExerciseKnowledgePointSuggestion

logger = logging.getLogger(__name__)


class ExerciseKnowledgePointSuggestionMapper:
    """习题-知识点候选推荐数据访问层。"""

    @staticmethod
    async def get_by_exercise_id(
        exercise_id: int, db_session: AsyncSession
    ) -> list[EduExerciseKnowledgePointSuggestion]:
        """获取题目的候选知识点推荐。

        :param db_session: 数据库会话
        :param exercise_id: 习题 ID
        :return: 候选推荐列表
        """
        stmt = select(EduExerciseKnowledgePointSuggestion).where(
            EduExerciseKnowledgePointSuggestion.exercise_id == exercise_id
        )
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def replace_suggestions(
        exercise_id: int,
        items: list[tuple[UUID, float]],
        db_session: AsyncSession,
    ) -> None:
        """覆盖式写入题目的候选推荐（先删该题旧候选，再批量插入）。

        :param db_session: 数据库会话
        :param exercise_id: 习题 ID
        :param items: [(node_uuid, relevance_score), ...]
        """
        # 先删旧候选
        stmt = delete(EduExerciseKnowledgePointSuggestion).where(
            EduExerciseKnowledgePointSuggestion.exercise_id == exercise_id
        )
        await db_session.execute(stmt)

        # 批量插新候选
        for node_uuid, relevance_score in items:
            db_session.add(
                EduExerciseKnowledgePointSuggestion(
                    exercise_id=exercise_id,
                    node_uuid=node_uuid,
                    relevance_score=relevance_score,
                )
            )
        await db_session.flush()

    @staticmethod
    async def delete_by_exercise_and_node(exercise_id: int, node_uuid: UUID, db_session: AsyncSession) -> int:
        """删除指定题目的某个候选（教师确认绑定时调用，清理已确认的候选）。

        :param db_session: 数据库会话
        :param exercise_id: 习题 ID
        :param node_uuid: 知识点业务 UUID
        :return: 删除的行数
        """
        stmt = delete(EduExerciseKnowledgePointSuggestion).where(
            EduExerciseKnowledgePointSuggestion.exercise_id == exercise_id,
            EduExerciseKnowledgePointSuggestion.node_uuid == node_uuid,
        )
        result = await db_session.execute(stmt)
        await db_session.flush()
        return result.rowcount
