"""FastAPI 应用创建模块

使用延迟创建模式，确保配置在应用创建前已加载
"""

import asyncio
from contextlib import asynccontextmanager
import logging
import sys

from fastapi import FastAPI

from graphedu.api.banner import service_banner
from graphedu.api.middleware import add_middlewares
from graphedu.api.services import add_routers
from graphedu.common.config.manager import get_config
from graphedu.common.exceptions import handle_exception
from graphedu.common.resource import ContainerMode, shutdown_container, try_get_container

logger = logging.getLogger(__name__)

# Windows 平台兼容性修复：设置事件循环策略
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def fastapi_lifespan(fastapi_instance: FastAPI):
    """FastAPI 应用生命周期管理器"""
    # 启动阶段 - 使用 SERVICE 模式
    await try_get_container(ContainerMode.SERVICE)
    logger.info(service_banner)
    logger.info(f"{fastapi_instance.title} start successfully!")
    yield
    # 关闭阶段
    await shutdown_container()


def create_fastapi() -> FastAPI:
    """创建并配置 FastAPI 应用实例

    在配置加载完成后调用，确保可以使用配置信息

    Returns:
        配置好的 FastAPI 实例
    """
    config = get_config()
    instance = FastAPI(
        title=config.app.name,
        description=f"{config.app.name}接口文档",
        version=config.app.version,
        debug=True,
        lifespan=fastapi_lifespan,
    )

    # 添加中间件
    add_middlewares(instance)
    add_routers(instance)
    handle_exception(instance)

    return instance


# 2. 创建应用实例（模块级别创建，配置已就绪）
app = create_fastapi()
