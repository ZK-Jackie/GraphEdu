"""聊天相关 DTO 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery


class ChatSessionCreateDTO(DTO):
    """创建对话会话 DTO

    用于创建新的对话会话

    Attributes:
        title: 会话标题（可选）
        course_id: 关联课程ID（可选）
    """

    title: str | None = Field(default=None, description="会话标题")
    course_id: int | None = Field(default=None, description="关联课程ID")


class ChatSessionUpdateDTO(DTO):
    """更新对话会话 DTO

    用于更新对话会话信息

    Attributes:
        session_id: 会话ID
        title: 会话标题（可选）
        context_summary: 上下文摘要（可选）
    """

    session_id: int = Field(description="会话ID")
    title: str | None = Field(default=None, description="会话标题")
    context_summary: str | None = Field(default=None, description="上下文摘要")


class ChatSessionQueryDTO(PageQuery):
    """对话会话查询 DTO"""

    session_id: int | None = Field(default=None, description="会话ID")
    user_id: int | None = Field(default=None, description="用户ID")
    course_id: int | None = Field(default=None, description="关联课程ID")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="聊天会话状态（0正常 1停用 2已删除）")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class ChatSessionUpdateTitleDTO(DTO):
    """更新对话会话标题 DTO。"""

    title: str = Field(min_length=1, max_length=255, description="会话标题")
