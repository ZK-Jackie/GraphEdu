"""课程相关异常

包含课程管理相关的异常定义，包含基类 CourseException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class CourseException(ServiceException):
    """课程异常基类"""

    def __init__(self, error_code: str = ErrorCode.COURSE_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class CourseNotFoundException(CourseException):
    """课程不存在"""

    def __init__(self, course_id: int = None, message: str = None, **kwargs):
        if course_id and message is None:
            message = f"课程ID {course_id} 不存在"

        super().__init__(error_code=ErrorCode.COURSE_NOT_FOUND.value, message=message, course_id=course_id, **kwargs)


class CourseCodeAlreadyExistsException(CourseException):
    """课程代码已存在"""

    def __init__(self, course_code: str = None, message: str = None, **kwargs):
        if course_code and message is None:
            message = f"课程代码 {course_code} 已存在"

        super().__init__(
            error_code=ErrorCode.COURSE_CODE_ALREADY_EXISTS.value, message=message, course_code=course_code, **kwargs
        )


class CourseIdListEmptyException(CourseException):
    """课程ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "课程ID列表不能为空"

        super().__init__(error_code=ErrorCode.COURSE_ID_LIST_EMPTY.value, message=message, **kwargs)


class CourseNoPermissionException(CourseException):
    """无权访问该课程数据"""

    def __init__(self, course_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"无权访问课程ID {course_id} 的数据" if course_id else "无权访问该课程数据"

        super().__init__(
            error_code=ErrorCode.COURSE_NO_PERMISSION.value, message=message, course_id=course_id, **kwargs
        )


# 导出所有异常类
__all__ = [
    "CourseCodeAlreadyExistsException",
    "CourseException",
    "CourseIdListEmptyException",
    "CourseNoPermissionException",
    "CourseNotFoundException",
]
