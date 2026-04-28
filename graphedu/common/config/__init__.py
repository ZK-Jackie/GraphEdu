"""配置模块 v2（Spring Boot 风格）

使用 pydantic-settings 的新配置系统，提供标准化的配置加载机制。

使用示例:
    from graphedu.common.config import load_config, get_config

    # 加载配置（自动发现，或指定文件）
    config = load_config()          # 自动发现: prod > dev > *.config.yaml > config.yaml
    config = load_config("dev.config.yaml")  # 显式指定

    # 获取配置
    config = get_config()
    print(f"Service: {config.app.name} v{config.app.version}")
    print(f"Model: {config.model.chat.name}")
    print(f"Database: {config.datasource.postgresql.dsn}")
    print(f"Token expire: {config.security.token.expire}")
"""

# 新配置系统（v2）
from .core import BaseAppSettings, ConfigConstants, RunningConstants
from .manager import ConfigManager, get_config, load_config
from .modes import ServiceConfig

__all__ = [
    "BaseAppSettings",
    "ConfigConstants",
    "ConfigManager",
    "RunningConstants",
    "ServiceConfig",
    "get_config",
    "load_config",
]
