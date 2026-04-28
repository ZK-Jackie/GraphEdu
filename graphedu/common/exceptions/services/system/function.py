"""功能相关异常

包含功能管理、功能操作等相关的异常定义，包含基类 FunctionException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class FunctionException(ServiceException):
    """功能异常基类"""

    def __init__(self, error_code: str = ErrorCode.FUNCTION_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class FunctionNotFoundException(FunctionException):
    """功能不存在"""

    def __init__(self, function_id: int = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.FUNCTION_NOT_FOUND.value, message=message, function_id=function_id, **kwargs
        )


class FunctionAlreadyExistsException(FunctionException):
    """功能已存在"""

    def __init__(self, function_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.FUNCTION_ALREADY_EXISTS.value, message=message, function_name=function_name, **kwargs
        )


class FunctionNameAlreadyExistsException(FunctionException):
    """功能名称已存在"""

    def __init__(self, function_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.FUNCTION_NAME_ALREADY_EXISTS.value,
            message=message,
            function_name=function_name,
            **kwargs,
        )


class FunctionExternalLinkInvalidException(FunctionException):
    """外链地址格式无效"""

    def __init__(self, function_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.FUNCTION_EXTERNAL_LINK_INVALID.value,
            message=message,
            function_name=function_name,
            **kwargs,
        )


class FunctionParentItselfException(FunctionException):
    """上级功能不能选择自己"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.FUNCTION_PARENT_IS_ITSELF.value, message=message, **kwargs)


class FunctionHasChildrenException(FunctionException):
    """功能存在子功能，不允许删除"""

    def __init__(self, function_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.FUNCTION_HAS_CHILDREN.value, message=message, function_name=function_name, **kwargs
        )


class FunctionAssignedToRoleException(FunctionException):
    """功能已分配给角色，不允许删除"""

    def __init__(self, function_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.FUNCTION_ASSIGNED_TO_ROLE.value, message=message, function_name=function_name, **kwargs
        )


class FunctionCreateFailedException(FunctionException):
    """功能创建失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.FUNCTION_CREATE_FAILED.value, message=message, **kwargs)


class FunctionUpdateFailedException(FunctionException):
    """功能更新失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.FUNCTION_UPDATE_FAILED.value, message=message, **kwargs)


class FunctionDeleteFailedException(FunctionException):
    """功能删除失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.FUNCTION_DELETE_FAILED.value, message=message, **kwargs)


# 导出所有异常类
__all__ = [
    "FunctionAlreadyExistsException",
    "FunctionAssignedToRoleException",
    "FunctionCreateFailedException",
    "FunctionDeleteFailedException",
    "FunctionException",
    "FunctionExternalLinkInvalidException",
    "FunctionHasChildrenException",
    "FunctionNameAlreadyExistsException",
    "FunctionNotFoundException",
    "FunctionParentItselfException",
    "FunctionUpdateFailedException",
]
