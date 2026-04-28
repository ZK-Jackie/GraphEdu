"""Redis 缓存配置。"""

from pydantic import BaseModel, Field, RedisDsn


class RedisConfig(BaseModel):
    """Redis 缓存配置。"""

    dsn: RedisDsn = Field(
        default="redis://:password@localhost:6379/0",
        description="Redis 连接 URL，包含认证信息、数据库索引等参数（敏感信息）",
    )
