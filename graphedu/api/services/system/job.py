"""定时任务管理 API 控制器

本模块提供定时任务管理相关的 REST API 接口，包括任务的增删改查、
状态管理、立即执行等功能，以及任务执行日志的查询和删除。

主要接口：
- 任务列表：分页查询任务列表，支持多条件筛选
- 任务管理：新增、修改、删除任务
- 状态管理：启用/停用任务
- 立即执行：立即执行一次任务
- 任务日志：查询/删除任务执行日志
"""

from fastapi import APIRouter, Body, Depends, Header, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.toolv2.job import (
    JobCreateDTO,
    JobExecuteOnceDTO,
    JobLogQueryDTO,
    JobQueryDTO,
    JobStatusChangeDTO,
    JobUpdateDTO,
)
from graphedu.common.models.vo.base import Empty, PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.toolv2.job import JobDetailVO, JobExecuteResultVO, JobListVO, JobLogListVO
from graphedu.common.resource.deps import get_db, get_scheduler
from graphedu.common.resource.modules.scheduler import AsyncSchedulerResource
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import SecurityService
from graphedu.services.system.job import JobLogService, JobService

job_controller = APIRouter(prefix="/system/job", dependencies=[Depends(SecurityService.get_current_user)])

# Webhook 触发路由（无需认证，供外部系统调用）
job_webhook_controller = APIRouter(prefix="/webhook", tags=["定时任务-Webhook触发"])


# ============================================================================
# 任务列表查询
# ============================================================================
@job_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("system:job:list"))],
    response_model=ResponseType[PageResponse[JobListVO]],
)
async def get_system_job_list(
    query: JobQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取任务列表（分页）"""
    job_page_result: PageResponse[JobListVO] = await JobService.list_job(query_db, query)
    return ResponseUtil.success(data=job_page_result)


# ============================================================================
# 任务详情查询
# ============================================================================
@job_controller.get(
    "/{job_id}",
    dependencies=[Depends(CheckUserInterfacePermit("system:job:query"))],
    response_model=ResponseType[JobDetailVO],
)
async def get_system_job_detail(
    job_id: int = Path(description="任务ID"),
    request: Request = Depends(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取任务详情"""
    # 获取基础 URL
    base_url = str(request.base_url)
    job_detail = await JobService.get_job_detail(query_db, job_id, base_url)
    return ResponseUtil.success(data=job_detail)


# ============================================================================
# 用户新增
# ============================================================================
@job_controller.post(
    "", dependencies=[Depends(CheckUserInterfacePermit("system:job:add"))], response_model=ResponseType[JobDetailVO]
)
@SystemLog(
    title="定时任务管理",
    business_type=SysConst.BusinessType.INSERT,
    exclude_params={"query_db", "current_user", "request"},
)
async def add_system_job(
    job_data: JobCreateDTO = Body(),
    request: Request = Depends(),
    query_db: AsyncSession = Depends(get_db),
    scheduler: AsyncSchedulerResource = Depends(get_scheduler),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """新增定时任务"""
    # 获取基础 URL
    base_url = str(request.base_url)
    job_detail = await JobService.add_job(query_db, scheduler, job_data, current_user.detail.user.user_id, base_url)
    return ResponseUtil.success(data=job_detail)


# ============================================================================
# 任务修改
# ============================================================================
@job_controller.put(
    "", dependencies=[Depends(CheckUserInterfacePermit("system:job:edit"))], response_model=ResponseType[JobDetailVO]
)
@SystemLog(
    title="定时任务管理",
    business_type=SysConst.BusinessType.UPDATE,
    exclude_params={"query_db", "current_user", "request"},
)
async def update_system_job(
    job_data: JobUpdateDTO = Body(),
    request: Request = Depends(),
    query_db: AsyncSession = Depends(get_db),
    scheduler: AsyncSchedulerResource = Depends(get_scheduler),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改定时任务"""
    # 获取基础 URL
    base_url = str(request.base_url)
    job_detail = await JobService.update_job(query_db, scheduler, job_data, current_user.detail.user.user_id, base_url)
    return ResponseUtil.success(data=job_detail)


# ============================================================================
# 任务删除
# ============================================================================
@job_controller.delete(
    "/{job_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("system:job:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(
    title="定时任务管理",
    business_type=SysConst.BusinessType.DELETE,
    exclude_params={"query_db"},
)
async def delete_system_job(
    job_ids: str = Path(description="任务ID列表，逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
    scheduler: AsyncSchedulerResource = Depends(get_scheduler),
):
    """删除定时任务（支持批量删除）"""
    job_id_list = [int(job_id) for job_id in job_ids.split(",")]
    await JobService.delete_job(query_db, scheduler, job_id_list)
    return ResponseUtil.success()


# ============================================================================
# 修改任务状态
# ============================================================================
@job_controller.put(
    "/changeStatus",
    dependencies=[Depends(CheckUserInterfacePermit("system:job:changeStatus"))],
    response_model=ResponseType[Empty],
)
@SystemLog(
    title="定时任务管理",
    business_type=SysConst.BusinessType.UPDATE,
    exclude_params={"query_db", "current_user"},
)
async def change_system_job_status(
    status_data: JobStatusChangeDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
    scheduler: AsyncSchedulerResource = Depends(get_scheduler),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """修改任务状态"""
    await JobService.change_job_status(query_db, scheduler, status_data, current_user.detail.user.user_id)
    return ResponseUtil.success()


# ============================================================================
# 立即执行一次任务
# ============================================================================
@job_controller.put(
    "/run",
    dependencies=[Depends(CheckUserInterfacePermit("system:job:execute"))],
    response_model=ResponseType[JobExecuteResultVO],
)
@SystemLog(
    title="定时任务管理",
    business_type=SysConst.BusinessType.OTHER,
    exclude_params={"query_db"},
)
async def execute_system_job_once(
    execute_data: JobExecuteOnceDTO = Body(),
    query_db: AsyncSession = Depends(get_db),
):
    """立即执行一次任务"""
    result = await JobService.execute_job_once(query_db, execute_data)
    return ResponseUtil.success(data=result)


# ============================================================================
# 任务日志列表查询
# ============================================================================
@job_controller.get(
    "/log/list",
    dependencies=[Depends(CheckUserInterfacePermit("system:job:log:query"))],
    response_model=ResponseType[PageResponse[JobLogListVO]],
)
async def get_system_job_log_list(
    query: JobLogQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
):
    """获取任务日志列表（分页）"""
    job_log_page_result: PageResponse[JobLogListVO] = await JobLogService.list_job_log(query_db, query)
    return ResponseUtil.success(data=job_log_page_result)


# ============================================================================
# 清空任务日志（必须在 /log/{job_log_ids} 之前注册，避免 "clean" 被误匹配为日志ID）
# ============================================================================
@job_controller.delete(
    "/log/clean",
    dependencies=[Depends(CheckUserInterfacePermit("system:job:log:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(
    title="定时任务日志",
    business_type=SysConst.BusinessType.CLEAN,
    exclude_params={"query_db"},
)
async def clear_system_job_log(
    query_db: AsyncSession = Depends(get_db),
):
    """清空任务日志"""
    await JobLogService.clear_job_log(query_db)
    return ResponseUtil.success()


# ============================================================================
# Webhook 触发接口（无需登录认证，供外部系统调用）
# 注意：/job/by-name/{job_name} 必须在 /job/{job_id} 之前注册，
#       否则 "by-name" 会被误匹配为整数 job_id 导致 422
# ============================================================================
@job_webhook_controller.post(
    "/job/by-name/{job_name}",
    response_model=ResponseType[JobExecuteResultVO],
    summary="通过任务名称触发 Webhook",
)
async def trigger_job_by_name(
    job_name: str = Path(description="任务名称"),
    request: Request = Depends(),
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature", description="Webhook 密钥"),
    query_db: AsyncSession = Depends(get_db),
):
    """外部系统通过任务名称触发任务执行（Webhook）"""
    try:
        body = await request.json()
        args = body.get("args", [])
        kwargs = body.get("kwargs", {})
    except Exception:
        args = []
        kwargs = {}

    result = await JobService.trigger_by_webhook_name(query_db, job_name, x_webhook_signature, args, kwargs)
    return ResponseUtil.success(data=result)


@job_webhook_controller.post(
    "/job/{job_id}",
    response_model=ResponseType[JobExecuteResultVO],
    summary="通过任务ID触发 Webhook",
)
async def trigger_job_by_webhook(
    job_id: int = Path(description="任务ID"),
    request: Request = Depends(),
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature", description="Webhook 密钥"),
    query_db: AsyncSession = Depends(get_db),
):
    """外部系统通过任务ID触发任务执行（Webhook）"""
    try:
        body = await request.json()
        args = body.get("args", [])
        kwargs = body.get("kwargs", {})
    except Exception:
        args = []
        kwargs = {}

    result = await JobService.trigger_by_webhook(query_db, job_id, x_webhook_signature, args, kwargs)
    return ResponseUtil.success(data=result)


# ============================================================================
# 任务日志删除
# ============================================================================
@job_controller.delete(
    "/log/{job_log_ids}",
    dependencies=[Depends(CheckUserInterfacePermit("system:job:log:remove"))],
    response_model=ResponseType[Empty],
)
@SystemLog(
    title="定时任务日志",
    business_type=SysConst.BusinessType.DELETE,
    exclude_params={"query_db"},
)
async def delete_system_job_log(
    job_log_ids: str = Path(description="日志ID列表，逗号分隔"),
    query_db: AsyncSession = Depends(get_db),
):
    """删除任务日志（支持批量删除）"""
    job_log_id_list = [int(job_log_id) for job_log_id in job_log_ids.split(",")]
    await JobLogService.delete_job_log(query_db, job_log_id_list)
    return ResponseUtil.success()
