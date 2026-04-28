"""学生相关异常

包含学生管理相关的异常定义，包含基类 StudentException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class StudentException(ServiceException):
    """学生异常基类"""

    def __init__(self, error_code: str = ErrorCode.STUDENT_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class StudentNotFoundException(StudentException):
    """学生不存在"""

    def __init__(self, student_id: int = None, message: str = None, **kwargs):
        if student_id and message is None:
            message = f"学生ID {student_id} 不存在"

        super().__init__(error_code=ErrorCode.STUDENT_NOT_FOUND.value, message=message, student_id=student_id, **kwargs)


class StudentAlreadyExistsException(StudentException):
    """学生已存在"""

    def __init__(self, student_id: int = None, message: str = None, **kwargs):
        if student_id and message is None:
            message = f"学生ID {student_id} 已存在"

        super().__init__(
            error_code=ErrorCode.STUDENT_ALREADY_EXISTS.value, message=message, student_id=student_id, **kwargs
        )


class StudentNoAlreadyExistsException(StudentException):
    """学号已存在"""

    def __init__(self, student_no: str = None, message: str = None, **kwargs):
        if student_no and message is None:
            message = f"学号 {student_no} 已存在"

        super().__init__(
            error_code=ErrorCode.STUDENT_NO_ALREADY_EXISTS.value, message=message, student_no=student_no, **kwargs
        )


class StudentIdListEmptyException(StudentException):
    """学生ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "学生ID列表不能为空"

        super().__init__(error_code=ErrorCode.STUDENT_ID_LIST_EMPTY.value, message=message, **kwargs)


class StudentCreateFailedException(StudentException):
    """学生新增失败"""

    def __init__(self, real_name: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"学生新增失败: {real_name}" if real_name else "学生新增失败"

        super().__init__(
            error_code=ErrorCode.STUDENT_CREATE_FAILED.value, message=message, real_name=real_name, **kwargs
        )


class StudentUpdateFailedException(StudentException):
    """学生更新失败"""

    def __init__(self, student_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"学生更新失败: {student_id}" if student_id else "学生更新失败"

        super().__init__(
            error_code=ErrorCode.STUDENT_UPDATE_FAILED.value, message=message, student_id=student_id, **kwargs
        )


class StudentDeleteFailedException(StudentException):
    """学生删除失败"""

    def __init__(self, student_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"学生删除失败: {student_id}" if student_id else "学生删除失败"

        super().__init__(
            error_code=ErrorCode.STUDENT_DELETE_FAILED.value, message=message, student_id=student_id, **kwargs
        )


class StudentChangeStatusFailedException(StudentException):
    """学生状态修改失败"""

    def __init__(self, student_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"学生状态修改失败: {student_id}" if student_id else "学生状态修改失败"

        super().__init__(
            error_code=ErrorCode.STUDENT_CHANGE_STATUS_FAILED.value,
            message=message,
            student_id=student_id,
            **kwargs,
        )


class StudentUserNotFoundException(StudentException):
    """关联的用户不存在"""

    def __init__(self, user_id: int = None, message: str = None, **kwargs):
        if user_id and message is None:
            message = f"关联的用户ID {user_id} 不存在"

        super().__init__(error_code=ErrorCode.STUDENT_USER_NOT_FOUND.value, message=message, user_id=user_id, **kwargs)


class StudentNoPermissionException(StudentException):
    """无权访问该学生数据"""

    def __init__(self, student_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"无权访问学生ID {student_id} 的数据" if student_id else "无权访问该学生数据"

        super().__init__(
            error_code=ErrorCode.STUDENT_NO_PERMISSION.value, message=message, student_id=student_id, **kwargs
        )


class StudentAlreadyBoundException(StudentException):
    """学生已绑定其他用户"""

    def __init__(self, student_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"学生ID {student_id} 已绑定其他用户" if student_id else "该学生已绑定其他用户"

        super().__init__(
            error_code=ErrorCode.STUDENT_ALREADY_BOUND.value, message=message, student_id=student_id, **kwargs
        )


# 导出所有异常类
__all__ = [
    "StudentAlreadyBoundException",
    "StudentAlreadyExistsException",
    "StudentChangeStatusFailedException",
    "StudentCreateFailedException",
    "StudentDeleteFailedException",
    "StudentException",
    "StudentIdListEmptyException",
    "StudentNoAlreadyExistsException",
    "StudentNoPermissionException",
    "StudentNotFoundException",
    "StudentUpdateFailedException",
    "StudentUserNotFoundException",
]
