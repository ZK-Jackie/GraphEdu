"""容器管理模块：容器模式定义、工厂函数和全局生命周期管理。"""

from enum import StrEnum
import logging

from graphedu.common.resource.container import (
    CliContainer,
    GeneratorContainer,
    ServiceContainer,
    WorkerContainer,
)

logger = logging.getLogger(__name__)

# 容器类型联合，用于类型注解
ContainerType = ServiceContainer | WorkerContainer | GeneratorContainer | CliContainer


class ContainerMode(StrEnum):
    """容器运行模式。"""

    SERVICE = "service"
    WORKER = "worker"
    GENERATOR = "generator"
    CLI = "cli"


def create_container(
    mode: "ContainerMode | str" = ContainerMode.SERVICE,
) -> ContainerType:
    """根据运行模式创建对应的容器。

    Args:
        mode: 运行模式，默认为 SERVICE。

    Returns:
        容器实例。
    """
    mode = ContainerMode(mode)

    if mode == ContainerMode.SERVICE:
        return ServiceContainer()
    if mode == ContainerMode.WORKER:
        return WorkerContainer()
    if mode == ContainerMode.GENERATOR:
        return GeneratorContainer()
    # CLI
    return CliContainer()


# ==================== 全局容器状态 ====================

_container: ContainerType | None = None


async def try_get_container(
    mode: ContainerMode | str = ContainerMode.SERVICE,
) -> ContainerType:
    """获取容器实例，如果未初始化则先初始化。

    Args:
        mode: 运行模式，默认为 SERVICE。

    Returns:
        容器实例。
    """
    global _container
    if _container is None:
        _container = create_container(mode)
        await _container.init_resources()
    return _container


def get_container() -> ContainerType:
    """获取容器实例。

    Returns:
        容器实例。

    Raises:
        RuntimeError: 如果容器未初始化。
    """
    global _container
    if _container is None:
        raise RuntimeError("Container is not initialized. Call try_get_container() first.")
    return _container


def set_container(container: ContainerType | None) -> None:
    """设置容器实例（主要用于测试）。

    Args:
        container: 要设置的容器实例。
    """
    global _container
    _container = container


async def shutdown_container() -> None:
    """关闭容器并释放所有资源。"""
    global _container
    if _container:

        await _container.shutdown_resources()
        _container = None
        logger.info("Container released")
    else:
        logger.info("Container already released")
