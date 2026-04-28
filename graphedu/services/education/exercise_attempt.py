"""习题作答记录管理服务模块。"""

from datetime import datetime
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.education.exercise_attempt import (
    ExerciseAttemptCreateFailedException,
    ExerciseAttemptExerciseNotFoundException,
)
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.educationv2.course_exercise import ExerciseAttemptQueryDTO, ExerciseAttemptSubmitDTO
from graphedu.common.models.orm.education import EduExerciseAttempt
from graphedu.common.models.vo.base import PageResponse
from graphedu.common.models.vo.educationv2.course_exercise import ExerciseAttemptStatisticsVO, ExerciseAttemptVO
from graphedu.mapper.education.course_exercise import CourseExerciseMapper
from graphedu.mapper.education.exercise_attempt import ExerciseAttemptMapper

logger = logging.getLogger(__name__)


def _get_user_id(current_user: CurrentUser | None) -> int | None:
    if current_user and current_user.detail and current_user.detail.user:
        return current_user.detail.user.user_id
    return None


def _convert_orm_to_vo(attempt_orm: EduExerciseAttempt) -> ExerciseAttemptVO:
    return ExerciseAttemptVO(
        attempt_id=attempt_orm.attempt_id,
        exercise_id=attempt_orm.exercise_id,
        student_id=attempt_orm.student_id,
        student_answer=attempt_orm.student_answer,
        is_correct=attempt_orm.is_correct,
        time_spent=attempt_orm.time_spent,
        attempt_time=attempt_orm.attempt_time,
    )


def _judge_answer(
    exercise_data: dict[str, Any] | list | None,
    student_answer: list[str] | str,
) -> bool | None:
    """根据题目类型评判答案。

    Args:
        exercise_data: 题目内容（JSONB），需包含 answer 字段
        student_answer: 学生提交的答案

    Returns:
        True=正确, False=错误, None=无法评判（简答题等）
    """
    if exercise_data is None:
        return None

    # 统一为 dict 处理
    question: dict[str, Any]
    if isinstance(exercise_data, list):
        # 如果是题目列表，取第一个
        question = exercise_data[0] if exercise_data else {}
    else:
        question = exercise_data

    question_type = question.get("question_type", "single")
    correct_answer = question.get("answer")

    if correct_answer is None:
        return None

    # 简答题无法自动评判
    if question_type == "essay":
        return None

    # 标准化学生答案为列表
    if isinstance(student_answer, str):
        student_set = {student_answer.strip()}
    else:
        student_set = {a.strip() for a in student_answer}

    # 标准化正确答案为集合
    if isinstance(correct_answer, bool):
        correct_set = {"正确" if correct_answer else "错误"}
    elif isinstance(correct_answer, str):
        correct_set = {correct_answer.strip()}
    elif isinstance(correct_answer, list):
        correct_set = {str(a).strip() for a in correct_answer}
    else:
        return None

    return student_set == correct_set


class ExerciseAttemptService:
    """习题作答记录管理服务类。"""

    @staticmethod
    async def submit_attempt(
        query_db: AsyncSession,
        dto: ExerciseAttemptSubmitDTO,
        current_user: CurrentUser,
    ) -> ExerciseAttemptVO:
        """学生提交作答。

        Args:
            query_db: 数据库会话
            dto: 作答提交数据
            current_user: 当前用户

        Returns:
            作答记录
        """
        # 1. 验证习题存在
        exercise = await CourseExerciseMapper.get_by_id(dto.exercise_id, query_db)
        if not exercise:
            raise ExerciseAttemptExerciseNotFoundException(exercise_id=dto.exercise_id)

        # 2. 评判答案
        is_correct = _judge_answer(exercise.exercise, dto.student_answer)

        # 3. 创建记录
        student_id = _get_user_id(current_user)
        if student_id is None:
            raise ExerciseAttemptCreateFailedException(exercise_id=dto.exercise_id, message="无法获取当前用户信息")

        try:
            attempt = EduExerciseAttempt(
                exercise_id=dto.exercise_id,
                student_id=student_id,
                student_answer=dto.student_answer,
                is_correct=is_correct,
                time_spent=dto.time_spent,
                attempt_time=datetime.now(),
            )
            await ExerciseAttemptMapper.add_attempt(attempt, query_db)
        except Exception as e:
            raise ExerciseAttemptCreateFailedException(exercise_id=dto.exercise_id) from e

        return _convert_orm_to_vo(attempt)

    @staticmethod
    async def list_attempts(
        query_db: AsyncSession,
        query_object: ExerciseAttemptQueryDTO,
    ) -> PageResponse[ExerciseAttemptVO]:
        """获取作答记录列表。

        Args:
            query_db: 数据库会话
            query_object: 查询条件

        Returns:
            分页响应
        """
        rows, total = await ExerciseAttemptMapper.get_attempt_list(query_db, query_object, is_page=True)
        item_list = [_convert_orm_to_vo(row) for row in rows]
        return PageResponse(
            rows=item_list,
            page=query_object.page or 1,
            size=query_object.size or 10,
            total=total,
        )

    @staticmethod
    async def get_attempt_detail(
        query_db: AsyncSession,
        attempt_id: int,
    ) -> ExerciseAttemptVO | None:
        """获取作答记录详情。

        Args:
            query_db: 数据库会话
            attempt_id: 作答记录 ID

        Returns:
            作答记录详情，不存在则返回 None
        """
        attempt = await ExerciseAttemptMapper.get_by_id(attempt_id, query_db)
        if not attempt:
            return None
        return _convert_orm_to_vo(attempt)

    @staticmethod
    async def get_exercise_statistics(
        query_db: AsyncSession,
        exercise_id: int,
    ) -> ExerciseAttemptStatisticsVO:
        """获取单个习题的作答统计。

        Args:
            query_db: 数据库会话
            exercise_id: 习题ID

        Returns:
            作答统计
        """
        stats = await ExerciseAttemptMapper.get_statistics_by_exercise(exercise_id, query_db)
        if stats is None:
            return ExerciseAttemptStatisticsVO(
                exercise_id=exercise_id,
                total_attempts=0,
                correct_count=0,
                correct_rate=0.0,
                avg_time_spent=None,
            )
        return ExerciseAttemptStatisticsVO(**stats)

    @staticmethod
    async def get_student_attempts_for_exercise(
        query_db: AsyncSession,
        exercise_id: int,
        student_id: int,
    ) -> list[ExerciseAttemptVO]:
        """获取学生在某道题上的所有作答记录。

        Args:
            query_db: 数据库会话
            exercise_id: 习题ID
            student_id: 学生ID

        Returns:
            作答记录列表
        """
        query_object = ExerciseAttemptQueryDTO(
            exercise_id=exercise_id,
            student_id=student_id,
            page=None,
            size=None,
        )
        rows, _ = await ExerciseAttemptMapper.get_attempt_list(query_db, query_object, is_page=False)
        return [_convert_orm_to_vo(row) for row in rows]
