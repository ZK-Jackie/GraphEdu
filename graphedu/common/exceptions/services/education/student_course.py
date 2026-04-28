"""选课相关异常

包含选课管理相关的异常定义，包含基类 StudentCourseException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class StudentCourseException(ServiceException):
    """选课异常基类"""

    def __init__(self, error_code: str = ErrorCode.STUDENT_COURSE_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class StudentCourseNotFoundException(StudentCourseException):
    """选课记录不存在"""

    def __init__(self, enrollment_id: int = None, message: str = None, **kwargs):
        if enrollment_id and message is None:
            message = f"选课记录ID {enrollment_id} 不存在"

        super().__init__(
            error_code=ErrorCode.STUDENT_COURSE_NOT_FOUND.value, message=message, enrollment_id=enrollment_id, **kwargs
        )


class StudentCourseAlreadyExistsException(StudentCourseException):
    """学生已选过该课程"""

    def __init__(self, student_id: int = None, course_id: int = None, message: str = None, **kwargs):
        if message is None and student_id and course_id:
            message = f"学生 {student_id} 已选过课程 {course_id}"

        super().__init__(
            error_code=ErrorCode.STUDENT_COURSE_ALREADY_EXISTS.value,
            message=message,
            student_id=student_id,
            course_id=course_id,
            **kwargs,
        )


class CourseNotAvailableException(StudentCourseException):
    """课程不可选（停用或未公开）"""

    def __init__(self, course_id: int = None, message: str = None, **kwargs):
        if message is None and course_id:
            message = f"课程 {course_id} 不可选"

        super().__init__(
            error_code=ErrorCode.COURSE_NOT_AVAILABLE.value, message=message, course_id=course_id, **kwargs
        )


# 导出所有异常类
__all__ = [
    "CourseNotAvailableException",
    "StudentCourseAlreadyExistsException",
    "StudentCourseException",
    "StudentCourseNotFoundException",
]
