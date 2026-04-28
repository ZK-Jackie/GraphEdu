"""定时任务管理相关 DTO 模块

本模块定义了定时任务管理相关的数据传输对象，包括：

- **JobQueryDTO**: 任务查询 DTO
- **JobCreateDTO**: 创建任务 DTO
- **JobUpdateDTO**: 更新任务 DTO
- **JobStatusChangeDTO**: 修改任务状态 DTO
- **JobExecuteOnceDTO**: 执行一次任务 DTO
- **JobWebhookConfigDTO**: Webhook 配置 DTO
"""

import json
import re
from typing import Literal

from pydantic import Field, model_validator
from pydantic_extra_types.cron import CronStr

from graphedu.common.models.dto.base import DTO, PageQuery


# ============================================================================
# 定时任务查询相关 DTO
# ============================================================================
class JobQueryDTO(PageQuery):
    """定时任务查询 DTO

    用于查询定时任务列表

    Attributes:
        job_name: 任务名称（可选）
        job_group: 任务分组（可选）
        status: 任务状态（可选）
        job_executor: 执行器类型（可选）
    """

    job_name: str | None = Field(default=None, description="任务名称")
    job_group: str | None = Field(default=None, description="任务分组（DEFAULT, SYSTEM）")
    status: Literal["0", "1"] | None = Field(default=None, description="任务状态（0正常 1暂停）")
    job_executor: str | None = Field(default=None, description="执行器类型（python, webhook）")


# ============================================================================
# 定时任务创建/更新相关 DTO
# ============================================================================
class JobCreateDTO(DTO):
    """创建定时任务 DTO

    用于管理员创建新的定时任务

    Attributes:
        job_name: 任务名称
        job_group: 任务分组（DEFAULT=默认, SYSTEM=系统）
        job_executor: 执行器类型（python=Python函数, webhook=Webhook调用）
        invoke_target: 调用目标字符串
        job_args: 位置参数（可选，JSON字符串）
        job_kwargs: 关键字参数（可选，JSON字符串）
        cron_expression: Cron执行表达式
        misfire_policy: 执行策略（1=立即执行, 2=执行一次, 3=放弃执行）
        concurrent: 是否并发（0=禁止, 1=允许）
        status: 任务状态（0=正常, 1=暂停）
        webhook_enabled: 是否启用Webhook（可选）
        webhook_url: Webhook URL（可选）
        webhook_secret: Webhook密钥（可选）
        remark: 备注（可选）
    """

    job_name: str = Field(description="任务名称")
    job_group: Literal["DEFAULT", "SYSTEM"] = Field(default="DEFAULT", description="任务分组")
    job_executor: Literal["python", "webhook"] = Field(default="python", description="执行器类型")
    invoke_target: str = Field(description="调用目标字符串")
    job_args: str | None = Field(default=None, description="位置参数（JSON字符串）")
    job_kwargs: str | None = Field(default=None, description="关键字参数（JSON字符串）")
    cron_expression: CronStr = Field(description="Cron执行表达式")
    misfire_policy: Literal["1", "2", "3"] = Field(default="1", description="执行策略")
    concurrent: Literal["0", "1"] = Field(default="0", description="是否并发")
    status: Literal["0", "1"] = Field(default="0", description="任务状态")
    webhook_enabled: Literal["0", "1"] = Field(default="0", description="是否启用Webhook")
    webhook_url: str | None = Field(default=None, description="Webhook URL")
    webhook_secret: str | None = Field(default=None, description="Webhook密钥")
    remark: str | None = Field(default=None, description="备注")

    @model_validator(mode="after")
    def validate_job(self) -> "JobCreateDTO":
        """验证任务数据

        验证内容包括：
        1. Cron表达式格式
        2. JSON参数格式
        3. Webhook配置（当执行器类型为webhook时）

        Returns:
            验证通过的任务对象

        Raises:
            ValueError: 验证失败时抛出
        """
        # 验证Cron表达式
        if self.cron_expression and not self._validate_cron_expression(self.cron_expression):
            raise ValueError("Cron表达式格式无效")

        # 验证JSON参数
        if self.job_args:
            try:
                json.loads(self.job_args)
            except json.JSONDecodeError as e:
                raise ValueError("位置参数(job_args)必须是有效的JSON字符串") from e

        if self.job_kwargs:
            try:
                json.loads(self.job_kwargs)
            except json.JSONDecodeError as e:
                raise ValueError("关键字参数(job_kwargs)必须是有效的JSON字符串") from e

        # 验证Webhook配置
        if self.job_executor == "webhook" and self.webhook_enabled == "1" and not self.webhook_url:
            raise ValueError("启用Webhook时必须提供webhook_url")

        return self

    @staticmethod
    def _validate_cron_expression(expression: str) -> bool:
        """验证Cron表达式格式

        支持6位或7位Cron表达式：
        - 6位：秒 分 时 日 月 周
        - 7位：秒 分 时 日 月 周 年

        Args:
            expression: Cron表达式

        Returns:
            是否为有效的Cron表达式
        """
        # Cron表达式基本格式验证
        pattern = (
            r"^([0-9\*\-/\,?LW]+)\s+"
            r"([0-9\*\-/\,?LW]+)\s+"
            r"([0-9\*\-/\,?LW]+)\s+"
            r"([0-9\*\-/\,?LW]+)\s+"
            r"([0-9\*\-/\,?LW]+)\s+"
            r"([0-9\*\-/\,?LW?]+)"
            r"(?:\s+([0-9\*\-/\,?LW]+))?$"
        )
        return bool(re.match(pattern, expression.strip()))


class JobUpdateDTO(DTO):
    """更新定时任务 DTO

    用于管理员更新定时任务信息

    Attributes:
        job_id: 任务 ID（必需）
        job_name: 任务名称（可选）
        job_group: 任务分组（可选）
        job_executor: 执行器类型（可选）
        invoke_target: 调用目标字符串（可选）
        job_args: 位置参数（可选，JSON字符串）
        job_kwargs: 关键字参数（可选，JSON字符串）
        cron_expression: Cron执行表达式（可选）
        misfire_policy: 执行策略（可选）
        concurrent: 是否并发（可选）
        status: 任务状态（可选）
        webhook_enabled: 是否启用Webhook（可选）
        webhook_url: Webhook URL（可选）
        webhook_secret: Webhook密钥（可选）
        remark: 备注（可选）
    """

    job_id: int = Field(description="任务ID")
    job_name: str | None = Field(default=None, description="任务名称")
    job_group: Literal["DEFAULT", "SYSTEM"] | None = Field(default=None, description="任务分组")
    job_executor: Literal["python", "webhook"] | None = Field(default=None, description="执行器类型")
    invoke_target: str | None = Field(default=None, description="调用目标字符串")
    job_args: str | None = Field(default=None, description="位置参数（JSON字符串）")
    job_kwargs: str | None = Field(default=None, description="关键字参数（JSON字符串）")
    cron_expression: CronStr | None = Field(default=None, description="Cron执行表达式")
    misfire_policy: Literal["1", "2", "3"] | None = Field(default=None, description="执行策略")
    concurrent: Literal["0", "1"] | None = Field(default=None, description="是否并发")
    status: Literal["0", "1"] | None = Field(default=None, description="任务状态")
    webhook_enabled: Literal["0", "1"] | None = Field(default=None, description="是否启用Webhook")
    webhook_url: str | None = Field(default=None, description="Webhook URL")
    webhook_secret: str | None = Field(default=None, description="Webhook密钥")
    remark: str | None = Field(default=None, description="备注")

    @model_validator(mode="after")
    def validate_job(self) -> "JobUpdateDTO":
        """验证任务数据

        与JobCreateDTO的验证逻辑相同

        Returns:
            验证通过的任务对象

        Raises:
            ValueError: 验证失败时抛出
        """
        # 验证Cron表达式
        if self.cron_expression and not JobCreateDTO._validate_cron_expression(self.cron_expression):
            raise ValueError("Cron表达式格式无效")

        # 验证JSON参数
        if self.job_args:
            try:
                json.loads(self.job_args)
            except json.JSONDecodeError as e:
                raise ValueError("位置参数(job_args)必须是有效的JSON字符串") from e

        if self.job_kwargs:
            try:
                json.loads(self.job_kwargs)
            except json.JSONDecodeError as e:
                raise ValueError("关键字参数(job_kwargs)必须是有效的JSON字符串") from e

        return self


class JobStatusChangeDTO(DTO):
    """修改定时任务状态 DTO

    用于启用或停用定时任务

    Attributes:
        job_id: 任务 ID
        status: 任务状态（0正常 1暂停）
    """

    job_id: int = Field(description="任务ID")
    status: Literal["0", "1"] = Field(description="任务状态（0正常 1暂停）")


class JobExecuteOnceDTO(DTO):
    """执行一次任务 DTO

    用于立即执行一次定时任务

    Attributes:
        job_id: 任务 ID
    """

    job_id: int = Field(description="任务ID")


# ============================================================================
# 任务日志查询相关 DTO
# ============================================================================
class JobLogQueryDTO(PageQuery):
    """任务日志查询 DTO

    用于查询任务执行日志

    Attributes:
        job_id: 任务ID（可选）
        job_name: 任务名称（可选）
        job_group: 任务分组（可选）
        status: 执行状态（可选）
    """

    job_id: int | None = Field(default=None, description="任务ID")
    job_name: str | None = Field(default=None, description="任务名称")
    job_group: str | None = Field(default=None, description="任务分组")
    status: Literal["0", "1"] | None = Field(default=None, description="执行状态（0成功 1失败）")
