"""Infrastructure Mixin：AsyncExecutorMixin + HttpClientMixin。"""

from dependency_injector import containers, providers

from graphedu.common.resource.modules.infrastructure.async_executor import AsyncExecutor
from graphedu.common.resource.modules.infrastructure.request import AsyncHttpClient


class AsyncExecutorMixin(containers.DeclarativeContainer):
    """提供异步执行器资源。

    Attributes:
        async_executor: 异步执行器实例，用于并发执行异步任务（默认最大 5 个工作线程）。
    """

    async_executor = providers.Resource(AsyncExecutor, max_workers=5)


class HttpClientMixin(containers.DeclarativeContainer):
    """提供 HTTP 客户端资源。

    Attributes:
        http_client: 异步 HTTP 客户端实例，用于发起 HTTP 请求（默认超时 30 秒）。
    """

    http_client = providers.Resource(AsyncHttpClient, config={"timeout": 30.0})
