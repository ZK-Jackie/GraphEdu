"""课程教师关联 Mapper 层

负责课程与教师关联数据的访问操作，包括绑定、解绑教师等功能。
"""

from collections.abc import Sequence

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.orm.education import EduCourseTeacher, EduTeacher


class CourseTeacherMapper:
    """课程教师关联数据访问层

    提供课程与教师关联的 CRUD 操作。
    """

    @staticmethod
    async def bind_teacher(
        course_id: int,
        teacher_id: int,
        db_session: AsyncSession,
        role_type: str = "instructor",
        display_order: int = 0,
    ) -> None:
        """为课程绑定教师

        :param course_id: 课程ID
        :param teacher_id: 教师ID
        :param db_session: 数据库会话
        :param role_type: 教师角色（instructor主讲/assistant助教/consultant顾问）
        :param display_order: 显示顺序
        :return: None
        """
        # 检查是否已绑定
        existing = await CourseTeacherMapper.get_binding(course_id, teacher_id, db_session)
        if not existing:
            new_binding = EduCourseTeacher(
                course_id=course_id, teacher_id=teacher_id, role_type=role_type, display_order=display_order
            )
            db_session.add(new_binding)
            await db_session.flush()

    @staticmethod
    async def unbind_teacher(course_id: int, teacher_id: int, db_session: AsyncSession) -> None:
        """解绑课程的教师

        :param course_id: 课程ID
        :param teacher_id: 教师ID
        :param db_session: 数据库会话
        :return: None
        """
        stmt = delete(EduCourseTeacher).where(
            and_(EduCourseTeacher.course_id == course_id, EduCourseTeacher.teacher_id == teacher_id)
        )
        await db_session.execute(stmt)
        await db_session.flush()

    @staticmethod
    async def unbind_all_teachers(course_id: int, db_session: AsyncSession) -> None:
        """解绑课程的所有教师

        :param course_id: 课程ID
        :param db_session: 数据库会话
        :return: None
        """
        stmt = delete(EduCourseTeacher).where(EduCourseTeacher.course_id == course_id)
        await db_session.execute(stmt)
        await db_session.flush()

    @staticmethod
    async def get_binding(course_id: int, teacher_id: int, db_session: AsyncSession) -> EduCourseTeacher | None:
        """检查课程是否已绑定某位教师

        :param course_id: 课程ID
        :param teacher_id: 教师ID
        :param db_session: 数据库会话
        :return: 关联记录对象
        """
        stmt = select(EduCourseTeacher).where(
            and_(EduCourseTeacher.course_id == course_id, EduCourseTeacher.teacher_id == teacher_id)
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_by_ids(course_id: int, teacher_id: int, db_session: AsyncSession) -> EduCourseTeacher | None:
        """根据课程ID和教师ID获取关联记录（别名方法，与 get_binding 功能相同）

        :param course_id: 课程ID
        :param teacher_id: 教师ID
        :param db_session: 数据库会话
        :return: 关联记录对象
        """
        return await CourseTeacherMapper.get_binding(course_id, teacher_id, db_session)

    @staticmethod
    async def get_course_teacher_list(course_id: int, db: AsyncSession) -> tuple[Sequence[EduTeacher], int]:
        """查询课程绑定的教师列表

        :param course_id: 课程ID
        :param db: 数据库会话
        :return: (rows, total) 元组，rows为教师列表，total为总数
        """
        # 构建主查询（关联 edu_course_teacher 表和 edu_teacher 表）
        query = (
            select(EduTeacher)
            .join(
                EduCourseTeacher,
                and_(
                    EduCourseTeacher.teacher_id == EduTeacher.teacher_id,
                    EduTeacher.status != SystemConstants.Status.DELETED,
                ),
            )
            .where(EduCourseTeacher.course_id == course_id)
            .order_by(EduCourseTeacher.display_order, EduCourseTeacher.teacher_id)
            .distinct()
        )

        # 获取总数
        count_query = (
            select(func.count())
            .select_from(EduTeacher)
            .join(
                EduCourseTeacher,
                and_(
                    EduCourseTeacher.teacher_id == EduTeacher.teacher_id,
                    EduTeacher.status != SystemConstants.Status.DELETED,
                ),
            )
            .where(EduCourseTeacher.course_id == course_id)
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        result = await db.execute(query)
        rows = result.scalars().all()

        return rows, total

    @staticmethod
    async def get_bound_teacher_ids(course_id: int, db_session: AsyncSession) -> list[int]:
        """获取课程已绑定的教师ID列表

        :param course_id: 课程ID
        :param db_session: 数据库会话
        :return: 教师ID列表
        """
        stmt = select(EduCourseTeacher.teacher_id).where(EduCourseTeacher.course_id == course_id)
        result = await db_session.execute(stmt)
        return list(result.scalars().all())
