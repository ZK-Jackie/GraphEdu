"""Service 模式配置（Spring Boot 风格重构版）。"""

from graphedu.common.config.modules.agent import AgentConfig
from graphedu.common.config.modules.app import AppMetaConfig
from graphedu.common.config.modules.datasource import DatasourceConfig
from graphedu.common.config.modules.dify import DifyConfig
from graphedu.common.config.modules.infrastructure import LogConfig
from graphedu.common.config.modules.model import ModelConfig
from graphedu.common.config.modules.scheduler import SchedulerConfig
from graphedu.common.config.modules.security import SecurityConfig
from graphedu.common.config.modules.system import SystemConfig
from graphedu.common.config.modules.worker import CeleryConfig, GraphRAGConfig, MinerUConfig

from ..core.base import BaseAppSettings
from ..modules.deploy import DeployConfig


class ServiceConfig(BaseAppSettings):
    """Service 模式主配置类。

    配置结构按功能域分组，符合 Spring Boot 配置习惯：
    - app: 应用元数据
    - model: AI 模型配置
    - datasource: 数据源配置（PostgreSQL、Redis、Neo4j、OSS）
    - security: 安全配置（登录、Token、验证码）
    - agent: AI Agent 配置
    - logging: 日志配置
    - system: 系统配置
    - worker: Worker 配置（Celery、MinerU）

    配置访问示例：
        config.app.name                       # 应用名称
        config.model.chat.name                # 聊天模型名称
        config.datasource.postgresql.dsn      # PostgreSQL 连接字符串
        config.security.token.expire          # Token 过期时间
        config.logging.version                # 日志配置版本
        config.worker.celery.broker_url       # Celery broker URL
        config.worker.mineru.base_url         # MinerU API URL
        config.dify.workflows.exercise_generation.id  # 习题生成 workflow ID
    """

    # 部署配置（Docker Compose Profiles + 镜像版本）
    deploy: DeployConfig = DeployConfig()

    # 应用元数据
    app: AppMetaConfig = AppMetaConfig()

    # AI 模型配置
    model: ModelConfig = ModelConfig()

    # 数据源配置
    datasource: DatasourceConfig = DatasourceConfig()

    # 安全配置
    security: SecurityConfig = SecurityConfig()

    # AI Agent 配置
    agent: AgentConfig = AgentConfig()

    # 日志配置（Spring Boot 风格：logging）
    logging: LogConfig = LogConfig()

    # 系统配置
    system: SystemConfig = SystemConfig()

    # 调度器配置
    scheduler: SchedulerConfig = SchedulerConfig()

    # Worker 配置
    celery: CeleryConfig = CeleryConfig()

    # MinerU 配置
    mineru: MinerUConfig = MinerUConfig()

    # GraphRAG 配置
    graphrag: GraphRAGConfig = GraphRAGConfig()

    # Dify 配置
    dify: DifyConfig = DifyConfig()
