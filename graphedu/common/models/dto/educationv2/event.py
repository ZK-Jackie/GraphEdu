"""学习事件和资料进度 DTO 模型"""

from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO


class LearningEventCreateDTO(DTO):
    """学习事件上报 DTO

    学生端通用事件上报，支持所有学习事件类型。
    """

    student_id: int | None = Field(default=None, description="学生ID，由后端填充")
    course_id: int = Field(description="课程ID")
    event_type: Literal[
        "question",
        "revisit",
        "interest",
        "explain_request",
        "map_click",
        "tool_map_query",
        "ai_assess",
        "chapter_open",
        "chapter_progress",
        "resource_view",
        "resource_progress",
        "resource_complete",
    ] = Field(description="事件类型")
    message_id: str | None = Field(default=None, description="关联消息ID（如事件来源于对话消息）")
    chapter_id: int | None = Field(default=None, description="章节ID")
    node_uuid: str | None = Field(default=None, description="知识点UUID")
    event_source: str | None = Field(default=None, description="事件来源")
    event_content: str | None = Field(default=None, description="事件文本内容")
    event_payload: dict | None = Field(default=None, description="事件扩展数据（JSONB）")
    session_id: int | None = Field(default=None, description="会话ID")
    duration_seconds: int | None = Field(default=None, description="事件持续时长（秒）")


class ResourceProgressReportDTO(DTO):
    """学生上报资料进度 DTO（前端定时/关闭时调用，与管理端 CreateDTO 分离）"""

    resource_id: int = Field(description="资料ID")
    position: dict | None = Field(default=None, description="当前位置（页码/秒数/滚动百分比）")
    duration_seconds: int = Field(default=0, ge=0, description="本次增量时长（秒），后端负责累加")
    completion_rate: int | None = Field(
        default=None, ge=0, le=100, description="完成度（0-100），不传则后端根据 position 自算"
    )
    effective_duration_seconds: int | None = Field(default=None, ge=0, description="本次有效增量时长（秒），排除空闲")
    idle_seconds: int | None = Field(default=None, ge=0, description="本次空闲时长（秒）")
