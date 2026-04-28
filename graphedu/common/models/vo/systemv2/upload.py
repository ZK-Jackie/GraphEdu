"""文件上传相关视图对象模块。"""

from datetime import datetime

from pydantic import Field

from graphedu.common.models.vo.base import VO


class FileInfoVO(VO):
    """文件信息视图对象。"""

    file_id: int = Field(description="文件ID")
    file_name: str = Field(description="原始文件名")
    file_path: str = Field(description="存储路径/URL")
    file_size: int = Field(description="文件大小(字节)")
    file_type: str = Field(description="MIME类型(如: image/jpeg, application/pdf)")
    file_category: int = Field(description="文件分类，对照sys_upload_file_category字典")
    storage_type: int = Field(description="存储类型，对照sys_upload_storage_type字典")
    access_level: int = Field(description="访问级别，对照sys_upload_access_level字典")
    download_flag: str = Field(description="是否允许下载，对照sys_data_option字典")
    view_count: int = Field(description="查看次数")
    download_count: int = Field(description="下载次数")
    ref_count: int = Field(description="被引用次数")
    audit_status: str = Field(description="审核状态，对照sys_upload_audit_status")
    audit_by: int | None = Field(default=None, description="审核人ID")
    audit_time: datetime | None = Field(default=None, description="审核时间")
    audit_remark: str | None = Field(default=None, description="审核备注")
    status: str = Field(description="对照sys_data_status（0正常 1停用 2已删除）")
    create_ip: str = Field(description="上传者IP地址")
    create_by: int = Field(description="上传者ID")
    create_time: datetime = Field(description="上传时间")
    update_by: int | None = Field(default=None, description="更新者")
    update_time: datetime | None = Field(default=None, description="更新时间")
    remark: str | None = Field(default=None, description="备注")


class FileDownloadVO(VO):
    """文件下载视图对象。"""

    # file_path 是内部存储路径/内部URL/object名称；file_url 是外部直接访问/下载URL，数据库没有这个字段
    file_url: str = Field(description="文件下载URL")
    # 数据库中暂时没有这个字段
    thumbnail_url: str | None = Field(default=None, description="缩略图URL（如果为图片且有）")

    file_name: str = Field(description="文件名称")
    file_type: str = Field(description="文件类型（MIME类型）")
    file_size: int = Field(description="文件大小（字节）")
