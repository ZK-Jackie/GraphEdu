"""文件上传下载服务模块。

该模块提供文件上传、下载、信息查询等核心业务逻辑。
"""

from datetime import datetime
import logging

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions import (
    DownloadFailedException,
    DownloadFileNotFoundException,
    DownloadNoPermissionException,
    DownloadNotAllowedException,
    UploadFailedException,
    UploadFilenameEmptyException,
    UploadFileNotFoundException,
    UploadFileTypeNotAllowed,
    UploadS3ClientNotInitialized,
    UploadS3ConfigNotInitialized,
)
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.systemv2.upload import FileDTO
from graphedu.common.models.orm.system import SysUpload
from graphedu.common.models.vo.systemv2.upload import FileDownloadVO, FileInfoVO
from graphedu.common.resource import AioS3Client
from graphedu.common.utils.uuids import uuid7_str
from graphedu.mapper.system.upload import UploadMapper

logger = logging.getLogger(__name__)


# ============================================================================
# 文件分类常量
# ============================================================================
CATEGORY_DIR_MAP = {
    SystemConstants.FileCategory.AVATAR: "avatar",
    SystemConstants.FileCategory.COURSE_COVER: "course-cover",
    SystemConstants.FileCategory.BOOK_COVER: "book-cover",
    SystemConstants.FileCategory.BOOK_FILE: "book",
    SystemConstants.FileCategory.ATTACHMENT: "attachment",
    SystemConstants.FileCategory.HOMEWORK_FILE: "homework",
    SystemConstants.FileCategory.TEACHING_MATERIAL: "material",
}


# ============================================================================
# 辅助函数
# ============================================================================
def _get_file_extension(filename: str) -> str:
    """获取文件扩展名（小写）。

    Args:
        filename: 文件名。

    Returns:
        str: 扩展名，无扩展名返回空字符串。
    """
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _check_file_extension(filename: str) -> bool:
    """检查文件扩展名是否在允许列表中。

    Args:
        filename: 文件名。

    Returns:
        bool: 是否允许上传。
    """
    ext = _get_file_extension(filename)
    all_extensions = set()
    for exts in UploadService.ALLOWED_EXTENSIONS.values():
        all_extensions.update(exts)
    return ext in all_extensions


def _generate_object_name(filename: str, category: str | None = None) -> str:
    """生成 OSS 对象名称。

    格式: category_dir/YYYYMMDD/uuid.扩展名

    Args:
        filename: 原始文件名。
        category: 文件分类 ID。

    Returns:
        str: OSS 对象名称。
    """
    ext = _get_file_extension(filename)
    date_str = datetime.now().strftime("%Y%m%d")
    uuid_str = uuid7_str()

    # 根据分类确定目录
    category_dir = CATEGORY_DIR_MAP.get(category) if category else "other"

    return f"{category_dir}/{date_str}/{uuid_str}.{ext}"


# ============================================================================
# 服务类
# ============================================================================
class UploadService:
    """文件上传下载服务类。

    提供文件上传、下载、信息查询等功能。
    """

    # 允许的文件扩展名分类
    ALLOWED_EXTENSIONS = {
        "image": {"jpg", "jpeg", "png", "gif", "bmp", "webp"},
        "document": {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "md"},
        "archive": {"zip", "rar", "7z", "tar", "gz"},
        "video": {"mp4", "avi", "mkv", "mov", "wmv", "flv"},
        "audio": {"mp3", "wav", "ogg", "flac", "aac"},
    }

    # 最大文件大小 (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    @staticmethod
    async def upload_file(
        file: UploadFile, file_dto: FileDTO, current_user: CurrentUser, query_db: AsyncSession, s3_client: AioS3Client
    ) -> FileInfoVO:
        """上传文件到 OSS 并记录到数据库。

        Args:
            file: 上传的文件对象。
            file_dto: 文件上传参数（包含文件名、大小、类型等）。
            current_user: 当前登录用户。
            query_db: 数据库会话。
            s3_client: S3 客户端。

        Returns:
            FileInfoVO: 文件信息 VO。

        Raises:
            UploadFilenameEmptyException: 文件名为空。
            UploadFileTypeNotAllowed: 文件类型不允许。
            UploadFailedException: 上传失败。
        """
        try:
            # 1. 参数校验
            if not file_dto.file_name:
                raise UploadFilenameEmptyException

            if not _check_file_extension(file_dto.file_name):
                raise UploadFileTypeNotAllowed(filename=file_dto.file_name, file_type=file_dto.file_type)

            # 检查文件大小
            if file_dto.file_size > UploadService.MAX_FILE_SIZE:
                raise UploadFailedException(
                    filename=file_dto.file_name,
                    reason=f"文件大小超过限制 ({file_dto.file_size} > {UploadService.MAX_FILE_SIZE})",
                )

            # 2. 生成OSS对象名称
            object_name = _generate_object_name(file_dto.file_name, file_dto.file_category)

            # 3. 上传到OSS
            await s3_client.upload_uploadfile(file, object_name)
            logger.info(f"文件上传到OSS成功: {object_name}")

            # 4. 获取当前用户ID
            user_id = current_user.detail.user.user_id if current_user.detail and current_user.detail.user else None

            # 5. 创建数据库记录
            upload_data = SysUpload(
                file_name=file_dto.file_name,
                file_path=object_name,
                file_type=file_dto.file_type,
                file_size=file_dto.file_size,
                file_category=file_dto.file_category,
                storage_type=1,  # 1-OSS存储
                access_level=file_dto.access_level,
                download_flag=file_dto.download_flag,
                status=SystemConstants.Status.NORMAL,  # 0-正常
                create_by=user_id,
                create_ip=file_dto.create_ip,
                create_time=datetime.now(),
                update_by=user_id,
                update_time=datetime.now(),
                remark=file_dto.remark,
            )

            upload_obj = await UploadMapper.add_upload(upload_data, query_db)
            logger.info(f"文件记录已保存到数据库: file_id={upload_obj.file_id}")

            return FileInfoVO.model_validate(upload_obj)

        except (
            UploadFileTypeNotAllowed,
            UploadFilenameEmptyException,
            UploadS3ClientNotInitialized,
            UploadS3ConfigNotInitialized,
        ):
            # 业务异常直接抛出
            raise
        except Exception as e:
            raise UploadFailedException(filename=file.filename, reason=str(e)) from e

    @staticmethod
    async def get_download_info(
        file_id: int, current_user: CurrentUser, query_db: AsyncSession, s3_client: AioS3Client
    ) -> FileDownloadVO:
        """获取文件下载信息（生成预签名 URL）。

        Args:
            file_id: 文件 ID。
            current_user: 当前登录用户。
            query_db: 数据库会话。
            s3_client: S3 客户端。

        Returns:
            FileDownloadVO: 文件下载信息 VO（包含预签名 URL）。

        Raises:
            DownloadFileNotFoundException: 文件不存在。
            DownloadNoPermissionException: 无访问权限。
            DownloadNotAllowedException: 不允许下载。
            DownloadFailedException: 下载失败。
        """
        try:
            # 1. 查询文件信息
            file_info = await UploadMapper.get_by_id(file_id, query_db)
            if not file_info:
                raise DownloadFileNotFoundException(file_id=file_id)

            # 2. 检查访问权限
            if file_info.access_level == SystemConstants.AccessLevel.PRIVATE:
                # 私有文件：只有上传者和管理员可访问
                user_id = current_user.detail.user.user_id if current_user.detail and current_user.detail.user else None
                if file_info.create_by != user_id and not current_user.is_admin():
                    raise DownloadNoPermissionException(file_id=file_id)

            # 3. 检查是否允许下载
            if file_info.download_flag == "0":
                raise DownloadNotAllowedException(file_id=file_id, filename=file_info.file_name)

            # 4. 更新下载计数
            await UploadMapper.update_counts(query_db, file_id, download_count=True)

            username = (
                current_user.detail.user.user_name if current_user.detail and current_user.detail.user else "Unknown"
            )
            logger.info(f"用户 {username} 下载文件: {file_info.file_name} (ID: {file_id})")

            # 5. 构建返回对象
            ret_obj = FileDownloadVO.model_validate(file_info)

            # 6. 根据存储类型生成访问URL
            if file_info.storage_type == 1:  # OSS存储
                # 生成预签名URL，默认1小时有效期
                ret_obj.file_url = await s3_client.generate_presigned_url(file_info.file_path, expiration=3600)
            else:
                # 其他存储类型暂不支持
                raise DownloadFailedException(file_id=file_id, reason=f"不支持的存储类型: {file_info.storage_type}")

            return ret_obj

        except (
            DownloadFileNotFoundException,
            DownloadNoPermissionException,
            DownloadNotAllowedException,
            UploadS3ClientNotInitialized,
            UploadS3ConfigNotInitialized,
        ):
            # 业务异常直接抛出
            raise
        except Exception as e:
            raise DownloadFailedException(file_id=file_id, reason=str(e)) from e

    @staticmethod
    async def get_info(file_id: int, current_user: CurrentUser, query_db: AsyncSession) -> FileInfoVO:
        """获取文件信息。

        Args:
            file_id: 文件 ID。
            current_user: 当前登录用户。
            query_db: 数据库会话。

        Returns:
            FileInfoVO: 文件信息 VO。

        Raises:
            UploadFileNotFoundException: 文件不存在。
            DownloadNoPermissionException: 无访问权限。
        """
        # 1. 查询文件信息
        file_info = await UploadMapper.get_by_id(file_id, query_db)
        if not file_info:
            raise UploadFileNotFoundException(file_id=file_id)

        # 2. 检查访问权限
        if file_info.access_level == SystemConstants.AccessLevel.PRIVATE:
            # 私有文件：只有上传者和管理员可访问
            user_id = current_user.detail.user.user_id if current_user.detail and current_user.detail.user else None
            if file_info.create_by != user_id and not current_user.is_admin():
                raise DownloadNoPermissionException(file_id=file_id)

        return FileInfoVO.model_validate(file_info)

    @staticmethod
    async def check_file_ownership(file_id: int, user_id: int, query_db: AsyncSession) -> bool:
        """检查文件是否属于指定用户。

        Args:
            file_id: 文件 ID。
            user_id: 用户 ID。
            query_db: 数据库会话。

        Returns:
            bool: 是否属于该用户。
        """
        file_info = await UploadMapper.get_by_id(file_id, query_db)
        if not file_info:
            return False

        return file_info.create_by == user_id

    @staticmethod
    async def get_avatar_url(user_id: int, file_id: int, query_db: AsyncSession, s3_client: AioS3Client) -> str | None:
        """获取用户头像 URL。

        不计算预签名 URL、查看次数、下载次数等。

        Args:
            user_id: 用户 ID。
            file_id: 文件 ID。
            query_db: 数据库会话。
            s3_client: S3 客户端。

        Returns:
            str | None: 头像 URL 或 None。
        """
        avatar_info = await UploadMapper.get_by_id(file_id, query_db)
        if not avatar_info or avatar_info.create_by != user_id:
            return None
        return s3_client.build_object_url(avatar_info.file_path)

    @staticmethod
    async def get_file_url(file_id: int | None, query_db: AsyncSession, s3_client: AioS3Client) -> str | None:
        """获取文件访问 URL。

        Args:
            file_id: 文件 ID。
            query_db: 数据库会话。
            s3_client: S3 客户端。

        Returns:
            str | None: 文件访问 URL，文件不存在时返回 None。
        """
        if not file_id:
            return None

        file_info = await UploadMapper.get_by_id(file_id, query_db)
        if not file_info:
            return None

        # 生成公共访问 URL（非预签名，长期有效）
        return s3_client.build_object_url(file_info.file_path)

    @staticmethod
    async def get_file_url_map(file_ids: list[int], query_db: AsyncSession, s3_client: AioS3Client) -> dict[int, str]:
        """批量获取文件访问 URL。

        Args:
            file_ids: 文件 ID 列表。
            query_db: 数据库会话。
            s3_client: S3 客户端。

        Returns:
            dict[int, str]: 文件 ID 到 URL 的映射字典。
        """
        if not file_ids:
            return {}

        # 批量查询文件信息
        file_infos = await UploadMapper.get_by_ids(file_ids, query_db)

        # 构建映射字典
        url_map = {}
        for file_info in file_infos:
            url_map[file_info.file_id] = s3_client.build_object_url(file_info.file_path)

        return url_map
