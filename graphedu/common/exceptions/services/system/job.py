"""定时任务相关异常

包含定时任务管理、任务执行等相关的异常定义，包含基类 JobException 及其子类

异常消息均通过 graphedu/common/exceptions/messages/zh_cn.py 中的模板格式化，
不在构造函数中硬编码，以便支持多语言扩展。
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class JobException(ServiceException):
    """定时任务异常基类"""

    def __init__(self, error_code: str = ErrorCode.JOB_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class JobNotFoundException(JobException):
    """定时任务不存在"""

    def __init__(self, job_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.JOB_NOT_FOUND.value, message=message, job_id=job_id, **kwargs)


class JobNameAlreadyExistsException(JobException):
    """任务名称已存在"""

    def __init__(self, job_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.JOB_NAME_ALREADY_EXISTS.value, message=message, job_name=job_name, **kwargs
        )


class JobCronInvalidException(JobException):
    """Cron表达式无效"""

    def __init__(self, cron_expression: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.JOB_CRON_INVALID.value,
            message=message,
            cron_expression=cron_expression,
            **kwargs,
        )


class JobTargetInvalidException(JobException):
    """调用目标非法"""

    def __init__(self, invoke_target: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.JOB_TARGET_INVALID.value,
            message=message,
            invoke_target=invoke_target,
            **kwargs,
        )


class JobConfigInvalidException(JobException):
    """任务配置无效"""

    def __init__(self, reason: str = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.JOB_CONFIG_INVALID.value, message=message, reason=reason, **kwargs)


class JobExecuteFailedException(JobException):
    """任务执行失败"""

    def __init__(self, job_name: str = None, reason: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.JOB_EXECUTE_FAILED.value,
            message=message,
            job_name=job_name,
            reason=reason,
            **kwargs,
        )


class JobChangeStatusFailedException(JobException):
    """任务状态修改失败"""

    def __init__(self, job_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.JOB_CHANGE_STATUS_FAILED.value, message=message, job_id=job_id, **kwargs)


class JobIdListEmptyException(JobException):
    """任务ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.JOB_ID_LIST_EMPTY.value, message=message, **kwargs)


class JobCreateFailedException(JobException):
    """任务创建失败"""

    def __init__(self, job_name: str = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.JOB_CREATE_FAILED.value, message=message, job_name=job_name, **kwargs)


class JobUpdateFailedException(JobException):
    """任务更新失败"""

    def __init__(self, job_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.JOB_UPDATE_FAILED.value, message=message, job_id=job_id, **kwargs)


class JobDeleteFailedException(JobException):
    """任务删除失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.JOB_DELETE_FAILED.value, message=message, **kwargs)


class JobNoPermissionException(JobException):
    """无权访问该任务"""

    def __init__(self, job_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.JOB_NO_PERMISSION.value, message=message, job_id=job_id, **kwargs)


class JobLogNotFoundException(JobException):
    """任务日志不存在"""

    def __init__(self, job_log_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.JOB_LOG_NOT_FOUND.value, message=message, job_log_id=job_log_id, **kwargs)


class JobLogIdListEmptyException(JobException):
    """任务日志ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.JOB_LOG_ID_LIST_EMPTY.value, message=message, **kwargs)


class JobLogDeleteFailedException(JobException):
    """任务日志删除失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.JOB_LOG_DELETE_FAILED.value, message=message, **kwargs)


class JobLogClearFailedException(JobException):
    """任务日志清空失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.JOB_LOG_CLEAR_FAILED.value, message=message, **kwargs)


# 导出所有异常类
__all__ = [
    "JobChangeStatusFailedException",
    "JobConfigInvalidException",
    "JobCreateFailedException",
    "JobCronInvalidException",
    "JobDeleteFailedException",
    "JobException",
    "JobExecuteFailedException",
    "JobIdListEmptyException",
    "JobLogClearFailedException",
    "JobLogDeleteFailedException",
    "JobLogIdListEmptyException",
    "JobLogNotFoundException",
    "JobNameAlreadyExistsException",
    "JobNoPermissionException",
    "JobNotFoundException",
    "JobTargetInvalidException",
    "JobUpdateFailedException",
]
