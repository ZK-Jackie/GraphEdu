"""学生 VO 模型。"""
from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo import VO


class StudentListVO(VO):
    """学生列表项 VO"""

    student_id: int = Field(description="学生ID（关联user_id）")
    real_name: str = Field(description="真实姓名")
    student_no: str | None = Field(default=None, description="学号")
    faculty: str | None = Field(default=None, description="学院")
    major: str | None = Field(default=None, description="专业")
    grade: str | None = Field(default=None, description="年级")
    class_name: str | None = Field(default=None, description="班级")
    gender: int | None = Field(default=None, description="性别，对照 sys_user_sex（1男 2女 0未知 9其他）")
    status: str = Field(description="学生状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_time: datetime | None = Field(default=None, description="创建时间")

    # 关联信息
    user_id: int = Field(default=None, description="用户ID")
    user_name: str | None = Field(default=None, description="用户账号")
    avatar_file_id: int | None = Field(default=None, description="头像文件ID")


class StudentDetailVO(StudentListVO):
    """学生详细信息 VO"""

    age: int | None = Field(default=None, description="年龄")
    study_style: str | None = Field(default=None, description="学习风格")
    study_habit: str | None = Field(default=None, description="学习习惯")
    continue_day: int = Field(default=0, description="连续签到天数")
    vip_level: int = Field(default=0, description="VIP等级")
    vip_expire_time: datetime | None = Field(default=None, description="VIP过期时间")
    total_study_time: int | None = Field(default=None, description="总学习时长（分钟）")
    course_count: int | None = Field(default=None, description="学习课程数")
    description: str | None = Field(default=None, description="自我介绍")
    create_by: int | None = Field(default=None, description="创建者")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
