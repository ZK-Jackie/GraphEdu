"""文件上传下载接口"""

import logging

from fastapi import APIRouter, Depends, File, Form, Header, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models.constants import SystemConstants as SysConst
from graphedu.common.models.dto.systemv2.upload import FileDTO, UploadFileDTO
from graphedu.common.models.vo.base import ResponseType, ResponseUtil
from graphedu.common.models.vo.systemv2.upload import FileDownloadVO, FileInfoVO
from graphedu.common.resource import AioS3Client
from graphedu.common.resource.deps import get_db, get_s3
from graphedu.security.aspect.interface_auth import CheckUserInterfacePermit
from graphedu.security.aspect.log_annotation import SystemLog
from graphedu.security.auth import CurrentUser, SecurityService
from graphedu.services.system.upload import UploadService

logger = logging.getLogger(__name__)

upload_controller = APIRouter(prefix="/common", tags=["文件上传下载"])


# ============================================================================
# 文件上传
# ============================================================================
@upload_controller.post(
    "/upload",
    dependencies=[Depends(CheckUserInterfacePermit("common:upload:upload"))],
    response_model=ResponseType[FileInfoVO],
)
@SystemLog(title="文件上传", business_type=SysConst.BusinessType.INSERT)
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="上传的文件"),
    content_length: int = Header(lt=1024 * 1024 * 100, description="文件大小，单位字节，最大100MB"),
    upload_info: UploadFileDTO = Form(..., description="上传文件的附加信息"),
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """上传文件到OSS

    - 支持的文件类型：图片、文档、压缩包、视频、音频
    - 最大文件大小：100MB
    - 文件会自动分类存储到OSS
    """
    # 获取客户端IP
    file_dto = FileDTO.model_validate(upload_info)
    file_dto.file_name = file.filename
    file_dto.create_ip = request.client.host if request.client else "未知"
    file_dto.file_size = file.size
    file_dto.file_type = file.content_type or "application/octet-stream"

    # 上传文件
    file_info = await UploadService.upload_file(file, file_dto, current_user, query_db, s3_client)
    return ResponseUtil.success(data=file_info)


# ============================================================================
# 文件下载
# ============================================================================
@upload_controller.get(
    "/download/{file_id}",
    dependencies=[Depends(CheckUserInterfacePermit("common:upload:download"))],
    response_model=ResponseType[FileDownloadVO],
)
@SystemLog(title="文件下载", business_type=SysConst.BusinessType.EXPORT)
async def download_file(
    file_id: int,
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """从OSS下载文件

    - 需要有相应的访问权限
    - 私有文件只有上传者和管理员可以下载
    """
    # 获取下载文件信息
    download_info = await UploadService.get_download_info(
        file_id=file_id, current_user=current_user, query_db=query_db, s3_client=s3_client
    )
    # 返回下载链接
    return ResponseUtil.success(data=download_info)


# ============================================================================
# 获取文件信息
# ============================================================================
@upload_controller.get(
    "/fileInfo/{file_id}",
    dependencies=[Depends(CheckUserInterfacePermit("common:upload:query"))],
    response_model=ResponseType[FileInfoVO],
)
async def get_file_info(
    file_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """获取文件信息

    - 需要有相应的访问权限
    """
    file_info = await UploadService.get_info(file_id=file_id, current_user=current_user, query_db=query_db)
    return ResponseUtil.success(data=file_info)


# ============================================================================
# 头像上传（专用接口）
# ============================================================================
@upload_controller.post("/avatar", response_model=ResponseType[FileInfoVO])
@SystemLog(title="头像上传", business_type=SysConst.BusinessType.UPDATE)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(..., description="头像图片文件"),
    query_db: AsyncSession = Depends(get_db),
    s3_client: AioS3Client = Depends(get_s3),
    current_user: CurrentUser = Depends(SecurityService.get_current_user),
):
    """上传用户头像

    - 自动设置为头像分类 (category=1)
    - 访问级别为公开 (access_level=2)
    """
    # 获取客户端IP
    client_ip = request.client.host if request.client else None

    # 上传文件（固定为头像分类）
    file_info = await UploadService.upload_file(
        file=file,
        file_dto=FileDTO(
            file_name=file.filename,
            file_size=file.size,
            file_type=file.content_type or "application/octet-stream",
            file_category="1",  # 头像分类
            access_level="2",  # 公开访问
            create_ip=client_ip,
            download_flag="1",  # 允许下载
            remark="用户头像上传",
        ),
        current_user=current_user,
        query_db=query_db,
        s3_client=s3_client,
    )

    return ResponseUtil.success(data=file_info)
