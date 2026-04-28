"""
base.py 资源类测试

测试 BaseSyncResource 和 BaseAsyncResource 基类的功能。
"""

from unittest.mock import Mock

import pytest
from pydantic import BaseModel

from graphedu.common.resource.core.base import (
    BaseAsyncResource,
    BaseSyncResource,
)


class DummyConfig(BaseModel):
    """用于测试的配置模型"""

    name: str = "test"
    value: int = 42


class DummySyncResource(BaseSyncResource):
    """用于测试的同步资源类"""

    config: DummyConfig | None = None
    _initialized: bool = False
    _resource: Mock | None = None

    def init(self, *args, **kwargs):
        """初始化资源"""
        self._initialized = True
        self._resource = Mock()
        self._resource.value = "test_resource"
        return self

    def shutdown(self, instance=None):
        """关闭资源"""
        self._initialized = False
        if self._resource:
            self._resource.cleanup.return_value = None
        self._resource = None


class DummyAsyncResource(BaseAsyncResource):
    """用于测试的异步资源类"""

    config: DummyConfig | None = None
    _initialized: bool = False
    _resource: Mock | None = None

    async def init(self, *args, **kwargs):
        """初始化资源"""
        self._initialized = True
        self._resource = Mock()
        self._resource.value = "test_async_resource"
        return self

    async def shutdown(self, instance=None):
        """关闭资源"""
        self._initialized = False
        if self._resource:
            self._resource.cleanup.return_value = None
        self._resource = None


class TestBaseSyncResource:
    """BaseSyncResource 基类测试"""

    def test_mode_attribute(self):
        """测试 mode 属性"""
        resource = DummySyncResource()
        assert resource.mode == "sync"

    def test_init_abstract_method(self):
        """测试 init 抽象方法"""
        resource = DummySyncResource()
        resource.init()
        assert resource._initialized is True
        assert resource._resource is not None

    def test_shutdown_abstract_method(self):
        """测试 shutdown 抽象方法"""
        resource = DummySyncResource()
        resource.init()
        assert resource._initialized is True

        resource.shutdown()
        assert resource._initialized is False
        assert resource._resource is None

    def test_shutdown_without_init(self):
        """测试在未初始化的情况下调用 shutdown"""
        resource = DummySyncResource()
        # 应该可以正常调用 shutdown，即使未初始化
        resource.shutdown()
        assert resource._initialized is False

    def test_init_returns_self(self):
        """测试 init 方法返回 self"""
        resource = DummySyncResource()
        result = resource.init()
        assert result is resource

    def test_config_attribute(self):
        """测试 config 属性"""
        resource = DummySyncResource()
        config = DummyConfig()
        resource.config = config
        assert resource.config is config


class TestBaseAsyncResource:
    """BaseAsyncResource 基类测试"""

    @pytest.mark.asyncio
    async def test_mode_attribute(self):
        """测试 mode 属性"""
        resource = DummyAsyncResource()
        assert resource.mode == "async"

    @pytest.mark.asyncio
    async def test_init_abstract_method(self):
        """测试 init 抽象方法"""
        resource = DummyAsyncResource()
        await resource.init()
        assert resource._initialized is True
        assert resource._resource is not None

    @pytest.mark.asyncio
    async def test_shutdown_abstract_method(self):
        """测试 shutdown 抽象方法"""
        resource = DummyAsyncResource()
        await resource.init()
        assert resource._initialized is True

        await resource.shutdown()
        assert resource._initialized is False
        assert resource._resource is None

    @pytest.mark.asyncio
    async def test_shutdown_without_init(self):
        """测试在未初始化的情况下调用 shutdown"""
        resource = DummyAsyncResource()
        # 应该可以正常调用 shutdown，即使未初始化
        await resource.shutdown()
        assert resource._initialized is False

    @pytest.mark.asyncio
    async def test_init_returns_self(self):
        """测试 init 方法返回 self"""
        resource = DummyAsyncResource()
        result = await resource.init()
        assert result is resource

    @pytest.mark.asyncio
    async def test_config_attribute(self):
        """测试 config 属性"""
        resource = DummyAsyncResource()
        config = DummyConfig()
        resource.config = config
        assert resource.config is config


class TestResourceLifecycle:
    """资源生命周期测试"""

    def test_sync_resource_lifecycle(self):
        """测试同步资源的完整生命周期"""
        resource = DummySyncResource()

        # 初始状态
        assert resource._initialized is False
        assert resource._resource is None

        # 初始化
        resource.init()
        assert resource._initialized is True
        assert resource._resource is not None
        assert resource._resource.value == "test_resource"

        # 关闭
        resource.shutdown()
        assert resource._initialized is False
        assert resource._resource is None

    @pytest.mark.asyncio
    async def test_async_resource_lifecycle(self):
        """测试异步资源的完整生命周期"""
        resource = DummyAsyncResource()

        # 初始状态
        assert resource._initialized is False
        assert resource._resource is None

        # 初始化
        await resource.init()
        assert resource._initialized is True
        assert resource._resource is not None
        assert resource._resource.value == "test_async_resource"

        # 关闭
        await resource.shutdown()
        assert resource._initialized is False
        assert resource._resource is None

    def test_sync_resource_reinitialize(self):
        """测试同步资源重新初始化"""
        resource = DummySyncResource()

        # 第一次初始化
        resource.init()
        first_resource = resource._resource
        assert first_resource is not None

        # 第二次初始化
        resource.init()
        second_resource = resource._resource
        assert second_resource is not None

        # 资源应该被替换
        assert first_resource is not second_resource

    @pytest.mark.asyncio
    async def test_async_resource_reinitialize(self):
        """测试异步资源重新初始化"""
        resource = DummyAsyncResource()

        # 第一次初始化
        await resource.init()
        first_resource = resource._resource
        assert first_resource is not None

        # 第二次初始化
        await resource.init()
        second_resource = resource._resource
        assert second_resource is not None

        # 资源应该被替换
        assert first_resource is not second_resource


class TestResourceWithConfig:
    """带配置的资源测试"""

    def test_sync_resource_with_config(self):
        """测试带配置的同步资源"""
        resource = DummySyncResource()
        config = DummyConfig()

        resource.config = config
        resource.init()

        assert resource.config is config
        assert resource._initialized is True

    @pytest.mark.asyncio
    async def test_async_resource_with_config(self):
        """测试带配置的异步资源"""
        resource = DummyAsyncResource()
        config = DummyConfig()

        resource.config = config
        await resource.init()

        assert resource.config is config
        assert resource._initialized is True
