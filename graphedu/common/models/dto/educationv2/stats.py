"""统计 DTO 模型。"""
from datetime import date, datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import PageQuery


class ChapterProgressQueryDTO(PageQuery):
    """章节进度查询 DTO（查询物化视图）"""

    student_id: int | None = Field(default=None, description="学生ID")
    chapter_id: int | None = Field(default=None, description="章节ID")
    is_completed: Literal["Y", "N"] | None = Field(default=None, description="是否完成（Y/N）")
    begin_time: datetime | None = Field(default=None, description="开始时间")
    end_time: datetime | None = Field(default=None, description="结束时间")


class StudyAnalyticsQueryDTO(PageQuery):
    """学习分析视图通用查询 DTO

    用于查询各种学习分析视图，支持按学生、课程、章节、时间范围筛选
    """

    student_id: int | None = Field(default=None, description="学生ID")
    course_id: int | None = Field(default=None, description="课程ID")
    chapter_id: int | None = Field(default=None, description="章节ID")
    node_uuid: str | None = Field(default=None, description="知识点UUID")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")
    study_date: date | None = Field(default=None, description="学习日期（用于日级统计）")
