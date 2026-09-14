"""Celery 异步任务运行时共享组件。

提供与具体业务表无关的通用能力，供各类长耗时异步任务复用：

- 协作式取消（基于 Celery revoke 状态）
- 异常分类（取消 / 超时 / 业务，决定是否重试）
- 统一取消操作（先持久化状态再 revoke，消除竞态）

设计目标：让 graphrag 跑通的“协作取消 + 异常分类 + 超时兜底”模式可被
knowledge_graph / course_exercise 等任务复用，避免每类任务各搞一套。

设计背景详见 docs/architecture/async-task.md。
"""

from collections.abc import Awaitable, Callable
import logging
from typing import Literal

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded, TimeLimitExceeded

logger = logging.getLogger(__name__)


class TaskCancelledError(Exception):
    """任务被取消时抛出，用于协作式中断长耗时任务。

    由 :func:`raise_if_cancelled` 在检测到 Celery revoke 状态后抛出。任务函数的
    ``except`` 应将其识别为“取消”而非“失败”，标记 cancelled 且不重试。
    """


TaskExceptionCategory = Literal["cancelled", "timeout", "business"]
"""异常分类取值：cancelled（取消）/ timeout（超时）/ business（业务异常）。"""


def is_task_cancelled(task: Task) -> bool:
    """检查当前任务是否已被撤销（用户取消触发 Celery revoke）。

    基于 Celery 原生 revoke 状态（``request.is_revoked()``），纯内存查询，
    可在任务执行的关键步骤间高频调用。

    Args:
        task: Celery 任务实例（``bind=True`` 传入的 ``self``）。

    Returns:
        bool: 已撤销返回 True。检查本身抛异常时返回 False（不阻断正常流程）。
    """
    try:
        return bool(task.request.is_revoked())
    except Exception:
        logger.warning("检查任务取消状态失败", exc_info=True)
        return False


def raise_if_cancelled(task: Task) -> None:
    """检查取消状态，若已撤销则抛出 :class:`TaskCancelledError`。

    供长耗时任务在关键步骤间调用，实现协作式中断，而不必依赖 SIGTERM 在
    CPU 密集段的不确定中断时机。
    """
    if is_task_cancelled(task):
        raise TaskCancelledError("任务已被取消")


def categorize_exception(exc: BaseException) -> TaskExceptionCategory:
    """将异常归类为 cancelled / timeout / business，用于决定重试策略。

    - ``cancelled``：用户主动取消（TaskCancelledError）→ 标记 cancelled，不重试
    - ``timeout``：Celery 软/硬超时 → 标记 failed，不重试（长任务重试只会再超时）
    - ``business``：其他业务异常（多为瞬时错误）→ 可重试
    """
    if isinstance(exc, TaskCancelledError):
        return "cancelled"
    if isinstance(exc, (SoftTimeLimitExceeded, TimeLimitExceeded)):
        return "timeout"
    return "business"


async def cancel_celery_task(
    celery_task_id: str,
    mark_cancelled: Callable[[], Awaitable[None]],
) -> None:
    """统一的取消操作：先持久化取消状态，再 revoke 发送 SIGTERM。

    顺序关键——若先 revoke，任务可能在持久化完成前被 SIGTERM 中断，进入异常
    处理后读不到 cancelled 状态而误判为失败并重试（取消“复活”）。

    Args:
        celery_task_id: Celery 任务 ID（通常 == ``str(db_task_id)``）。
        mark_cancelled: 业务侧回调，负责将任务记录标记为 cancelled（如写 DB）。
    """
    from graphedu.workers.celery import celery_app

    await mark_cancelled()
    celery_app.control.revoke(celery_task_id, terminate=True)
