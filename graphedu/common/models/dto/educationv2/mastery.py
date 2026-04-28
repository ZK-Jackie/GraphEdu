"""掌握度 DTO 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery


class StudentMasteryCreateDTO(DTO):
    """创建学生掌握度评估记录 DTO

    用于AI评估完成后记录学生知识点掌握度

    Attributes:
        student_id: 学生ID
        course_id: 课程ID
        node_uuid: 知识点业务UUID（可选）
        session_id: 触发评估的会话ID（可选）
        mastery_score: 掌握度评分（可选）
        mastery_level: 掌握等级（可选）
        trigger_type: 触发类型（可选）
        assessed_at: 评估时间（可选）
    """

    student_id: int = Field(description="学生ID")
    course_id: int = Field(description="课程ID")
    node_uuid: str | None = Field(default=None, description="知识点业务UUID")
    session_id: int | None = Field(default=None, description="触发评估的会话ID")
    mastery_score: float | None = Field(default=None, description="掌握度评分（0-100）")
    mastery_level: Literal["unknown", "low", "medium", "high"] | None = Field(
        default=None, description="掌握等级（unknown/low/medium/high）"
    )
    trigger_type: Literal["quiz_complete", "periodic", "manual", "system"] | None = Field(
        default=None, description="触发类型（quiz_complete/periodic/manual/system）"
    )
    assessed_at: datetime | None = Field(default=None, description="评估时间")


class StudentMasteryQueryDTO(PageQuery):
    """学生掌握度评估记录查询 DTO"""

    student_id: int | None = Field(default=None, description="学生ID")
    course_id: int | None = Field(default=None, description="课程ID")
    node_uuid: str | None = Field(default=None, description="知识点业务UUID")
    mastery_level: Literal["unknown", "low", "medium", "high"] | None = Field(default=None, description="掌握等级")
    trigger_type: str | None = Field(default=None, description="触发类型")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="状态（0正常 1停用 2已删除）")
    begin_time: datetime | None = Field(default=None, description="评估开始时间")
    end_time: datetime | None = Field(default=None, description="评估结束时间")
