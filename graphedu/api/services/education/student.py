"""学生管理 API 控制器

本模块提供学生管理相关的 REST API 接口，包括学生的增删改查、
状态管理等功能。

主要接口：
- 学生列表：分页查询学生列表，支持多条件筛选
- 学生管理：新增、修改、删除学生
- 状态管理：启用/停用学生账号
- 学生详情：查询学生详细信息
"""

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.educationv2.student import StudentCreateDTO, StudentQueryDTO, StudentUpdateDTO
from graphedu.common.models.vo.base import BatchDeleteResponse, Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.student import StudentDetailVO, StudentListVO
from graphedu.common.resource.deps import get_db
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.education.student import StudentService

student_controller = APIRouter(prefix="/education/student", dependencies=[Depends(SecurityService.get_current_user)])


# ============================================================================
# 学生列表查询
# ============================================================================
@student_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("education:student:list"))],
    response_model=ResponseType[PageResponse[StudentListVO]],
)
async def get_student_list(
    query: StudentQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取学生列表（分页）"""
    student_page_result: PageResponse[StudentListVO] = await StudentService.list_student(query_db, query)
    return ResponseUtil.success(data=student_page_result)


# ============================================================================
# 学生新增
# ============================================================================
@student_controller.post(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:student:add"))],
    response_model=ResponseType[StudentDetailVO],
)
@SystemLog(
    title="学生管理",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"current_user"},
)
async def add_student(
    student_data: StudentCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """新增学生"""
    result_vo = await StudentService.add_student(query_db, student_data, current_user)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 学生修改
# ============================================================================
@student_controller.put(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:student:edit"))],
    response_model=ResponseType[StudentDetailVO],
)
@SystemLog(title="学生管理", business_type=SysConst.BusinessType.UPDATE)
async def edit_student(
    student_data: StudentUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改学生"""
    result_vo = await StudentService.update_student(query_db, student_data, current_user)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 学生删除
# ============================================================================
@student_controller.delete(
    "/{student_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("education:student:remove"))],
    response_model=ResponseType[BatchDeleteResponse[int]],
)
@SystemLog(title="学生管理", business_type=SysConst.BusinessType.DELETE)
async def delete_student(
    student_ids: str = Path(..., pattern="^[0-9,]+$", description="学生ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """删除学生（支持批量删除，返回详细结果）"""
    student_id_list = [int(sid) for sid in student_ids.split(",") if sid]
    result = await StudentService.delete_student(query_db, student_id_list, current_user)
    return ResponseUtil.success(data=result)


# ============================================================================
# 修改学生状态
# ============================================================================
@student_controller.put(
    "/changeStatus",
    dependencies=[Depends(CheckUserInterfacePermit("education:student:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="学生管理", business_type=SysConst.BusinessType.UPDATE)
async def change_student_status(
    student_id: int = Body(..., embed=True, description="学生ID"),
    status: str = Body(..., embed=True, description="状态"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改学生状态"""
    await StudentService.change_student_status(query_db, student_id, status, current_user)
    return ResponseUtil.success()


# ============================================================================
# 获取学生详情
# ============================================================================
@student_controller.get(
    "/{student_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:student:query"))],
    response_model=ResponseType[StudentDetailVO],
)
async def get_student_detail(
    student_id: int,
    query_db: AsyncSession = Depends(get_db),
):
    """获取学生详细信息"""
    detail_result = await StudentService.get_student_detail(query_db, student_id)
    return ResponseUtil.success(data=detail_result)
