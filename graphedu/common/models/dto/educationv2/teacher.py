"""教师相关 DTO 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery


class TeacherQueryDTO(PageQuery):
    """教师查询 DTO"""

    teacher_id: int | None = Field(default=None, description="教师ID")
    real_name: str | None = Field(default=None, description="真实姓名")
    teacher_no: str | None = Field(default=None, description="工号")
    faculty: str | None = Field(default=None, description="所属学院")
    title: str | None = Field(default=None, description="职称")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="教师状态（0正常 1停用 2已删除）")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class TeacherCreateDTO(DTO):
    """创建教师 DTO

    用于管理员创建新教师

    Attributes:
        teacher_id: 教师ID（关联user_id）
        real_name: 真实姓名
        teacher_no: 工号（可选）
        faculty: 所属学院（可选）
        title: 职称（可选）
        research_direction: 研究方向（可选）
        description: 个人简介（可选）
    """

    teacher_id: int = Field(description="教师ID（关联user_id）")
    real_name: str = Field(description="真实姓名")
    teacher_no: str | None = Field(default=None, description="工号")
    faculty: str | None = Field(default=None, description="所属学院")
    title: str | None = Field(default=None, description="职称：教授/副教授/讲师/助教")
    research_direction: str | None = Field(default=None, description="研究方向")
    description: str | None = Field(default=None, description="个人简介")


class TeacherUpdateDTO(DTO):
    """更新教师 DTO

    用于管理员更新教师信息

    Attributes:
        teacher_id: 教师ID
        real_name: 真实姓名（可选）
        teacher_no: 工号（可选）
        faculty: 所属学院（可选）
        title: 职称（可选）
        research_direction: 研究方向（可选）
        description: 个人简介（可选）
        status: 教师状态（可选）
    """

    teacher_id: int = Field(description="教师ID")
    real_name: str | None = Field(default=None, description="真实姓名")
    teacher_no: str | None = Field(default=None, description="工号")
    faculty: str | None = Field(default=None, description="所属学院")
    title: str | None = Field(default=None, description="职称：教授/副教授/讲师/助教")
    research_direction: str | None = Field(default=None, description="研究方向")
    description: str | None = Field(default=None, description="个人简介")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="教师状态（0正常 1停用 2已删除）")
