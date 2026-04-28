"""Common 模块

提供项目中通用的工具、配置、异常和资源管理功能。

主要模块:
    - config: 配置管理
    - exceptions: 异常类
    - resource: 资源类（数据库、缓存、存储等）
    - utils: 工具函数
    - models: 数据模型

使用示例:
    # 配置
    from graphedu.common.config import load_config, get_config
    from graphedu.common.config.modules.datasource import PostgresqlConfig, RedisConfig

    # 异常
    from graphedu.common.exceptions import DatabaseConnectionException
    from graphedu.common.exceptions.resource import ResourceException

    # 资源
    from graphedu.common.resource import PostgresqlClient, RedisClient, AsyncPostgresqlClient

    # 工具
    from graphedu.common.utils import logger, files
"""

# 导出核心配置
# 导出资源模块（直接导入，便于使用）
from .config import (
    # 基础类
    BaseAppSettings,
    ConfigConstants,
    get_config,
    load_config,
)
from .exceptions import ConfigurationException

__all__ = [
    "BaseAppSettings",
    "ConfigConstants",
    "ConfigurationException",
    "get_config",
    "load_config",
]
