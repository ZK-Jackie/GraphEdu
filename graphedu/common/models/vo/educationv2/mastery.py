"""掌握度 VO 模型。"""
from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo import VO


class StudentMasteryListVO(VO):
    """学生知识点掌握度评估记录列表项 VO"""

    mastery_id: int = Field(description="评估记录ID")
    student_id: int = Field(description="学生ID")
    course_id: int = Field(description="课程ID")
    node_uuid: str | None = Field(default=None, description="知识点业务UUID")
    mastery_score: float | None = Field(default=None, description="掌握度评分（0-100）")
    mastery_level: str | None = Field(default=None, description="掌握等级（unknown/low/medium/high）")
    trigger_type: str | None = Field(default=None, description="触发类型")
    assessed_at: datetime | None = Field(default=None, description="评估时间")
    create_time: datetime | None = Field(default=None, description="创建时间")

    # 关联信息
    student_name: str | None = Field(default=None, description="学生姓名")
    course_name: str | None = Field(default=None, description="课程名称")
    node_title: str | None = Field(default=None, description="知识点标题")


class StudentMasteryDetailVO(StudentMasteryListVO):
    """学生知识点掌握度评估记录详细信息 VO"""

    session_id: int | None = Field(default=None, description="触发评估的会话ID")
    status: str = Field(default="0", description="状态（0正常 1停用 2已删除）")
    update_time: datetime | None = Field(default=None, description="更新时间")
