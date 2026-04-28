"""聊天 VO 模型。"""
from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo import VO
from graphedu.common.models.vo.educationv2.course import CourseListVO


class ChatSessionDetailVO(VO):
    """对话会话详细信息 VO"""

    conv_id: int = Field(description="对话ID")
    user_id: int = Field(description="用户ID")
    course_id: int | None = Field(default=None, description="关联课程ID")
    title: str | None = Field(default=None, description="会话标题")
    context_summary: str | None = Field(default=None, description="上下文摘要")
    message_count: int = Field(default=0, description="消息数量")
    status: str = Field(description="聊天会话状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    last_message_time: datetime = Field(description="最后消息时间")

    # 关联的课程信息
    course: CourseListVO | None = Field(default=None, description="关联课程信息")


class ChatSessionListVO(VO):
    """对话会话列表项 VO"""

    conv_id: int = Field(description="对话ID")
    user_id: int = Field(description="用户ID")
    course_id: int | None = Field(default=None, description="关联课程ID")
    title: str | None = Field(default=None, description="会话标题")
    message_count: int = Field(default=0, description="消息数量")
    status: str = Field(description="聊天会话状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_time: datetime | None = Field(default=None, description="创建时间")
    last_message_time: datetime = Field(description="最后消息时间")

    # 关联的课程信息
    course_name: str | None = Field(default=None, description="关联课程名称")
