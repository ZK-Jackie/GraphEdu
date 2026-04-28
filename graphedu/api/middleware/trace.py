"""请求追踪中间件

为每个请求生成唯一的 request_id，并将其存储到：
1. RequestManager（ContextVar）- 可在整个请求链路中访问
2. request.state - 可在 FastAPI 请求对象中访问
3. 响应头 X-Request-ID - 返回给客户端
"""

from collections.abc import Callable
import time
from typing import Any

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from graphedu.common.utils.context import RequestManager
from graphedu.common.utils.uuids import uuid7_str


class TraceMiddleware(BaseHTTPMiddleware):
    """请求追踪中间件

    功能：
    1. 从请求头获取或生成 request_id
    2. 将 request_id 和 request_time 存储到 RequestManager
    3. 将 request_id 存储到 request.state
    4. 在响应头中返回 request_id 和处理时间
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """处理传入请求，添加请求追踪信息"""
        # 1. 从请求头获取或生成 request_id
        request_id = request.headers.get("X-Request-ID") or uuid7_str()
        request_time = time.time()

        # 2. 初始化请求上下文（存储到 ContextVar）
        RequestManager.set_context(request, request_id, request_time)

        # 3. 存储到 request.state
        request.state.request_id = request_id
        request.state.request_time = RequestManager.get_request_time()

        # 4. 处理请求
        response = await call_next(request)

        # 5. 添加响应头
        response.headers["X-Request-ID"] = request_id

        # 6. 计算并添加处理时间
        process_time = time.time() - RequestManager.get_request_time()
        response.headers["X-Process-Time"] = f"{process_time:.6f}"

        # 7. 清理请求上下文
        RequestManager.clear()

        return response


def add_trace_middleware(app: FastAPI):
    """添加请求追踪中间件

    :param app: FastAPI对象
    :return:
    """
    app.add_middleware(TraceMiddleware)
