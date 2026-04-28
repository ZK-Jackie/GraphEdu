"""聊天会话相关异常。

包含聊天会话管理相关的异常定义，包含基类 ChatSessionException 及其子类。
"""

from graphedu.common.exceptions.services.base import ServiceException
from graphedu.common.exceptions.services.codes import ErrorCode


class ChatSessionException(ServiceException):
    """聊天会话异常基类。"""

    def __init__(self, error_code: str = ErrorCode.CHAT_SESSION_NOT_FOUND.value, message: str = None, **kwargs):
        super().__init__(error_code=error_code, message=message, **kwargs)


class ChatSessionNotFoundException(ChatSessionException):
    """会话不存在。"""

    def __init__(self, session_uuid: str = None, message: str = None, **kwargs):
        if session_uuid and message is None:
            message = f"会话 {session_uuid} 不存在"

        super().__init__(
            error_code=ErrorCode.CHAT_SESSION_NOT_FOUND.value,
            message=message,
            session_uuid=session_uuid,
            **kwargs,
        )


class ChatSessionAccessDeniedException(ChatSessionException):
    """无权访问该会话。"""

    def __init__(self, session_uuid: str = None, user_id: int = None, message: str = None, **kwargs):
        if message is None:
            if session_uuid and user_id:
                message = f"用户 {user_id} 无权访问会话 {session_uuid}"
            else:
                message = "无权访问该会话"

        super().__init__(
            error_code=ErrorCode.CHAT_SESSION_ACCESS_DENIED.value,
            message=message,
            session_uuid=session_uuid,
            user_id=user_id,
            **kwargs,
        )


class ChatSessionCreateFailedException(ChatSessionException):
    """会话创建失败。"""

    def __init__(self, user_id: int = None, message: str = None, **kwargs):
        if message is None:
            message = f"用户 {user_id} 会话创建失败" if user_id else "会话创建失败"

        super().__init__(
            error_code=ErrorCode.CHAT_SESSION_CREATE_FAILED.value,
            message=message,
            user_id=user_id,
            **kwargs,
        )


class ChatMessageSendException(ChatSessionException):
    """消息发送失败。"""

    def __init__(self, session_uuid: str = None, message: str = None, **kwargs):
        if message is None:
            message = f"会话 {session_uuid} 消息发送失败" if session_uuid else "消息发送失败"

        super().__init__(
            error_code=ErrorCode.CHAT_MESSAGE_SEND_FAILED.value,
            message=message,
            session_uuid=session_uuid,
            **kwargs,
        )


class ChatAgentNotInitializedException(ChatSessionException):
    """聊天服务未初始化。"""

    def __init__(self, message: str = None, **kwargs):
        if message is None:
            message = "聊天服务未初始化"

        super().__init__(error_code=ErrorCode.CHAT_AGENT_NOT_INITIALIZED.value, message=message, **kwargs)


# 向后兼容旧命名
ChatSessionCreateException = ChatSessionCreateFailedException


__all__ = [
    "ChatAgentNotInitializedException",
    "ChatMessageSendException",
    "ChatSessionAccessDeniedException",
    "ChatSessionCreateException",
    "ChatSessionCreateFailedException",
    "ChatSessionException",
    "ChatSessionNotFoundException",
]
