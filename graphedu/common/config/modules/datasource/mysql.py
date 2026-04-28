"""MySQL 数据库配置。"""

from pydantic import BaseModel, ConfigDict, Field, MySQLDsn

from .base import PoolConfig


class MysqlConfig(BaseModel):
    """MySQL 数据库配置。"""

    dsn: MySQLDsn = Field(
        default="mysql://user:password@localhost:3306/graphedu", description="MySQL 连接地址（敏感信息）"
    )
    echo: bool = Field(default=False, description="是否输出 SQL 日志到标准输出")
    timeout: int = Field(default=30, gt=0, description="连接超时时间（秒）")
    retry: int = Field(default=3, gt=0, description="连接重试次数")
    pool: PoolConfig = Field(default_factory=PoolConfig, description="数据库连接池配置")

    model_config = ConfigDict(validate_default=True)

    def get_sa_sync_dsn(self) -> str:
        """获取用于 SQLAlchemy 的同步连接 DSN"""
        # TODO Reporting bug of redundant slashes in the generated DSN
        return (
            str(
                self.dsn.build(
                    scheme="mysql+pymysql",
                    hosts=self.dsn.hosts(),
                    path=self.dsn.path if not self.dsn.path.startswith("/") else self.dsn.path[1:],
                    query=self.dsn.query,
                )
            )
            + self.dsn.path
        )

    def get_sa_async_dsn(self) -> str:
        """获取用于 SQLAlchemy 的异步连接 DSN"""
        # TODO Reporting bug of redundant slashes in the generated DSN
        return str(
            self.dsn.build(
                scheme="mysql+aiomysql",
                hosts=self.dsn.hosts(),
                path=self.dsn.path if not self.dsn.path.startswith("/") else self.dsn.path[1:],
                query=self.dsn.query,
            )
        )
