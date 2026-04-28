"""章节相关 DTO 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery


class ChapterQueryDTO(PageQuery):
    """章节查询 DTO"""

    chapter_id: int | None = Field(default=None, description="章节ID")
    course_id: int = Field(default=None, description="课程ID")
    parent_id: int | None = Field(default=None, description="父章节ID（0表示根节点）")
    chapter_name: str | None = Field(default=None, description="章节名称")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="章节状态（0正常 1停用 2已删除）")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class ChapterCreateDTO(DTO):
    """创建章节 DTO

    用于创建新的课程章节

    Attributes:
        course_id: 课程ID
        parent_id: 父章节ID（可选）
        chapter_name: 章节名称
        chapter_no: 章节序号（可选）
        description: 章节描述（可选）
    """

    course_id: int = Field(description="课程ID")
    parent_id: int | None = Field(default=0, description="父章节ID（0表示根节点）")
    chapter_name: str = Field(min_length=1, max_length=128, description="章节名称")
    chapter_no: int | None = Field(default=0, description="章节序号（用于排序）")
    description: str | None = Field(default=None, description="章节描述")


class ChapterUpdateDTO(DTO):
    """更新章节 DTO

    用于更新课程章节信息

    Attributes:
        chapter_id: 章节ID
        parent_id: 父章节ID（可选）
        chapter_name: 章节名称（可选）
        chapter_no: 章节序号（可选）
        description: 章节描述（可选）
        status: 章节状态（可选）
    """

    chapter_id: int = Field(description="章节ID")
    parent_id: int | None = Field(default=None, description="父章节ID（0表示根节点）")
    chapter_name: str | None = Field(default=None, min_length=1, max_length=128, description="章节名称")
    chapter_no: int | None = Field(default=None, description="章节序号（用于排序）")
    description: str | None = Field(default=None, description="章节描述")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="章节状态（0正常 1停用 2已删除）")


class ChapterStatusChangeDTO(DTO):
    """修改章节状态 DTO"""

    chapter_id: int = Field(description="章节ID")
    status: Literal["0", "1", "2"] = Field(description="状态（0正常 1停用 2已删除）")


class ChapterMoveDTO(DTO):
    """移动章节 DTO"""

    chapter_id: int = Field(description="章节ID")
    new_parent_id: int = Field(description="新父章节ID（0表示根节点）")
    new_chapter_no: int = Field(description="新章节序号")


class ChapterDescriptionGenerateDTO(DTO):
    """生成章节描述请求 DTO"""

    graphrag_task_id: int = Field(description="要查询的 EduGraphRAGTask 主键 ID")
