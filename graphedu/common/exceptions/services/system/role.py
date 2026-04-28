"""角色相关异常

包含角色管理、角色操作等相关的异常定义，包含基类 RoleException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class RoleException(ServiceException):
    """角色异常基类"""

    def __init__(self, error_code: str = ErrorCode.ROLE_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class RoleNotFoundException(RoleException):
    """角色不存在"""

    def __init__(self, role_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ROLE_NOT_FOUND.value, message=message, role_id=role_id, **kwargs)


class RoleAlreadyExistsException(RoleException):
    """角色已存在"""

    def __init__(self, role_name: str = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ROLE_ALREADY_EXISTS.value, message=message, role_name=role_name, **kwargs)


class RoleNameAlreadyExistsException(RoleException):
    """角色名称已存在"""

    def __init__(self, role_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.ROLE_NAME_ALREADY_EXISTS.value, message=message, role_name=role_name, **kwargs
        )


class RoleKeyAlreadyExistsException(RoleException):
    """角色标识已存在"""

    def __init__(self, role_key: str = None, role_name: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.ROLE_KEY_ALREADY_EXISTS.value,
            message=message,
            role_key=role_key,
            role_name=role_name,
            **kwargs,
        )


class RoleCreateFailedException(RoleException):
    """角色创建失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ROLE_CREATE_FAILED.value, message=message, **kwargs)


class RoleUpdateFailedException(RoleException):
    """角色更新失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ROLE_UPDATE_FAILED.value, message=message, **kwargs)


class RoleDeleteFailedException(RoleException):
    """角色删除失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ROLE_DELETE_FAILED.value, message=message, **kwargs)


class RoleHasUsersException(RoleException):
    """角色已分配给用户，无法删除"""

    def __init__(self, role_name: str = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ROLE_HAS_USERS.value, message=message, role_name=role_name, **kwargs)


class RoleIdListEmptyException(RoleException):
    """角色ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ROLE_ID_LIST_EMPTY.value, message=message, **kwargs)


class RoleModifyAdminForbiddenException(RoleException):
    """不允许修改超级管理员角色"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ROLE_MODIFY_ADMIN_FORBIDDEN.value, message=message, **kwargs)


class RoleDeleteAdminForbiddenException(RoleException):
    """不允许删除超级管理员角色"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ROLE_DELETE_ADMIN_FORBIDDEN.value, message=message, **kwargs)


class RoleChangeAdminStatusForbiddenException(RoleException):
    """不允许修改超级管理员角色状态"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ROLE_CHANGE_ADMIN_STATUS_FORBIDDEN.value, message=message, **kwargs)


class RoleNoPermissionException(RoleException):
    """无权访问该角色"""

    def __init__(self, role_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ROLE_NO_PERMISSION.value, message=message, role_id=role_id, **kwargs)


class RoleAuthorizeUsersFailedException(RoleException):
    """批量授权用户失败"""

    def __init__(self, reason: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.ROLE_AUTHORIZE_USERS_FAILED.value, message=message, reason=reason, **kwargs
        )


class RoleRevokeUsersFailedException(RoleException):
    """取消用户角色授权失败"""

    def __init__(self, reason: str = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.ROLE_REVOKE_USERS_FAILED.value, message=message, reason=reason, **kwargs)


class RoleRevokeUsersBatchFailedException(RoleException):
    """批量取消用户角色授权失败"""

    def __init__(self, reason: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.ROLE_REVOKE_USERS_BATCH_FAILED.value, message=message, reason=reason, **kwargs
        )


class RoleUpdateDataScopeFailedException(RoleException):
    """修改角色数据权限范围失败"""

    def __init__(self, reason: str = None, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.ROLE_UPDATE_DATA_SCOPE_FAILED.value, message=message, reason=reason, **kwargs
        )


# 导出所有异常类
__all__ = [
    "RoleAlreadyExistsException",
    "RoleAuthorizeUsersFailedException",
    "RoleChangeAdminStatusForbiddenException",
    "RoleCreateFailedException",
    "RoleDeleteAdminForbiddenException",
    "RoleDeleteFailedException",
    "RoleException",
    "RoleHasUsersException",
    "RoleIdListEmptyException",
    "RoleKeyAlreadyExistsException",
    "RoleModifyAdminForbiddenException",
    "RoleNameAlreadyExistsException",
    "RoleNoPermissionException",
    "RoleNotFoundException",
    "RoleRevokeUsersBatchFailedException",
    "RoleRevokeUsersFailedException",
    "RoleUpdateDataScopeFailedException",
    "RoleUpdateFailedException",
]
