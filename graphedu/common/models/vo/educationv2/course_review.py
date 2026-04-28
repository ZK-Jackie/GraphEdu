"""课程评价 VO 模型。"""
from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo import VO
from graphedu.common.models.vo.educationv2.course import CourseListVO
from graphedu.common.models.vo.educationv2.student import StudentListVO


class CourseReviewDetailVO(VO):
    """课程评价详细信息 VO"""

    review_id: int = Field(description="评价ID")
    course_id: int = Field(description="课程ID")
    student_id: int = Field(description="学生ID")
    rating: int = Field(description="整体评分（1-5星）")
    content: str | None = Field(default=None, description="评价内容")
    dimension_scores: dict | None = Field(default=None, description="分项评分（JSONB格式）")
    like_count: int = Field(default=0, description="点赞数")
    status: str = Field(description="状态（0正常 1停用 2已删除）")
    is_visible: str = Field(description="是否可见（Y/N）")
    create_by: int | None = Field(default=None, description="创建者")
    create_time: datetime | None = Field(default=None, description="创建时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")

    # 关联信息
    course: CourseListVO | None = Field(default=None, description="关联课程信息")
    student: StudentListVO | None = Field(default=None, description="评价学生信息")


class CourseReviewListVO(VO):
    """课程评价列表项 VO"""

    review_id: int = Field(description="评价ID")
    course_id: int = Field(description="课程ID")
    student_id: int = Field(description="学生ID")
    rating: int = Field(description="整体评分（1-5星）")
    content: str | None = Field(default=None, description="评价内容")
    dimension_scores: dict | None = Field(default=None, description="分项评分（JSONB格式）")
    like_count: int = Field(default=0, description="点赞数")
    is_visible: str = Field(description="是否可见（Y/N）")
    status: str = Field(description="状态（0正常 1停用 2已删除）")
    create_time: datetime | None = Field(default=None, description="创建时间")

    # 关联信息
    course_name: str | None = Field(default=None, description="课程名称")
    student_name: str | None = Field(default=None, description="学生姓名")
    avatar_file_id: int | None = Field(default=None, description="学生头像ID")
