"""资源基类模块。"""

from abc import abstractmethod
from typing import TypeVar

from dependency_injector import resources
from pydantic import BaseModel

_ReturnedResource = TypeVar("_ReturnedResource")


class BaseSyncResource(resources.Resource):
    """同步资源基类。"""

    config: BaseModel

    mode: str = "sync"

    @abstractmethod
    def init(self, *args, **kwargs) -> _ReturnedResource:
        """初始化资源方法，必须实现"""
        raise NotImplementedError

    @abstractmethod
    def shutdown(self, instance: _ReturnedResource = None):
        """销毁资源方法，必须实现"""
        raise NotImplementedError


class BaseAsyncResource(resources.AsyncResource):
    """异步资源基类。"""

    config: BaseModel

    mode: str = "async"

    @abstractmethod
    async def init(self, *args, **kwargs) -> _ReturnedResource:
        """初始化资源方法，必须实现"""
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self, instance: _ReturnedResource = None):
        """销毁资源方法，必须实现"""
        raise NotImplementedError
