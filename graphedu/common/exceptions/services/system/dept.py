"""部门相关异常

包含部门管理、部门操作等相关的异常定义，包含基类 DeptException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class DeptException(ServiceException):
    """部门异常基类"""

    def __init__(self, error_code: str = ErrorCode.DEPT_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class DeptNotFoundException(DeptException):
    """部门不存在"""

    def __init__(self, dept_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DEPT_NOT_FOUND.value, message=message, dept_id=dept_id, **kwargs)


class DeptAlreadyExistsException(DeptException):
    """部门已存在"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DEPT_ALREADY_EXISTS.value, message=message, **kwargs)


class DeptNameAlreadyExistsException(DeptException):
    """部门名称在同一父部门下已存在"""

    def __init__(self, dept_name: str = None, parent_id: int = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DEPT_NAME_ALREADY_EXISTS.value,
            message=message,
            dept_name=dept_name,
            parent_id=parent_id,
            **kwargs,
        )


class DeptKeyAlreadyExistsException(DeptException):
    """部门编码已存在"""

    def __init__(self, dept_key: str = None, dept_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DEPT_KEY_ALREADY_EXISTS.value,
            message=message,
            dept_key=dept_key,
            dept_name=dept_name,
            **kwargs,
        )


class DeptHasChildrenException(DeptException):
    """部门存在子部门，无法删除"""

    def __init__(self, dept_name: str = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DEPT_HAS_CHILDREN.value, message=message, dept_name=dept_name, **kwargs)


class DeptHasUsersException(DeptException):
    """部门存在关联用户，无法删除"""

    def __init__(self, dept_name: str = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DEPT_HAS_USERS.value, message=message, dept_name=dept_name, **kwargs)


class DeptCreateFailedException(DeptException):
    """部门创建失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DEPT_CREATE_FAILED.value, message=message, **kwargs)


class DeptUpdateFailedException(DeptException):
    """部门更新失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DEPT_UPDATE_FAILED.value, message=message, **kwargs)


class DeptDeleteFailedException(DeptException):
    """部门删除失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DEPT_DELETE_FAILED.value, message=message, **kwargs)


class DeptParentNotFoundException(DeptException):
    """父部门不存在"""

    def __init__(self, parent_id: int = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DEPT_PARENT_NOT_FOUND.value, message=message, parent_id=parent_id, **kwargs
        )


class DeptParentDisabledException(DeptException):
    """父部门已停用，不允许新增子部门"""

    def __init__(self, parent_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DEPT_PARENT_DISABLED.value, message=message, parent_name=parent_name, **kwargs
        )


class DeptParentItselfException(DeptException):
    """上级部门不能是自己"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DEPT_PARENT_IS_ITSELF.value, message=message, **kwargs)


class DeptParentCycleException(DeptException):
    """不能将父部门设为自己的子部门（循环引用）"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DEPT_PARENT_CYCLE.value, message=message, **kwargs)


class DeptHasActiveChildrenException(DeptException):
    """部门包含未停用的子部门"""

    def __init__(self, dept_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.DEPT_HAS_ACTIVE_CHILDREN.value, message=message, dept_name=dept_name, **kwargs
        )


class DeptNoPermissionException(DeptException):
    """没有权限访问该部门数据"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DEPT_NO_PERMISSION.value, message=message, **kwargs)


class DeptIdListEmptyException(DeptException):
    """部门ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.DEPT_ID_LIST_EMPTY.value, message=message, **kwargs)


# 导出所有异常类
__all__ = [
    "DeptAlreadyExistsException",
    "DeptCreateFailedException",
    "DeptDeleteFailedException",
    "DeptException",
    "DeptHasActiveChildrenException",
    "DeptHasChildrenException",
    "DeptHasUsersException",
    "DeptIdListEmptyException",
    "DeptKeyAlreadyExistsException",
    "DeptNameAlreadyExistsException",
    "DeptNoPermissionException",
    "DeptNotFoundException",
    "DeptParentCycleException",
    "DeptParentDisabledException",
    "DeptParentItselfException",
    "DeptParentNotFoundException",
    "DeptUpdateFailedException",
]
