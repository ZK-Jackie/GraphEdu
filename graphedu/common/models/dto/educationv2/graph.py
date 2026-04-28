"""知识图谱 DTO 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery


class KnowledgeNodeChapterQueryDTO(PageQuery):
    """知识点-章节关联查询 DTO"""

    node_chapter_id: int | None = Field(default=None, description="关系ID")
    chapter_id: int | None = Field(default=None, description="章节ID")
    node_uuid: str | None = Field(default=None, description="知识点业务UUID")
    is_primary: Literal["Y", "N"] | None = Field(default=None, description="是否主要关联（Y是 N否）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="关系状态（0正常 1停用 2已删除）")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class KnowledgeNodeChapterCreateDTO(DTO):
    """创建知识点-章节关联 DTO

    用于创建新的知识点-章节关联关系

    Attributes:
        chapter_id: 章节ID
        node_uuid: 知识点业务UUID
        relevance_score: 相关性评分（可选）
        description: 关系描述（可选）
        is_primary: 是否主要关联（可选）
    """

    chapter_id: int = Field(description="章节ID")
    node_uuid: str = Field(description="知识点业务UUID")
    relevance_score: float | None = Field(default=0, ge=0, le=1, description="知识点与章节的相关性评分（0-1）")
    description: str | None = Field(default=None, description="关系描述")
    is_primary: Literal["Y", "N"] | None = Field(default="N", description="是否主要关联（Y是 N否）")


class KnowledgeNodeChapterUpdateDTO(DTO):
    """更新知识点-章节关联 DTO

    用于更新知识点-章节关联关系

    Attributes:
        node_chapter_id: 关系ID
        relevance_score: 相关性评分（可选）
        description: 关系描述（可选）
        is_primary: 是否主要关联（可选）
        status: 关系状态（可选）
    """

    node_chapter_id: int = Field(description="关系ID")
    relevance_score: float | None = Field(default=None, ge=0, le=1, description="知识点与章节的相关性评分（0-1）")
    description: str | None = Field(default=None, description="关系描述")
    is_primary: Literal["Y", "N"] | None = Field(default=None, description="是否主要关联（Y是 N否）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="关系状态（0正常 1停用 2已删除）")


class KnowledgeNodeChapterBatchLinkDTO(DTO):
    """知识点-章节批量关联 DTO"""

    node_uuids: list[str] = Field(description="要关联的知识点业务UUID列表")
