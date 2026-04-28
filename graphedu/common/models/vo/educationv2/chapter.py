"""章节 VO 模型。"""
from datetime import datetime
from typing import Any

from pydantic import Field

from graphedu.common.models.vo import VO
from graphedu.common.models.vo.educationv2.course import CourseListVO


class ChapterCompletionItemVO(VO):
    """教师工作台：章节完成率列表项 VO"""

    chapter_id: int = Field(description="章节ID")
    chapter: str = Field(description="章节名称")
    completion: int = Field(default=0, description="平均完成率（0-100）")
    students: int = Field(default=0, description="有学习记录的学生数")


class ChapterListVO(VO):
    """章节列表项 VO"""

    chapter_id: int = Field(description="章节ID")
    course_id: int = Field(description="课程ID")
    parent_id: int = Field(description="父章节ID（0表示根节点）")
    chapter_name: str = Field(description="章节名称")
    chapter_no: int = Field(default=0, description="章节序号（用于排序）")
    description: str | None = Field(default=None, description="章节描述")
    status: str = Field(description="章节状态，对照 sys_data_status（0正常 1停用 2已删除）")
    create_time: datetime | None = Field(default=None, description="创建时间")


class ChapterDetailVO(ChapterListVO):
    """章节详细信息 VO"""

    create_by: int | None = Field(default=None, description="创建者")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")

    # 关联信息（使用 Any 暂时绕过前向引用，model_rebuild() 在文件末尾解析）
    course: CourseListVO | None = Field(default=None, description="关联课程信息")
    resources: list[Any] | None = Field(default=None, description="章节资料列表")
    progress: Any | None = Field(default=None, description="学习进度（当前用户）")


class ChapterTreeVO(VO):
    """章节树形结构 VO"""

    chapter_id: int = Field(description="章节ID")
    course_id: int = Field(description="课程ID")
    parent_id: int = Field(description="父章节ID（0表示根节点）")
    chapter_name: str = Field(description="章节名称")
    chapter_no: int = Field(default=0, description="章节序号（用于排序）")
    description: str | None = Field(default=None, description="章节描述")
    status: str = Field(description="章节状态，对照 sys_data_status（0正常 1停用 2已删除）")
    # 树形结构字段
    children: list["ChapterTreeVO"] | None = Field(default=None, description="子章节列表")
    has_children: bool | None = Field(default=None, description="是否有子章节")
    # 关联信息
    content_count: int = Field(default=0, description="资料数量")


class ChapterTreeBriefVO(VO):
    """章节树节点简要 VO（用于下拉选择）"""

    chapter_id: int = Field(description="章节ID")
    parent_id: int = Field(description="父章节ID")
    chapter_name: str = Field(description="章节名称")
    chapter_no: int = Field(default=0, description="章节序号")
    children: list["ChapterTreeBriefVO"] = Field(default_factory=list, description="子章节列表")


class ChapterDescriptionResultVO(VO):
    """章节描述生成结果 VO"""

    description: str = Field(description="生成的描述文本")
    chapter_id: int = Field(description="章节ID")
