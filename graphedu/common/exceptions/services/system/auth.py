"""认证授权相关异常

包含基类 LoginException、RegisterException、PermissionDeniedException、TokenException、PasswordException 及其子类
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode

# ============================================================================
# 权限相关
# ============================================================================


class PermissionDeniedException(ServiceException):
    """权限不足异常"""

    def __init__(self, message: str = None, **kwargs):
        base = {"message": message, "error_code": ErrorCode.AUTH_NO_INTERFACE_PERMISSION.value}
        base.update(kwargs)
        super().__init__(**base)


class NoInterfacePermissionException(PermissionDeniedException):
    """没有接口访问权限"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.AUTH_NO_INTERFACE_PERMISSION.value, message=message, **kwargs)


class NoFunctionPermissionException(PermissionDeniedException):
    """没有功能访问权限"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.AUTH_NO_FUNCTION_PERMISSION.value, message=message, **kwargs)


# ============================================================================
# Token相关
# ============================================================================


class TokenException(ServiceException):
    """Token异常基类"""

    def __init__(self, error_code: str = ErrorCode.AUTH_TOKEN_INVALID.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class TokenMissingException(TokenException):
    """Token缺失"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.AUTH_TOKEN_MISSING.value, message=message, **kwargs)


class TokenExpiredException(TokenException):
    """Token已过期"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.AUTH_TOKEN_EXPIRED.value, message=message, **kwargs)


class TokenInvalidException(TokenException):
    """Token无效"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.AUTH_TOKEN_INVALID.value, message=message, **kwargs)


class TokenMalformedException(TokenException):
    """Token格式错误"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.AUTH_TOKEN_MALFORMED.value, message=message, **kwargs)


class TokenSignatureInvalidException(TokenException):
    """Token签名无效"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.AUTH_TOKEN_SIGNATURE_INVALID.value, message=message, **kwargs)


class TokenRefreshFailedException(TokenException):
    """Token刷新失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.AUTH_TOKEN_REFRESH_FAILED.value, message=message, **kwargs)


# ============================================================================
# 登录相关
# ============================================================================


class LoginException(ServiceException):
    """登录异常基类"""

    def __init__(self, error_code: str = ErrorCode.LOGIN_FAILED.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class LoginFailedException(LoginException):
    """登录失败"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_FAILED.value, message=message, **kwargs)


class LoginUserNotFoundException(LoginException):
    """登录用户不存在"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_USER_NOT_FOUND.value, message=message, **kwargs)


class LoginPasswordErrorException(LoginException):
    """登录密码错误"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_PASSWORD_ERROR.value, message=message, **kwargs)


class LoginUsernameLockedException(LoginException):
    """用户名登录被锁定"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_USERNAME_LOCKED.value, message=message, **kwargs)


class LoginAccountLockedException(LoginException):
    """账号被锁定"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_ACCOUNT_LOCKED.value, message=message, **kwargs)


class LoginAccountDisabledException(LoginException):
    """账号被禁用"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_ACCOUNT_DISABLED.value, message=message, **kwargs)


class LoginAccountExpiredException(LoginException):
    """账号已过期"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_ACCOUNT_EXPIRED.value, message=message, **kwargs)


class LoginCredentialsExpiredException(LoginException):
    """用户凭证已过期"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_CREDENTIALS_EXPIRED.value, message=message, **kwargs)


class LoginIpErrorException(LoginException):
    """登录IP异常"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_IP_INVALID.value, message=message, **kwargs)


class LoginAccountNotActivatedException(LoginException):
    """账号未激活"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_ACCOUNT_NOT_ACTIVATED.value, message=message, **kwargs)


class LoginAccountPendingReviewException(LoginException):
    """账号待审核"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_ACCOUNT_PENDING_REVIEW.value, message=message, **kwargs)


class LoginAccountRejectedException(LoginException):
    """账号审核未通过"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_ACCOUNT_REJECTED.value, message=message, **kwargs)


class LoginTooManyAttemptsException(LoginException):
    """登录尝试次数过多"""

    def __init__(
        self, period_seconds: int = 300, tries: int = 5, wait_seconds: int = 300, message: str = None, **kwargs
    ):
        """登录尝试次数过多异常

        Args:
            period_seconds: 尝试时间范围（秒）
            tries: 尝试次数
            wait_seconds: 要求等待间隔（秒）
            message: 自定义消息
            **kwargs: 其他参数
        """
        from graphedu.common.utils.strings import format_duration

        if message is None:
            message = "{try_time_range}内登录尝试次数过多，请{wait_time_range}后再试"

        super().__init__(
            error_code=ErrorCode.LOGIN_TOO_MANY_ATTEMPTS.value,
            message=message,
            try_time_range=format_duration(period_seconds),
            wait_time_range=format_duration(wait_seconds),
            data={"retryAfter": wait_seconds},
            **kwargs,
        )


class LoginSessionExpiredException(LoginException):
    """登录会话已过期"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_SESSION_EXPIRED.value, message=message, **kwargs)


class LoginSessionInvalidException(LoginException):
    """登录会话无效"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_SESSION_INVALID.value, message=message, **kwargs)


class LoginCaptchaErrorException(LoginException):
    """验证码错误"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_CAPTCHA_ERROR.value, message=message, **kwargs)


class LoginCaptchaExpiredException(LoginException):
    """验证码已过期"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_CAPTCHA_EXPIRED.value, message=message, **kwargs)


class LoginCaptchaRequiredException(LoginException):
    """需要验证码"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_CAPTCHA_REQUIRED.value, message=message, **kwargs)


class LoginTimeoutException(LoginException):
    """登录超时"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_TIMEOUT.value, message=message, **kwargs)


class LoginUnsupportedException(LoginException):
    """不支持的登录方式"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_UNSUPPORTED.value, message=message, **kwargs)


class LoginUserNotLockedException(LoginException):
    """用户未被锁定"""

    def __init__(self, username: str = None, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_USER_NOT_LOCKED.value, message=message, username=username, **kwargs)


class LoginStudentNotFoundException(LoginException):
    """学号不存在或未关联用户账号"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_STUDENT_NOT_FOUND.value, message=message, **kwargs)


class LoginTeacherNotFoundException(LoginException):
    """工号不存在或未关联用户账号"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_TEACHER_NOT_FOUND.value, message=message, **kwargs)


class LoginPhoneNotFoundException(LoginException):
    """手机号未注册"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.LOGIN_PHONE_NOT_FOUND.value, message=message, **kwargs)


# ============================================================================
# 注册相关
# ============================================================================


class RegisterException(ServiceException):
    """注册异常基类"""

    def __init__(self, error_code: str = ErrorCode.REGISTER_FAILED.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class RegisterFunctionDisabledException(RegisterException):
    """注册功能已关闭"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.REGISTER_FUNCTION_DISABLED.value, message=message, **kwargs)


class RegisterIllegalUsernameException(RegisterException):
    """用户名不合法"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.REGISTER_ILLEGAL_USERNAME.value, message=message, **kwargs)


class RegisterIllegalEmailException(RegisterException):
    """邮箱不合法"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.REGISTER_ILLEGAL_EMAIL.value, message=message, **kwargs)


class RegisterIllegalPhoneException(RegisterException):
    """手机号不合法"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.REGISTER_ILLEGAL_PHONE.value, message=message, **kwargs)


class RegisterIllegalPasswordException(RegisterException):
    """密码不合法"""

    def __init__(self, reason: str = None, message: str = None, **kwargs):
        if reason and message is None:
            message = f"密码非法，{reason}"

        super().__init__(error_code=ErrorCode.REGISTER_ILLEGAL_PASSWORD.value, message=message, **kwargs)


class RegisterIllegalDoublePasswordException(RegisterException):
    """两次输入密码不一致"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.REGISTER_ILLEGAL_DOUBLE_PASSWORD.value, message=message, **kwargs)


class RegisterUsernameExistsException(RegisterException):
    """用户名已存在"""

    def __init__(self, username: str = None, message: str = None, **kwargs):
        if username and message is None:
            message = f"用户注册失败，用户名{username}已被注册"

        super().__init__(
            error_code=ErrorCode.REGISTER_USERNAME_ALREADY_EXISTS.value, message=message, username=username, **kwargs
        )


class RegisterPhonenumberExistsException(RegisterException):
    """手机号已存在"""

    def __init__(self, phonenumber: str = None, message: str = None, **kwargs):
        if phonenumber and message is None:
            message = "用户注册失败，手机号已被注册"

        super().__init__(
            error_code=ErrorCode.REGISTER_PHONENUMBER_ALREADY_EXISTS.value,
            message=message,
            phonenumber=phonenumber,
            **kwargs,
        )


class RegisterEmailExistsException(RegisterException):
    """邮箱已存在"""

    def __init__(self, email: str = None, message: str = None, **kwargs):
        if email and message is None:
            message = "用户注册失败，邮箱已被注册"

        super().__init__(
            error_code=ErrorCode.REGISTER_EMAIL_ALREADY_EXISTS.value, message=message, email=email, **kwargs
        )


# ============================================================================
# 密码相关
# ============================================================================


class PasswordException(ServiceException):
    """密码异常基类"""

    def __init__(self, error_code: str = ErrorCode.PASSWORD_INCORRECT.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class PasswordTooWeakException(PasswordException):
    """密码强度不足"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.PASSWORD_TOO_WEAK.value, message=message, **kwargs)


class PasswordSameAsOldException(PasswordException):
    """新密码与旧密码相同"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.PASSWORD_SAME_AS_OLD.value, message=message, **kwargs)


class PasswordIncorrectException(PasswordException):
    """密码错误"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.PASSWORD_INCORRECT.value, message=message, **kwargs)


class PasswordExpiredException(PasswordException):
    """密码已过期"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.PASSWORD_EXPIRED.value, message=message, **kwargs)


class PasswordResetRequiredException(PasswordException):
    """需要重置密码"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.PASSWORD_RESET_REQUIRED.value, message=message, **kwargs)


class PasswordResetSmsCodeExpiredException(PasswordException):
    """短信验证码已过期"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.PASSWORD_RESET_SMS_CODE_EXPIRED.value, message=message, **kwargs)


class PasswordResetSmsCodeErrorException(PasswordException):
    """短信验证码错误"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(error_code=ErrorCode.PASSWORD_RESET_SMS_CODE_ERROR.value, message=message, **kwargs)


class PasswordResetSmsCodeSendTooFrequentException(PasswordException):
    """短信验证码发送过于频繁"""

    def __init__(self, message: str = None, **kwargs):
        super().__init__(
            error_code=ErrorCode.PASSWORD_RESET_SMS_CODE_SEND_TOO_FREQUENT.value, message=message, **kwargs
        )


# 导出所有异常类
__all__ = [
    "LoginAccountDisabledException",
    "LoginAccountExpiredException",
    "LoginAccountLockedException",
    "LoginAccountNotActivatedException",
    "LoginAccountPendingReviewException",
    "LoginAccountRejectedException",
    "LoginCaptchaErrorException",
    "LoginCaptchaExpiredException",
    "LoginCaptchaRequiredException",
    "LoginCredentialsExpiredException",
    # 登录
    "LoginException",
    "LoginFailedException",
    "LoginIpErrorException",
    "LoginPasswordErrorException",
    "LoginPhoneNotFoundException",
    "LoginSessionExpiredException",
    "LoginSessionInvalidException",
    "LoginStudentNotFoundException",
    "LoginTeacherNotFoundException",
    "LoginTimeoutException",
    "LoginTooManyAttemptsException",
    "LoginUnsupportedException",
    "LoginUserNotFoundException",
    "LoginUserNotLockedException",
    "LoginUsernameLockedException",
    "NoFunctionPermissionException",
    "NoInterfacePermissionException",
    # 密码
    "PasswordException",
    "PasswordExpiredException",
    "PasswordIncorrectException",
    "PasswordResetRequiredException",
    "PasswordResetSmsCodeErrorException",
    "PasswordResetSmsCodeExpiredException",
    "PasswordResetSmsCodeSendTooFrequentException",
    "PasswordSameAsOldException",
    "PasswordTooWeakException",
    # 权限
    "PermissionDeniedException",
    "RegisterEmailExistsException",
    # 注册
    "RegisterException",
    "RegisterFunctionDisabledException",
    "RegisterIllegalDoublePasswordException",
    "RegisterIllegalEmailException",
    "RegisterIllegalPasswordException",
    "RegisterIllegalPhoneException",
    "RegisterIllegalUsernameException",
    "RegisterPhonenumberExistsException",
    "RegisterUsernameExistsException",
    # Token
    "TokenException",
    "TokenExpiredException",
    "TokenInvalidException",
    "TokenMalformedException",
    "TokenMissingException",
    "TokenRefreshFailedException",
    "TokenSignatureInvalidException",
]
