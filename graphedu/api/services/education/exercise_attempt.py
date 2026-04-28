"""习题作答记录管理 API 控制器。"""

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.educationv2.course_exercise import ExerciseAttemptQueryDTO, ExerciseAttemptSubmitDTO
from graphedu.common.models.vo.base import PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.course_exercise import ExerciseAttemptStatisticsVO, ExerciseAttemptVO
from graphedu.common.resource.deps import get_db
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.auth import SecurityService
from graphedu.services.education.exercise_attempt import ExerciseAttemptService

exercise_attempt_controller = APIRouter(
    prefix="/education/exercise-attempt",
    dependencies=[Depends(SecurityService.get_current_user)],
)


@exercise_attempt_controller.post(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:exercise-attempt:add"))],
    response_model=ResponseType[ExerciseAttemptVO],
)
async def submit_exercise_attempt(
    dto: ExerciseAttemptSubmitDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """学生提交习题作答。"""
    result = await ExerciseAttemptService.submit_attempt(query_db, dto, current_user)
    return ResponseUtil.success(data=result)


@exercise_attempt_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("education:exercise-attempt:list"))],
    response_model=ResponseType[PageResponse[ExerciseAttemptVO]],
)
async def get_exercise_attempt_list(
    query: ExerciseAttemptQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取作答记录列表（分页）。"""
    result = await ExerciseAttemptService.list_attempts(query_db, query)
    return ResponseUtil.success(data=result)


@exercise_attempt_controller.get(
    "/statistics/{exercise_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:exercise-attempt:list"))],
    response_model=ResponseType[ExerciseAttemptStatisticsVO],
)
async def get_exercise_statistics(
    exercise_id: int = Path(..., description="习题ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取习题的作答统计。"""
    result = await ExerciseAttemptService.get_exercise_statistics(query_db, exercise_id)
    return ResponseUtil.success(data=result)


@exercise_attempt_controller.get(
    "/{attempt_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:exercise-attempt:query"))],
    response_model=ResponseType[ExerciseAttemptVO],
)
async def get_exercise_attempt_detail(
    attempt_id: int = Path(..., description="作答记录ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取作答记录详情。"""
    from graphedu.common.exceptions.services.education.exercise_attempt import ExerciseAttemptNotFoundException

    result = await ExerciseAttemptService.get_attempt_detail(query_db, attempt_id)
    if result is None:
        raise ExerciseAttemptNotFoundException(attempt_id=attempt_id)
    return ResponseUtil.success(data=result)


@exercise_attempt_controller.get(
    "/student/{exercise_id}/{student_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:exercise-attempt:list"))],
    response_model=ResponseType[list[ExerciseAttemptVO]],
)
async def get_student_attempts_for_exercise(
    exercise_id: int = Path(..., description="习题ID"),
    student_id: int = Path(..., description="学生ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取学生在某道题上的所有作答记录。"""
    result = await ExerciseAttemptService.get_student_attempts_for_exercise(query_db, exercise_id, student_id)
    return ResponseUtil.success(data=result)
