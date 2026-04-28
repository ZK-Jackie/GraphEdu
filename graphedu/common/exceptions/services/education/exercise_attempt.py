"""习题作答记录相关异常。"""

from typing import Any

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class ExerciseAttemptException(ServiceException):
    """习题作答记录异常基类。"""

    def __init__(
        self,
        error_code: str = ErrorCode.EXERCISE_ATTEMPT_NOT_FOUND.value,
        message: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(error_code=error_code, message=message, **kwargs)


class ExerciseAttemptNotFoundException(ExerciseAttemptException):
    """作答记录不存在。"""

    def __init__(self, attempt_id: int | None = None, message: str | None = None, **kwargs: Any):
        if attempt_id and message is None:
            message = f"作答记录ID {attempt_id} 不存在"

        super().__init__(
            error_code=ErrorCode.EXERCISE_ATTEMPT_NOT_FOUND.value,
            message=message,
            attempt_id=attempt_id,
            **kwargs,
        )


class ExerciseAttemptCreateFailedException(ExerciseAttemptException):
    """作答记录创建失败。"""

    def __init__(self, exercise_id: int | None = None, message: str | None = None, **kwargs: Any):
        if message is None:
            message = f"习题ID {exercise_id} 的作答记录创建失败" if exercise_id else "作答记录创建失败"

        super().__init__(
            error_code=ErrorCode.EXERCISE_ATTEMPT_CREATE_FAILED.value,
            message=message,
            exercise_id=exercise_id,
            **kwargs,
        )


class ExerciseAttemptExerciseNotFoundException(ExerciseAttemptException):
    """关联习题不存在。"""

    def __init__(self, exercise_id: int | None = None, message: str | None = None, **kwargs: Any):
        if message is None:
            message = f"关联习题ID {exercise_id} 不存在"

        super().__init__(
            error_code=ErrorCode.EXERCISE_ATTEMPT_EXERCISE_NOT_FOUND.value,
            message=message,
            exercise_id=exercise_id,
            **kwargs,
        )


__all__ = [
    "ExerciseAttemptCreateFailedException",
    "ExerciseAttemptException",
    "ExerciseAttemptExerciseNotFoundException",
    "ExerciseAttemptNotFoundException",
]
