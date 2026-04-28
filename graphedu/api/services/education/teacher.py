"""教师管理 API 控制器

本模块提供教师管理相关的 REST API 接口，包括教师的增删改查、
状态管理等功能。

主要接口：
- 教师列表：分页查询教师列表，支持多条件筛选
- 教师管理：新增、修改、删除教师
- 状态管理：启用/停用教师账号
- 教师详情：查询教师详细信息
"""

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.educationv2.teacher import TeacherCreateDTO, TeacherQueryDTO, TeacherUpdateDTO
from graphedu.common.models.vo.base import BatchDeleteResponse, Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.educationv2.teacher import TeacherDetailVO, TeacherListVO
from graphedu.common.resource.deps import get_db
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.education.teacher import TeacherService

teacher_controller = APIRouter(prefix="/education/teacher", dependencies=[Depends(SecurityService.get_current_user)])


# ============================================================================
# 教师列表查询
# ============================================================================
@teacher_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("education:teacher:list"))],
    response_model=ResponseType[PageResponse[TeacherListVO]],
)
async def get_teacher_list(
    query: TeacherQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取教师列表（分页）"""
    teacher_page_result: PageResponse[TeacherListVO] = await TeacherService.list_teacher(query_db, query)
    return ResponseUtil.success(data=teacher_page_result)


# ============================================================================
# 教师新增
# ============================================================================
@teacher_controller.post(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:teacher:add"))],
    response_model=ResponseType[TeacherDetailVO],
)
@SystemLog(
    title="教师管理",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"current_user"},
)
async def add_teacher(
    teacher_data: TeacherCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """新增教师"""
    result_vo = await TeacherService.add_teacher(query_db, teacher_data, current_user)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 教师修改
# ============================================================================
@teacher_controller.put(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("education:teacher:edit"))],
    response_model=ResponseType[TeacherDetailVO],
)
@SystemLog(title="教师管理", business_type=SysConst.BusinessType.UPDATE)
async def edit_teacher(
    teacher_data: TeacherUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改教师"""
    result_vo = await TeacherService.update_teacher(query_db, teacher_data, current_user)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 教师删除
# ============================================================================
@teacher_controller.delete(
    "/{teacher_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("education:teacher:remove"))],
    response_model=ResponseType[BatchDeleteResponse[int]],
)
@SystemLog(title="教师管理", business_type=SysConst.BusinessType.DELETE)
async def delete_teacher(
    teacher_ids: str = Path(..., pattern="^[0-9,]+$", description="教师ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """删除教师（支持批量删除，返回详细结果）"""
    teacher_id_list = [int(tid) for tid in teacher_ids.split(",") if tid]
    result = await TeacherService.delete_teacher(query_db, teacher_id_list, current_user)
    return ResponseUtil.success(data=result)


# ============================================================================
# 修改教师状态
# ============================================================================
@teacher_controller.put(
    "/changeStatus",
    dependencies=[Depends(CheckUserInterfacePermit("education:teacher:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="教师管理", business_type=SysConst.BusinessType.UPDATE)
async def change_teacher_status(
    teacher_id: int = Body(..., embed=True, description="教师ID"),
    status: str = Body(..., embed=True, description="状态"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改教师状态"""
    await TeacherService.change_teacher_status(query_db, teacher_id, status, current_user)
    return ResponseUtil.success()


# ============================================================================
# 获取教师详情
# ============================================================================
@teacher_controller.get(
    "/{teacher_id}",
    dependencies=[Depends(CheckUserInterfacePermit("education:teacher:query"))],
    response_model=ResponseType[TeacherDetailVO],
)
async def get_teacher_detail(
    teacher_id: int,
    query_db: AsyncSession = Depends(get_db),
):
    """获取教师详细信息"""
    detail_result = await TeacherService.get_teacher_detail(query_db, teacher_id)
    return ResponseUtil.success(data=detail_result)
