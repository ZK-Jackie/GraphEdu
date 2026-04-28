"""用户相关异常

包含用户管理、用户操作等相关的异常定义，包含基类 UserException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class UserException(ServiceException):
    """用户异常基类"""

    def __init__(self, error_code: str = ErrorCode.USER_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class UserNotFoundException(UserException):
    """用户不存在"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.USER_NOT_FOUND.value, message=message, **kwargs)


class UserDisabledException(UserException):
    """用户已被禁用"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.USER_DISABLED.value, message=message, **kwargs)


class UserDeactivatedException(UserException):
    """用户已被停用"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.USER_DEACTIVATED.value, message=message, **kwargs)


class UserAlreadyExistsException(UserException):
    """用户已存在"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.USER_ALREADY_EXISTS.value, message=message, **kwargs)


class UserEmailAlreadyExistsException(UserException):
    """邮箱已被注册"""

    def __init__(self, email: str = None, message: str = None, **kwargs):
        if email and message is None:
            message = f"邮箱 {email} 已被注册"

        super().__init__(error_code=ErrorCode.USER_EMAIL_ALREADY_EXISTS.value, message=message, email=email, **kwargs)


class UserPhoneAlreadyExistsException(UserException):
    """手机号已被注册"""

    def __init__(self, phone: str = None, message: str = None, **kwargs):
        if phone and message is None:
            message = f"手机号 {phone} 已被注册"

        super().__init__(error_code=ErrorCode.USER_PHONE_ALREADY_EXISTS.value, message=message, phone=phone, **kwargs)


class UserOldPasswordIncorrectException(UserException):
    """旧密码不正确"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "重置密码失败，旧密码不正确"

        super().__init__(error_code=ErrorCode.USER_RESET_PASSWORD_OLD_INCORRECT.value, message=message, **kwargs)


class UserPasswordUnchangeException(UserException):
    """新密码不能与旧密码相同"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "重置密码失败，新密码不能与旧密码相同"

        super().__init__(error_code=ErrorCode.USER_RESET_PASSWORD_UNCHANGED.value, message=message, **kwargs)


class UserUpdateFailedException(UserException):
    """用户信息更新失败"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "用户信息更新失败"

        super().__init__(error_code=ErrorCode.USER_UPDATE_FAILED.value, message=message, **kwargs)


class UserDeleteFailedException(UserException):
    """用户删除失败"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "用户删除失败"

        super().__init__(error_code=ErrorCode.USER_DELETE_FAILED.value, message=message, **kwargs)


class UserIdNotFoundException(UserException):
    """用户ID不存在"""

    def __init__(self, user_id: int = None, message: str = None, **kwargs):
        if user_id and message is None:
            message = f"用户ID {user_id} 不存在"

        super().__init__(error_code=ErrorCode.USER_NOT_FOUND.value, message=message, user_id=user_id, **kwargs)


class UserIdListEmptyException(UserException):
    """用户ID列表为空"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "用户ID列表为空"

        super().__init__(error_code=ErrorCode.USER_OPERATION_FAILED.value, message=message, **kwargs)


class UserPhoneAlreadyExistsException(UserException):  # noqa: F811
    """手机号码已存在（重复定义，用于不同场景）"""

    def __init__(self, phone: str = None, message: str = None, **kwargs):
        if phone and message is None:
            message = f"手机号码{phone}已被注册"
        elif message is None:
            message = "手机号码已存在"

        super().__init__(error_code=ErrorCode.USER_PHONE_ALREADY_EXISTS.value, message=message, phone=phone, **kwargs)


class UserEmailAlreadyExistsException2(UserException):
    """邮箱账号已存在（用于更新场景）"""

    def __init__(self, email: str = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.USER_EMAIL_ALREADY_EXISTS.value, message=message, email=email, **kwargs)


class UserDeleteAdminForbiddenException(UserException):
    """不允许删除超级管理员用户"""

    def __init__(self, user_id: int = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.USER_DELETE_ADMIN.value, message=message, user_id=user_id, **kwargs)


class UserDeleteSelfForbiddenException(UserException):
    """不允许删除当前登录用户"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.USER_DELETE_SELF.value, message=message, **kwargs)


class UserResetPasswordFailedException(UserException):
    """用户修改密码失败"""

    def __init__(self, reason: str = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.USER_OPERATION_FAILED.value, message=message, reason=reason, **kwargs)


class UserOnlyAdminException(UserException):
    """只有管理员才能执行此操作"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.AUTH_NO_PERMISSION.value, message=message, **kwargs)


class UserCannotChangeOwnPasswordException(UserException):
    """只能修改自己的密码"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.AUTH_NO_PERMISSION.value, message=message, **kwargs)


class UserUpdateRoleFailedException(UserException):
    """更新用户角色关联失败"""

    def __init__(self, reason: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"更新用户角色关联失败: {reason}" if reason else "更新用户角色关联失败"

        super().__init__(error_code=ErrorCode.USER_UPDATE_FAILED.value, message=message, reason=reason, **kwargs)


class UserNoPermissionException(UserException):
    """无权访问该用户"""

    def __init__(self, user_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"无权访问用户ID {user_id}" if user_id else "无权访问该用户"

        super().__init__(error_code=ErrorCode.AUTH_NO_PERMISSION.value, message=message, user_id=user_id, **kwargs)


class UserAvatarOwnershipException(UserException):
    """头像文件必须是由当前用户上传的"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "头像文件必须是由当前用户上传的"

        super().__init__(error_code=ErrorCode.AUTH_NO_PERMISSION.value, message=message, **kwargs)


class UserCreateFailedException(UserException):
    """用户新增失败"""

    def __init__(self, user_name: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"用户新增失败: {user_name}" if user_name else "用户新增失败"

        super().__init__(
            error_code=ErrorCode.USER_OPERATION_FAILED.value, message=message, user_name=user_name, **kwargs
        )


class UserChangeStatusFailedException(UserException):
    """用户状态修改失败"""

    def __init__(self, user_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"用户状态修改失败: {user_id}" if user_id else "用户状态修改失败"

        super().__init__(error_code=ErrorCode.USER_UPDATE_FAILED.value, message=message, user_id=user_id, **kwargs)


class UserProfileUpdateFailedException(UserException):
    """用户个人信息修改失败"""

    def __init__(self, user_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"用户个人信息修改失败: {user_id}" if user_id else "用户个人信息修改失败"

        super().__init__(error_code=ErrorCode.USER_UPDATE_FAILED.value, message=message, user_id=user_id, **kwargs)


class UserAvatarUpdateFailedException(UserException):
    """用户头像修改失败"""

    def __init__(self, user_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"用户头像修改失败: {user_id}" if user_id else "用户头像修改失败"

        super().__init__(error_code=ErrorCode.USER_UPDATE_FAILED.value, message=message, user_id=user_id, **kwargs)


# ============================================================================
# 用户身份绑定相关异常
# ============================================================================


class UserIdentityAlreadyBoundException(UserException):
    """用户已绑定身份"""

    def __init__(self, user_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = "用户已绑定身份，无法重复绑定"

        super().__init__(
            error_code=ErrorCode.USER_IDENTITY_ALREADY_BOUND.value, message=message, user_id=user_id, **kwargs
        )


class UserIdentityNotBoundException(UserException):
    """用户未绑定身份"""

    def __init__(self, user_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = "用户未绑定身份"

        super().__init__(error_code=ErrorCode.USER_IDENTITY_NOT_BOUND.value, message=message, user_id=user_id, **kwargs)


class UserIdentityNotFoundException(UserException):
    """待绑定的身份信息不存在"""

    def __init__(self, identity_type: str = None, identity_no: str = None, message: str = None, **kwargs):
        if message is None:
            if identity_type == "student":
                message = f"学号 {identity_no} 对应的学生信息不存在" if identity_no else "学生信息不存在"
            elif identity_type == "teacher":
                message = f"工号 {identity_no} 对应的教师信息不存在" if identity_no else "教师信息不存在"
            else:
                message = "身份信息不存在"

        super().__init__(
            error_code=ErrorCode.USER_IDENTITY_NOT_FOUND.value,
            message=message,
            identity_type=identity_type,
            identity_no=identity_no,
            **kwargs,
        )


class UserIdentityAlreadyBoundByOtherException(UserException):
    """该身份已被其他用户绑定"""

    def __init__(self, identity_type: str = None, identity_no: str = None, message: str = None, **kwargs):
        if message is None:
            if identity_type == "student":
                message = f"学号 {identity_no} 已被其他用户绑定" if identity_no else "该学生已被其他用户绑定"
            elif identity_type == "teacher":
                message = f"工号 {identity_no} 已被其他用户绑定" if identity_no else "该教师已被其他用户绑定"
            else:
                message = "该身份已被其他用户绑定"

        super().__init__(
            error_code=ErrorCode.USER_IDENTITY_ALREADY_BOUND_BY_OTHER.value,
            message=message,
            identity_type=identity_type,
            identity_no=identity_no,
            **kwargs,
        )


class UserIdentityMismatchException(UserException):
    """身份ID与用户ID不匹配"""

    def __init__(self, user_id: int = None, identity_id: int = None, message: str = None, **kwargs):
        if message is None:
            if user_id and identity_id:
                message = f"身份ID {identity_id} 与用户ID {user_id} 不匹配，无法绑定"
            else:
                message = "身份ID与用户ID不匹配，无法绑定"

        super().__init__(
            error_code=ErrorCode.USER_IDENTITY_MISMATCH.value,
            message=message,
            user_id=user_id,
            identity_id=identity_id,
            **kwargs,
        )


# 导出所有异常类
__all__ = [
    "UserAlreadyExistsException",
    "UserAvatarOwnershipException",
    "UserAvatarUpdateFailedException",
    "UserCannotChangeOwnPasswordException",
    "UserChangeStatusFailedException",
    "UserCreateFailedException",
    "UserDeactivatedException",
    "UserDeleteAdminForbiddenException",
    "UserDeleteFailedException",
    "UserDeleteSelfForbiddenException",
    "UserDisabledException",
    "UserEmailAlreadyExistsException",
    "UserEmailAlreadyExistsException2",
    "UserException",
    "UserIdListEmptyException",
    "UserIdNotFoundException",
    "UserIdentityAlreadyBoundByOtherException",
    "UserIdentityAlreadyBoundException",
    "UserIdentityMismatchException",
    "UserIdentityNotBoundException",
    "UserIdentityNotFoundException",
    "UserNoPermissionException",
    "UserNotFoundException",
    "UserOldPasswordIncorrectException",
    "UserOnlyAdminException",
    "UserPasswordUnchangeException",
    "UserPhoneAlreadyExistsException",
    "UserProfileUpdateFailedException",
    "UserResetPasswordFailedException",
    "UserUpdateFailedException",
    "UserUpdateRoleFailedException",
]
