"""配置管理器单例。"""

import logging
import os
from pathlib import Path
from typing import Literal

from ..utils.context import ContextManager
from ..utils.logger import initialize_logging
from .core.constants import ConfigConstants, RunningConstants
from .modes.service import ServiceConfig

logger = logging.getLogger(__name__)

_RunningModes = Literal["service", "builder", "clean", "lint", "test", "unknown"]

# 自动发现优先级（从高到低）
_DISCOVERY_PRIORITY = ["prod.config.yaml", "dev.config.yaml"]


def _discover_config_file(search_dir: Path) -> str | None:
    """在指定目录下自动发现配置文件。

    优先级：prod.config.yaml > dev.config.yaml > 按字典序的 *.config.yaml > config.yaml

    Args:
        search_dir: 搜索目录

    Returns:
        找到的配置文件绝对路径，未找到返回 None
    """
    if not search_dir.is_dir():
        return None

    # 1. 按固定优先级查找
    for name in _DISCOVERY_PRIORITY:
        candidate = (search_dir / name).resolve()
        if candidate.is_file():
            return str(candidate)

    # 2. 按字典序查找其他 *.config.yaml（排除已检查的）
    for p in sorted(search_dir.glob("*.config.yaml")):
        if p.name not in _DISCOVERY_PRIORITY:
            return str(p.resolve())

    # 3. 最后尝试 config.yaml
    fallback = (search_dir / "config.yaml").resolve()
    if fallback.is_file():
        return str(fallback)

    return None


def _resolve_config_path(filename: str | None, search_dir: Path) -> str:
    """解析配置文件路径。

    - filename 为 None 或文件不存在时，自动发现
    - 否则解析为绝对路径

    Args:
        filename: 显式指定的文件名/路径，None 表示自动发现
        search_dir: 搜索目录

    Returns:
        配置文件绝对路径

    Raises:
        FileNotFoundError: 无法找到任何配置文件
    """
    if filename is not None:
        resolved = Path(filename).resolve()
        if resolved.is_file():
            return str(resolved)
        logger.warning("指定的配置文件不存在: %s，尝试自动发现", filename)

    discovered = _discover_config_file(search_dir)
    if discovered:
        return discovered

    raise FileNotFoundError(
        f"在 {search_dir} 下未找到任何配置文件 (prod.config.yaml / dev.config.yaml / *.config.yaml / config.yaml)"
    )


class ConfigManager:
    """配置管理器单例。"""

    _instance: ServiceConfig | None = None

    @classmethod
    def load(
        cls,
        filename: str | None = None,
        use_cwd: bool = True,
        reload: bool = False,
        running_mode: _RunningModes = "service",
    ) -> ServiceConfig:
        """加载配置到全局上下文。

        优先级：默认值 < 本地 YAML < 环境 YAML < 环境变量

        Args:
            filename: 配置文件名/路径，None 则自动发现
            use_cwd: 是否从当前工作目录搜索
            reload: 强制重新加载
            running_mode: 应用运行模式

        Returns:
            加载的配置实例
        """
        if not reload and cls._instance:
            return cls._instance

        search_dir = Path.cwd() if use_cwd else Path(".")
        config_path = _resolve_config_path(filename, search_dir)

        # 设置本地配置文件环境变量（绝对路径）
        if not os.environ.get(ConfigConstants.CONFIG_FILE_LOCAL):
            os.environ[ConfigConstants.CONFIG_FILE_LOCAL] = config_path

        logger.info("加载配置文件: %s", config_path)

        # 创建配置实例（pydantic-settings 自动处理加载）
        config = ServiceConfig()

        # 缓存实例
        cls._instance = config

        # 存储到上下文
        ContextManager.set_global_context(RunningConstants.RUNNING_STATE, running_mode.upper())
        ContextManager.set_global_context(RunningConstants.CONFIG_INSTANCE, config)
        ContextManager.set_global_context(RunningConstants.RES_INITED_STATE, True)

        return config

    @classmethod
    def get(cls) -> ServiceConfig:
        """获取配置实例。如果未加载则自动加载默认配置。"""
        if cls._instance:
            return cls._instance

        # 尝试从上下文获取
        config = ContextManager.get_global_context(RunningConstants.CONFIG_INSTANCE)
        if config:
            cls._instance = config
            return config

        # 自动加载默认配置
        return cls.load()


def load_config(
    filename: str | None = None,
    use_cwd: bool = True,
    reload: bool = False,
    running_mode: _RunningModes = "service",
    init_logging: bool = True,
) -> ServiceConfig:
    """加载配置（向后兼容的包装函数）

    当前版本无论如何最终返回的都是 ServiceConfig 实例，仅在注册模式上有区别
    """
    conf = ConfigManager.load(filename, use_cwd, reload, running_mode)
    if init_logging:
        initialize_logging(conf.logging.get_dict_config())
    return conf


def get_config() -> ServiceConfig:
    """获取配置实例（向后兼容的包装函数）。"""
    return ConfigManager.get()
