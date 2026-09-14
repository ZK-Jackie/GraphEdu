"""习题-知识点关联 Mapper 模块。

提供习题与知识点关联关系的数据访问操作。
"""

import logging
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.orm.education import EduExerciseKnowledgePoint

logger = logging.getLogger(__name__)


class ExerciseKnowledgePointMapper:
    """习题-知识点关联数据访问层。"""

    @staticmethod
    async def get_exercises_by_node_uuids(
        db_session: AsyncSession,
        node_uuids: list[UUID],
        course_id: int,
        student_id: int | None = None,
        limit: int = 1,
    ) -> list[int]:
        """根据知识点 UUID 列表获取相关题目 ID。可指定学生过滤已做或优先薄弱点（预留）。

        :param db_session: 数据库会话
        :param node_uuids: 知识点 UUID 列表
        :param course_id: 课程 ID
        :param student_id: 学生 ID（预留过滤已做题目）
        :param limit: 获取题目数量
        :return: 题目 ID 列表
        """
        from sqlalchemy import desc, select

        from graphedu.common.models import SystemConstants
        from graphedu.common.models.orm.education import EduCourseExercise, EduExerciseKnowledgePoint

        if not node_uuids:
            return []

        # 简单实现：关联 edu_course_exercise 和 edu_exercise_knowledge_point
        # TODO: 加入学生做题历史过滤，错题优先等
        stmt = (
            select(EduCourseExercise.exercise_id)
            .join(
                EduExerciseKnowledgePoint,
                EduCourseExercise.exercise_id == EduExerciseKnowledgePoint.exercise_id,
            )
            .where(
                EduCourseExercise.course_id == course_id,
                EduCourseExercise.status == SystemConstants.Status.NORMAL,
                EduExerciseKnowledgePoint.node_uuid.in_(node_uuids),
            )
            .order_by(desc(EduExerciseKnowledgePoint.relevance_score))
            .limit(limit)
        )

        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_by_node_uuid(node_uuid: UUID, db_session: AsyncSession) -> int:
        """删除指定知识点关联的所有习题记录。

        :param node_uuid: 知识点业务 UUID
        :param db_session: 数据库会话
        :return: 删除的行数
        """
        stmt = delete(EduExerciseKnowledgePoint).where(EduExerciseKnowledgePoint.node_uuid == node_uuid)
        result = await db_session.execute(stmt)
        await db_session.flush()
        return result.rowcount

    @staticmethod
    async def delete_by_node_uuids(node_uuids: list[UUID], db_session: AsyncSession) -> int:
        """批量删除指定知识点关联的所有习题记录。

        :param node_uuids: 知识点业务 UUID 列表
        :param db_session: 数据库会话
        :return: 删除的行数
        """
        if not node_uuids:
            return 0
        stmt = delete(EduExerciseKnowledgePoint).where(EduExerciseKnowledgePoint.node_uuid.in_(node_uuids))
        result = await db_session.execute(stmt)
        await db_session.flush()
        return result.rowcount

    @staticmethod
    async def get_by_exercise_id(exercise_id: int, db_session: AsyncSession) -> list[EduExerciseKnowledgePoint]:
        """获取题目已绑定的知识点关联。

        :param db_session: 数据库会话
        :param exercise_id: 习题 ID
        :return: 关联记录列表
        """
        from sqlalchemy import select

        stmt = select(EduExerciseKnowledgePoint).where(EduExerciseKnowledgePoint.exercise_id == exercise_id)
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_association(
        exercise_id: int,
        node_uuid: UUID,
        db_session: AsyncSession,
        source: str = "manual",
        relevance_score: float = 0,
    ) -> EduExerciseKnowledgePoint:
        """创建题目-知识点关联（教师绑定时调用）。

        :param db_session: 数据库会话
        :param exercise_id: 习题 ID
        :param node_uuid: 知识点业务 UUID
        :param source: 关联来源（manual 手动）
        :param relevance_score: 相关性评分
        :return: 创建的关联记录
        """
        association = EduExerciseKnowledgePoint(
            exercise_id=exercise_id,
            node_uuid=node_uuid,
            source=source,
            relevance_score=relevance_score,
        )
        db_session.add(association)
        await db_session.flush()
        return association

    @staticmethod
    async def delete_by_exercise_and_node(exercise_id: int, node_uuid: UUID, db_session: AsyncSession) -> int:
        """删除指定题目与指定知识点的关联（教师解绑时调用）。

        :param db_session: 数据库会话
        :param exercise_id: 习题 ID
        :param node_uuid: 知识点业务 UUID
        :return: 删除的行数
        """
        stmt = delete(EduExerciseKnowledgePoint).where(
            EduExerciseKnowledgePoint.exercise_id == exercise_id,
            EduExerciseKnowledgePoint.node_uuid == node_uuid,
        )
        result = await db_session.execute(stmt)
        await db_session.flush()
        return result.rowcount

    @staticmethod
    async def has_manual_association(exercise_id: int, db_session: AsyncSession) -> bool:
        """检查题目是否已有手动绑定的知识点（推荐任务据此跳过，不覆盖教师决策）。

        :param db_session: 数据库会话
        :param exercise_id: 习题 ID
        :return: 是否已有 manual 关联
        """
        from sqlalchemy import func, select

        stmt = (
            select(func.count())
            .select_from(EduExerciseKnowledgePoint)
            .where(
                EduExerciseKnowledgePoint.exercise_id == exercise_id,
                EduExerciseKnowledgePoint.source == "manual",
            )
        )
        result = await db_session.execute(stmt)
        return (result.scalar() or 0) > 0
