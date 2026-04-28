"""聊天会话管理"""

import asyncio
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
import logging
import threading

logger: logging.Logger = logging.getLogger(__name__)


class RequestMetadata:
    """用于存储请求的元数据"""

    request_id: str
    """请求 ID"""

    request_start_time: datetime
    """请求开始时间"""

    last_visit_time: datetime
    """请求最后访问时间"""

    request_end_time: datetime | None
    """请求结束时间"""

    revoke: asyncio.Event
    """本次请求是否被撤销"""

    _asyncio_lock: asyncio.Lock
    """异步锁"""

    @property
    def request_duration(self) -> float | None:
        """请求持续时间"""
        if self.request_start_time and self.request_end_time:
            return (self.request_end_time - self.request_start_time).total_seconds()
        return None

    def __init__(self, request_id: str):
        self.request_id = request_id
        self.request_start_time = datetime.now()
        self.last_visit_time = datetime.now()
        self.revoke = asyncio.Event()
        self.request_end_time = None
        self._asyncio_lock = asyncio.Lock()

    async def is_revoked(self) -> bool:
        """检查请求是否被撤销"""
        async with self._asyncio_lock:
            self.last_visit_time = datetime.now()
            return self.revoke.is_set()

    async def revoke_request(self) -> None:
        """撤销请求"""
        async with self._asyncio_lock:
            logger.info(f"{self.request_id} request is revoked")
            self.request_end_time = datetime.now()
            self.revoke.set()

    async def is_expired(self) -> bool:
        """检查请求是否过期"""
        if self.request_end_time:
            return True
        if self.request_duration and self.request_duration > 3600:  # noqa: SIM103
            return True
        return False

    async def safe_clean(self) -> None:
        """安全清理"""
        async with self._asyncio_lock:
            logger.info(f"{self.request_id} request is expired, cleaning up")
            self.request_end_time = datetime.now()
            self.revoke.set()


class ChatSessionManager:
    """聊天会话池，用于控制某一会话状态"""

    _pool: dict[str, RequestMetadata] = {}
    _pool_lock: threading.Lock = threading.Lock()  # 类级锁

    @classmethod
    def get(cls, key: str) -> RequestMetadata | None:
        """获取请求上下文"""
        with cls._pool_lock:
            if key not in cls._pool:
                logger.warning(f"Session pool key '{key}' not found.")
                return None
            return cls._pool[key]

    @classmethod
    def set(cls, key: str, value: RequestMetadata) -> None:
        """设置请求上下文"""
        with cls._pool_lock:
            logger.debug(f"Setting session pool key '{key}' with value: {value}")
            cls._pool[key] = value

    @classmethod
    def delete(cls, key: str) -> None:
        """删除请求上下文"""
        with cls._pool_lock:
            if key in cls._pool:
                logger.debug(f"Deleting session pool key '{key}'")
                del cls._pool[key]
            else:
                logger.warning(f"Session pool key '{key}' not found for deletion.")

    @classmethod
    async def cron_clean(cls) -> None:
        """定期清理长期不用的会话"""
        with cls._pool_lock:
            logger.debug("Cleaning session pool...")
            for key in list(cls._pool.keys()):
                if await cls._pool[key].is_expired():
                    logger.debug(f"Cleaning expired session pool key '{key}'")
                    del cls._pool[key]
                else:
                    logger.debug(f"Session pool key '{key}' is still valid.")

    @classmethod
    @contextmanager
    def session_context(cls, session_id, initial_data: RequestMetadata) -> Generator[None]:
        """上下文管理器：自动初始化和清理请求级数据"""
        cls.set(session_id, initial_data)
        try:
            yield  # 在此处执行请求处理代码
        finally:
            cls.delete(session_id)
