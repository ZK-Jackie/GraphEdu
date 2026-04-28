"""学生资料阅读进度 VO"""

from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo import VO


class StudentResourceProgressDetailVO(VO):
    """学生资料阅读进度详细信息 VO"""

    progress_id: int = Field(description="进度记录ID")
    student_id: int = Field(description="学生ID")
    course_id: int = Field(description="课程ID")
    chapter_id: int = Field(description="章节ID")
    resource_id: int = Field(description="资料ID（关联edu_resource.resource_id）")
    resource_type: str = Field(description="资料类型（video/document/text）")
    completion_rate: int = Field(default=0, description="完成度（0-100）")
    is_completed: str = Field(description="是否完成（Y/N）")
    view_count: int = Field(default=0, description="阅读次数")
    total_duration: int = Field(default=0, description="累计阅读时长（秒）")
    effective_duration: int = Field(default=0, description="有效阅读时长（秒）")
    review_duration: int = Field(default=0, description="复习时长（秒）")
    first_read_duration: int = Field(default=0, description="首次阅读时长（秒）")
    last_position: dict | None = Field(default=None, description="最后阅读位置（JSONB格式）")
    first_view_time: datetime | None = Field(default=None, description="首次阅读时间")
    last_view_time: datetime | None = Field(default=None, description="最后阅读时间")
    complete_time: datetime | None = Field(default=None, description="完成时间")
    status: str = Field(description="状态（0正常 1停用 2已删除）")
    create_time: datetime = Field(description="创建时间")
    update_time: datetime = Field(description="更新时间")

    # 关联信息
    chapter_name: str | None = Field(default=None, description="章节名称")
    resource_name: str | None = Field(default=None, description="资料名称")
