"""定时任务管理相关 VO 模型 (View Objects - 响应模型)

职责：
1. 定义 API 响应的数据结构
2. 配置序列化规则（from_attributes=True 支持从 ORM 对象创建）
"""

from datetime import datetime

from pydantic import Field
from pydantic_extra_types.cron import CronStr

from graphedu.common.models.vo.base import VO


class JobListVO(VO):
    """定时任务列表项 VO"""

    job_id: int = Field(description="任务ID")
    job_name: str = Field(description="任务名称")
    job_group: str = Field(description="任务分组")
    job_executor: str = Field(description="执行器类型")
    invoke_target: str = Field(description="调用目标字符串")
    cron_expression: CronStr = Field(description="Cron执行表达式")
    misfire_policy: str = Field(description="执行策略")
    concurrent: str = Field(description="是否并发")
    status: str = Field(description="任务状态")
    webhook_enabled: str = Field(default="0", description="是否启用Webhook")
    create_time: datetime | None = Field(default=None, description="创建时间")
    remark: str | None = Field(default=None, description="备注")


class JobDetailVO(VO):
    """定时任务详细信息 VO"""

    job_id: int = Field(description="任务ID")
    job_name: str = Field(description="任务名称")
    job_group: str = Field(description="任务分组")
    job_executor: str = Field(description="执行器类型")
    invoke_target: str = Field(description="调用目标字符串")
    job_args: str | None = Field(default=None, description="位置参数（JSON字符串）")
    job_kwargs: str | None = Field(default=None, description="关键字参数（JSON字符串）")
    cron_expression: CronStr = Field(description="Cron执行表达式")
    misfire_policy: str = Field(description="执行策略")
    concurrent: str = Field(description="是否并发")
    status: str = Field(description="任务状态")
    webhook_enabled: str = Field(default="0", description="是否启用Webhook")
    webhook_url: str | None = Field(default=None, description="Webhook URL")
    webhook_secret: str | None = Field(default=None, description="Webhook密钥")
    webhook_url_display: str | None = Field(default=None, description="外部 Webhook 触发 URL（只读，自动生成）")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    remark: str | None = Field(default=None, description="备注")


class JobLogListVO(VO):
    """任务执行日志列表项 VO"""

    job_log_id: int = Field(description="日志ID")
    job_id: int = Field(description="任务ID")
    job_name: str = Field(description="任务名称")
    job_group: str = Field(description="任务分组")
    invoke_target: str = Field(description="调用目标字符串")
    job_message: str | None = Field(default=None, description="执行信息")
    status: str = Field(description="执行状态（0成功 1失败）")
    exception_info: str | None = Field(default=None, description="异常信息")
    create_time: datetime = Field(description="创建时间")


class JobWebhookInfoVO(VO):
    """任务 Webhook 信息 VO"""

    job_id: int = Field(description="任务ID")
    webhook_enabled: str = Field(description="是否启用Webhook")
    webhook_url: str | None = Field(default=None, description="Webhook URL")
    webhook_secret: str | None = Field(default=None, description="Webhook密钥")


class JobExecuteResultVO(VO):
    """任务执行结果 VO"""

    job_id: int = Field(description="任务ID")
    job_name: str = Field(description="任务名称")
    status: str = Field(description="执行状态（0成功 1失败）")
    message: str = Field(description="执行信息")
