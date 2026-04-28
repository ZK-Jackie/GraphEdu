"""通用异步任务相关异常"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class AsyncTaskException(ServiceException):
    """异步任务异常基类"""

    def __init__(self, error_code: str = ErrorCode.ASYNC_TASK_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class AsyncTaskNotFoundException(AsyncTaskException):
    """异步任务不存在"""

    def __init__(self, task_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ASYNC_TASK_NOT_FOUND.value, message=message, task_id=task_id, **kwargs)


class AsyncTaskCannotCancelException(AsyncTaskException):
    """异步任务无法取消"""

    def __init__(self, current_status: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.ASYNC_TASK_CANNOT_CANCEL.value,
            message=message,
            current_status=current_status,
            **kwargs,
        )


class AsyncTaskCannotRetryException(AsyncTaskException):
    """异步任务无法重试"""

    def __init__(self, current_status: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.ASYNC_TASK_CANNOT_RETRY.value,
            message=message,
            current_status=current_status,
            **kwargs,
        )


class AsyncTaskCreateFailedException(AsyncTaskException):
    """异步任务创建失败"""

    def __init__(self, task_type: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.ASYNC_TASK_CREATE_FAILED.value,
            message=message,
            task_type=task_type,
            **kwargs,
        )


class AsyncTaskUpdateFailedException(AsyncTaskException):
    """异步任务状态更新失败"""

    def __init__(self, task_id: int = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.ASYNC_TASK_UPDATE_FAILED.value,
            message=message,
            task_id=task_id,
            **kwargs,
        )
