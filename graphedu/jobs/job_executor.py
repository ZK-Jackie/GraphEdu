"""任务执行器

由调度器或 Service 层直接调用，根据执行器类型选择执行方式。

设计原则：
- 使用 Mapper 层进行所有数据库操作
- 失败时抛出自定义异常（JobExecuteFailedException 等），而非通用异常
- 独立获取数据库事务（不依赖 FastAPI 请求生命周期）
"""

import importlib
import inspect
import logging
import traceback

from graphedu.common.exceptions import (
    JobConfigInvalidException,
    JobExecuteFailedException,
    JobNotFoundException,
)
from graphedu.common.models.orm.system import SysJobLog
from graphedu.jobs import webhook_entry
from graphedu.mapper.system.job import JobLogMapper, JobMapper

logger = logging.getLogger(__name__)


def _get_db_client():
    """延迟导入 get_db_client，避免模块级循环导入。

    job_executor 在调度器后台运行，不在 FastAPI 请求生命周期内，
    需要独立获取数据库客户端并创建新事务（而非使用请求级 session）。
    """
    from graphedu.common.resource.deps import get_db_client

    return get_db_client


async def job_executor(job_id: int, executor_type: str, target: str, args: list, kwargs: dict):
    """任务执行器（由调度器或 Service 层直接调用）。

    根据 executor_type 选择执行方式：
    - python: 动态导入模块并执行目标函数
    - webhook: 调用 webhook_entry 发送 HTTP 请求

    执行结果（成功/失败）均写入任务日志表。
    执行失败时在写完日志后抛出 JobExecuteFailedException。

    Args:
        job_id: 任务ID
        executor_type: 执行器类型（python / webhook）
        target: 调用目标字符串
        args: 位置参数列表
        kwargs: 关键字参数字典

    Raises:
        JobNotFoundException: 任务不存在
        JobConfigInvalidException: 不支持的执行器类型（无日志写入）
        JobExecuteFailedException: 执行失败（日志已写入）
    """
    get_db_client = _get_db_client()
    client = await get_db_client()

    async with client.session_context() as db:
        # 1. 通过 Mapper 查询任务信息
        job_orm = await JobMapper.get_by_id(job_id, db)
        if not job_orm:
            raise JobNotFoundException(job_id=job_id)

        job_name = job_orm.job_name
        job_group = job_orm.job_group

        # 2. 不支持的执行器类型：直接抛异常，不写日志
        if executor_type not in ("python", "webhook"):
            raise JobConfigInvalidException(reason=f"不支持的执行器类型: {executor_type}")

        # 3. 执行任务并捕获运行时错误
        status = "0"
        job_message = ""
        exception_info = None
        exec_error: Exception | None = None

        try:
            if executor_type == "python":
                logger.info(f"执行 Python 函数任务: job_id={job_id}, target={target}")

                parts = target.split(".")
                if len(parts) < 2:
                    raise ValueError(f"无效的调用目标（格式应为 'module.function'）: {target}")

                module_path = ".".join(parts[:-1])
                function_name = parts[-1]

                module = importlib.import_module(module_path)
                func = getattr(module, function_name)

                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                job_message = f"任务执行成功: {result}"

            elif executor_type == "webhook":
                logger.info(f"执行 Webhook 任务: job_id={job_id}, url={job_orm.webhook_url}")

                result = await webhook_entry(
                    job_id,
                    job_orm.webhook_url,
                    job_orm.webhook_secret or "",
                    *args,
                    **kwargs,
                )
                job_message = f"Webhook 调用成功: {result}"

        except Exception as e:
            status = "1"
            exception_info = f"{e!s}\n{traceback.format_exc()}"
            job_message = f"任务执行失败: {e!s}"
            exec_error = e
            logger.error(f"任务执行失败: job_id={job_id}, error={exception_info}")

        # 4. 通过 Mapper 写入执行日志（无论成功或失败）
        log_orm = SysJobLog(
            job_id=job_id,
            job_name=job_name,
            job_group=job_group,
            invoke_target=target,
            job_message=job_message,
            status=status,
            exception_info=exception_info,
        )
        await JobLogMapper.add_log(log_orm, db)
        await db.commit()

        logger.info(f"任务执行完成: job_id={job_id}, status={status}")

    # 5. 日志已落库后再抛出自定义异常（调度器上下文中会被 APScheduler 捕获并记录）
    if exec_error is not None:
        raise JobExecuteFailedException(job_name=job_name, reason=str(exec_error)) from exec_error
