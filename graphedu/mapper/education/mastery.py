"""学生知识点掌握度评估 Mapper 模块。"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.orm.education import EduStudentMastery


class MasteryMapper:
    """学生知识点掌握度评估数据访问层。"""

    @staticmethod
    async def create_mastery(
        student_id: int,
        course_id: int,
        node_uuid: UUID,
        mastery_score: float,
        mastery_level: str,
        trigger_type: str,
        session_id: int | None = None,
        reason: str | None = None,
        db_session: AsyncSession | None = None,
    ) -> EduStudentMastery:
        """创建一条掌握度评估记录。

        :param student_id: 学生 ID
        :param course_id: 课程 ID
        :param node_uuid: 知识点业务 UUID
        :param mastery_score: 掌握度评分（0-100）
        :param mastery_level: 掌握等级（unknown/low/medium/high）
        :param trigger_type: 触发类型（chat_round/quiz_complete/periodic/manual/system）
        :param session_id: 触发评估的会话 ID（可选）
        :param reason: AI 评估理由（可选）
        :param db_session: 数据库会话
        :return: 创建的掌握度评估记录
        """
        record = EduStudentMastery(
            student_id=student_id,
            course_id=course_id,
            node_uuid=node_uuid,
            session_id=session_id,
            mastery_score=mastery_score,
            mastery_level=mastery_level,
            trigger_type=trigger_type,
            reason=reason,
        )
        db_session.add(record)
        await db_session.flush()
        return record

    @staticmethod
    async def upsert_mastery(
        student_id: int,
        course_id: int,
        node_uuid: UUID,
        mastery_score: float,
        mastery_level: str,
        trigger_type: str,
        session_id: int | None = None,
        reason: str | None = None,
        db_session: AsyncSession | None = None,
    ) -> EduStudentMastery:
        """按 (student_id, course_id, node_uuid, session_id) 查找已有记录，
        存在则更新 mastery_score/mastery_level/assessed_at，不存在则新建。

        :return: 更新或创建的掌握度评估记录
        """
        stmt = select(EduStudentMastery).where(
            EduStudentMastery.student_id == student_id,
            EduStudentMastery.course_id == course_id,
            EduStudentMastery.node_uuid == node_uuid,
            EduStudentMastery.session_id == session_id,
            EduStudentMastery.status == "0",
        )
        result = await db_session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.mastery_score = mastery_score
            existing.mastery_level = mastery_level
            existing.trigger_type = trigger_type
            existing.reason = reason
            existing.assessed_at = datetime.now()
            await db_session.flush()
            return existing

        return await MasteryMapper.create_mastery(
            student_id=student_id,
            course_id=course_id,
            node_uuid=node_uuid,
            mastery_score=mastery_score,
            mastery_level=mastery_level,
            trigger_type=trigger_type,
            session_id=session_id,
            reason=reason,
            db_session=db_session,
        )

    @staticmethod
    async def get_by_student_session(
        student_id: int,
        course_id: int,
        session_id: int | None = None,
        db_session: AsyncSession | None = None,
    ) -> list[EduStudentMastery]:
        """查询学生在某次会话中的所有评估记录。

        :param student_id: 学生 ID
        :param course_id: 课程 ID
        :param session_id: 会话 ID（可选，为 None 时查询该课程全部记录）
        :param db_session: 数据库会话
        :return: 评估记录列表
        """
        stmt = select(EduStudentMastery).where(
            EduStudentMastery.student_id == student_id,
            EduStudentMastery.course_id == course_id,
            EduStudentMastery.status == "0",
        )
        if session_id is not None:
            stmt = stmt.where(EduStudentMastery.session_id == session_id)
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_mastery(mastery_id: int, db_session: AsyncSession) -> None:
        """逻辑删除指定评估记录（status 设为 "2"）。

        :param mastery_id: 评估记录 ID
        :param db_session: 数据库会话
        """
        stmt = (
            update(EduStudentMastery)
            .where(EduStudentMastery.mastery_id == mastery_id)
            .values(status="2")
        )
        await db_session.execute(stmt)
        await db_session.flush()
