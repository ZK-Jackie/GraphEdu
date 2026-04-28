"""章节资料相关异常

包含章节资料管理相关的异常定义，包含基类 ChapterResourceException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class ChapterResourceException(ServiceException):
    """章节资料异常基类"""

    def __init__(self, error_code: str = ErrorCode.CHAPTER_RESOURCE_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class ChapterResourceNotFoundException(ChapterResourceException):
    """章节资料不存在"""

    def __init__(self, resource_id: int = None, message: str = None, **kwargs):
        if resource_id and message is None:
            message = f"章节资料ID {resource_id} 不存在"

        super().__init__(
            error_code=ErrorCode.CHAPTER_RESOURCE_NOT_FOUND.value, message=message, resource_id=resource_id, **kwargs
        )


class ChapterResourceIdListEmptyException(ChapterResourceException):
    """资料ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "资料ID列表不能为空"

        super().__init__(error_code=ErrorCode.CHAPTER_RESOURCE_ID_LIST_EMPTY.value, message=message, **kwargs)


class ChapterResourceCreateFailedException(ChapterResourceException):
    """资料新增失败"""

    def __init__(self, resource_name: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"资料新增失败: {resource_name}" if resource_name else "资料新增失败"

        super().__init__(
            error_code=ErrorCode.CHAPTER_RESOURCE_CREATE_FAILED.value,
            message=message,
            resource_name=resource_name,
            **kwargs,
        )


class ChapterResourceUpdateFailedException(ChapterResourceException):
    """资料更新失败"""

    def __init__(self, resource_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"资料更新失败: {resource_id}" if resource_id else "资料更新失败"

        super().__init__(
            error_code=ErrorCode.CHAPTER_RESOURCE_UPDATE_FAILED.value,
            message=message,
            resource_id=resource_id,
            **kwargs,
        )


class ChapterResourceDeleteFailedException(ChapterResourceException):
    """资料删除失败"""

    def __init__(self, resource_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"资料删除失败: {resource_id}" if resource_id else "资料删除失败"

        super().__init__(
            error_code=ErrorCode.CHAPTER_RESOURCE_DELETE_FAILED.value,
            message=message,
            resource_id=resource_id,
            **kwargs,
        )


class ChapterResourceChangeStatusFailedException(ChapterResourceException):
    """资料状态修改失败"""

    def __init__(self, resource_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"资料状态修改失败: {resource_id}" if resource_id else "资料状态修改失败"

        super().__init__(
            error_code=ErrorCode.CHAPTER_RESOURCE_CHANGE_STATUS_FAILED.value,
            message=message,
            resource_id=resource_id,
            **kwargs,
        )


# 导出所有异常类
__all__ = [
    "ChapterResourceChangeStatusFailedException",
    "ChapterResourceCreateFailedException",
    "ChapterResourceDeleteFailedException",
    "ChapterResourceException",
    "ChapterResourceIdListEmptyException",
    "ChapterResourceNotFoundException",
    "ChapterResourceUpdateFailedException",
]
