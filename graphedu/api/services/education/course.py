"""课程管理 API 控制器

本模块提供课程管理相关的 REST API 接口，包括课程的增删改查、
状态管理等功能。

主要接口：
- 课程列表：分页查询课程列表，支持多条件筛选
- 课程管理：新增、修改、删除课程
- 状态管理：启用/停用课程
- 课程详情：查询课程详细信息
"""

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.educationv2.course import CourseCreateDTO, CourseQueryDTO, CourseUpdateDTO
from graphedu.common.models.vo.base import BatchDeleteResponse, Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.course import CourseDetailVO, CourseListVO
from graphedu.common.models.vo.educationv2.teacher import TeacherListVO
from graphedu.common.resource import AioS3Client
from graphedu.common.resource.deps import get_db, get_s3
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.education.course import CourseService

course_controller = APIRouter(prefix="/education/course", dependencies=[Depends(SecurityService.get_current_user)])


# ============================================================================
# 课程列表查询
# ============================================================================
@course_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:list"))],
    response_model=ResponseType[PageResponse[CourseListVO]],
)
async def get_course_list(
    query: CourseQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
):
    """获取课程列表（分页）"""
    course_page_result: PageResponse[CourseListVO] = await CourseService.list_course(query_db, query, s3_client)
    return ResponseUtil.success(data=course_page_result)


# ============================================================================
# 教师自己的课程列表
# ============================================================================
@course_controller.get(
    "/my-courses",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:list"))],
    response_model=ResponseType[PageResponse[CourseListVO]],
)
async def get_my_courses(
    query: CourseQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    s3_client: AioS3Client = Depends(get_s3),
):
    """获取当前登录教师的课程列表（分页）"""
    result: PageResponse[CourseListVO] = await CourseService.list_my_courses(query_db, query, current_user, s3_client)
    return ResponseUtil.success(data=result)


# ============================================================================
# 课程新增
# ============================================================================
@course_controller.post(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:add"))],
    response_model=ResponseType[CourseDetailVO],
)
@SystemLog(
    title="课程管理",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"current_user"},
)
async def add_course(
    course_data: CourseCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    s3_client: AioS3Client = Depends(get_s3),
):
    """新增课程

    如果提供了 teacher_ids，会在同一事务中完成教师绑定。
    """
    result_vo = await CourseService.add_course(query_db, course_data, current_user, s3_client)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 课程修改
# ============================================================================
@course_controller.put(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:edit"))],
    response_model=ResponseType[CourseDetailVO],
)
@SystemLog(title="课程管理", business_type=SysConst.BusinessType.UPDATE)
async def edit_course(
    course_data: CourseUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    s3_client: AioS3Client = Depends(get_s3),
):
    """修改课程"""
    result_vo = await CourseService.update_course(query_db, course_data, current_user, s3_client)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 课程删除
# ============================================================================
@course_controller.delete(
    "/{course_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:remove"))],
    response_model=ResponseType[BatchDeleteResponse[int]],
)
@SystemLog(title="课程管理", business_type=SysConst.BusinessType.DELETE)
async def delete_course(
    course_ids: str = Path(..., pattern="^[0-9,]+$", description="课程ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """删除课程（支持批量删除，返回详细结果）"""
    course_id_list = [int(cid) for cid in course_ids.split(",") if cid]
    result = await CourseService.delete_course(query_db, course_id_list, current_user)
    return ResponseUtil.success(data=result)


# ============================================================================
# 修改课程状态
# ============================================================================
@course_controller.put(
    "/changeStatus",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="课程管理", business_type=SysConst.BusinessType.UPDATE)
async def change_course_status(
    course_id: int = Body(..., embed=True, alias="courseId", description="课程ID"),
    status: str = Body(..., embed=True, description="状态"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改课程状态"""
    await CourseService.change_course_status(query_db, course_id, status, current_user)
    return ResponseUtil.success()


# ============================================================================
# 获取课程详情
# ============================================================================
@course_controller.get(
    "/{course_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:query"))],
    response_model=ResponseType[CourseDetailVO],
)
async def get_course_detail(
    course_id: int,
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
):
    """获取课程详细信息"""
    from graphedu.common.exceptions.services.education.course import CourseNotFoundException

    detail_result = await CourseService.get_course_detail(query_db, course_id, s3_client)
    if detail_result is None:
        raise CourseNotFoundException(course_id=course_id)
    return ResponseUtil.success(data=detail_result)


# ============================================================================
# 绑定教师
# ============================================================================
@course_controller.post(
    "/{course_id}/teachers/bind",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="课程管理", business_type=SysConst.BusinessType.UPDATE)
async def bind_teachers(
    course_id: int,
    teacher_ids: list[int] = Body(..., description="教师ID列表"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """为课程绑定教师（管理员操作）"""
    await CourseService.bind_teachers(query_db, course_id, teacher_ids, current_user)
    return ResponseUtil.success()


# ============================================================================
# 解绑教师
# ============================================================================
@course_controller.delete(
    "/{course_id}/teachers/unbind",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="课程管理", business_type=SysConst.BusinessType.UPDATE)
async def unbind_teachers(
    course_id: int,
    teacher_ids: list[int] = Body(..., description="教师ID列表"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """解绑课程的教师（管理员操作）"""
    await CourseService.unbind_teachers(query_db, course_id, teacher_ids, current_user)
    return ResponseUtil.success()


# ============================================================================
# 获取课程绑定的教师列表
# ============================================================================
@course_controller.get(
    "/{course_id}/teachers",
    dependencies=[Depends(CheckUserInterfacePermit("education:course:query"))],
    response_model=ResponseType[list[TeacherListVO]],
)
async def get_course_teachers(
    course_id: int,
    query_db: AsyncSession = Depends(get_db),
):
    """获取课程绑定的教师列表"""
    teachers = await CourseService.get_course_teachers(query_db, course_id)
    return ResponseUtil.success(data=teachers)


# ============================================================================
# 检查课程代码是否存在
# ============================================================================
@course_controller.get(
    "/check-code-exists",
    dependencies=[Depends(SecurityService.get_current_user)],
    response_model=ResponseType[bool],
)
async def check_course_code_exists(
    course_code: str = Query(..., description="课程代码"),
    exclude_course_id: int | None = Query(None, description="排除的课程ID（用于编辑时校验）"),
    query_db: AsyncSession = Depends(get_db),
):
    """检查课程代码是否存在

    用于前端表单的实时验证，防止提交重复的课程代码
    """
    from graphedu.services.education.course import _check_course_code_exists, _check_course_code_unique_for_update

    if exclude_course_id:
        # 编辑模式：排除当前课程
        exists = await _check_course_code_unique_for_update(exclude_course_id, course_code, query_db)
    else:
        # 新增模式：检查是否存在
        exists = await _check_course_code_exists(course_code, query_db)

    return ResponseUtil.success(data=exists)
