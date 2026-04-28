"""APScheduler 资源类模块。

提供 APScheduler 的资源类，负责调度器的生命周期管理、启动时任务恢复及调度操作。
"""

from collections.abc import Callable
import contextlib
import json
import logging
from typing import Self

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from graphedu.common.config.modules.datasource import PostgresqlConfig
from graphedu.common.config.modules.scheduler import SchedulerConfig
from graphedu.common.exceptions import (
    JobChangeStatusFailedException,
    JobCronInvalidException,
)
from graphedu.common.resource.core.base import BaseAsyncResource
from graphedu.jobs.job_executor import job_executor
from graphedu.mapper.system.job import JobMapper

logger = logging.getLogger(__name__)


class AsyncSchedulerResource(BaseAsyncResource):
    """APScheduler 资源类。

    管理 APScheduler 的完整生命周期，包括：
    1. 启动调度器
    2. 根据配置从数据库恢复已有的启用任务
    3. 正确关闭调度器
    4. 提供任务调度操作（添加、移除、暂停、恢复）
    """

    _scheduler: AsyncIOScheduler | None = None
    _scheduler_config: SchedulerConfig | None = None

    async def init(self, postgresql_config: PostgresqlConfig, scheduler_config: SchedulerConfig) -> Self:
        """初始化调度器，并在配置允许时从数据库恢复已有任务。

        Args:
            postgresql_config: PostgreSQL 配置（用于连接数据库获取任务列表）
            scheduler_config: 调度器配置（控制恢复行为、时区等）

        Returns:
            Self: 返回自身实例
        """
        self._scheduler_config = scheduler_config
        self._scheduler = AsyncIOScheduler(timezone=scheduler_config.timezone)
        self._scheduler.start()
        logger.info("APScheduler started successfully")

        if scheduler_config.restore_on_startup:
            await self._restore_jobs(postgresql_config)

        return self

    async def _restore_jobs(self, postgresql_config: PostgresqlConfig) -> None:
        """从数据库恢复已启用的定时任务到调度器。

        使用独立的数据库引擎（不依赖 DI 容器），避免启动时序问题。
        通过 Mapper 层查询任务数据，遵循分层架构约束。
        """
        engine = create_async_engine(str(postgresql_config.get_sa_async_dsn()), echo=False, pool_pre_ping=True)
        restored_count = 0
        failed_count = 0

        try:
            async with AsyncSession(engine) as session:
                jobs = await JobMapper.get_job_list_for_scheduler(session)

            for job in jobs:
                try:
                    await self.add_job(
                        func=job_executor,
                        job_id=job.job_id,
                        cron_expression=job.cron_expression,
                        executor_type=job.job_executor,
                        target=job.invoke_target,
                        args=job.job_args,
                        kwargs=job.job_kwargs,
                        misfire_policy=job.misfire_policy,
                        job_name=job.job_name,
                    )
                    restored_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.warning(f"Scheduler restore failed for job_id={job.job_id}: error={e}")

        except Exception as e:
            logger.error(f"Scheduler restore failed: error={e}")
        finally:
            await engine.dispose()
        logger.info(f"Scheduler restore completed: restored={restored_count}, failed={failed_count}")

    async def shutdown(self, instance: "AsyncSchedulerResource" = None):
        """正确关闭调度器。

        Args:
            instance: 调度器实例（可选，用于 dependency_injector 资源管理）
        """
        scheduler = self._scheduler
        if scheduler and scheduler.running:
            with contextlib.suppress(Exception):
                await scheduler.shutdown(wait=True)
            logger.info("APScheduler shutdown complete")
        self._scheduler = None

    # ========================================================================
    # 调度器操作方法
    # ========================================================================

    async def add_job(
        self,
        func: Callable,
        job_id: int,
        cron_expression: str,
        executor_type: str,
        target: str,
        args: str | None = None,
        kwargs: str | None = None,
        misfire_policy: str = "1",
        job_name: str | None = None,
    ) -> None:
        """添加任务到调度器。

        Args:
            func: 任务执行函数（如 job_executor）
            job_id: 任务ID
            cron_expression: 6 位 Cron 表达式（秒 分 时 日 月 周）
            executor_type: 执行器类型（python / webhook）
            target: 调用目标字符串
            args: 位置参数（JSON 字符串），可为 None
            kwargs: 关键字参数（JSON 字符串），可为 None
            misfire_policy: 错过执行策略（1=立即补跑, 2=执行一次, 3=放弃）
            job_name: 任务名称（可选，用于调度器显示）

        Raises:
            JobCronInvalidException: Cron 表达式格式不合法
        """
        cron_parts = cron_expression.strip().split()
        if len(cron_parts) < 6:
            raise JobCronInvalidException(cron_expression=cron_expression)

        second, minute, hour, day, month, day_of_week = cron_parts[:6]

        parsed_args = json.loads(args) if args else []
        parsed_kwargs = json.loads(kwargs) if kwargs else {}

        default_grace = self._scheduler_config.misfire_grace_time_default if self._scheduler_config else 60
        if misfire_policy == "1":
            misfire_grace_time = 3600
        elif misfire_policy == "2":
            misfire_grace_time = default_grace
        else:
            misfire_grace_time = 1

        self._scheduler.add_job(
            func,
            trigger=CronTrigger(
                second=second,
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
            ),
            args=[job_id, executor_type, target, parsed_args, parsed_kwargs],
            id=str(job_id),
            name=job_name or f"job_{job_id}",
            misfire_grace_time=misfire_grace_time,
            replace_existing=True,
        )

        logger.info(f"任务添加到调度器: job_id={job_id}, cron={cron_expression}")

    async def remove_job(self, job_id: int) -> None:
        """从调度器移除任务。

        移除失败时仅记录 warning，不抛出异常（任务可能已不在调度器中）。

        Args:
            job_id: 任务ID
        """
        try:
            self._scheduler.remove_job(str(job_id))
            logger.info(f"任务已从调度器移除: job_id={job_id}")
        except Exception as e:
            logger.warning(f"从调度器移除任务失败（可能已不存在）: job_id={job_id}, error={e}")

    async def pause_job(self, job_id: int) -> None:
        """暂停调度器中的任务。

        Args:
            job_id: 任务ID

        Raises:
            JobChangeStatusFailedException: 暂停失败
        """
        try:
            self._scheduler.pause_job(str(job_id))
            logger.info(f"任务已暂停: job_id={job_id}")
        except Exception as e:
            logger.error(f"任务暂停失败: job_id={job_id}, error={e}")
            raise JobChangeStatusFailedException(job_id=job_id) from e

    async def resume_job(self, job_id: int) -> None:
        """恢复调度器中已暂停的任务。

        Args:
            job_id: 任务ID

        Raises:
            JobChangeStatusFailedException: 恢复失败
        """
        try:
            self._scheduler.resume_job(str(job_id))
            logger.info(f"任务已恢复: job_id={job_id}")
        except Exception as e:
            logger.error(f"任务恢复失败: job_id={job_id}, error={e}")
            raise JobChangeStatusFailedException(job_id=job_id) from e

    def is_job_running(self, job_id: int) -> bool:
        """检查任务是否已在调度器中注册且有下次运行计划。

        Args:
            job_id: 任务ID

        Returns:
            bool: 任务存在且未暂停时返回 True
        """
        job = self._scheduler.get_job(str(job_id))
        return job is not None and job.next_run_time is not None
