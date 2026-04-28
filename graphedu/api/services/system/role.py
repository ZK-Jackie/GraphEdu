"""角色管理 Controller

职责：
1. 接收 DTO 请求
2. 返回 VO 响应
3. 权限验证、日志记录
"""

import logging

from fastapi import APIRouter, Body, Depends, Path, Query
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.systemv2.role import (
    RoleCreateDTO,
    RoleDatascopeChangeDTO,
    RoleQueryDTO,
    RoleStatusChangeDTO,
    RoleUpdateDTO,
    RoleUserQueryDTO,
)
from graphedu.common.models.vo import RoleDetailVO, RoleListVO, UserListVO
from graphedu.common.models.vo.base import Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.systemv2.role import RoleDeptVO
from graphedu.common.resource.deps import get_db, get_redis
from graphedu.security.aspect.data_scope import GetDataScope
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.system.role import RoleService

logger = logging.getLogger(__name__)

role_controller = APIRouter(prefix="/system/role", dependencies=[Depends(SecurityService.get_current_user)])


# ============================================================================
# 获取角色列表（分页）
# ============================================================================
@role_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("system:role:list"))],
    response_model=ResponseType[PageResponse[RoleListVO]],
)
async def get_system_role_list(
    page_query: RoleQueryDTO = Depends(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取角色列表（支持分页）- 返回 RoleListVO"""
    # 如果有分页参数则分页，否则返回全部
    result = await RoleService.get_role_list(query_db, page_query)
    logger.info("获取角色分页列表成功")
    # 类型断言：当有分页参数时，返回 PageResponse
    return ResponseUtil.success(data=result)


# ============================================================================
# 新增角色
# ============================================================================
@role_controller.post(
    "", dependencies=[Depends(CheckUserInterfacePermit("system:role:add"))], response_model=ResponseType[RoleDetailVO]
)
@SystemLog(title="角色管理", business_type=SysConst.BusinessType.INSERT)
async def add_system_role(
    role_data: RoleCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """新增角色 - 返回 RoleDetailVO"""
    result = await RoleService.add_role(query_db, role_data, current_user)
    logger.info(f"新增角色 {role_data.role_name} 成功")

    return ResponseUtil.success(data=result)


# ============================================================================
# 修改角色
# ============================================================================
@role_controller.put(
    "", dependencies=[Depends(CheckUserInterfacePermit("system:role:edit"))], response_model=ResponseType[RoleDetailVO]
)
@SystemLog(title="角色管理", business_type=SysConst.BusinessType.UPDATE)
async def update_system_role(
    role_data: RoleUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改角色信息 - 返回 RoleDetailVO"""
    result = await RoleService.update_role(query_db, role_data, current_user, redis_session)
    logger.info(f"修改角色ID {role_data.role_id} 成功")

    return ResponseUtil.success(data=result)


# ============================================================================
# 修改角色状态
# ============================================================================
@role_controller.put(
    "/status",
    dependencies=[Depends(CheckUserInterfacePermit("system:role:edit"))],
    response_model=ResponseType[RoleDetailVO],
)
@SystemLog(title="角色管理", business_type=SysConst.BusinessType.UPDATE)
async def change_system_role_status(
    status_data: RoleStatusChangeDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改角色状态 - 返回 RoleDetailVO"""
    result = await RoleService.change_role_status(query_db, status_data.role_id, status_data.status, current_user)
    logger.info(f"修改角色ID {status_data.role_id} 状态为 {status_data.status}")

    return ResponseUtil.success(data=result, msg="修改角色状态成功")


# ============================================================================
# 修改角色数据权限范围
# ============================================================================
@role_controller.put(
    "/dataScope",
    dependencies=[Depends(CheckUserInterfacePermit("system:role:edit"))],
    response_model=ResponseType[RoleDetailVO],
)
@SystemLog(title="角色管理", business_type=SysConst.BusinessType.GRANT)
async def update_system_role_data_scope(
    scope_data: RoleDatascopeChangeDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope("SysRole")),
):
    """修改角色数据权限范围 - 返回 RoleDetailVO"""
    # 数据权限检查
    if not current_user.is_admin():
        await RoleService.check_role_data_scope(query_db, scope_data.role_id, data_scope_sql)

    result = await RoleService.update_role_data_scope(query_db, scope_data, current_user)

    return ResponseUtil.success(data=result, msg="修改数据权限成功")


# ============================================================================
# 删除角色
# ============================================================================
@role_controller.delete(
    "/{role_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("system:role:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="角色管理", business_type=SysConst.BusinessType.DELETE)
async def delete_system_role(
    role_ids: str = Path(..., pattern="^[0-9,]+$", description="角色ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """删除角色（支持批量）"""
    role_id_list = [int(role_id) for role_id in role_ids.split(",") if role_id]

    await RoleService.delete_role(query_db, role_id_list, current_user)
    logger.info(f"删除角色ID {role_ids} 成功")

    return ResponseUtil.success()


# ============================================================================
# 获取角色详细信息
# ============================================================================
@role_controller.get(
    "/{role_id}",
    dependencies=[Depends(CheckUserInterfacePermit("system:role:query"))],
    response_model=ResponseType[RoleDetailVO],
)
async def get_system_role_detail(role_id: int = Path(description="角色ID"), query_db: AsyncSession = Depends(get_db)):
    """获取角色详细信息（含功能权限）- 返回 RoleDetailVO"""
    role = await RoleService.get_role_detail(query_db, role_id)
    if not role:
        return ResponseUtil.fail(msg=f"角色ID {role_id} 不存在")

    logger.info(f"获取角色ID {role_id} 的详细信息成功")

    return ResponseUtil.success(data=role)


# ============================================================================
# 获取角色的部门树（用于数据权限配置）
# ============================================================================
@role_controller.get(
    "/deptTree/{role_id}",
    dependencies=[Depends(CheckUserInterfacePermit("system:role:query"))],
    response_model=ResponseType[RoleDeptVO],
)
async def get_system_role_dept(role_id: int = Path(description="角色ID"), query_db: AsyncSession = Depends(get_db)):
    """获取角色的部门 id（用于数据权限配置）"""
    # 自己去 dept 接口获取部门树
    # dept_tree = await DeptService.get_dept_tree(query_db, None, data_scope_sql)

    # 获取角色已分配的部门ID列表
    role_dept_ids = await RoleService.get_role_dept_ids(query_db, role_id)

    logger.info(f"获取角色ID {role_id} 的部门树成功")

    return ResponseUtil.success(data=RoleDeptVO(checked_ids=role_dept_ids))


# ============================================================================
# 获取角色已分配的用户列表
# ============================================================================
@role_controller.get(
    "/authUser/allocatedList",
    dependencies=[Depends(CheckUserInterfacePermit("system:role:list"))],
    response_model=ResponseType[PageResponse[UserListVO]],
)
async def get_system_role_allocated_user_list(
    query_object: RoleUserQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope("SysUser")),
):
    """获取角色关联的用户列表（分页）"""
    result = await RoleService.get_role_allocated_user_list(query_db, query_object, data_scope_sql)

    logger.info(f"获取角色ID {query_object.role_id} 已分配用户列表成功")

    return ResponseUtil.success(data=result)


# ============================================================================
# 获取角色未分配的用户列表
# ============================================================================
@role_controller.get(
    "/authUser/unallocatedList",
    dependencies=[Depends(CheckUserInterfacePermit("system:role:list"))],
    response_model=ResponseType[PageResponse[UserListVO]],
)
async def get_system_role_unallocated_user_list(
    query_object: RoleUserQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
    data_scope_sql: str = Depends(GetDataScope("SysUser")),
):
    """获取角色未分配的用户列表（分页）"""
    result = await RoleService.get_role_unallocated_user_list(query_db, query_object, data_scope_sql)

    logger.info(f"获取角色ID {query_object.role_id} 未分配用户列表成功")

    return ResponseUtil.success(data=result)


# ============================================================================
# 批量授权用户到角色
# ============================================================================
@role_controller.put(
    "/authUser/grant",
    dependencies=[Depends(CheckUserInterfacePermit("system:role:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="角色管理", business_type=SysConst.BusinessType.GRANT)
async def add_system_role_users(
    role_id: int = Query(..., description="角色ID"),
    user_ids: str = Query(..., description="用户ID列表，逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
    data_scope_sql: str = Depends(GetDataScope("SysRole")),
):
    """批量授权用户到角色"""
    # 数据权限检查
    if not current_user.is_admin():
        await RoleService.check_role_data_scope(query_db, role_id, data_scope_sql)

    user_id_list = [int(uid) for uid in user_ids.split(",") if uid]

    await RoleService.add_role_users(query_db, role_id, user_id_list, current_user)
    logger.info(f"批量授权用户到角色ID {role_id} 成功")

    return ResponseUtil.success()


# ============================================================================
# 取消单个用户授权
# ============================================================================
@role_controller.put(
    "/authUser/revoke",
    dependencies=[Depends(CheckUserInterfacePermit("system:role:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="角色管理", business_type=SysConst.BusinessType.GRANT)
async def cancel_system_role_user(
    role_id: int = Query(..., description="角色ID"),
    user_id: int = Query(..., description="用户ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """取消单个用户的角色授权"""
    await RoleService.remove_role_user(query_db, role_id, user_id, current_user)
    logger.info(f"取消用户ID {user_id} 的角色ID {role_id} 授权成功")

    return ResponseUtil.success(msg="取消授权成功")


# ============================================================================
# 批量取消用户授权
# ============================================================================
@role_controller.put(
    "/authUser/revokeAll",
    dependencies=[Depends(CheckUserInterfacePermit("system:role:edit"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="角色管理", business_type=SysConst.BusinessType.GRANT)
async def batch_cancel_system_role_users(
    role_id: int = Query(..., description="角色ID"),
    user_ids: str = Query(..., description="用户ID列表，逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """批量取消用户的角色授权"""
    user_id_list = [int(uid) for uid in user_ids.split(",") if uid]

    await RoleService.remove_role_users(query_db, role_id, user_id_list, current_user)
    logger.info(f"批量取消角色ID {role_id} 的用户授权成功")

    return ResponseUtil.success(msg="批量取消授权成功")
