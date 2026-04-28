"""课程练习管理 API 控制器。"""

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.educationv2.course_exercise import (
    CourseExerciseBatchGenerateDTO,
    CourseExerciseCreateDTO,
    CourseExerciseQueryDTO,
    CourseExerciseUpdateDTO,
)
from graphedu.common.models.vo.base import BatchDeleteResponse, Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.course_exercise import (
    CourseExerciseDetailVO,
    CourseExerciseGenerateProgressVO,
    CourseExerciseGenerateTaskVO,
    CourseExerciseListVO,
)
from graphedu.common.resource.deps import get_db
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.education.course_exercise import CourseExerciseService

course_exercise_controller = APIRouter(
    prefix="/education/course-exercise",
    dependencies=[Depends(SecurityService.get_current_user)],
)


@course_exercise_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("education:course-exercise:list"))],
    response_model=ResponseType[PageResponse[CourseExerciseListVO]],
)
async def get_course_exercise_list(
    query: CourseExerciseQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取课程练习列表（分页）。"""
    result = await CourseExerciseService.list_course_exercise(query_db, query)
    return ResponseUtil.success(data=result)


@course_exercise_controller.post(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:course-exercise:add"))],
    response_model=ResponseType[CourseExerciseDetailVO],
)
@SystemLog(title="课程练习管理", business_type=SysConst.BusinessType.INSERT)
async def add_course_exercise(
    exercise_data: CourseExerciseCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """新增课程练习。"""
    result = await CourseExerciseService.add_course_exercise(query_db, exercise_data, current_user)
    return ResponseUtil.success(data=result)


@course_exercise_controller.post(
    "/batch-generate",
    dependencies=[Depends(CheckUserInterfacePermit("education:course-exercise:add"))],
    response_model=ResponseType[CourseExerciseGenerateTaskVO],
)
@SystemLog(title="课程练习管理", business_type=SysConst.BusinessType.INSERT)
async def batch_generate_exercises(
    dto: CourseExerciseBatchGenerateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """教师端批量生成课程练习（异步）。"""
    result = await CourseExerciseService.submit_generate_task(query_db, dto, current_user)
    return ResponseUtil.success(data=result)


@course_exercise_controller.put(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:course-exercise:edit"))],
    response_model=ResponseType[CourseExerciseDetailVO],
)
@SystemLog(title="课程练习管理", business_type=SysConst.BusinessType.UPDATE)
async def update_course_exercise(
    exercise_data: CourseExerciseUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改课程练习。"""
    result = await CourseExerciseService.update_course_exercise(query_db, exercise_data, current_user)
    return ResponseUtil.success(data=result)


@course_exercise_controller.put(
    "/changeStatus",
    dependencies=[Depends(CheckUserInterfacePermit("education:course-exercise:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="课程练习管理", business_type=SysConst.BusinessType.UPDATE)
async def change_exercise_status(
    exercise_id: int = Body(..., embed=True, alias="exerciseId", description="练习ID"),
    status: str = Body(..., embed=True, description="状态"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改课程练习状态。"""
    await CourseExerciseService.change_exercise_status(query_db, exercise_id, status, current_user)
    return ResponseUtil.success()


@course_exercise_controller.get(
    "/generate-progress/{task_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:course-exercise:query"))],
    response_model=ResponseType[CourseExerciseGenerateProgressVO],
)
async def get_generate_progress(
    task_id: str = Path(..., description="异步任务 ID"),
):
    """查询 AI 出题异步任务进度。"""
    result = await CourseExerciseService.get_generate_progress(task_id)
    return ResponseUtil.success(data=result)


@course_exercise_controller.get(
    "/{exercise_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:course-exercise:query"))],
    response_model=ResponseType[CourseExerciseDetailVO],
)
async def get_course_exercise_detail(
    exercise_id: int = Path(..., description="练习ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取课程练习详情。"""
    from graphedu.common.exceptions.services.education.course_exercise import CourseExerciseNotFoundException

    result = await CourseExerciseService.get_course_exercise_detail(query_db, exercise_id)
    if result is None:
        raise CourseExerciseNotFoundException(exercise_id=exercise_id)
    return ResponseUtil.success(data=result)


@course_exercise_controller.delete(
    "/{exercise_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("education:course-exercise:remove"))],
    response_model=ResponseType[BatchDeleteResponse[int]],
)
@SystemLog(title="课程练习管理", business_type=SysConst.BusinessType.DELETE)
async def delete_course_exercise(
    exercise_ids: str = Path(..., pattern="^[0-9,]+$", description="练习ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """删除课程练习（支持批量）。"""
    exercise_id_list = [int(eid) for eid in exercise_ids.split(",") if eid]
    result = await CourseExerciseService.delete_course_exercise(query_db, exercise_id_list, current_user)
    return ResponseUtil.success(data=result)
