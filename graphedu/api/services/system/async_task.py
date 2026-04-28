"""通用异步任务 API 控制器。"""

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.systemv2.async_task import AsyncTaskQueryDTO
from graphedu.common.models.vo.base import PageResponse, ResponseType, ResponseUtil
from graphedu.common.models.vo.systemv2.async_task import (
    AsyncTaskDetailVO,
    AsyncTaskProgressVO,
    AsyncTaskVO,
)
from graphedu.common.resource.deps import get_db
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.auth import SecurityService
from graphedu.services.system.async_task import AsyncTaskService

async_task_controller = APIRouter(
    prefix="/system/async-task",
    dependencies=[Depends(SecurityService.get_current_user)],
)


@async_task_controller.get(
    "/list",
    dependencies=[Depends(CheckUserInterfacePermit("system:asyncTask:list"))],
    response_model=ResponseType[PageResponse[AsyncTaskVO]],
)
async def list_async_tasks(
    query: AsyncTaskQueryDTO = Query(),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """分页查询异步任务列表。"""
    result = await AsyncTaskService.list_tasks(query_db, query, current_user)
    return ResponseUtil.success(data=result)


@async_task_controller.get(
    "/{task_id}",
    dependencies=[Depends(CheckUserInterfacePermit("system:asyncTask:query"))],
    response_model=ResponseType[AsyncTaskDetailVO],
)
async def get_async_task_detail(
    task_id: int = Path(..., description="任务ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """获取异步任务详情。"""
    result = await AsyncTaskService.get_task_detail(query_db, task_id)
    return ResponseUtil.success(data=result)


@async_task_controller.get(
    "/{task_id}/progress",
    dependencies=[Depends(CheckUserInterfacePermit("system:asyncTask:query"))],
    response_model=ResponseType[AsyncTaskProgressVO],
)
async def get_async_task_progress(
    task_id: int = Path(..., description="任务ID"),
    query_db: AsyncSession = Depends(get_db),
):
    """查询异步任务进度。"""
    result = await AsyncTaskService.get_progress(query_db, task_id)
    return ResponseUtil.success(data=result)


@async_task_controller.post(
    "/{task_id}/cancel",
    dependencies=[Depends(CheckUserInterfacePermit("system:asyncTask:edit"))],
    response_model=ResponseType[AsyncTaskDetailVO],
)
async def cancel_async_task(
    task_id: int = Path(..., description="任务ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """取消异步任务。"""
    result = await AsyncTaskService.cancel_task(query_db, task_id, current_user)
    return ResponseUtil.success(data=result)


@async_task_controller.post(
    "/{task_id}/retry",
    dependencies=[Depends(CheckUserInterfacePermit("system:asyncTask:edit"))],
    response_model=ResponseType[AsyncTaskDetailVO],
)
async def retry_async_task(
    task_id: int = Path(..., description="任务ID"),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """重试异步任务。"""
    result = await AsyncTaskService.retry_task(query_db, task_id, current_user)
    return ResponseUtil.success(data=result)
