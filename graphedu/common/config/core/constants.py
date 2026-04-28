"""配置常量定义。"""

CONFIG_PREFIX = "GRAPHEDU"  # 环境变量前缀


class ConfigConstants:
    """配置相关常量。"""

    CONFIG_FILE_ENV = "GE_CONFIG_FILE_ENV"  # 环境配置文件路径
    CONFIG_FILE_LOCAL = "GE_CONFIG_FILE_LOCAL"  # 本地配置文件路径
    CONFIG_FILE_DEFAULT = "dev.config.yaml"  # 默认配置文件名


class RunningConstants:
    """运行状态常量。"""

    RUNNING_STATE = "RUNNING_STATE"  # 运行模式
    CONFIG_INSTANCE = "CONFIG_INSTANCE"  # 配置实例
    RES_INITED_STATE = "RES_INITED_STATE"  # 资源初始化状态
