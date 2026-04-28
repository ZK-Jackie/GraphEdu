"""AI Agent 配置（对应 agent 命名空间）。"""

from typing import Literal

from pydantic import BaseModel, Field, PostgresDsn


class AgentConfig(BaseModel):
    """AI Agent 配置（Spring Boot 风格）。"""

    checkpoint_provider: Literal["mongodb", "postgresql"] = Field(
        default="postgresql", description="Agent 检查点数据的存储提供商（mongodb 或 postgresql）"
    )

    dsn: PostgresDsn = Field(
        default="postgresql://postgres:postgres@localhost:5432/graphedu",
        description="检查点数据库连接字符串（用于存储 Agent 对话状态）",
    )

    checkpoint_collection_name: str = Field(default="checkpoints", description="检查点数据集合/表名称")

    writes_collection_name: str = Field(default="checkpoint_writes", description="检查点写入记录集合/表名称")
