"""教师 VO 模型。"""
from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo import VO


class TeacherListVO(VO):
    """教师列表项 VO"""

    teacher_id: int = Field(description="教师ID（关联user_id）")
    real_name: str = Field(description="真实姓名")
    teacher_no: str | None = Field(default=None, description="工号")
    faculty: str | None = Field(default=None, description="所属学院")
    title: str | None = Field(default=None, description="职称：教授/副教授/讲师/助教")
    max_student_count: int = Field(default=100, description="最大带教学生数")
    current_student_count: int | None = Field(default=None, description="当前学生数")
    status: str = Field(description="教师状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_time: datetime | None = Field(default=None, description="创建时间")

    # 关联信息
    user_id: int | None = Field(default=None, description="用户ID")
    user_name: str | None = Field(default=None, description="用户账号")
    avatar_file_id: int | None = Field(default=None, description="头像文件ID")


class TeacherDetailVO(TeacherListVO):
    """教师详细信息 VO"""

    research_direction: str | None = Field(default=None, description="研究方向")
    description: str | None = Field(default=None, description="个人简介")
    create_by: int | None = Field(default=None, description="创建者")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
