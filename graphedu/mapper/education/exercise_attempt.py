"""习题作答记录 Mapper 层。"""

from collections.abc import Sequence

import sqlalchemy
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.dto.educationv2.course_exercise import ExerciseAttemptQueryDTO
from graphedu.common.models.orm.education import EduCourseExercise, EduExerciseAttempt


class ExerciseAttemptMapper:
    """习题作答记录数据访问层。"""

    @staticmethod
    async def add_attempt(attempt: EduExerciseAttempt, db_session: AsyncSession) -> EduExerciseAttempt:
        """添加作答记录。

        Args:
            attempt: 作答记录信息
            db_session: 数据库会话

        Returns:
            添加后的作答记录
        """
        db_session.add(attempt)
        await db_session.flush()
        return attempt

    @staticmethod
    async def get_by_id(attempt_id: int, db_session: AsyncSession) -> EduExerciseAttempt | None:
        """根据 ID 获取作答记录。

        Args:
            attempt_id: 作答记录 ID
            db_session: 数据库会话

        Returns:
            作答记录，不存在则返回 None
        """
        stmt = select(EduExerciseAttempt).where(EduExerciseAttempt.attempt_id == attempt_id)
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_attempt_list(
        db: AsyncSession, query_object: ExerciseAttemptQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[EduExerciseAttempt], int]:
        """获取作答记录列表。

        Args:
            db: 数据库会话
            query_object: 查询条件
            is_page: 是否分页

        Returns:
            (作答记录列表, 总数)
        """
        base_conditions: list = []

        if query_object.exercise_id is not None:
            base_conditions.append(EduExerciseAttempt.exercise_id == query_object.exercise_id)
        if query_object.student_id is not None:
            base_conditions.append(EduExerciseAttempt.student_id == query_object.student_id)
        if query_object.is_correct is not None:
            base_conditions.append(EduExerciseAttempt.is_correct == query_object.is_correct)

        # 通过课程ID间接筛选：先找该课程下的习题，再筛选作答记录
        if query_object.course_id is not None:
            exercise_subquery = select(EduCourseExercise.exercise_id).where(
                EduCourseExercise.course_id == query_object.course_id,
                EduCourseExercise.status != "2",
            )
            base_conditions.append(EduExerciseAttempt.exercise_id.in_(exercise_subquery))

        query = (
            select(EduExerciseAttempt).where(and_(*base_conditions)).order_by(EduExerciseAttempt.attempt_time.desc())
        )

        count_query = select(func.count()).select_from(EduExerciseAttempt).where(and_(*base_conditions))
        total = (await db.execute(count_query)).scalar() or 0

        if is_page and query_object.page and query_object.size:
            offset = (query_object.page - 1) * query_object.size
            query = query.offset(offset).limit(query_object.size)

        rows = (await db.execute(query)).scalars().all()
        return rows, total

    @staticmethod
    async def get_statistics_by_exercise(exercise_id: int, db_session: AsyncSession) -> dict | None:
        """获取单个习题的作答统计。

        Args:
            exercise_id: 习题ID
            db_session: 数据库会话

        Returns:
            统计信息字典
        """
        stmt = select(
            func.count(EduExerciseAttempt.attempt_id).label("total_attempts"),
            func.count(EduExerciseAttempt.is_correct).label("graded_count"),
            func.sum(func.cast(EduExerciseAttempt.is_correct, sqlalchemy.Integer)).label("correct_count"),
            func.avg(func.cast(EduExerciseAttempt.time_spent, sqlalchemy.Float)).label("avg_time_spent"),
        ).where(EduExerciseAttempt.exercise_id == exercise_id)

        result = (await db_session.execute(stmt)).first()
        if result is None or result.total_attempts == 0:
            return None

        graded = result.graded_count or 0
        correct = result.correct_count or 0
        correct_rate = (correct / graded * 100) if graded > 0 else 0.0

        return {
            "exercise_id": exercise_id,
            "total_attempts": result.total_attempts,
            "correct_count": correct,
            "correct_rate": round(correct_rate, 1),
            "avg_time_spent": round(result.avg_time_spent, 1) if result.avg_time_spent else None,
        }
