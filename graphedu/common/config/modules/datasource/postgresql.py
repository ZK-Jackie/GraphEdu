"""PostgreSQL 数据库配置。"""

from pydantic import BaseModel, ConfigDict, Field, PostgresDsn

from .base import PoolConfig


class PostgresqlConfig(BaseModel):
    """PostgreSQL 数据库配置。"""

    dsn: PostgresDsn = Field(
        "postgresql://postgres:postgres@localhost:5432/graphedu", description="数据库连接字符串（敏感信息）"
    )
    echo: bool = Field(default=False, description="是否输出 SQL 日志到标准输出")
    pool: PoolConfig = Field(default_factory=PoolConfig, description="数据库连接池配置")

    model_config = ConfigDict(validate_default=True)

    def get_sa_sync_dsn(self) -> str:
        """获取用于 SQLAlchemy 的同步连接 DSN"""
        # TODO Reporting bug of redundant slashes in the generated DSN
        return (
            str(
                self.dsn.build(
                    scheme="postgresql+psycopg",
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
                scheme="postgresql+psycopg",
                hosts=self.dsn.hosts(),
                path=self.dsn.path if not self.dsn.path.startswith("/") else self.dsn.path[1:],
                query=self.dsn.query,
            )
        )


class AgeConfig(PostgresqlConfig):
    """Apache AGE 图数据库配置。

    AGE 是 PostgreSQL 的扩展，因此使用 PostgreSQL DSN。
    """

    visualized_graph_name: str = Field(default="edu_visualized_graph", description="可视化知识图谱名称")
    graphrag_graph_name: str = Field(default="graphrag", description="Graphrag 图数据库名称")
