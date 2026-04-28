"""日志管理 Controller 层

职责：
1. 接收HTTP请求，使用DTO进行参数验证
2. 调用Service层处理业务逻辑
3. 响应VO对象给前端
"""

import logging

from fastapi import APIRouter, Depends, Path, Query
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.systemv2.log import LoginLogQueryDTO, OperLogQueryDTO, UnlockUserDTO
from graphedu.common.models.vo import LoginLogListVO, OperLogDetailVO, OperLogListVO
from graphedu.common.models.vo.base import Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.resource.deps import get_db, get_redis
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.system.log import LoginLogService, OperationLogService

logger = logging.getLogger(__name__)

log_controller = APIRouter(prefix="/monitor", dependencies=[Depends(SecurityService.get_current_user)])


# ============================================================================
# 操作日志管理接口
# ============================================================================


@log_controller.get(
    "/log/operation/list",
    dependencies=[Depends(CheckUserInterfacePermit("monitor:log:operation:list"))],
    response_model=ResponseType[PageResponse[OperLogListVO]],
)
async def get_system_operation_log_list(
    query_object: OperLogQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取操作日志列表（分页）"""
    operation_log_result = await OperationLogService.get_operation_log_list(query_db, query_object)
    return ResponseUtil.success(data=operation_log_result)


@log_controller.delete(
    "/log/operation/clean",
    dependencies=[Depends(CheckUserInterfacePermit("monitor:log:operation:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="操作日志", business_type=SysConst.BusinessType.CLEAN)
async def clear_system_operation_log(
    query_db: AsyncSession = Depends(get_db),
):
    """清空操作日志"""
    await OperationLogService.clear_operation_log(query_db)
    return ResponseUtil.success()


@log_controller.delete(
    "/log/operation/{oper_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("monitor:log:operation:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="操作日志", business_type=SysConst.BusinessType.DELETE)
async def delete_system_operation_log(
    oper_ids: str = Path(pattern="^[0-9,]+$", description="操作日志ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
):
    """删除操作日志（支持批量删除）"""
    delete_ids = [int(oper_id) for oper_id in oper_ids.split(",")]
    await OperationLogService.delete_operation_log(query_db, delete_ids)
    return ResponseUtil.success()


@log_controller.get(
    "/log/operation/{oper_id}",
    dependencies=[Depends(CheckUserInterfacePermit("monitor:log:operation:query"))],
    response_model=ResponseType[OperLogDetailVO],
)
async def get_system_operation_log_detail(
    oper_id: int = Path(description="操作日志ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取操作日志详情"""
    detail = await OperationLogService.get_operation_log_detail(oper_id, query_db)
    if detail is None:
        return ResponseUtil.fail(msg="操作日志不存在")
    return ResponseUtil.success(data=detail)


# @log_controller.post(
#     '/log/operation/export',
#     dependencies=[Depends(CheckUserInterfacePermit('monitor:log:operation:export'))],
#     response_model=ResponseType[Empty]
# )
# @log(title='操作日志', business_type=SysConst.BusinessType.EXPORT)
# async def export_system_operation_log_list(
#         request: Request,
#         query: OperLogQueryDTO = Body(),
#         query_db: AsyncSession = Depends(get_db),
#         redis_session: AsyncRedis = Depends(get_redis),
# ):
#     """导出操作日志"""
#     # 获取全量数据
#     operation_log_result = await OperationLogService.get_operation_log_list(query_db, query, is_page=False)
#     operation_log_export_result = await OperationLogService.export_operation_log_list(
#         redis_session, operation_log_result
#     )
#     logger.info('导出操作日志成功')
#     # TODO: 返回Excel文件
#     return ResponseUtil.success()


# ============================================================================
# 登录日志管理接口
# ============================================================================


@log_controller.get(
    "/log/login/list",
    dependencies=[Depends(CheckUserInterfacePermit("monitor:log:login:list"))],
    response_model=ResponseType[PageResponse[LoginLogListVO]],
)
async def get_system_login_log_list(
    query: LoginLogQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取登录日志列表（分页）"""
    login_log_result = await LoginLogService.get_login_log_list(query_db, query)
    return ResponseUtil.success(data=login_log_result)


@log_controller.delete(
    "/log/login/clean",
    dependencies=[Depends(CheckUserInterfacePermit("monitor:log:login:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="登录日志", business_type=SysConst.BusinessType.CLEAN)
async def clear_system_login_log(
    query_db: AsyncSession = Depends(get_db),
):
    """清空登录日志"""
    await LoginLogService.clear_login_log(query_db)
    return ResponseUtil.success()


@log_controller.delete(
    "/log/login/{info_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("monitor:log:login:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="登录日志", business_type=SysConst.BusinessType.DELETE)
async def delete_system_login_log(
    info_ids: str = Path(pattern="^[0-9,]+$", description="登录日志ID，多个以逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
):
    """删除登录日志（支持批量删除）"""
    delete_ids = [int(info_id) for info_id in info_ids.split(",")]
    await LoginLogService.delete_login_log(query_db, delete_ids)
    return ResponseUtil.success()


@log_controller.get(
    "/log/login/unlock/{user_name}",
    dependencies=[Depends(CheckUserInterfacePermit("monitor:log:login:unlock"))],
    response_model=ResponseType[Empty],
)
@SystemLog(title="账户解锁", business_type=SysConst.BusinessType.OTHER)
async def unlock_system_user(
    user_name: str,
    redis_session: AsyncRedis = Depends(get_redis),
):
    """解锁用户账户"""
    unlock_user = UnlockUserDTO(user_name=user_name)
    await LoginLogService.unlock_user(redis_session, unlock_user)
    return ResponseUtil.success()


# @log_controller.post(
#     '/log/login/export',
#     dependencies=[Depends(CheckUserInterfacePermit('monitor:log:login:export'))]
# )
# @SystemLog(title='登录日志', business_type=SysConst.BusinessType.EXPORT)
# async def export_system_login_log_list(
#         request: Request,
#         query: LoginLogQueryDTO = Body(),
#         query_db: AsyncSession = Depends(get_db),
# ):
#     """导出登录日志"""
#     # 获取全量数据
#     login_log_result = await LoginLogService.get_login_log_list(query_db, query)
#     await LoginLogService.export_login_log_list(login_log_result)
#     logger.info('导出登录日志成功')
#     # TODO: 返回Excel文件
#     return ResponseUtil.success(msg='导出功能待实现')
