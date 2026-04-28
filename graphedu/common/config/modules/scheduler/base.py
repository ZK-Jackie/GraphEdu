"""调度器配置（对应 scheduler 命名空间）。"""

from pydantic import BaseModel, Field


class SchedulerConfig(BaseModel):
    """APScheduler 调度器配置。"""

    restore_on_startup: bool = Field(
        default=True,
        description="启动时是否从数据库恢复已有的启用任务",
    )

    timezone: str = Field(
        default="Asia/Shanghai",
        description="调度器使用的时区（如 UTC、Asia/Shanghai）",
    )

    misfire_grace_time_default: int = Field(
        default=60,
        description="默认的任务错过宽限时间（秒），策略为'放弃执行'时实际使用 1 秒",
    )
