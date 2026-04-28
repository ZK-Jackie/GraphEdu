"""章节相关异常

包含章节管理相关的异常定义，包含基类 ChapterException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class ChapterException(ServiceException):
    """章节异常基类"""

    def __init__(self, error_code: str = ErrorCode.CHAPTER_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class ChapterNotFoundException(ChapterException):
    """章节不存在"""

    def __init__(self, chapter_id: int = None, message: str = None, **kwargs):
        if chapter_id and message is None:
            message = f"章节ID {chapter_id} 不存在"

        super().__init__(error_code=ErrorCode.CHAPTER_NOT_FOUND.value, message=message, chapter_id=chapter_id, **kwargs)


class ChapterNameAlreadyExistsException(ChapterException):
    """章节名称已存在（同一课程下）"""

    def __init__(self, chapter_name: str = None, message: str = None, **kwargs):
        if chapter_name and message is None:
            message = f"章节名称 {chapter_name} 已存在"

        super().__init__(
            error_code=ErrorCode.CHAPTER_NAME_ALREADY_EXISTS.value, message=message, chapter_name=chapter_name, **kwargs
        )


class ChapterIdListEmptyException(ChapterException):
    """章节ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "章节ID列表不能为空"

        super().__init__(error_code=ErrorCode.CHAPTER_ID_LIST_EMPTY.value, message=message, **kwargs)


class ChapterCreateFailedException(ChapterException):
    """章节新增失败"""

    def __init__(self, chapter_name: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"章节新增失败: {chapter_name}" if chapter_name else "章节新增失败"

        super().__init__(
            error_code=ErrorCode.CHAPTER_CREATE_FAILED.value, message=message, chapter_name=chapter_name, **kwargs
        )


class ChapterUpdateFailedException(ChapterException):
    """章节更新失败"""

    def __init__(self, chapter_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"章节更新失败: {chapter_id}" if chapter_id else "章节更新失败"

        super().__init__(
            error_code=ErrorCode.CHAPTER_UPDATE_FAILED.value, message=message, chapter_id=chapter_id, **kwargs
        )


class ChapterDeleteFailedException(ChapterException):
    """章节删除失败"""

    def __init__(self, chapter_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"章节删除失败: {chapter_id}" if chapter_id else "章节删除失败"

        super().__init__(
            error_code=ErrorCode.CHAPTER_DELETE_FAILED.value, message=message, chapter_id=chapter_id, **kwargs
        )


class ChapterChangeStatusFailedException(ChapterException):
    """章节状态修改失败"""

    def __init__(self, chapter_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"章节状态修改失败: {chapter_id}" if chapter_id else "章节状态修改失败"

        super().__init__(
            error_code=ErrorCode.CHAPTER_CHANGE_STATUS_FAILED.value,
            message=message,
            chapter_id=chapter_id,
            **kwargs,
        )


class ChapterNoPermissionException(ChapterException):
    """无权限操作章节"""

    def __init__(self, chapter_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"无权操作章节ID {chapter_id} 的数据" if chapter_id else "无权操作该章节数据"

        super().__init__(
            error_code=ErrorCode.CHAPTER_NO_PERMISSION.value, message=message, chapter_id=chapter_id, **kwargs
        )


class ChapterHasChildrenException(ChapterException):
    """章节包含子章节，无法删除"""

    def __init__(self, chapter_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"章节包含子章节，无法删除: {chapter_id}" if chapter_id else "该章节包含子章节，无法删除"

        super().__init__(
            error_code=ErrorCode.CHAPTER_HAS_CHILDREN.value, message=message, chapter_id=chapter_id, **kwargs
        )


class ChapterLoopException(ChapterException):
    """章节父级设置会形成循环"""

    def __init__(self, chapter_id: int = None, parent_id: int = None, message: str = None, **kwargs):
        if message is None:
            if chapter_id and parent_id:
                message = f"章节父级设置会形成循环: 章节 {chapter_id} -> 父级 {parent_id}"
            else:
                message = "章节父级设置会形成循环"

        super().__init__(
            error_code=ErrorCode.CHAPTER_LOOP.value,
            message=message,
            chapter_id=chapter_id,
            parent_id=parent_id,
            **kwargs,
        )


# 导出所有异常类
__all__ = [
    "ChapterChangeStatusFailedException",
    "ChapterCreateFailedException",
    "ChapterDeleteFailedException",
    "ChapterException",
    "ChapterHasChildrenException",
    "ChapterIdListEmptyException",
    "ChapterLoopException",
    "ChapterNameAlreadyExistsException",
    "ChapterNoPermissionException",
    "ChapterNotFoundException",
    "ChapterUpdateFailedException",
]
