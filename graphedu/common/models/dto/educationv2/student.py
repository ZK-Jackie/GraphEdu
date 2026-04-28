"""学生相关 DTO 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery


class StudentQueryDTO(PageQuery):
    """学生查询 DTO"""

    student_id: int | None = Field(default=None, description="学生ID")
    real_name: str | None = Field(default=None, description="真实姓名")
    student_no: str | None = Field(default=None, description="学号")
    faculty: str | None = Field(default=None, description="学院")
    major: str | None = Field(default=None, description="专业")
    grade: str | None = Field(default=None, description="年级")
    class_name: str | None = Field(default=None, description="班级")
    gender: Literal["0", "1", "2", "9"] | None = Field(default=None, description="性别（0未知 1男 2女 9其他）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="学生状态（0正常 1停用 2已删除）")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class StudentCreateDTO(DTO):
    """创建学生 DTO

    用于管理员创建新学生

    Attributes:
        student_id: 学生ID（关联user_id）
        real_name: 真实姓名
        student_no: 学号（可选）
        faculty: 学院（可选）
        major: 专业（可选）
        grade: 年级（可选）
        class_name: 班级（可选）
        gender: 性别（可选）
        age: 年龄（可选）
        description: 自我介绍（可选）
    """

    student_id: int = Field(description="学生ID（关联user_id）")
    real_name: str = Field(description="真实姓名")
    student_no: str | None = Field(default=None, description="学号")
    faculty: str | None = Field(default=None, description="学院")
    major: str | None = Field(default=None, description="专业")
    grade: str | None = Field(default=None, description="年级")
    class_name: str | None = Field(default=None, description="班级")
    gender: Literal["0", "1", "2", "9"] | None = Field(default=None, description="性别（0未知 1男 2女 9其他）")
    age: int | None = Field(default=None, description="年龄")
    description: str | None = Field(default=None, description="自我介绍")


class StudentUpdateDTO(DTO):
    """更新学生 DTO

    用于管理员更新学生信息

    Attributes:
        student_id: 学生ID
        real_name: 真实姓名（可选）
        student_no: 学号（可选）
        faculty: 学院（可选）
        major: 专业（可选）
        grade: 年级（可选）
        class_name: 班级（可选）
        gender: 性别（可选）
        age: 年龄（可选）
        study_style: 学习风格（可选）
        study_habit: 学习习惯（可选）
        description: 自我介绍（可选）
        status: 学生状态（可选）
    """

    student_id: int = Field(description="学生ID")
    real_name: str | None = Field(default=None, description="真实姓名")
    student_no: str | None = Field(default=None, description="学号")
    faculty: str | None = Field(default=None, description="学院")
    major: str | None = Field(default=None, description="专业")
    grade: str | None = Field(default=None, description="年级")
    class_name: str | None = Field(default=None, description="班级")
    gender: Literal["0", "1", "2", "9"] | None = Field(default=None, description="性别（0未知 1男 2女 9其他）")
    age: int | None = Field(default=None, description="年龄")
    study_style: str | None = Field(default=None, description="学习风格")
    study_habit: str | None = Field(default=None, description="学习习惯")
    description: str | None = Field(default=None, description="自我介绍")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="学生状态（0正常 1停用 2已删除）")
