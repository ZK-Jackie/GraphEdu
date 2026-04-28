"""FastAPI 中间件模块。"""

from fastapi import FastAPI

from graphedu.api.middleware.cors import add_cors_middleware
from graphedu.api.middleware.gzip import add_gzip_middleware
from graphedu.api.middleware.trace import add_trace_middleware


def add_middlewares(app: "FastAPI"):
    """添加所有中间件到 FastAPI 应用实例"""
    # 添加追踪中间件（应该最先执行，在其他中间件之前）
    add_trace_middleware(app)
    add_cors_middleware(app)
    add_gzip_middleware(app)
