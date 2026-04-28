"""Neo4j 图数据库配置。"""

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, UrlConstraints


class Neo4jDsn(AnyUrl):
    """A type that will accept any Neo4j DSN.

    * User info not required
    * TLD not required
    * Host not required
    """

    _constraints = UrlConstraints(
        allowed_schemes=[
            "bolt",
            "bolt+s",
            "bolt+ssc",
            "neo4j",
            "neo4j+s",
            "neo4j+ssc",
        ],
        host_required=True,
    )


class Neo4jConfig(BaseModel):
    """Neo4j 图数据库配置。"""

    dsn: Neo4jDsn = Field(
        default="bolt://localhost:7687",
        description="Neo4j 数据库连接地址，详见 https://neo4j.com/docs/python-manual/6/connect-advanced/#_connection_protocols_and_security",
    )
    auth: list[str] = Field(default=["neo4j:password"], description="认证信息，格式为 [username:password]")
    timeout: int = Field(default=30, gt=0, description="连接超时时间（秒）")

    model_config = ConfigDict(validate_default=True)

    def get_auth_tuples(self) -> tuple[str, str]:
        """将 auth 列表转换为 (username, password) 元组。"""
        if not self.auth or len(self.auth) == 0:
            raise ValueError("Auth list cannot be empty")
        auth_str = self.auth[0]
        if ":" not in auth_str:
            raise ValueError("Auth string must be in the format 'username:password'")
        username, password = auth_str.split(":", 1)
        return username, password
