"""通用异步任务服务模块。

提供异步任务的全生命周期管理：创建、进度查询、取消、重试。
业务模块通过此服务提交任务，Worker 通过辅助函数更新状态。
"""

from datetime import datetime
import logging
import uuid

from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.system.async_task import (
    AsyncTaskCannotCancelException,
    AsyncTaskCannotRetryException,
    AsyncTaskCreateFailedException,
    AsyncTaskNotFoundException,
    AsyncTaskUpdateFailedException,
)
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.systemv2.async_task import AsyncTaskCreateDTO, AsyncTaskQueryDTO
from graphedu.common.models.orm.system import SysAsyncTask
from graphedu.common.models.vo.base import PageResponse
from graphedu.common.models.vo.systemv2.async_task import (
    AsyncTaskDetailVO,
    AsyncTaskProgressVO,
    AsyncTaskVO,
)
from graphedu.mapper.system.async_task import AsyncTaskMapper

logger = logging.getLogger(__name__)


# ============================================================================
# ORM → VO 转换
# ============================================================================


def _convert_orm_to_vo(task: SysAsyncTask) -> AsyncTaskVO:
    return AsyncTaskVO(
        task_id=task.task_id,
        task_name=task.task_name,
        task_type=task.task_type,
        task_status=task.task_status,
        progress_percent=task.progress_percent,
        task_message=task.task_message,
        user_id=task.user_id,
        start_time=task.start_time,
        end_time=task.end_time,
        create_time=task.create_time,
    )


def _convert_orm_to_detail_vo(task: SysAsyncTask) -> AsyncTaskDetailVO:
    return AsyncTaskDetailVO(
        task_id=task.task_id,
        task_name=task.task_name,
        task_type=task.task_type,
        task_status=task.task_status,
        progress_percent=task.progress_percent,
        task_message=task.task_message,
        user_id=task.user_id,
        start_time=task.start_time,
        end_time=task.end_time,
        create_time=task.create_time,
        task_params=task.task_params,
        task_result=task.task_result,
        celery_task_id=task.celery_task_id,
        create_by=task.create_by,
        update_time=task.update_time,
    )


def _safe_user_id(current_user: CurrentUser | None) -> int | None:
    if current_user and current_user.detail and current_user.detail.user:
        return current_user.detail.user.user_id
    return None


# ============================================================================
# Celery 状态映射
# ============================================================================


def _map_celery_state(state: str) -> str:
    """将 Celery 状态映射为业务任务状态。"""
    mapping = {
        "PENDING": "pending",
        "STARTED": "processing",
        "PROGRESS": "processing",
        "SUCCESS": "success",
        "FAILURE": "failed",
        "REVOKED": "cancelled",
        "RETRY": "processing",
    }
    return mapping.get(state, "pending")


# ============================================================================
# 服务类
# ============================================================================


class AsyncTaskService:
    """通用异步任务服务类。"""

    # ========================================================================
    # 创建任务
    # ========================================================================

    @staticmethod
    async def create_task(
        db: AsyncSession,
        dto: AsyncTaskCreateDTO,
        current_user: CurrentUser | None = None,
    ) -> AsyncTaskDetailVO:
        """创建异步任务记录。

        由业务 Service 在派发 Celery 任务之前调用。
        创建后返回包含 task_id 的详情，业务层可据此派发 Celery。

        Args:
            db: 数据库会话
            dto: 任务创建参数
            current_user: 当前用户

        Returns:
            AsyncTaskDetailVO: 创建的任务详情
        """
        user_id = dto.user_id or _safe_user_id(current_user)
        now = datetime.now()

        task_orm = SysAsyncTask(
            task_name=dto.task_name,
            task_type=dto.task_type,
            task_status="pending",
            task_params=dto.task_params,
            celery_task_id=dto.celery_task_id,
            task_message="任务已提交，等待执行",
            progress_percent=0,
            user_id=user_id,
            status=SystemConstants.Status.NORMAL,
            create_by=user_id,
            create_time=now,
            update_by=user_id,
            update_time=now,
        )

        try:
            task_orm = await AsyncTaskMapper.insert(task_orm, db)
        except Exception as e:
            raise AsyncTaskCreateFailedException(task_type=dto.task_type) from e

        logger.info("创建异步任务: task_id=%s, type=%s, name=%s", task_orm.task_id, dto.task_type, dto.task_name)
        return _convert_orm_to_detail_vo(task_orm)

    # ========================================================================
    # 查询任务
    # ========================================================================

    @staticmethod
    async def get_task_detail(db: AsyncSession, task_id: int) -> AsyncTaskDetailVO:
        """获取任务详情。

        Args:
            db: 数据库会话
            task_id: 任务ID

        Returns:
            AsyncTaskDetailVO

        Raises:
            AsyncTaskNotFoundException: 任务不存在
        """
        task = await AsyncTaskMapper.get_by_id(task_id, db)
        if not task:
            raise AsyncTaskNotFoundException(task_id=task_id)
        return _convert_orm_to_detail_vo(task)

    @staticmethod
    async def get_progress(db: AsyncSession, task_id: int) -> AsyncTaskProgressVO:
        """查询任务进度。

        策略：优先使用 DB 中的持久化状态。
        仅在任务处于 pending/processing 时合并 Celery 实时进度。

        Args:
            db: 数据库会话
            task_id: 任务ID

        Returns:
            AsyncTaskProgressVO
        """
        task = await AsyncTaskMapper.get_by_id(task_id, db)
        if not task:
            raise AsyncTaskNotFoundException(task_id=task_id)

        # 已终态的任务直接返回 DB 状态
        if task.task_status in {"success", "failed", "cancelled"}:
            return AsyncTaskProgressVO(
                task_id=task.task_id,
                task_status=task.task_status,
                progress_percent=100 if task.task_status == "success" else task.progress_percent,
                task_message=task.task_message,
                task_result=task.task_result,
            )

        # 运行中的任务，尝试合并 Celery 实时进度
        progress_percent = task.progress_percent
        task_message = task.task_message

        if task.celery_task_id:
            try:
                from graphedu.workers.celery import celery_app

                celery_task = AsyncResult(task.celery_task_id, app=celery_app)
                meta = celery_task.info if isinstance(celery_task.info, dict) else {}

                mapped_status = _map_celery_state(celery_task.state)
                # Celery 报告失败且 DB 未更新时，同步状态
                if mapped_status == "failed" and task.task_status != "failed":
                    error_msg = str(celery_task.info) if celery_task.info else "任务执行失败"
                    await AsyncTaskMapper.update_fields(
                        task_id,
                        db,
                        task_status="failed",
                        task_message=error_msg,
                        end_time=datetime.now(),
                    )
                    return AsyncTaskProgressVO(
                        task_id=task_id,
                        task_status="failed",
                        progress_percent=progress_percent,
                        task_message=error_msg,
                    )

                # 合并 Celery 实时进度
                celery_percent = meta.get("percent", 0)
                if celery_percent > progress_percent:
                    progress_percent = celery_percent
                celery_msg = meta.get("step_description")
                if celery_msg:
                    task_message = celery_msg
            except Exception:
                logger.warning("查询 Celery 进度失败: task_id=%s", task_id, exc_info=True)

        return AsyncTaskProgressVO(
            task_id=task_id,
            task_status=task.task_status,
            progress_percent=progress_percent,
            task_message=task_message,
        )

    # ========================================================================
    # 列表查询
    # ========================================================================

    @staticmethod
    async def list_tasks(
        db: AsyncSession,
        query: AsyncTaskQueryDTO,
        current_user: CurrentUser | None = None,
    ) -> PageResponse[AsyncTaskVO]:
        """分页查询异步任务列表。

        Args:
            db: 数据库会话
            query: 查询条件
            current_user: 当前用户（非管理员只能看自己的任务）

        Returns:
            分页结果
        """
        user_id = _safe_user_id(current_user)
        rows, total = await AsyncTaskMapper.list_by_query(query, db, user_id=user_id)
        page = query.page or 1
        size = query.size or 10
        return PageResponse(rows=[_convert_orm_to_vo(r) for r in rows], page=page, size=size, total=total)

    # ========================================================================
    # 取消任务
    # ========================================================================

    @staticmethod
    async def cancel_task(db: AsyncSession, task_id: int, current_user: CurrentUser) -> AsyncTaskDetailVO:
        """取消异步任务。

        Args:
            db: 数据库会话
            task_id: 任务ID
            current_user: 当前用户

        Returns:
            AsyncTaskDetailVO

        Raises:
            AsyncTaskNotFoundException: 任务不存在
            AsyncTaskCannotCancelException: 任务状态不允许取消
        """
        task = await AsyncTaskMapper.get_by_id(task_id, db)
        if not task:
            raise AsyncTaskNotFoundException(task_id=task_id)

        if task.task_status not in {"pending", "processing"}:
            raise AsyncTaskCannotCancelException(current_status=task.task_status)

        # 撤销 Celery 任务
        if task.celery_task_id:
            try:
                from graphedu.workers.celery import celery_app

                celery_app.control.revoke(task.celery_task_id, terminate=True)
            except Exception:
                logger.warning("撤销 Celery 任务失败: celery_task_id=%s", task.celery_task_id, exc_info=True)

        now = datetime.now()
        user_id = _safe_user_id(current_user)
        await AsyncTaskMapper.update_fields(
            task_id,
            db,
            task_status="cancelled",
            task_message="用户取消任务",
            end_time=now,
            update_by=user_id,
            update_time=now,
        )

        logger.info("取消异步任务: task_id=%s", task_id)
        task = await AsyncTaskMapper.get_by_id(task_id, db)
        return _convert_orm_to_detail_vo(task)

    # ========================================================================
    # 重试任务
    # ========================================================================

    @staticmethod
    async def retry_task(
        db: AsyncSession,
        task_id: int,
        current_user: CurrentUser,
        apply_async_fn=None,
    ) -> AsyncTaskDetailVO:
        """重试异步任务。

        重置任务状态为 pending 并重新派发 Celery 任务。
        apply_async_fn 由业务层提供，负责实际的 Celery 派发逻辑。

        Args:
            db: 数据库会话
            task_id: 任务ID
            current_user: 当前用户
            apply_async_fn: 可选的 Celery 派发函数，签名为 async (task_orm) -> str (celery_task_id)

        Returns:
            AsyncTaskDetailVO

        Raises:
            AsyncTaskNotFoundException: 任务不存在
            AsyncTaskCannotRetryException: 任务状态不允许重试
        """
        task = await AsyncTaskMapper.get_by_id(task_id, db)
        if not task:
            raise AsyncTaskNotFoundException(task_id=task_id)

        if task.task_status not in {"failed", "cancelled"}:
            raise AsyncTaskCannotRetryException(current_status=task.task_status)

        now = datetime.now()
        user_id = _safe_user_id(current_user)

        # 清除旧的 Celery 结果
        new_celery_id = None
        if task.celery_task_id:
            try:
                from graphedu.workers.celery import celery_app

                celery_app.backend.delete(task.celery_task_id)
            except Exception:
                pass

        # 如果业务层提供了派发函数，调用它
        if apply_async_fn:
            try:
                new_celery_id = await apply_async_fn(task)
            except Exception as e:
                raise AsyncTaskUpdateFailedException(task_id=task_id) from e

        # 重置任务状态
        await AsyncTaskMapper.update_fields(
            task_id,
            db,
            task_status="pending",
            task_message="任务已重新提交，等待执行",
            progress_percent=0,
            start_time=None,
            end_time=None,
            task_result=None,
            celery_task_id=new_celery_id or f"{task_id}-retry-{uuid.uuid4().hex[:8]}",
            update_by=user_id,
            update_time=now,
        )

        logger.info("重试异步任务: task_id=%s", task_id)
        task = await AsyncTaskMapper.get_by_id(task_id, db)
        return _convert_orm_to_detail_vo(task)

    # ========================================================================
    # Worker 调用的更新方法（通过 DB session）
    # ========================================================================

    @staticmethod
    async def worker_update(db: AsyncSession, task_id: int, **kwargs) -> None:
        """Worker 中更新任务状态。

        供 workers/base.py 辅助函数调用。

        Args:
            db: 数据库会话
            task_id: 任务ID
            **kwargs: 要更新的字段（task_status, progress_percent, task_message, task_result 等）
        """
        await AsyncTaskMapper.update_fields(task_id, db, **kwargs)
