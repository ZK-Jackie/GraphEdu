"""Workflow running status callback for Celery tasks."""

from concurrent.futures import ThreadPoolExecutor
import logging
import time

from celery import Celery
from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.index.typing.pipeline_run_result import PipelineRunResult
from graphrag.logger.progress import Progress

logger = logging.getLogger(__name__)


class TaskCancelledError(Exception):
    """任务被取消时由回调抛出，用于在 graphrag 工作流内部协作式中断。

    当用户取消任务（Celery revoke）后，回调在每个 workflow / progress 节点
    检测到撤销状态即抛出此异常，使 graphrag 尽快停止，而不必依赖 SIGTERM
    在长耗时计算段中的不确定中断时机。
    """


class CeleryWorkflowCallbacks(NoopWorkflowCallbacks):
    """Celery workflow callbacks for handling task success and failure.

    每隔 ``throttle_seconds`` 秒向 Celery backend 写一次进度；
    关键节点（workflow 开始/结束、pipeline 错误/完成）强制立即上报。

    若传入 ``task``（Celery Task 实例），会在每个回调节点检查任务是否被
    撤销（``task.request.is_revoked()``），命中则抛出 :class:`TaskCancelledError`
    以协作式中断长耗时工作流。
    """

    _work_id: str
    _celery_app: Celery
    _throttle_seconds: float
    _executor: ThreadPoolExecutor
    _workflow_names: list[str]
    _current_workflow: str | None
    _completed_count: int
    _current_progress: Progress | None
    _last_report_time: float
    _task: object | None

    def __init__(
        self,
        work_id: str,
        celery_app: Celery,
        throttle_seconds: float = 5.0,
        task: object | None = None,
    ) -> None:
        self._work_id = work_id
        self._celery_app = celery_app
        self._throttle_seconds = throttle_seconds
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._task = task

        # 运行时状态
        self._workflow_names = []
        self._current_workflow = None
        self._completed_count = 0
        self._current_progress = None
        self._last_report_time = 0.0

    def _check_cancelled(self) -> None:
        """检查任务是否已被撤销，若已撤销则抛出 TaskCancelledError。

        依赖 Celery 原生的 revoke 状态（``request.is_revoked()``）：用户调用
        ``celery_app.control.revoke(..., terminate=True)`` 后，worker 会将该
        task_id 写入内存 revoked 集合。本检查为纯内存查询，开销极低，可在
        高频的 progress 回调中安全调用。
        """
        if self._task is None:
            return
        try:
            if self._task.request.is_revoked():
                raise TaskCancelledError(f"任务已被取消: work_id={self._work_id}")
        except TaskCancelledError:
            raise
        except Exception:
            # is_revoked 检查本身异常不应阻断正常工作流，仅记录告警
            logger.warning(
                "[CeleryWorkflowCallbacks] 检查取消状态失败: work_id=%s",
                self._work_id,
                exc_info=True,
            )

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _build_meta(self) -> dict:
        """组装当前进度的 meta dict。"""
        total = len(self._workflow_names) or 1

        # 整体百分比：以 workflow 为粒度
        # 当前 workflow 内的子进度作为小数部分
        sub_fraction = 0.0
        if self._current_progress is not None:
            completed = self._current_progress.completed_items or 0
            total_items = self._current_progress.total_items or 1
            sub_fraction = completed / total_items / total

        percent = round((self._completed_count / total + sub_fraction) * 100)

        meta: dict = {
            "percent": min(percent, 100),
            "completed_workflows": self._completed_count,
            "total_workflows": total,
            "current_workflow": self._current_workflow,
        }

        if self._current_progress is not None:
            meta["completed_items"] = self._current_progress.completed_items
            meta["total_items"] = self._current_progress.total_items

        return meta

    def _store_progress(self, state: str, meta: dict) -> None:
        """同步写入 Celery backend（在线程池中执行）。"""
        try:
            self._celery_app.backend.store_result(
                task_id=self._work_id,
                result=meta,
                state=state,
            )
            self._last_report_time = time.monotonic()
        except Exception:
            logger.exception("[CeleryWorkflowCallbacks] 上报进度失败: work_id=%s", self._work_id)

    def _schedule_report(self, state: str, force: bool = False) -> None:
        """将进度上报调度为异步任务（不阻塞调用方）。

        - ``force=True``：忽略节流，立即提交
        - ``force=False``：距上次上报不足 throttle_seconds 则跳过
        """
        if not force:
            elapsed = time.monotonic() - self._last_report_time
            if elapsed < self._throttle_seconds:
                return

        meta = self._build_meta()
        self._executor.submit(self._store_progress, state, meta)

    # ------------------------------------------------------------------
    # WorkflowCallbacks 实现
    # ------------------------------------------------------------------

    def pipeline_start(self, names: list[str]) -> None:
        """整个 pipeline 开始。"""
        self._check_cancelled()
        self._workflow_names = list(names)
        self._completed_count = 0
        self._current_workflow = None
        self._current_progress = None
        logger.info("[GraphRAG] Pipeline 开始，共 %d 个 workflow: %s", len(names), ", ".join(names))
        self._schedule_report("PROGRESS", force=True)

    def pipeline_end(self, results: list[PipelineRunResult]) -> None:
        """整个 pipeline 结束（成功）。

        注意：此处写 ``PROGRESS`` 而非 ``SUCCESS``，因为 Celery 任务函数
        在 pipeline 结束后仍有后续工作（更新 DB 资源状态等）。
        真正的 SUCCESS 由 Celery 任务函数 return 后 Celery 自身写入。
        """
        logger.info("[GraphRAG] Pipeline 完成")
        failed = [r for r in results if r.error is not None]
        meta = self._build_meta()
        meta["percent"] = 100
        meta["failed_workflows"] = [r.workflow for r in failed]
        self._store_progress("PROGRESS", meta)

    def workflow_start(self, name: str, instance: object) -> None:
        """单个 workflow 步骤开始。"""
        self._check_cancelled()
        self._current_workflow = name
        self._current_progress = None
        logger.info("[GraphRAG] Workflow 开始: %s", name)
        self._schedule_report("PROGRESS", force=True)

    def workflow_end(self, name: str, instance: object) -> None:
        """单个 workflow 步骤结束。"""
        self._check_cancelled()
        self._completed_count += 1
        self._current_progress = None
        logger.info("[GraphRAG] Workflow 完成: %s (%d/%d)", name, self._completed_count, len(self._workflow_names))
        self._schedule_report("PROGRESS", force=True)

    def pipeline_error(self, error: BaseException) -> None:
        """Pipeline 发生错误。

        注意：此处写 ``PROGRESS`` 而非 ``FAILURE``，因为 worker 的 except
        块可能会调用 ``self.retry()`` 进行重试。写 FAILURE 会导致
        ``get_build_progress`` 在 retry 期间误将 DB 状态同步为 failed。
        实际的 FAILURE 由 Celery 在任务最终失败后写入。
        """
        logger.error("[GraphRAG] Pipeline 错误: %s", error)
        meta = self._build_meta()
        meta["error"] = str(error)
        self._store_progress("PROGRESS", meta)

    def progress(self, progress: Progress) -> None:
        """Workflow 内的细粒度进度（高频回调，启用节流）。"""
        self._check_cancelled()
        self._current_progress = progress
        self._schedule_report("PROGRESS", force=False)
