"""课程练习 Mapper 层。"""

from collections.abc import Sequence
from datetime import datetime, time

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.educationv2.course_exercise import CourseExerciseQueryDTO
from graphedu.common.models.orm.education import EduCourseExercise


class CourseExerciseMapper:
    """课程练习数据访问层。"""

    @staticmethod
    async def add_course_exercise(exercise_info: EduCourseExercise, db_session: AsyncSession) -> EduCourseExercise:
        """添加课程练习。

        Args:
            exercise_info: 练习信息
            db_session: 数据库会话

        Returns:
            添加后的练习信息
        """
        db_session.add(exercise_info)
        await db_session.flush()
        return exercise_info

    @staticmethod
    async def get_by_id(exercise_id: int, db_session: AsyncSession) -> EduCourseExercise | None:
        """根据 ID 获取课程练习。

        Args:
            exercise_id: 练习 ID
            db_session: 数据库会话

        Returns:
            练习信息，不存在则返回 None
        """
        stmt = select(EduCourseExercise).where(
            EduCourseExercise.exercise_id == exercise_id,
            EduCourseExercise.status != SystemConstants.Status.DELETED,
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_exercise_list(
        db: AsyncSession, query_object: CourseExerciseQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[EduCourseExercise], int]:
        """获取课程练习列表。

        Args:
            db: 数据库会话
            query_object: 查询条件
            is_page: 是否分页

        Returns:
            (练习列表, 总数)
        """
        base_conditions = [EduCourseExercise.status != SystemConstants.Status.DELETED]

        if query_object.exercise_id is not None:
            base_conditions.append(EduCourseExercise.exercise_id == query_object.exercise_id)
        if query_object.course_id is not None:
            base_conditions.append(EduCourseExercise.course_id == query_object.course_id)
        if query_object.chapter_id is not None:
            base_conditions.append(EduCourseExercise.chapter_id == query_object.chapter_id)
        if query_object.source:
            base_conditions.append(EduCourseExercise.source.like(f"%{query_object.source}%"))
        if query_object.status:
            base_conditions.append(EduCourseExercise.status == query_object.status)
        if query_object.begin_time and query_object.end_time:
            base_conditions.append(
                EduCourseExercise.create_time.between(
                    datetime.combine(query_object.begin_time, time(0, 0, 0)),
                    datetime.combine(query_object.end_time, time(23, 59, 59)),
                )
            )

        query = select(EduCourseExercise).where(and_(*base_conditions)).order_by(EduCourseExercise.exercise_id.desc())

        count_query = select(func.count()).select_from(EduCourseExercise).where(and_(*base_conditions))
        total = (await db.execute(count_query)).scalar() or 0

        if is_page and query_object.page and query_object.size:
            offset = (query_object.page - 1) * query_object.size
            query = query.offset(offset).limit(query_object.size)

        rows = (await db.execute(query)).scalars().all()
        return rows, total

    @staticmethod
    async def update(exercise_info: EduCourseExercise, query_db: AsyncSession) -> None:
        """更新课程练习。

        Args:
            exercise_info: 练习信息
            query_db: 数据库会话
        """
        await query_db.merge(exercise_info)
        await query_db.flush()

    @staticmethod
    async def batch_add_course_exercises(
        exercises: list[EduCourseExercise], db_session: AsyncSession
    ) -> list[EduCourseExercise]:
        """批量添加课程练习。"""
        db_session.add_all(exercises)
        await db_session.flush()
        return exercises
