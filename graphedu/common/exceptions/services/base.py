"""基础异常类

定义所有API层业务异常的基类，包含基类 ServiceException 和警告类 ServiceWarning。
"""

import contextlib
from datetime import UTC, datetime
from typing import Any


class ServiceException(Exception):
    """API层业务异常基类

    特点：
    - 支持分层错误码（模块.编号）
    - 支持i18n错误消息（预留）
    - 包含HTTP状态码
    - 可附加额外数据
    - 向后兼容旧代码

    Attributes:
        error_code: 业务错误码（如 "AUTH.10001"）
        message: 错误消息
        http_status: HTTP状态码（如 401, 403等）
        data: 附加数据
    """

    def __init__(
        self,
        error_code: str | None = None,
        message: str | None = None,
        http_status: int | None = None,
        data: Any = None,
        code: int | None = None,  # 向后兼容：等同于http_status
        **kwargs,
    ):
        """初始化异常

        Args:
            error_code: 业务错误码（如 "AUTH.10001"）
            message: 自定义错误消息（为空则从i18n获取）
            http_status: HTTP状态码（为空则从错误码默认映射获取）
            data: 附加数据
            code: 向后兼容参数，等同于http_status
            **kwargs: 消息格式化参数（如 username="zhangsan"）
        """
        # 向后兼容：如果只传了code参数，当作http_status使用
        if code is not None and http_status is None:
            http_status = code

        # 如果error_code和message都没提供，使用默认值
        if error_code is None and message is None:
            from .codes import ErrorCode

            error_code = ErrorCode.SYSTEM_ERROR.value

        self.error_code = error_code
        self.data = data
        self.kwargs = kwargs

        # 确定HTTP状态码
        if http_status is None and error_code is not None:
            from .codes import ErrorCode

            try:
                error_code_enum = ErrorCode(error_code)
                http_status = error_code_enum.http_status
            except ValueError:
                # 如果error_code不是有效的枚举值，使用默认500
                http_status = 500

        if http_status is None:
            http_status = 500

        self.http_status = http_status
        self.code = http_status  # 向后兼容

        # 确定消息
        if message is None:
            message = self._get_message()
        elif kwargs:
            # 如果有格式化参数，格式化消息
            with contextlib.suppress(KeyError, ValueError):
                message = message.format(**kwargs)

        self.message = message

        super().__init__(self.message)

    def _get_message(self) -> str:
        """获取错误消息

        优先级：
        1. 从i18n获取（预留，当前未实现）
        2. 从默认消息映射获取
        3. 返回"未知错误"

        Returns:
            错误消息字符串
        """
        if self.error_code:
            try:
                from ..messages import get_message
                from .codes import ErrorCode

                error_code_enum = ErrorCode(self.error_code)
                return get_message(error_code_enum, **self.kwargs)
            except (ValueError, ImportError):
                pass

        return "未知错误"

    def to_dict(self) -> dict:
        """转换为字典（用于API响应）

        Returns:
            包含错误信息的字典
        """
        result = {
            "code": self.http_status,
            "msg": self.message,
            "data": self.data or {},
            "time": datetime.now(UTC).isoformat(),
        }

        # 如果有错误码，也包含在响应中
        if self.error_code:
            result["errorCode"] = self.error_code

        return result

    def __repr__(self) -> str:
        """调试用字符串表示"""
        if self.error_code:
            return (
                f"{self.__class__.__name__}(error_code={self.error_code}, "
                f"http_status={self.http_status}, message={self.message})"
            )
        return f"{self.__class__.__name__}(http_status={self.http_status}, message={self.message})"


class ServiceWarning(Exception):
    """服务警告（非错误）

    用于不需要中断流程的警告信息
    """

    def __init__(self, message: str, data: Any = None):
        self.message = message
        self.data = data
        super().__init__(self.message)


# 导出
__all__ = ["ServiceException", "ServiceWarning"]
