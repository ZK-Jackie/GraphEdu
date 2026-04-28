"""MongoDB 数据库配置。"""

from pydantic import BaseModel, ConfigDict, Field, MongoDsn


class MongodbConfig(BaseModel):
    """MongoDB 数据库配置。"""

    url: MongoDsn = Field(default="mongodb://localhost:27017", description="MongoDB 连接地址（敏感信息）")
    db_name: str = Field(default="graphedu", description="MongoDB 数据库名称")

    model_config = ConfigDict(validate_default=True)
