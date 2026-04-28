"""功能权限管理 Controller

职责：
1. 接收 DTO 请求
2. 返回 VO 响应
3. 权限验证、日志记录
"""

from fastapi import APIRouter, Body, Depends, Path, Query
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.systemv2.function import (
    FunctionCreateDTO,
    FunctionQueryDTO,
    FunctionUpdateDTO,
)
from graphedu.common.models.vo import FunctionDetailVO, FunctionTreeVO
from graphedu.common.models.vo.base import Empty, ResponseType, ResponseUtil
from graphedu.common.models.vo.systemv2.function import FunctionTreeBriefVO, RoleFunctionTreeVO
from graphedu.common.resource.deps import get_db, get_redis
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.system.function import FunctionService

function_controller = APIRouter(prefix="/system/function", dependencies=[Depends(SecurityService.get_current_user)])


# ============================================================================
# 获取功能树（用于下拉选择）
# ============================================================================
@function_controller.get(
    "/treeselect",
    dependencies=[Depends(CheckUserInterfacePermit("system:function:list"))],
    response_model=ResponseType[list[FunctionTreeBriefVO]],
)
async def get_system_function_treeselect(
    parent_id: int = Query(0, description="父功能ID，0表示根节点"), query_db: AsyncSession = Depends(get_db)
):
    """获取功能树（用于下拉选择）- 返回 FunctionTreeBriefVO"""
    function_tree = await FunctionService.get_function_tree_for_select(query_db, parent_id)
    return ResponseUtil.success(data=function_tree)


# ============================================================================
# 获取角色功能树（用于分配权限）
# ============================================================================
@function_controller.get(
    "/roleFunctionTreeselect/{role_id}",
    dependencies=[Depends(CheckUserInterfacePermit("system:function:list"))],
    response_model=ResponseType[RoleFunctionTreeVO],
)
async def get_system_role_function_tree(
    role_id: int = Path(..., description="角色ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取角色功能树（用于角色分配权限）"""
    role_function_tree = await FunctionService.get_role_function_tree(query_db, current_user, role_id)
    return ResponseUtil.success(data=role_function_tree)


# ============================================================================
# 功能列表查询
# ============================================================================
@function_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("system:function:list"))],
    response_model=ResponseType[list[FunctionTreeVO]],
)
async def get_system_function_list(query: FunctionQueryDTO = Query(), query_db: AsyncSession = Depends(get_db)):
    """获取功能列表（树形结构）- 返回 FunctionTreeVO"""
    function_tree = await FunctionService.get_function_tree(query_db, query)
    return ResponseUtil.success(data=function_tree)


@function_controller.get(
    "/listLazy",
    dependencies=[Depends(CheckUserInterfacePermit("system:function:list"))],
    response_model=ResponseType[list[FunctionTreeVO]],
)
async def get_system_function_list_lazy(
    parent: int = Query(0, description="父功能ID，0表示顶层", validation_alias="parentId"),
    scene: str | None = Query(None, description="应用场景（web-日常应用, admin-管理系统, mobile-移动端）"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取功能列表（异步加载模式，只返回指定父级的直接子节点）- 返回 FunctionTreeVO"""
    function_list = await FunctionService.get_function_tree_lazy(query_db, parent, scene)
    return ResponseUtil.success(data=function_list)


# ============================================================================
# 功能新增
# ============================================================================
@function_controller.post(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("system:function:add"))],
    response_model=ResponseType[FunctionDetailVO],
)
@SystemLog(title="功能管理", business_type=SysConst.BusinessType.INSERT)
async def add_system_function(
    function_data: FunctionCreateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """新增功能"""
    await FunctionService.add_function(query_db, function_data, current_user, redis_session)
    return ResponseUtil.success()


# ============================================================================
# 功能修改
# ============================================================================
@function_controller.put(
    "",
    dependencies=[Depends(CheckUserInterfacePermit("system:function:edit"))],
    response_model=ResponseType[FunctionDetailVO],
)
@SystemLog(title="功能管理", business_type=SysConst.BusinessType.UPDATE)
async def edit_system_function(
    function_data: FunctionUpdateDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改功能信息"""
    result = await FunctionService.update_function(query_db, function_data, current_user, redis_session)
    return ResponseUtil.success(data=result)


# ============================================================================
# 功能删除
# ============================================================================
@function_controller.delete(
    "/{function_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("system:function:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="功能管理", business_type=SysConst.BusinessType.DELETE)
async def delete_system_function(
    function_ids: str = Path(..., pattern="^[0-9,]+$", description="功能ID，多个用逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    redis_session: AsyncRedis = Depends(get_redis),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """删除功能（支持批量删除）"""
    function_id_list = [int(fid) for fid in function_ids.split(",") if fid]
    await FunctionService.delete_function(query_db, current_user, function_id_list, redis_session)
    return ResponseUtil.success()


# ============================================================================
# 获取功能详情
# ============================================================================
@function_controller.get(
    "/{function_id}",
    dependencies=[Depends(CheckUserInterfacePermit("system:function:query"))],
    response_model=ResponseType[FunctionDetailVO],
)
async def query_detail_system_function(
    function_id: int = Path(..., description="功能ID"), query_db: AsyncSession = Depends(get_db)
):
    """获取功能详细信息 - 返回 FunctionDetailVO"""
    function_detail = await FunctionService.get_function_detail(query_db, function_id)
    return ResponseUtil.success(data=function_detail)
