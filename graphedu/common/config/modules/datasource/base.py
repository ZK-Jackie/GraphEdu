"""数据源配置聚合类（Spring Boot 风格：datasource）。"""

from typing import Literal

from pydantic import BaseModel, Field


class PoolConfig(BaseModel):
    """数据库连接池配置。"""

    echo_pool: bool = Field(default=False, description="是否在连接池日志中输出 SQL 语句")
    pool_size: int = Field(default=10, gt=0, description="连接池最大连接数")
    pool_recycle: int = Field(default=3600, gt=0, description="连接回收时间（秒），超过此时间的连接会被回收")
    pool_timeout: int = Field(default=30, gt=0, description="获取连接的超时时间（秒）")
    pool_pre_ping: bool = Field(default=True, description="是否在每次使用连接前测试连接有效性")
    pool_reset_on_return: Literal["rollback", "commit"] | bool | None = Field(
        default="rollback", description="连接归还时的重置策略"
    )
    pool_use_lifo: bool = Field(default=False, description="是否使用后进先出（LIFO）策略分配连接")
    connect_args: dict = Field(
        default_factory=lambda: {
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
        description="传递给 DBAPI connect() 的额外参数，默认启用 TCP keepalive",
    )


class RelationalConfigBaseModel(BaseModel):
    """关系型数据库配置基类，包含通用字段。"""

    dsn: str = Field(..., description="数据库连接字符串（敏感信息）")
    echo: bool = Field(default=False, description="是否输出 SQL 日志到标准输出")
    pool: PoolConfig = Field(default_factory=PoolConfig, description="数据库连接池配置")
