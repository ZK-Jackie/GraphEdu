"""Celery Worker 公共辅助函数。

提供异步任务的状态管理工具，供各业务 Worker 调用。
Worker 通过这些函数统一更新任务状态、进度和结果。
"""

from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.resource import ContainerMode, WorkerContainer, try_get_container

logger = logging.getLogger(__name__)


async def _get_db_session() -> AsyncSession:
    """获取 Worker 容器中的数据库会话上下文管理器。"""
    container: WorkerContainer = await try_get_container(ContainerMode.WORKER)
    return await container.postgresql_client()


async def init_task(task_id: int) -> None:
    """标记任务为 processing 状态。

    Worker 开始执行业务逻辑前调用。

    Args:
        task_id: 异步任务ID
    """
    from graphedu.services.system.async_task import AsyncTaskService

    db_ctx = await _get_db_session()
    async with db_ctx.session_context() as db:
        await AsyncTaskService.worker_update(
            db,
            task_id,
            task_status="processing",
            start_time=datetime.now(),
            task_message="任务开始执行",
            progress_percent=0,
        )


async def update_progress(task_id: int, percent: int, message: str | None = None) -> None:
    """更新任务进度。

    Worker 在关键阶段调用，同时更新 DB 和 Celery backend。

    Args:
        task_id: 异步任务ID
        percent: 进度百分比 (0-100)
        message: 当前步骤描述
    """
    from graphedu.services.system.async_task import AsyncTaskService

    kwargs = {"progress_percent": percent, "update_time": datetime.now()}
    if message:
        kwargs["task_message"] = message

    db_ctx = await _get_db_session()
    async with db_ctx.session_context() as db:
        await AsyncTaskService.worker_update(db, task_id, **kwargs)


async def finish_task(task_id: int, result: dict | list | None = None) -> None:
    """标记任务为 success 状态。

    Worker 成功完成时调用。

    Args:
        task_id: 异步任务ID
        result: 任务结果数据
    """
    from graphedu.services.system.async_task import AsyncTaskService

    kwargs = {
        "task_status": "success",
        "progress_percent": 100,
        "end_time": datetime.now(),
        "update_time": datetime.now(),
    }
    if result is not None:
        kwargs["task_result"] = result

    db_ctx = await _get_db_session()
    async with db_ctx.session_context() as db:
        await AsyncTaskService.worker_update(db, task_id, **kwargs)


async def fail_task(task_id: int, error_message: str) -> None:
    """标记任务为 failed 状态。

    Worker 执行失败时调用。

    Args:
        task_id: 异步任务ID
        error_message: 错误描述
    """
    from graphedu.services.system.async_task import AsyncTaskService

    db_ctx = await _get_db_session()
    async with db_ctx.session_context() as db:
        await AsyncTaskService.worker_update(
            db,
            task_id,
            task_status="failed",
            task_message=error_message,
            end_time=datetime.now(),
            update_time=datetime.now(),
        )
