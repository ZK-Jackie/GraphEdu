"""课程相关 DTO 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery


class CourseQueryDTO(PageQuery):
    """课程查询 DTO"""

    course_id: int | None = Field(default=None, description="课程ID")
    course_code: str | None = Field(default=None, description="课程代码")
    course_name: str | None = Field(default=None, description="课程名称")
    faculty: str | None = Field(default=None, description="所属学院")
    category: str | None = Field(default=None, description="课程分类")
    difficulty_level: Literal["1", "2", "3"] | None = Field(default=None, description="难度级别（1初级 2中级 3高级）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="课程状态（0正常 1停用 2已删除）")
    is_public: Literal["Y", "N"] | None = Field(default=None, description="是否公开（Y是 N否）")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class CourseCreateDTO(DTO):
    """创建课程 DTO

    用于管理员创建新课程，可同时绑定教师。

    Attributes:
        course_code: 课程代码
        course_name: 课程名称
        faculty: 所属学院（可选）
        description: 课程描述（可选）
        cover_file_id: 课程封面文件ID（可选）
        category: 课程分类（可选）
        difficulty_level: 难度级别（可选）
        total_hours: 总学时（可选）
        course_outline: 课程大纲（可选）
        target_audience: 适用人群（可选）
        learning_goals: 学习目标（可选）
        tags: 课程标签（可选）
        is_public: 是否公开（可选）
        teacher_ids: 教师ID列表（可选，提供时自动绑定教师）
    """

    course_code: str = Field(min_length=1, max_length=32, description="课程代码")
    course_name: str = Field(min_length=1, max_length=128, description="课程名称")
    faculty: str | None = Field(default=None, description="所属学院")
    description: str | None = Field(default=None, description="课程描述")
    cover_file_id: int | None = Field(default=None, description="课程封面文件ID")
    category: str | None = Field(default=None, max_length=64, description="课程分类")
    difficulty_level: Literal["1", "2", "3"] | None = Field(default="1", description="难度级别（1初级 2中级 3高级）")
    total_hours: int | None = Field(default=0, description="总学时（小时）")
    course_outline: str | None = Field(default=None, description="课程大纲（富文本）")
    target_audience: str | None = Field(default=None, description="适用人群（富文本）")
    learning_goals: str | None = Field(default=None, description="学习目标（富文本）")
    tags: list[str] | None = Field(default=None, description="课程标签列表")
    is_public: Literal["Y", "N"] | None = Field(default="Y", description="是否公开（Y是 N否）")
    teacher_ids: list[int] = Field(default_factory=list, description="教师ID列表（可选，提供时自动绑定教师）")


class CourseUpdateDTO(DTO):
    """更新课程 DTO

    用于管理员更新课程信息

    Attributes:
        course_id: 课程ID
        course_code: 课程代码（可选）
        course_name: 课程名称（可选）
        faculty: 所属学院（可选）
        description: 课程描述（可选）
        cover_file_id: 课程封面文件ID（可选）
        category: 课程分类（可选）
        difficulty_level: 难度级别（可选）
        total_hours: 总学时（可选）
        course_outline: 课程大纲（可选）
        target_audience: 适用人群（可选）
        learning_goals: 学习目标（可选）
        tags: 课程标签（可选）
        is_public: 是否公开（可选）
        status: 课程状态（可选）
    """

    course_id: int = Field(description="课程ID")
    course_code: str | None = Field(default=None, min_length=1, max_length=32, description="课程代码")
    course_name: str | None = Field(default=None, min_length=1, max_length=128, description="课程名称")
    faculty: str | None = Field(default=None, description="所属学院")
    description: str | None = Field(default=None, description="课程描述")
    cover_file_id: int | None = Field(default=None, description="课程封面文件ID")
    category: str | None = Field(default=None, max_length=64, description="课程分类")
    difficulty_level: Literal["1", "2", "3"] | None = Field(default=None, description="难度级别（1初级 2中级 3高级）")
    total_hours: int | None = Field(default=None, description="总学时（小时）")
    course_outline: str | None = Field(default=None, description="课程大纲（富文本）")
    target_audience: str | None = Field(default=None, description="适用人群（富文本）")
    learning_goals: str | None = Field(default=None, description="学习目标（富文本）")
    tags: list[str] | None = Field(default=None, description="课程标签列表")
    is_public: Literal["Y", "N"] | None = Field(default=None, description="是否公开（Y是 N否）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="课程状态（0正常 1停用 2已删除）")


class CourseTeacherUpdateDTO(DTO):
    """更新课程教师关联 DTO

    用于管理员更新课程的教师关联

    Attributes:
        course_id: 课程ID
        teacher_ids: 教师ID列表
    """

    course_id: int = Field(description="课程ID")
    teacher_ids: list[int] = Field(description="教师ID列表")


class StudentCourseCreateDTO(DTO):
    """学生选课 DTO

    用于学生选择课程

    Attributes:
        course_id: 课程ID
    """

    course_id: int = Field(description="课程ID")


class StudentCourseQueryDTO(PageQuery):
    """学生选课查询 DTO"""

    student_id: int | None = Field(default=None, description="学生ID")
    course_id: int | None = Field(default=None, description="课程ID")
    begin_time: datetime | None = Field(default=None, description="选课开始时间")
    end_time: datetime | None = Field(default=None, description="选课结束时间")


class StudentCourseUpdateDTO(DTO):
    """更新学习进度 DTO

    用于更新学习进度

    Attributes:
        course_id: 课程ID
        progress: 学习进度（0-100）
    """

    course_id: int = Field(description="课程ID")
    progress: int = Field(ge=0, le=100, description="学习进度（0-100）")
