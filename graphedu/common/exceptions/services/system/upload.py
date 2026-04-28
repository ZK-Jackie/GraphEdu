"""文件上传下载相关异常

包含文件上传、下载、访问控制等相关的异常定义，包含基类 UploadException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class UploadException(ServiceException):
    """上传下载异常基类"""

    def __init__(self, error_code: str = ErrorCode.UPLOAD_FAILED.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


# ============================================================================
# 上传相关异常
# ============================================================================


class UploadFailedException(UploadException):
    """文件上传失败"""

    def __init__(self, filename: str = None, reason: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.UPLOAD_FAILED.value, message=message, filename=filename, reason=reason, **kwargs
        )


class UploadFileNotFoundException(UploadException):
    """文件不存在"""

    def __init__(self, file_id: int = None, filename: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.UPLOAD_FILE_NOT_FOUND.value,
            message=message,
            file_id=file_id,
            filename=filename,
            **kwargs,
        )


class UploadFileTooLargeException(UploadException):
    """文件大小超出限制"""

    def __init__(
        self, filename: str = None, file_size: int = None, max_size: int = None, message: str = None, **kwargs
    ):
        super().__init__(
            error_code=ErrorCode.UPLOAD_FILE_TOO_LARGE.value,
            message=message,
            filename=filename,
            file_size=file_size,
            max_size=max_size,
            **kwargs,
        )


class UploadFileTypeNotAllowed(UploadException):
    """不允许上传此类型的文件"""

    def __init__(self, filename: str = None, file_type: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.UPLOAD_FILE_TYPE_NOT_ALLOWED.value,
            message=message,
            filename=filename,
            file_type=file_type,
            **kwargs,
        )


class UploadFilenameEmptyException(UploadException):
    """文件名不能为空"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.UPLOAD_FILENAME_EMPTY.value, message=message, **kwargs)


class UploadS3ClientNotInitialized(UploadException):
    """S3客户端未初始化"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.UPLOAD_S3_CLIENT_NOT_INITIALIZED.value, message=message, **kwargs)


class UploadS3ConfigNotInitialized(UploadException):
    """S3配置未初始化"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.UPLOAD_S3_CONFIG_NOT_INITIALIZED.value, message=message, **kwargs)


# ============================================================================
# 下载相关异常
# ============================================================================


class DownloadFailedException(UploadException):
    """文件下载失败"""

    def __init__(self, file_id: int = None, reason: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DOWNLOAD_FAILED.value, message=message, file_id=file_id, reason=reason, **kwargs
        )


class DownloadFileNotFoundException(UploadException):
    """下载文件不存在"""

    def __init__(self, file_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DOWNLOAD_FILE_NOT_FOUND.value, message=message, file_id=file_id, **kwargs)


class DownloadNoPermissionException(UploadException):
    """无权访问该文件"""

    def __init__(self, file_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DOWNLOAD_NO_PERMISSION.value, message=message, file_id=file_id, **kwargs)


class DownloadNotAllowedException(UploadException):
    """该文件不允许下载"""

    def __init__(self, file_id: int = None, filename: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DOWNLOAD_NOT_ALLOWED.value,
            message=message,
            file_id=file_id,
            filename=filename,
            **kwargs,
        )


# 导出所有异常类
__all__ = [
    "DownloadFailedException",
    "DownloadFileNotFoundException",
    "DownloadNoPermissionException",
    "DownloadNotAllowedException",
    "UploadException",
    "UploadFailedException",
    "UploadFileNotFoundException",
    "UploadFileTooLargeException",
    "UploadFileTypeNotAllowed",
    "UploadFilenameEmptyException",
    "UploadS3ClientNotInitialized",
    "UploadS3ConfigNotInitialized",
]
