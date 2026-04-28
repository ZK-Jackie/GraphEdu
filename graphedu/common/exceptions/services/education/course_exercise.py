"""课程练习相关异常。"""

from typing import Any

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class CourseExerciseException(ServiceException):
    """课程练习异常基类。"""

    def __init__(
        self,
        error_code: str = ErrorCode.COURSE_EXERCISE_NOT_FOUND.value,
        message: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(error_code=error_code, message=message, **kwargs)


class CourseExerciseNotFoundException(CourseExerciseException):
    """课程练习不存在。"""

    def __init__(self, exercise_id: int | None = None, message: str | None = None, **kwargs: Any):
        if exercise_id and message is None:
            message = f"课程练习ID {exercise_id} 不存在"

        super().__init__(
            error_code=ErrorCode.COURSE_EXERCISE_NOT_FOUND.value,
            message=message,
            exercise_id=exercise_id,
            **kwargs,
        )


class CourseExerciseIdListEmptyException(CourseExerciseException):
    """课程练习ID列表为空。"""

    def __init__(self, message: str | None = None, **kwargs: Any):
        if message is None:
            message = "课程练习ID列表不能为空"

        super().__init__(
            error_code=ErrorCode.COURSE_EXERCISE_ID_LIST_EMPTY.value,
            message=message,
            **kwargs,
        )


class CourseExerciseCreateFailedException(CourseExerciseException):
    """课程练习创建失败。"""

    def __init__(self, course_id: int | None = None, message: str | None = None, **kwargs: Any):
        if message is None:
            message = f"课程ID {course_id} 的练习新增失败" if course_id else "课程练习新增失败"

        super().__init__(
            error_code=ErrorCode.COURSE_EXERCISE_CREATE_FAILED.value,
            message=message,
            course_id=course_id,
            **kwargs,
        )


class CourseExerciseUpdateFailedException(CourseExerciseException):
    """课程练习更新失败。"""

    def __init__(self, exercise_id: int | None = None, message: str | None = None, **kwargs: Any):
        if message is None:
            message = f"课程练习更新失败: {exercise_id}" if exercise_id else "课程练习更新失败"

        super().__init__(
            error_code=ErrorCode.COURSE_EXERCISE_UPDATE_FAILED.value,
            message=message,
            exercise_id=exercise_id,
            **kwargs,
        )


class CourseExerciseDeleteFailedException(CourseExerciseException):
    """课程练习删除失败。"""

    def __init__(self, exercise_id: int | None = None, message: str | None = None, **kwargs: Any):
        if message is None:
            message = f"课程练习删除失败: {exercise_id}" if exercise_id else "课程练习删除失败"

        super().__init__(
            error_code=ErrorCode.COURSE_EXERCISE_DELETE_FAILED.value,
            message=message,
            exercise_id=exercise_id,
            **kwargs,
        )


class CourseExerciseChangeStatusFailedException(CourseExerciseException):
    """课程练习状态修改失败。"""

    def __init__(self, exercise_id: int | None = None, message: str | None = None, **kwargs: Any):
        if message is None:
            message = f"课程练习状态修改失败: {exercise_id}" if exercise_id else "课程练习状态修改失败"

        super().__init__(
            error_code=ErrorCode.COURSE_EXERCISE_CHANGE_STATUS_FAILED.value,
            message=message,
            exercise_id=exercise_id,
            **kwargs,
        )


class CourseExerciseBatchGenerateFailedException(CourseExerciseException):
    """课程练习批量生成失败。"""

    def __init__(self, course_id: int | None = None, message: str | None = None, **kwargs: Any):
        if message is None:
            message = f"课程ID {course_id} 的练习批量生成失败" if course_id else "课程练习批量生成失败"

        super().__init__(
            error_code=ErrorCode.COURSE_EXERCISE_BATCH_GENERATE_FAILED.value,
            message=message,
            course_id=course_id,
            **kwargs,
        )


__all__ = [
    "CourseExerciseBatchGenerateFailedException",
    "CourseExerciseChangeStatusFailedException",
    "CourseExerciseCreateFailedException",
    "CourseExerciseDeleteFailedException",
    "CourseExerciseException",
    "CourseExerciseIdListEmptyException",
    "CourseExerciseNotFoundException",
    "CourseExerciseUpdateFailedException",
]
