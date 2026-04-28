"""Scheduler Mixin：SchedulerMixin。"""

from dependency_injector import containers, providers

from graphedu.common.config.manager import get_config
from graphedu.common.resource.modules.scheduler.async_scheduler import AsyncSchedulerResource


class SchedulerMixin(containers.DeclarativeContainer):
    """提供 APScheduler 异步调度器资源。

    Attributes:
        scheduler: APScheduler 异步调度器实例，用于定时任务和作业调度。
    """

    scheduler = providers.Resource(
        AsyncSchedulerResource,
        postgresql_config=get_config().datasource.postgresql,
        scheduler_config=get_config().scheduler,
    )
