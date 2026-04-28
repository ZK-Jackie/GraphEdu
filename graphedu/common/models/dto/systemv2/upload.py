"""文件上传相关 DTO 模块

本模块定义了文件上传相关的数据传输对象：

- **UploadFileDTO**: 上传文件参数 DTO
- **FileDTO**: 文件信息 DTO
"""

from pydantic import BaseModel, Field


class UploadFileDTO(BaseModel):
    """上传文件参数 DTO

    用于文件上传时的参数验证

    Attributes:
        file_category: 文件分类，对照sys_upload_file_category字典
        access_level: 访问级别，对照sys_upload_access_level字典
        download_flag: 是否允许下载，对照sys_data_option字典
        remark: 备注信息
    """

    file_category: int = Field(description="文件分类，对照sys_upload_file_category字典")
    access_level: int = Field(description="访问级别，对照sys_upload_access_level字典")
    download_flag: str = Field(description="是否允许下载，对照sys_data_option字典")
    remark: str | None = Field(default=None, description="备注信息")


class FileDTO(BaseModel):
    """文件信息 DTO

    用于记录文件的基本信息

    Attributes:
        file_name: 文件名称
        file_size: 文件大小（字节）
        file_type: 文件类型（MIME 类型）
        file_category: 文件分类，对照sys_upload_file_category字典
        access_level: 访问级别，对照sys_upload_access_level字典
        download_flag: 是否允许下载，对照sys_data_option字典
        create_ip: 上传者 IP 地址
        remark: 备注信息
    """

    file_name: str = Field(description="文件名称")
    file_size: int = Field(description="文件大小（字节）")
    file_type: str = Field(description="文件类型（MIME类型）")
    file_category: str = Field(description="文件分类，对照sys_upload_file_category字典")
    access_level: str = Field(description="访问级别，对照sys_upload_access_level字典")
    download_flag: str = Field(description="是否允许下载，对照sys_data_option字典")
    create_ip: str = Field(description="上传者IP地址")
    remark: str | None = Field(default=None, description="备注信息")
