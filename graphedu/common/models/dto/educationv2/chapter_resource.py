"""章节资源相关 DTO 模型。"""
from datetime import datetime
from typing import Literal

from pydantic import Field

from graphedu.common.models.dto.base import DTO, PageQuery


class ChapterResourceQueryDTO(PageQuery):
    """章节资料查询 DTO"""

    resource_id: int | None = Field(default=None, description="资料ID")
    chapter_id: int | None = Field(default=None, description="所属章节ID")
    resource_name: str | None = Field(default=None, description="资料名称")
    resource_type: Literal["video", "document", "text", "image", "audio"] | None = Field(
        default=None, description="资料类型"
    )
    is_visible: Literal["Y", "N"] | None = Field(default=None, description="是否可见（Y/N）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="状态（0正常 1停用 2已删除）")
    begin_time: datetime | None = Field(default=None, description="创建开始时间")
    end_time: datetime | None = Field(default=None, description="创建结束时间")


class ChapterResourceCreateDTO(DTO):
    """创建章节资料 DTO

    用于创建新的章节学习资料

    Attributes:
        chapter_id: 所属章节ID
        resource_name: 资料名称
        resource_type: 资料类型
        file_id: 文件ID（可选）
        resource_url: 外部链接URL（可选）
        description: 描述（可选）
        resource_data: 扩展数据（可选）
        display_order: 显示顺序
        is_visible: 是否可见（可选）
    """

    chapter_id: int = Field(description="所属章节ID")
    resource_name: str = Field(min_length=1, max_length=128, description="资料名称")
    resource_type: Literal["video", "document", "text", "image", "audio", "archive", "binary"] = Field(
        description="资料类型"
    )
    file_id: int | None = Field(default=None, description="文件ID（引用sys_upload.file_id）")
    resource_url: str | None = Field(default=None, max_length=512, description="外部链接URL")
    description: str | None = Field(default=None, max_length=2048, description="描述")
    resource_data: dict | None = Field(default=None, description="扩展数据（JSONB格式，存储视频时长、文档页数等）")
    display_order: int = Field(default=0, description="显示顺序")
    is_visible: Literal["Y", "N"] | None = Field(default="Y", description="是否可见（Y/N）")


class ChapterResourceUpdateDTO(DTO):
    """更新章节资料 DTO

    用于更新章节学习资料

    Attributes:
        resource_id: 资料ID
        resource_name: 资料名称（可选）
        resource_type: 资料类型（可选）
        file_id: 文件ID（可选）
        resource_url: 外部链接URL（可选）
        description: 描述（可选）
        resource_data: 扩展数据（可选）
        display_order: 显示顺序（可选）
        is_visible: 是否可见（可选）
        status: 状态（可选）
    """

    resource_id: int = Field(description="资料ID")
    resource_name: str | None = Field(default=None, min_length=1, max_length=128, description="资料名称")
    resource_type: Literal["video", "document", "text", "image", "audio", "archive", "binary"] | None = Field(
        default=None, description="资料类型"
    )
    file_id: int | None = Field(default=None, description="文件ID（引用sys_upload.file_id）")
    resource_url: str | None = Field(default=None, max_length=512, description="外部链接URL")
    description: str | None = Field(default=None, max_length=2048, description="描述")
    resource_data: dict | None = Field(default=None, description="扩展数据（JSONB格式）")
    display_order: int | None = Field(default=None, description="显示顺序")
    is_visible: Literal["Y", "N"] | None = Field(default=None, description="是否可见（Y/N）")
    status: Literal["0", "1", "2"] | None = Field(default=None, description="状态（0正常 1停用 2已删除）")


class ChapterResourceReorderDTO(DTO):
    """章节资源重排序 DTO"""

    resource_orders: dict[int, int] = Field(description="资源ID到新序号的映射")


class ChapterResourceStatusChangeDTO(DTO):
    """章节资源状态修改 DTO"""

    status: Literal["0", "1", "2"] = Field(description="状态（0正常 1停用 2已删除）")


class ChapterResourceBatchDeleteDTO(DTO):
    """章节资源批量删除 DTO"""

    resource_ids: str = Field(description="资源ID，多个以逗号分隔")
