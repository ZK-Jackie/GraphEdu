"""Worker 配置模块

包含 Celery、MinerU 和 GraphRAG 相关配置。
"""

from pydantic import BaseModel, Field

from graphedu.common.config.modules.model import EmbeddingsConfig, LLMConfig


class CeleryConfig(BaseModel):
    """Celery 配置"""

    broker_url: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    result_backend: str = Field(default="redis://localhost:6379/2", description="Celery result backend")
    task_serializer: str = Field(default="json", description="任务序列化格式")
    result_serializer: str = Field(default="json", description="结果序列化格式")
    accept_content: list[str] = Field(default=["json"], description="接受的内容类型")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    task_track_started: bool = Field(default=True, description="跟踪任务开始时间")
    task_time_limit: int = Field(default=3600, description="任务超时时间（秒）")
    task_soft_time_limit: int = Field(default=3000, description="任务软超时时间（秒）")
    result_expires: int = Field(default=86400, description="任务结果过期时间（秒）")
    worker_prefetch_multiplier: int = Field(default=1, description="Worker 预取倍数")
    redis_backend_health_check_interval: int = Field(default=20, description="Redis 健康检查间隔（秒）")
    redis_max_connections: int = Field(default=5, description="Redis 连接池最大连接数")
    redis_socket_connect_timeout: int = Field(default=10, description="Redis 连接超时（秒）")
    redis_socket_keepalive: bool = Field(default=True, description="是否启用 Redis Keepalive")
    beat_sync_embeddings_interval: int = Field(default=3600, description="嵌入同步间隔（秒）")


class MinerUConfig(BaseModel):
    """MinerU API 配置"""

    base_url: str = Field(default="http://localhost:8888", description="MinerU API 基础 URL")
    api_key: str | None = Field(default=None, description="MinerU API 密钥")
    timeout: int = Field(default=30, description="API 请求超时时间（秒）")
    poll_interval: int = Field(default=5, description="轮询间隔（秒）")
    max_poll_attempts: int = Field(default=120, description="最大轮询次数")


class GraphRAGConfig(BaseModel):
    """GraphRAG 配置"""

    working_dir: str = Field(default="data/graphrag", description="GraphRAG 工作目录（含 input/output/cache 子目录）")
    prompt_repo_dir: str = Field(default="data/prompts", description="GraphRAG Prompt 模板目录，相对于项目根目录")
    method: str = Field(
        default="standard", description="索引构建方法（standard / fast / standard-update / fast-update）"
    )
    chunking_encoding_model: str = Field(
        default="cl100k_base",
        description="Chunking 使用的 tiktoken 编码模型（如 cl100k_base / o200k_base）",
    )

    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="GraphRAG 使用的 LLM 配置，注意，必须要支持json_output特性，支持的模型可见：https://help.aliyun.com/zh/model-studio/qwen-structured-output#79f0119db1jfn",
    )
    embeddings: EmbeddingsConfig = Field(
        default_factory=EmbeddingsConfig, description="GraphRAG 使用的 Embeddings 配置"
    )

    community_level: int = Field(default=2, description="社区层级过滤（值越大越精细）")
    response_type: str = Field(default="Multiple Paragraphs", description="搜索响应类型")
