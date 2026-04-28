"""教师相关异常

包含教师管理相关的异常定义，包含基类 TeacherException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class TeacherException(ServiceException):
    """教师异常基类"""

    def __init__(self, error_code: str = ErrorCode.TEACHER_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class TeacherNotFoundException(TeacherException):
    """教师不存在"""

    def __init__(self, teacher_id: int = None, message: str = None, **kwargs):
        if teacher_id and message is None:
            message = f"教师ID {teacher_id} 不存在"

        super().__init__(error_code=ErrorCode.TEACHER_NOT_FOUND.value, message=message, teacher_id=teacher_id, **kwargs)


class TeacherAlreadyExistsException(TeacherException):
    """教师已存在"""

    def __init__(self, teacher_id: int = None, message: str = None, **kwargs):
        if teacher_id and message is None:
            message = f"教师ID {teacher_id} 已存在"

        super().__init__(
            error_code=ErrorCode.TEACHER_ALREADY_EXISTS.value, message=message, teacher_id=teacher_id, **kwargs
        )


class TeacherNoAlreadyExistsException(TeacherException):
    """工号已存在"""

    def __init__(self, teacher_no: str = None, message: str = None, **kwargs):
        if teacher_no and message is None:
            message = f"工号 {teacher_no} 已存在"

        super().__init__(
            error_code=ErrorCode.TEACHER_NO_ALREADY_EXISTS.value, message=message, teacher_no=teacher_no, **kwargs
        )


class TeacherIdListEmptyException(TeacherException):
    """教师ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "教师ID列表不能为空"

        super().__init__(error_code=ErrorCode.TEACHER_ID_LIST_EMPTY.value, message=message, **kwargs)


class TeacherCreateFailedException(TeacherException):
    """教师新增失败"""

    def __init__(self, real_name: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"教师新增失败: {real_name}" if real_name else "教师新增失败"

        super().__init__(
            error_code=ErrorCode.TEACHER_CREATE_FAILED.value, message=message, real_name=real_name, **kwargs
        )


class TeacherUpdateFailedException(TeacherException):
    """教师更新失败"""

    def __init__(self, teacher_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"教师更新失败: {teacher_id}" if teacher_id else "教师更新失败"

        super().__init__(
            error_code=ErrorCode.TEACHER_UPDATE_FAILED.value, message=message, teacher_id=teacher_id, **kwargs
        )


class TeacherDeleteFailedException(TeacherException):
    """教师删除失败"""

    def __init__(self, teacher_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"教师删除失败: {teacher_id}" if teacher_id else "教师删除失败"

        super().__init__(
            error_code=ErrorCode.TEACHER_DELETE_FAILED.value, message=message, teacher_id=teacher_id, **kwargs
        )


class TeacherChangeStatusFailedException(TeacherException):
    """教师状态修改失败"""

    def __init__(self, teacher_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"教师状态修改失败: {teacher_id}" if teacher_id else "教师状态修改失败"

        super().__init__(
            error_code=ErrorCode.TEACHER_CHANGE_STATUS_FAILED.value,
            message=message,
            teacher_id=teacher_id,
            **kwargs,
        )


class TeacherUserNotFoundException(TeacherException):
    """关联的用户不存在"""

    def __init__(self, user_id: int = None, message: str = None, **kwargs):
        if user_id and message is None:
            message = f"关联的用户ID {user_id} 不存在"

        super().__init__(error_code=ErrorCode.TEACHER_USER_NOT_FOUND.value, message=message, user_id=user_id, **kwargs)


class TeacherNoPermissionException(TeacherException):
    """无权访问该教师数据"""

    def __init__(self, teacher_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"无权访问教师ID {teacher_id} 的数据" if teacher_id else "无权访问该教师数据"

        super().__init__(
            error_code=ErrorCode.TEACHER_NO_PERMISSION.value, message=message, teacher_id=teacher_id, **kwargs
        )


class TeacherMaxStudentCountExceededException(TeacherException):
    """教师带教学生数量已达上限"""

    def __init__(self, teacher_id: int = None, max_count: int = None, message: str = None, **kwargs):
        message = (
            f"教师带教学生数量已达上限（{max_count}人）"
            if max_count
            else "教师带教学生数量已达上限"
            if message is None
            else message
        )

        super().__init__(
            error_code=ErrorCode.TEACHER_MAX_STUDENT_COUNT_EXCEEDED.value,
            message=message,
            teacher_id=teacher_id,
            max_count=max_count,
            **kwargs,
        )


class TeacherAlreadyBoundException(TeacherException):
    """教师已绑定其他用户"""

    def __init__(self, teacher_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"教师ID {teacher_id} 已绑定其他用户" if teacher_id else "该教师已绑定其他用户"

        super().__init__(
            error_code=ErrorCode.TEACHER_ALREADY_BOUND.value, message=message, teacher_id=teacher_id, **kwargs
        )


# 导出所有异常类
__all__ = [
    "TeacherAlreadyBoundException",
    "TeacherAlreadyExistsException",
    "TeacherChangeStatusFailedException",
    "TeacherCreateFailedException",
    "TeacherDeleteFailedException",
    "TeacherException",
    "TeacherIdListEmptyException",
    "TeacherMaxStudentCountExceededException",
    "TeacherNoAlreadyExistsException",
    "TeacherNoPermissionException",
    "TeacherNotFoundException",
    "TeacherUpdateFailedException",
    "TeacherUserNotFoundException",
]
