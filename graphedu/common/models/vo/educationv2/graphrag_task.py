"""GraphRAG 任务 VO 模型。"""
from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo import VO


class GraphRAGTaskListVO(VO):
    """GraphRAG 任务列表项 VO"""

    task_id: int = Field(description="任务ID")
    course_id: int = Field(description="关联课程ID")
    resource_ids: list[int] = Field(description="处理的文档ID列表（JSONB数组）")
    task_status: str = Field(description="任务状态（pending待处理/processing处理中/success成功/failed失败）")
    task_type: str = Field(description="任务类型")
    task_message: str | None = Field(default=None, description="任务最后信息（如果任务失败，记录错误详情）")
    entity_types: list[str] | None = Field(default=None, description="涉及的实体类型列表（JSONB数组）")
    prompt_template: str | None = Field(default=None, description="使用的提示词模板")
    stats: dict | None = Field(default=None, description="任务统计信息（JSONB格式）")
    start_time: datetime | None = Field(default=None, description="任务开始时间")
    end_time: datetime | None = Field(default=None, description="任务结束时间")
    enabled: str = Field(default="N", description="是否启用，对照 sys_data_option（Y是 N否）")
    status: str = Field(description="任务记录状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_time: datetime | None = Field(default=None, description="创建时间")


class GraphRAGTaskDetailVO(GraphRAGTaskListVO):
    """GraphRAG 任务详细信息 VO"""

    custom_prompt_template: dict | None = Field(
        default=None, description="自定义提示词模板（JSONB格式，允许用户覆盖默认模板中的某些部分）"
    )
    create_by: int | None = Field(default=None, description="创建者")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")


class GraphRAGBuildProgressVO(VO):
    """GraphRAG 构建进度 VO（从 Redis 获取）

    用于展示 GraphRAG 构建任务的实时进度信息

    Attributes:
        task_id: 任务ID
        task_status: 任务状态
        current_step: 当前步骤描述
        progress_percent: 进度百分比（0-100）
        stats: 统计信息
        start_time: 开始时间
        estimated_end_time: 预计结束时间
    """

    task_id: int = Field(description="任务ID")
    task_status: str = Field(description="任务状态")
    current_step: str | None = Field(default=None, description="当前步骤描述")
    progress_percent: int = Field(default=0, description="进度百分比（0-100）")
    stats: dict | None = Field(default=None, description="统计信息")
    start_time: datetime | None = Field(default=None, description="开始时间")
    estimated_end_time: datetime | None = Field(default=None, description="预计结束时间")
