"""通用异步任务 VO 模型。"""

from datetime import datetime
from typing import Any

from pydantic import Field

from graphedu.common.models.vo import VO


class AsyncTaskVO(VO):
    """异步任务列表项 VO"""

    task_id: int = Field(description="任务ID")
    task_name: str = Field(description="任务名称")
    task_type: str = Field(description="任务类型标识")
    task_status: str = Field(description="任务状态")
    progress_percent: int = Field(default=0, description="进度百分比 (0-100)")
    task_message: str | None = Field(default=None, description="进度描述或错误信息")
    user_id: int | None = Field(default=None, description="提交者用户ID")
    start_time: datetime | None = Field(default=None, description="开始执行时间")
    end_time: datetime | None = Field(default=None, description="完成时间")
    create_time: datetime | None = Field(default=None, description="创建时间")


class AsyncTaskDetailVO(AsyncTaskVO):
    """异步任务详情 VO"""

    task_params: dict[str, Any] | list | None = Field(default=None, description="任务输入参数")
    task_result: dict[str, Any] | list | None = Field(default=None, description="任务输出结果")
    celery_task_id: str | None = Field(default=None, description="Celery 任务 ID")
    create_by: int | None = Field(default=None, description="创建者")
    update_time: datetime | None = Field(default=None, description="更新时间")


class AsyncTaskProgressVO(VO):
    """异步任务进度 VO（用于轮询查询）"""

    task_id: int = Field(description="任务ID")
    task_status: str = Field(description="任务状态 (pending/processing/success/failed/cancelled)")
    progress_percent: int = Field(default=0, description="进度百分比 (0-100)")
    task_message: str | None = Field(default=None, description="进度描述或错误信息")
    task_result: dict[str, Any] | list | None = Field(default=None, description="任务输出结果（成功时有效）")
