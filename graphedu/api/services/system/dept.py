"""部门管理 Controller

职责：
1. 接收 HTTP 请求
2. 调用 Service 层
3. 返回响应（VO 对象）
"""

import logging
from types import NoneType

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.systemv2.dept import (
    DeptCreateDTO,
    DeptQueryDTO,
    DeptUpdateDTO,
)
from graphedu.common.models.vo.base import Empty, ResponseType, ResponseUtil
from graphedu.common.models.vo.systemv2.dept import DeptDetailVO, DeptTreeVO
from graphedu.common.models.vo.systemv2.user import UserListVO
from graphedu.common.resource.deps import get_db
from graphedu.security.aspect.data_scope import GetDataScope
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.system.dept import DeptService

logger = logging.getLogger(__name__)

dept_controller = APIRouter(prefix="/system/dept", dependencies=[Depends(SecurityService.get_current_user)])


# ============================================================================
# 获取部门树形列表
# ============================================================================
@dept_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("system:dept:list"))],
    response_model=ResponseType[list[DeptTreeVO]],
)
async def get_system_dept_list(
    query: DeptQueryDTO = Query(..., description="查询部门的条件参数"),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope("SysDept")),
):
    """获取完整部门树形列表"""
    dept_tree = await DeptService.get_dept_tree(query_db, query, data_scope_sql)
    return ResponseUtil.success(data=dept_tree)


# ============================================================================
# 获取部门列表（异步加载模式，只返回指定父级的直接子节点）
# ============================================================================
@dept_controller.get(
    "/listLazy",
    dependencies=[Depends(CheckUserInterfacePermit("system:dept:list"))],
    response_model=ResponseType[list[DeptTreeVO]],
)
async def get_system_dept_list_lazy(
    parent: int = Query(0, description="父部门ID，0表示顶层", validation_alias="parentId"),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope("SysDept")),
):
    """获取部门列表（异步加载模式，只返回指定父级的直接子节点）- 返回 DeptTreeVO"""
    dept_list = await DeptService.get_dept_children(query_db, data_scope_sql, parent)
    return ResponseUtil.success(data=dept_list)


# ============================================================================
# 获取部门树（排除指定部门及其子部门）
# ============================================================================
@dept_controller.get(
    "/list/exclude/{dept_id}",
    dependencies=[Depends(CheckUserInterfacePermit("system:dept:list"))],
    response_model=ResponseType[list[DeptTreeVO]],
)
async def get_system_dept_exclude_tree(
    dept_id: int = Path(..., description="查询部门时要排除的部门ID"),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope("SysDept")),
):
    """获取排除指定部门及其子部门的部门树（用于编辑时选择父部门）"""
    dept_tree = await DeptService.get_dept_exclude_tree(query_db, dept_id, data_scope_sql)
    return ResponseUtil.success(data=dept_tree)


# ============================================================================
# 新增部门
# ============================================================================
@dept_controller.post(
    "", dependencies=[Depends(CheckUserInterfacePermit("system:dept:add"))], response_model=ResponseType[DeptDetailVO]
)
@SystemLog(title="部门管理", business_type=SysConst.BusinessType.INSERT)
async def add_system_dept(
    dept_data: DeptCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """新增部门"""
    result_vo = await DeptService.add_dept(query_db, dept_data, current_user)
    return ResponseUtil.success(data=result_vo, msg="新增部门成功")


# ============================================================================
# 修改部门
# ============================================================================
@dept_controller.put(
    "", dependencies=[Depends(CheckUserInterfacePermit("system:dept:edit"))], response_model=ResponseType[DeptDetailVO]
)
@SystemLog(title="部门管理", business_type=SysConst.BusinessType.UPDATE)
async def update_system_dept(
    dept_data: DeptUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope("SysDept")),
):
    """修改部门信息"""
    # 数据权限检查
    if not current_user.is_admin():
        await DeptService.check_dept_data_scope(query_db, dept_data.dept_id, data_scope_sql)

    result_vo = await DeptService.update_dept(query_db, dept_data, current_user)
    return ResponseUtil.success(data=result_vo)


# ============================================================================
# 删除部门
# ============================================================================
@dept_controller.delete(
    "/{dept_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("system:dept:remove"))],
    response_model=ResponseType[NoneType],
)
@SystemLog(title="部门管理", business_type=SysConst.BusinessType.DELETE)
async def delete_system_dept(
    dept_ids: str = Path(..., pattern="^[0-9,]+$", description="部门ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope("SysDept")),
):
    """删除部门（支持批量）"""
    dept_id_list = [int(dept_id) for dept_id in dept_ids.split(",") if dept_id]

    # 数据权限检查
    if not current_user.is_admin():
        for dept_id in dept_id_list:
            await DeptService.check_dept_data_scope(query_db, dept_id, data_scope_sql)

    await DeptService.delete_dept(query_db, dept_id_list, current_user)
    return ResponseUtil.success()


# ============================================================================
# 获取部门详细信息
# ============================================================================
@dept_controller.get(
    "/{dept_id}",
    dependencies=[Depends(CheckUserInterfacePermit("system:dept:query"))],
    response_model=ResponseType[DeptDetailVO],
)
async def get_system_dept_detail(
    dept_id: int = Path(..., description="部门ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope("SysDept")),
):
    """获取某一部门详细信息"""
    # 数据权限检查
    if not current_user.is_admin():
        await DeptService.check_dept_data_scope(query_db, dept_id, data_scope_sql)

    dept_vo = await DeptService.get_dept_detail(query_db, dept_id)
    return ResponseUtil.success(data=dept_vo)


# ============================================================================
# 获取部门用户列表
# ============================================================================
@dept_controller.get(
    "/{dept_id}/users",
    dependencies=[Depends(CheckUserInterfacePermit("system:dept:list"))],
    response_model=ResponseType[list[UserListVO]],
)
async def get_system_dept_users(
    dept_id: int = Path(..., description="部门ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope("SysDept")),
):
    """获取部门关联的用户列表"""
    # 数据权限检查
    if not current_user.is_admin():
        await DeptService.check_dept_data_scope(query_db, dept_id, data_scope_sql)

    user_list = await DeptService.get_dept_users(query_db, dept_id)
    return ResponseUtil.success(data=user_list)


# ============================================================================
# 移除用户部门关联
# ============================================================================
@dept_controller.delete(
    "/{dept_id}/users/{user_id}",
    dependencies=[Depends(CheckUserInterfacePermit("system:dept:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="部门管理", business_type=SysConst.BusinessType.UPDATE)
async def remove_user_from_dept(
    dept_id: int = Path(..., description="部门ID"),
    user_id: int = Path(..., description="用户ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope("SysDept")),
):
    """移除用户的部门关联"""
    # 数据权限检查
    if not current_user.is_admin():
        await DeptService.check_dept_data_scope(query_db, dept_id, data_scope_sql)

    await DeptService.remove_user_from_dept(query_db, dept_id, user_id, current_user)
    return ResponseUtil.success()
