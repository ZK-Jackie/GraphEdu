"""章节资源 VO 模型。"""
from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo import VO
from graphedu.common.models.vo.systemv2.upload import FileInfoVO


class ChapterResourceBatchDeleteResultVO(VO):
    """章节资源批量删除结果 VO"""

    success_count: int = Field(description="成功删除数量")
    fail_count: int = Field(description="失败数量")
    results: list[dict] = Field(description="详细结果列表")


class ChapterResourceListVO(VO):
    """章节资料列表项 VO"""

    resource_id: int = Field(description="资料ID")
    chapter_id: int = Field(description="所属章节ID")
    resource_name: str = Field(description="资料名称")
    resource_type: str = Field(description="资料类型（video视频/document文档/text文本）")
    file_id: int | None = Field(default=None, description="文件ID（引用sys_upload.file_id）")
    resource_url: str | None = Field(default=None, description="外部链接URL")
    description: str | None = Field(default=None, description="描述")
    resource_data: dict | None = Field(default=None, description="扩展数据（JSONB格式）")
    # 解析相关字段（用于列表展示）
    parse_status: str | None = Field(default=None, description="解析状态（0待处理 1处理中 2处理成功 3处理失败）")
    display_order: int = Field(default=0, description="显示顺序")
    is_visible: str = Field(description="是否可见（Y/N）")
    status: str = Field(description="状态（0正常 1停用 2已删除）")
    create_time: datetime | None = Field(default=None, description="创建时间")

    # 关联信息
    file_url: str | None = Field(default=None, description="文件URL")
    file_info: FileInfoVO | None = Field(default=None, description="文件上传信息（sys_upload）")


class ChapterResourceDetailVO(ChapterResourceListVO):
    """章节资料详细信息 VO"""

    text_file_id: int | None = Field(default=None, description="纯文本文件ID")
    create_by: int | None = Field(default=None, description="创建者")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")


class ChapterResourceParseSubmitVO(VO):
    """提交章节资料 PDF 解析任务响应 VO"""

    resource_id: int = Field(description="资料ID")
    mineru_task_id: str = Field(description="MinerU 任务ID")
    parse_status: str = Field(description="解析状态")


class ChapterResourceParseStatusVO(VO):
    """章节资料解析与 GraphRAG 状态 VO"""

    resource_id: int = Field(description="资料ID")
    parse_status: str = Field(description="PDF 解析状态：0待处理 / 1处理中 / 2处理成功 / 3处理失败")
    mineru_task_id: str | None = Field(default=None, description="MinerU 任务ID")
    text_file_id: int | None = Field(default=None, description="纯文本文件ID")
    page_count: int | None = Field(default=None, description="解析页数")
    markdown_length: int | None = Field(default=None, description="Markdown 内容长度")
    markdown_s3_key: str | None = Field(default=None, description="Markdown 结果对象存储 Key")
    markdown_url: str | None = Field(default=None, description="Markdown 临时访问链接")
    error_message: str | None = Field(default=None, description="错误信息")




class CeleryTaskVO(VO):
    """Celery 异步任务提交响应 VO"""

    celery_task_id: str = Field(description="Celery 任务ID")
    status: str = Field(description="提交状态，固定为 'submitted'")
    document_id: int | None = Field(default=None, description="关联文档ID（build-graph 时）")
    chapter_id: int | None = Field(default=None, description="关联章节ID（generate-description 时）")
