"""课程评价相关 DTO 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery


class CourseReviewQueryDTO(PageQuery):
    """课程评价查询 DTO"""

    review_id: int | None = Field(default=None, description="评价ID")
    course_id: int | None = Field(default=None, description="课程ID")
    student_id: int | None = Field(default=None, description="学生ID")
    rating: int | None = Field(default=None, ge=1, le=5, description="整体评分（1-5星）")
    is_visible: Literal["Y", "N"] | None = Field(default=None, description="是否可见（Y/N）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="状态（0正常 1停用 2已删除）")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class CourseReviewCreateDTO(DTO):
    """创建课程评价 DTO

    用于创建新的课程评价

    Attributes:
        course_id: 课程ID
        rating: 整体评分（1-5星）
        content: 评价内容（可选）
        dimension_scores: 分项评分（可选）
    """

    course_id: int = Field(description="课程ID")
    rating: int = Field(ge=1, le=5, description="整体评分（1-5星）")
    content: str | None = Field(default=None, description="评价内容")
    dimension_scores: dict | None = Field(default=None, description="分项评分（JSONB格式）")


class CourseReviewUpdateDTO(DTO):
    """更新课程评价 DTO

    用于更新课程评价

    Attributes:
        review_id: 评价ID
        rating: 整体评分（可选）
        content: 评价内容（可选）
        dimension_scores: 分项评分（可选）
        is_visible: 是否可见（可选）
        status: 状态（可选）
    """

    review_id: int = Field(description="评价ID")
    rating: int | None = Field(default=None, ge=1, le=5, description="整体评分（1-5星）")
    content: str | None = Field(default=None, description="评价内容")
    dimension_scores: dict | None = Field(default=None, description="分项评分（JSONB格式）")
    is_visible: Literal["Y", "N"] | None = Field(default=None, description="是否可见（Y/N）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="状态（0正常 1停用 2已删除）")
