"""通用异步任务 DTO 模型。"""

from datetime import datetime

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery


class AsyncTaskQueryDTO(PageQuery):
    """异步任务查询 DTO"""

    task_type: str | None = Field(default=None, description="任务类型标识")
    task_status: str | None = Field(default=None, description="任务状态")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class AsyncTaskCreateDTO(DTO):
    """创建异步任务 DTO（内部使用，由业务 Service 调用）"""

    task_name: str = Field(description="任务名称")
    task_type: str = Field(description="任务类型标识")
    task_params: dict | list | None = Field(default=None, description="任务输入参数")
    user_id: int | None = Field(default=None, description="提交者用户ID")
    celery_task_id: str | None = Field(default=None, description="Celery 任务 ID")
