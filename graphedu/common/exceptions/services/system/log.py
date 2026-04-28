"""日志服务异常模块。"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class LogException(ServiceException):
    """日志异常基类"""

    def __init__(self, error_code: str = ErrorCode.LOG_UNEXPECTED_ERROR.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class LogIdListEmptyException(LogException):
    """日志ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOG_ID_LIST_EMPTY.value, message=message, **kwargs)


class LogCreateFailedException(LogException):
    """日志创建失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOG_CREATE_FAILED.value, message=message, **kwargs)


class LogDeleteFailedException(LogException):
    """日志删除失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOG_DELETE_FAILED.value, message=message, **kwargs)


class LogClearFailedException(LogException):
    """日志清空失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOG_CLEAR_FAILED.value, message=message, **kwargs)


# 导出所有异常类
__all__ = [
    "LogClearFailedException",
    "LogCreateFailedException",
    "LogDeleteFailedException",
    "LogException",
    "LogIdListEmptyException",
]
