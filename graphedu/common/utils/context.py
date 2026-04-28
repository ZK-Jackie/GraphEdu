"""请求上下文管理工具

提供请求级别的数据存储和访问，基于 ContextVar 实现，
支持在 FastAPI 请求的整个生命周期中访问请求上下文数据。
"""

from contextlib import contextmanager
from contextvars import ContextVar, Token
import threading
from typing import Any, ClassVar

from starlette.datastructures import State
from starlette.requests import Request

# ========== RequestData：请求上下文数据结构 ==========


class RequestData(State):
    """请求上下文数据"""

    request: Request
    request_id: str
    request_time: float


# ========== RequestManager：请求上下文管理器 ==========


class RequestManager:
    """请求上下文管理器

    使用 ContextVar 存储请求级别的数据，提供静态方法进行访问。
    存储的数据包括：request_id（请求ID）和 request_time（请求时间戳）
    """

    _request_context: ContextVar[RequestData | None] = ContextVar("request_context", default=None)

    @classmethod
    def get_request_id(cls) -> str:
        """获取当前请求 ID"""
        ctx = cls._request_context.get()
        if ctx is None:
            return ""
        return ctx.request_id

    @classmethod
    def get_request_time(cls) -> float | None:
        """获取当前请求时间戳"""
        ctx = cls._request_context.get()
        if ctx is None:
            return 0.0
        return ctx.request_time

    @classmethod
    def get_request(cls) -> Request[RequestData] | None:
        """获取当前请求对象"""
        ctx = cls._request_context.get()
        if ctx is None:
            return None
        return ctx.request

    @classmethod
    def get_context(cls) -> RequestData | None:
        """获取完整的请求上下文"""
        return cls._request_context.get()

    @classmethod
    def set_context(cls, request: Request, request_id: str, request_time: float) -> None:
        """设置请求上下文"""
        request_data = RequestData({"request": request, "request_id": request_id, "request_time": request_time})
        cls._request_context.set(request_data)

    @classmethod
    def clear(cls) -> None:
        """清除请求上下文"""
        cls._request_context.set(None)


# ========== ContextManager：通用上下文管理器 ==========


class ContextManager:
    """通用上下文管理器。

    提供全局上下文和请求级上下文的存储和访问功能。
    """

    # 全局共享数据（类属性）
    _global_context: ClassVar[threading.local] = threading.local()
    _global_lock: ClassVar[threading.Lock] = threading.Lock()  # 类级锁

    # 请求级上下文变量（类属性）
    _request_context_dict: ContextVar[dict | None] = ContextVar("request_context_dict", default=None)

    # ---------- 全局数据操作（类方法） ----------
    @classmethod
    def get_global_context(cls, key: str, default: Any = None) -> Any:
        """获取全局配置（需类级锁保证线程安全）"""
        with cls._global_lock:
            return getattr(cls._global_context, key, default)

    @classmethod
    def set_global_context(cls, key: str, value: Any) -> None:
        """更新全局配置（需类级锁保证线程安全）"""
        with cls._global_lock:
            setattr(cls._global_context, key, value)

    # ---------- 请求级数据操作（类方法） ----------
    @classmethod
    def init_request_context(cls, initial_data: dict | None = None) -> Token:
        """初始化请求上下文"""
        request_data = initial_data or {}
        return cls._request_context_dict.set(request_data)

    @classmethod
    def get_request_data(cls, key: str, default: Any = None) -> Any:
        """获取当前请求数据"""
        ctx = cls._request_context_dict.get()
        if ctx is None:
            raise RuntimeError("Request context not initialized!")
        return ctx.get(key, default)

    @classmethod
    def reset_request_context(cls, token: Token) -> None:
        """清除请求上下文"""
        cls._request_context_dict.reset(token)

    @classmethod
    def set_request_data(cls, key: str, value: Any) -> None:
        """修改或添加当前请求上下文中的数据"""
        ctx = cls._request_context_dict.get()
        if ctx is None:
            raise RuntimeError("Request context not initialized!")

        # 创建一个新的字典，包含现有内容和新的键值对
        updated_ctx = {**ctx, key: value}
        # 更新上下文变量
        cls._request_context_dict.set(updated_ctx)

    @classmethod
    @contextmanager
    def request_context(cls, initial_data: dict | None = None):
        """上下文管理器：自动初始化和清理请求级数据"""
        token = cls._request_context_dict.set(initial_data or {})
        try:
            yield  # 在此处执行请求处理代码
        finally:
            cls._request_context_dict.reset(token)
