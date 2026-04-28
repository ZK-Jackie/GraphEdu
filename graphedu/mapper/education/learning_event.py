"""学习事件 Mapper 模块。"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.dto.educationv2.event import LearningEventCreateDTO
from graphedu.common.models.orm.education import EduStudentLearningEvent


class LearningEventMapper:
    """学习事件 Mapper。"""

    @staticmethod
    async def create_event(
        obj: LearningEventCreateDTO,
        db_session: AsyncSession,
    ) -> EduStudentLearningEvent:
        """创建学习事件记录。

        Args:
            obj: 添加对象
            db_session: 数据库会话

        Returns:
            EduStudentLearningEvent: 创建的事件记录
        """
        event = EduStudentLearningEvent(
            student_id=obj.student_id,
            course_id=obj.course_id,
            session_id=obj.session_id,
            node_uuid=obj.node_uuid,
            chapter_id=obj.chapter_id,
            event_type=obj.event_type,
            event_source=obj.event_source,
            message_id=obj.message_id,
            event_content=obj.event_content,
            event_payload=obj.event_payload,
            duration_seconds=obj.duration_seconds,
            event_time=datetime.now(),
        )
        db_session.add(event)
        await db_session.flush()
        return event

    @staticmethod
    async def get_question_count(
        student_id: int,
        node_uuid: UUID,
        db_session: AsyncSession,
    ) -> int:
        """获取学生对某知识点的提问次数。

        Args:
            student_id: 学生 ID
            node_uuid: 知识点 UUID
            db_session: 数据库会话

        Returns:
            int: 提问次数（包含 question 和 revisit 类型）
        """
        stmt = select(EduStudentLearningEvent).where(
            EduStudentLearningEvent.student_id == student_id,
            EduStudentLearningEvent.node_uuid == node_uuid,
            EduStudentLearningEvent.event_type.in_(["question", "revisit"]),
        )
        result = await db_session.execute(stmt)
        return len(result.all())

    @staticmethod
    async def get_latest_events(
        student_id: int,
        course_id: int | None = None,
        event_type: str | None = None,
        limit: int = 10,
        db_session: AsyncSession | None = None,
    ) -> list[EduStudentLearningEvent]:
        """获取学生的最新学习事件。

        Args:
            student_id: 学生 ID
            course_id: 课程 ID（可选）
            event_type: 事件类型（可选）
            limit: 返回数量限制
            db_session: 数据库会话

        Returns:
            list[EduStudentLearningEvent]: 事件列表
        """
        stmt = select(EduStudentLearningEvent).where(EduStudentLearningEvent.student_id == student_id)
        if course_id is not None:
            stmt = stmt.where(EduStudentLearningEvent.course_id == course_id)
        if event_type is not None:
            stmt = stmt.where(EduStudentLearningEvent.event_type == event_type)
        stmt = stmt.order_by(EduStudentLearningEvent.event_time.desc()).limit(limit)
        result = await db_session.execute(stmt)
        return list(result.scalars())

    @staticmethod
    async def get_session_events(
        session_id: int,
        event_type: str | None = None,
        db_session: AsyncSession | None = None,
    ) -> list[EduStudentLearningEvent]:
        """获取指定会话的学习事件。

        Args:
            session_id: 会话 ID
            event_type: 事件类型过滤（可选）
            db_session: 数据库会话

        Returns:
            list[EduStudentLearningEvent]: 事件列表（按时间升序）
        """
        stmt = (
            select(EduStudentLearningEvent)
            .where(
                EduStudentLearningEvent.session_id == session_id,
                EduStudentLearningEvent.status == "0",
            )
            .order_by(EduStudentLearningEvent.event_time.asc())
        )
        if event_type is not None:
            stmt = stmt.where(EduStudentLearningEvent.event_type == event_type)
        result = await db_session.execute(stmt)
        return list(result.scalars())
