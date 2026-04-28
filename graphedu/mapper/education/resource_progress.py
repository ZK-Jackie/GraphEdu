"""学生资料阅读进度 Mapper 层

负责资料进度数据的访问操作，包括 upsert、查询、统计等功能。
"""

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.orm.education import EduStudentResourceProgress


class ResourceProgressMapper:
    """学生资料阅读进度数据访问层"""

    @staticmethod
    async def get_by_student_and_resource(
        student_id: int, resource_id: int, db_session: AsyncSession
    ) -> EduStudentResourceProgress | None:
        """根据学生ID和资料ID查询进度

        :param db_session: 数据库会话
        :param student_id: 学生ID
        :param resource_id: 资料ID
        :return: 进度对象
        """
        stmt = select(EduStudentResourceProgress).where(
            and_(
                EduStudentResourceProgress.student_id == student_id,
                EduStudentResourceProgress.resource_id == resource_id,
                EduStudentResourceProgress.status != SystemConstants.Status.DELETED,
            )
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def add(progress: EduStudentResourceProgress, db_session: AsyncSession) -> EduStudentResourceProgress:
        """添加资料进度记录

        :param db_session: 数据库会话
        :param progress: 进度对象
        :return: 进度对象
        """
        db_session.add(progress)
        await db_session.flush()
        return progress

    @staticmethod
    async def update(progress: EduStudentResourceProgress, db_session: AsyncSession) -> None:
        """更新资料进度

        :param db_session: 数据库会话
        :param progress: 进度对象
        """
        await db_session.merge(progress)
        await db_session.flush()

    @staticmethod
    async def get_by_id(progress_id: int, db_session: AsyncSession) -> EduStudentResourceProgress | None:
        """根据进度ID查询

        :param db_session: 数据库会话
        :param progress_id: 进度记录ID
        :return: 进度对象
        """
        stmt = select(EduStudentResourceProgress).where(
            EduStudentResourceProgress.progress_id == progress_id,
            EduStudentResourceProgress.status != SystemConstants.Status.DELETED,
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_progresses_by_chapter(
        student_id: int, chapter_id: int, db_session: AsyncSession
    ) -> list[EduStudentResourceProgress]:
        """获取学生对某章节所有资料的进度

        :param db_session: 数据库会话
        :param student_id: 学生ID
        :param chapter_id: 章节ID
        :return: 进度列表
        """
        stmt = select(EduStudentResourceProgress).where(
            and_(
                EduStudentResourceProgress.student_id == student_id,
                EduStudentResourceProgress.chapter_id == chapter_id,
                EduStudentResourceProgress.status != SystemConstants.Status.DELETED,
            )
        )
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_student_course_progresses(
        student_id: int, course_id: int, db_session: AsyncSession
    ) -> list[EduStudentResourceProgress]:
        """获取学生对某课程所有资料的进度

        :param db_session: 数据库会话
        :param student_id: 学生ID
        :param course_id: 课程ID
        :return: 进度列表
        """
        stmt = select(EduStudentResourceProgress).where(
            and_(
                EduStudentResourceProgress.student_id == student_id,
                EduStudentResourceProgress.course_id == course_id,
                EduStudentResourceProgress.status != SystemConstants.Status.DELETED,
            )
        )
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def calculate_chapter_completion_rate(student_id: int, chapter_id: int, db_session: AsyncSession) -> int:
        """计算学生对某章节的平均完成度

        :param db_session: 数据库会话
        :param student_id: 学生ID
        :param chapter_id: 章节ID
        :return: 平均完成度（0-100）
        """
        stmt = select(func.avg(EduStudentResourceProgress.completion_rate)).where(
            and_(
                EduStudentResourceProgress.student_id == student_id,
                EduStudentResourceProgress.chapter_id == chapter_id,
                EduStudentResourceProgress.status != SystemConstants.Status.DELETED,
            )
        )
        result = await db_session.execute(stmt)
        avg = result.scalar()
        return int(avg) if avg else 0
