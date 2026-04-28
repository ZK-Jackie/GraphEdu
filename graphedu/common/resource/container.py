"""专用容器模块：按运行模式组合各资源 Mixin。

每个容器只声明它所需的 Mixin，资源粒度一目了然：

    ServiceContainer   → 全量资源（FastAPI 服务模式）
    BuilderContainer   → GraphRAG 数据构建（无 Scheduler / S3）
    GeneratorContainer → 代码生成（仅 DB + HTTP）
    CliContainer       → 纯 CLI（仅异步执行器）
"""

from dependency_injector import containers

from graphedu.common.resource.modules.agent.mixin import CheckpointMixin
from graphedu.common.resource.modules.cache.mixin import RedisMixin
from graphedu.common.resource.modules.database.mixin import PostgresqlMixin, S3Mixin
from graphedu.common.resource.modules.infrastructure.mixin import AsyncExecutorMixin, HttpClientMixin
from graphedu.common.resource.modules.llm.mixin import ModelsMixin
from graphedu.common.resource.modules.scheduler.mixin import SchedulerMixin


class ServiceContainer(
    PostgresqlMixin,
    RedisMixin,
    ModelsMixin,
    CheckpointMixin,
    SchedulerMixin,
    S3Mixin,
    HttpClientMixin,
):
    """服务容器：全量资源，用于 FastAPI service 模式。

    包含：
        AsyncExecutor + PostgreSQL + Redis + LLM(chat/long/think) +
        LangGraph Checkpoint + Scheduler + S3 + HTTP Client

    Attributes:
        postgresql_client: PostgreSQL 异步客户端实例（来自 PostgresqlMixin）。
        redis_client: Redis 异步客户端实例（来自 RedisMixin）。
        redis_decorator: Cashews 缓存装饰器实例（来自 RedisMixin）。
        chat_llm: 对话型 LLM 实例（来自 LLMMixin）。
        long_llm: 长文本 LLM 实例（来自 LLMMixin）。
        think_llm: 思考型 LLM 实例（来自 LLMMixin）。
        langgraph_checkpointer: LangGraph 检查点实例（来自 CheckpointMixin）。
        scheduler: APScheduler 异步调度器实例（来自 SchedulerMixin）。
        s3_client: S3/OSS 异步客户端实例（来自 S3Mixin）。
        http_client: 异步 HTTP 客户端实例（来自 HttpClientMixin）。
    """

    wiring_config = containers.WiringConfiguration(
        packages=["graphedu.common.resource.deps", "graphedu.services.agent.chat_agent"],
    )


class WorkerContainer(
    PostgresqlMixin, RedisMixin, S3Mixin, HttpClientMixin, ModelsMixin, CheckpointMixin
):
    """构建容器：用于 GraphRAG 数据构建。

    包含：AsyncExecutor + PostgreSQL + Redis + S3 + HTTP Client

    Attributes:
        postgresql_client: PostgreSQL 异步客户端实例（来自 PostgresqlMixin）。
        redis_client: Redis 异步客户端实例（来自 RedisMixin）。
        redis_decorator: Cashews 缓存装饰器实例（来自 RedisMixin）。
        s3_client: S3/OSS 异步客户端实例（来自 S3Mixin）。
        http_client: 异步 HTTP 客户端实例（来自 HttpClientMixin）。
        chat_llm: 对话型 LLM 实例（来自 LLMMixin）。
        long_llm: 长文本 LLM 实例（来自 LLMMixin）。
        think_llm: 思考型 LLM 实例（来自 LLMMixin）。
        langgraph_checkpointer: LangGraph 检查点实例（来自 CheckpointMixin）。
    """

    wiring_config = containers.WiringConfiguration(
        packages=["graphedu.workers.deps"],
    )


class GeneratorContainer(AsyncExecutorMixin, PostgresqlMixin, HttpClientMixin):
    """代码生成器容器：最小化依赖，仅需数据库连接。

    包含：AsyncExecutor + PostgreSQL + HTTP Client
    不含：Redis、Neo4j、LLM、Checkpoint、Scheduler、S3

    Attributes:
        async_executor: 异步执行器实例（来自 AsyncExecutorMixin）。
        postgresql_client: PostgreSQL 异步客户端实例（来自 PostgresqlMixin）。
        http_client: 异步 HTTP 客户端实例（来自 HttpClientMixin）。
    """


class CliContainer(AsyncExecutorMixin):
    """CLI 容器：用于 lint / clean 等不需要数据库的命令。

    包含：AsyncExecutor

    Attributes:
        async_executor: 异步执行器实例（来自 AsyncExecutorMixin）。
    """
