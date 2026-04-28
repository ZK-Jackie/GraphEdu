# 配置系统文档

## 概述

GraphEdu 采用基于 Pydantic Settings 的分层配置系统，提供类型安全、模块化、多优先级的配置管理能力。

### 核心特性

- **多级加载优先级**：默认值 < 本地 YAML < 环境 YAML < 环境变量
- **类型安全验证**：基于 Pydantic 的自动类型验证和转换
- **模块化设计**：按功能域分组的配置结构（Spring Boot 风格）
- **环境变量覆盖**：支持通过环境变量覆盖任意配置项
- **敏感信息保护**：通过环境变量管理密钥等敏感信息

## 架构设计

### 配置管理器

`ConfigManager` 是配置系统的入口点，负责加载和管理配置实例。

**位置**：`graphedu/common/config/manager.py`

```python
from graphedu.common.config.manager import ConfigManager, load_config, get_config

# 加载配置
config = ConfigManager.load(
    filename="dev.config.yaml",
    running_mode="service"
)

# 获取已加载的配置
config = ConfigManager.get()
```

### 配置加载优先级

配置加载遵循以下优先级（从高到低）：

1. **初始化值**：直接传入的配置值
2. **环境变量**：以 `GRAPHEDU_` 为前缀的环境变量
3. **环境配置文件**：由 `GE_CONFIG_FILE_ENV` 指定的 YAML 文件
4. **本地配置文件**：由 `GE_CONFIG_FILE_LOCAL` 指定的 YAML 文件（默认 `dev.config.yaml`）
5. **默认值**：配置类中定义的默认值

### 配置源

#### YAML 配置源

自定义的 `YamlSettingsSource` 负责从 YAML 文件加载配置：

```python
class YamlSettingsSource(PydanticBaseSettingsSource):
    """YAML 文件配置源。"""
```

#### 环境变量

环境变量使用 `__` 作为嵌套分隔符：

```bash
# 配置: config.datasource.postgresql.dsn
export GRAPHEDU__DATASOURCE__POSTGRESQL__DSN="postgresql://..."

# 配置: config.security.token.expire
export GRAPHEDU__SECURITY__TOKEN__EXPIRE=120
```

### 配置基类

**BaseAppSettings**：顶层配置类基类，集成 YAML 配置源和环境变量支持。

```python
class BaseAppSettings(BaseSettings):
    """应用程序设置基类。"""

    model_config = SettingsConfigDict(
        env_prefix=CONFIG_PREFIX + "_",      # GRAPHEDU_
        case_sensitive=False,                  # 不区分大小写
        env_nested_delimiter="__",             # 嵌套分隔符
        extra="ignore",                        # 忽略额外字段
    )
```

## 配置模块详解

### app - 应用元数据

应用基础信息配置。

**配置类**：`AppMetaConfig`
**文件**：`modules/app/meta.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `name` | `str` | `graphedu-service` | 应用程序名称 |
| `version` | `str` | `0.0.1` | 应用程序版本号（语义化版本） |
| `author` | `str \| None` | `None` | 应用程序作者 |
| `repository` | `str \| None` | `None` | 代码仓库地址 |

**配置示例**：
```yaml
app:
  name: "graphedu-service"
  version: "1.0.0"
  author: "Your Name"
  repository: "https://github.com/yourorg/graphedu"
```

**代码访问**：
```python
config.app.name
config.app.version
```

### model - AI 模型配置

AI 模型相关配置，包括 LLM 和 Embeddings。

**配置类**：`ModelConfig`
**文件**：`modules/model/base.py`

#### 子配置

##### chat - 聊天 LLM

**配置类**：`LLMConfig`
**文件**：`modules/model/llm.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `name` | `str` | `glm-5-flash` | LLM 模型名称 |
| `api_key` | `str` | `""` | API 密钥（敏感） |
| `api_base` | `str` | `https://open.bigmodel.cn/api/paas/v4` | API 基础 URL |
| `temperature` | `float` | `0.7` | 采样温度（0.0-2.0） |
| `max_tokens` | `int` | `4096` | 最大生成令牌数 |
| `top_p` | `float` | `0.9` | Top-p 采样参数 |
| `concur_limit` | `float` | `2` | 并发限制（请求/秒） |

##### think - 思考 LLM

配置结构同 `chat`，用于 AI Agent 思考环节。

##### long - 长文本 LLM

配置结构同 `chat`，用于长文本处理。

##### embeddings - 嵌入模型

**配置类**：`EmbeddingsConfig`
**文件**：`modules/model/embeddings.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `name` | `str` | `embedding-2` | 嵌入模型名称 |
| `api_key` | `str` | `""` | API 密钥（敏感） |
| `api_base` | `str` | `https://open.bigmodel.cn/api/paas/v4` | API 基础 URL |
| `dimensions` | `int` | `2048` | 向量维度 |
| `max_tokens` | `int` | `4095` | 最大 token 数 |
| `concur_limit` | `int` | `1` | 并发限制 |
| `batch_size` | `int` | `16` | 批处理大小 |
| `batch_max_tokens` | `int` | `8000` | 批处理最大 token 数 |

**配置示例**：
```yaml
model:
  chat:
    name: "glm-4-flash"
    api_key: "YOUR_API_KEY"
    api_base: "https://open.bigmodel.cn/api/paas/v4"
    temperature: 0.1
    concur_limit: 200
  embeddings:
    name: "BAAI/bge-m3"
    api_key: "YOUR_API_KEY"
    dimensions: 1024
```

**代码访问**：
```python
config.model.chat.name
config.model.embeddings.dimensions
```

### datasource - 数据源配置

所有数据存储相关配置。

**配置类**：`DatasourceConfig`
**文件**：`modules/datasource/base.py`

#### postgresql - PostgreSQL 数据库

**配置类**：`PostgresqlConfig`
**文件**：`modules/datasource/postgresql.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `dsn` | `PostgresDsn` | `postgresql://postgres:postgres@localhost:5432/graphedu` | 连接字符串（敏感） |
| `echo` | `bool` | `false` | 是否输出 SQL 日志 |
| `pool` | `PoolConfig` | - | 连接池配置 |

##### 连接池配置 (PoolConfig)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `echo_pool` | `bool` | `false` | 连接池日志 |
| `pool_size` | `int` | `10` | 最大连接数 |
| `pool_recycle` | `int` | `3600` | 连接回收时间（秒） |
| `pool_timeout` | `int` | `30` | 连接超时（秒） |
| `pool_pre_ping` | `bool` | `true` | 使用前测试连接 |
| `pool_reset_on_return` | `str` | `"rollback"` | 连接归还策略 |
| `pool_use_lifo` | `bool` | `false` | 后进先出策略 |

#### redis - Redis 缓存

**配置类**：`RedisConfig`
**文件**：`modules/datasource/redis.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `dsn` | `RedisDsn` | `redis://:password@localhost:6379/0` | 连接 URL（敏感） |

#### neo4j - Neo4j 图数据库

**配置类**：`Neo4jConfig`
**文件**：`modules/datasource/neo4j.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `dsn` | `Neo4jDsn` | `bolt://localhost:7687` | 连接地址 |
| `auth` | `list[str]` | `["neo4j:password"]` | 认证信息 |
| `timeout` | `int` | `30` | 连接超时（秒） |

#### oss - 对象存储

**配置类**：`OssConfig`
**文件**：`modules/datasource/oss.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `provider` | `Literal` | `"minio"` | 服务提供商 |
| `endpoint` | `AnyHttpUrl` | `http://localhost:9000` | 服务器地址 |
| `access_key` | `str` | `"minioadmin"` | 访问密钥 ID（敏感） |
| `secret_key` | `str` | `"minioadmin"` | 访问密钥 Secret（敏感） |
| `use_ssl` | `bool` | `false` | 是否使用 SSL |
| `bucket` | `str` | `"test"` | 默认存储桶 |
| `upload_from` | `str` | `"/tmp/graphedu"` | 上传临时目录 |
| `download_to` | `str` | `"/tmp/graphedu"` | 下载目标目录 |

**配置示例**：
```yaml
datasource:
  postgresql:
    dsn: 'postgresql://postgres:postgres@localhost:5432/graphedu'
    echo: true
    pool:
      pool_size: 50
      pool_recycle: 1800
  redis:
    dsn: 'redis://localhost:6379/0'
  neo4j:
    dsn: 'bolt://localhost:7687'
    auth: ['neo4j:password']
    timeout: 20
  oss:
    endpoint: 'http://localhost:9000'
    access_key: 'YOUR_ACCESS_KEY'
    secret_key: 'YOUR_SECRET_KEY'
    bucket: 'graphedu'
```

**代码访问**：
```python
config.datasource.postgresql.dsn
config.datasource.redis.dsn
config.datasource.neo4j.auth
config.datasource.oss.bucket
```

### security - 安全配置

安全相关配置，包括登录、Token 和验证码。

**配置类**：`SecurityConfig`
**文件**：`modules/security/base.py`

#### token - JWT Token

**配置类**：`TokenConfig`
**文件**：`modules/security/token.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `header` | `str` | `"authorization"` | HTTP 请求头字段名 |
| `secret` | `str` | `"secret"` | JWT 签名密钥（敏感） |
| `algorithm` | `str` | `"HS512"` | 加密算法 |
| `expire` | `int` | `120` | 过期时间（分钟） |

#### login - 登录配置

**配置类**：`LoginConfig`
**文件**：`modules/security/login.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `single_end` | `bool` | `true` | 单点登录模式 |
| `captcha` | `bool` | `true` | 是否启用验证码 |

#### turnstile - Turnstile 验证码

**配置类**：`TurnstileConfig`
**文件**：`modules/model/turnstile.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `secret` | `str` | `""` | Turnstile 密钥（敏感） |
| `verify_url` | `str` | `"https://challenges.cloudflare.com/turnstile/v0/siteverify"` | 验证 API |
| `timeout` | `float` | `10.0` | 请求超时（秒） |

**配置示例**：
```yaml
security:
  token:
    header: 'Authorization'
    secret: 'your-secret-key-here'
    expire: 120
    algorithm: 'HS512'
  login:
    single_end: true
    captcha: true
  turnstile:
    secret: 'YOUR_TURNSTILE_SECRET'
```

**代码访问**：
```python
config.security.token.secret
config.security.login.captcha
```

### agent - AI Agent 配置

AI Agent 相关配置。

**配置类**：`AgentConfig`
**文件**：`modules/agent/base.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `checkpoint_provider` | `Literal` | `"postgresql"` | 检查点存储提供商 |
| `dsn` | `PostgresDsn` | - | 检查点数据库连接字符串 |
| `checkpoint_collection_name` | `str` | `"checkpoints"` | 检查点集合/表名 |
| `writes_collection_name` | `str` | `"checkpoint_writes"` | 写入记录集合/表名 |

**配置示例**：
```yaml
agent:
  checkpoint_provider: postgresql
  dsn: 'postgresql://postgres:postgres@localhost:5432/graphedu'
  checkpoint_collection_name: 'checkpoints'
  writes_collection_name: 'checkpoint_writes'
```

### logging - 日志配置

日志系统配置。

**配置类**：`LogConfig`
**文件**：`modules/infrastructure/log.py`

日志配置使用 Python 标准 logging 配置格式，支持控制台和文件日志。

**配置示例**：
```yaml
logging:
  version: 1
  disable_existing_loggers: false
  formatters:
    standard:
      format: '%(asctime)s.%(msecs)03d - %(levelname)s - %(name)s - %(message)s'
      datefmt: '%Y-%m-%d %H:%M:%S'
  handlers:
    console:
      class: logging.StreamHandler
      level: INFO
      formatter: standard
      stream: ext://sys.stdout
    daily_file:
      class: graphedu.common.utils.logger.TimeLoggerRolloverHandler
      level: DEBUG
      formatter: standard
      filename: /logs/graphedu.debug
      when: midnight
      interval: 1
      backupCount: 30
  root:
    level: DEBUG
    handlers: ['console', 'daily_file']
```

**代码访问**：
```python
config.logging.get_dict_config()
```

### system - 系统配置

系统级配置。

**配置类**：`SystemConfig`
**文件**：`modules/system/base.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `timezone` | `str` | `"UTC"` | 系统时区 |
| `location_query` | `bool` | `true` | 是否启用 IP 位置查询 |

**配置示例**：
```yaml
system:
  timezone: Asia/Shanghai
  location_query: true
```

### deploy - 部署配置

Docker Compose 部署配置（Profiles + 镜像版本）。

**配置类**：`DeployConfig`
**文件**：`modules/deploy/profile.py`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `profiles` | `list[str]` | `[]` | Docker Compose profiles 列表 |
| `images.postgres` | `str` | `"18.3.0"` | PostgreSQL 镜像版本 |
| `images.redis` | `str` | `"8.6.2-alpine"` | Redis 镜像版本 |
| `images.backend` | `str` | `"latest"` | 后端服务镜像版本 |
| `images.frontend` | `str` | `"latest"` | 前端服务镜像版本 |

**配置示例**：
```yaml
deploy:
  profiles: ["postgres", "redis", "neo4j", "backend"]
  images:
    postgres: "18.3.0"
    redis: "8.6.2-alpine"
    backend: "0.0.1"
    frontend: "0.0.1"
```

## 使用指南

### 配置文件格式

配置文件使用 YAML 格式，按命名空间组织：

```yaml
# 主配置文件示例
app:
  name: "graphedu-service"
  version: "1.0.0"

model:
  chat:
    name: "glm-4-flash"
    api_key: "YOUR_API_KEY"

datasource:
  postgresql:
    dsn: "postgresql://user:pass@localhost:5432/graphedu"

security:
  token:
    secret: "your-secret-key"
```

### 环境变量覆盖

使用 `GRAPHEDU_` 前缀和 `__` 分隔符覆盖配置：

```bash
# 设置数据库连接
export GRAPHEDU__DATASOURCE__POSTGRESQL__DSN="postgresql://..."

# 设置 Token 密钥
export GRAPHEDU__SECURITY__TOKEN__SECRET="my-secret"

# 设置 LLM API Key
export GRAPHEDU__MODEL__CHAT__API_KEY="sk-..."
```

### 配置文件路径

通过环境变量指定配置文件路径：

```bash
# 本地配置文件
export GE_CONFIG_FILE_LOCAL="dev.config.yaml"

# 环境配置文件（优先级高于本地）
export GE_CONFIG_FILE_ENV="/etc/graphedu/prod.config.yaml"
```

### 代码中访问配置

```python
from graphedu.common.config import get_config

# 获取配置实例
config = get_config()

# 访问配置项
app_name = config.app.name
db_dsn = config.datasource.postgresql.dsn
token_expire = config.security.token.expire

# 使用工具方法
async_dsn = config.datasource.postgresql.get_sa_async_dsn()
auth_tuple = config.datasource.neo4j.get_auth_tuples()
```

### 配置验证

配置系统使用 Pydantic 自动验证：

```python
from pydantic import ValidationError

try:
    config = ServiceConfig()
except ValidationError as e:
    print(f"配置错误: {e}")
```

## 配置示例

### 开发环境配置

```yaml
# dev.config.yaml
app:
  name: "graphedu-service"
  version: "1.0.0-dev"

model:
  chat:
    name: "glm-4-flash"
    api_key: "dev-api-key"
    temperature: 0.1

datasource:
  postgresql:
    dsn: "postgresql://postgres:postgres@localhost:5432/graphedu"
    echo: true
  redis:
    dsn: "redis://localhost:6379/0"

security:
  token:
    secret: "dev-secret-key"
    expire: 480  # 8小时

logging:
  version: 1
  root:
    level: DEBUG
```

### 生产环境配置

```yaml
# prod.config.yaml
app:
  name: "graphedu-service"
  version: "1.0.0"

model:
  chat:
    name: "glm-4-plus"
    api_key: "${LLM_API_KEY}"  # 从环境变量读取
    temperature: 0.1

datasource:
  postgresql:
    dsn: "${DATABASE_URL}"  # 从环境变量读取
    echo: false
  redis:
    dsn: "${REDIS_URL}"

security:
  token:
    secret: "${JWT_SECRET}"  # 从环境变量读取
    expire: 120

system:
  timezone: Asia/Shanghai
```

生产环境配合环境变量：

```bash
export LLM_API_KEY="sk-prod-..."
export DATABASE_URL="postgresql://prod:***@prod-db:5432/graphedu"
export REDIS_URL="redis://:***@prod-redis:6379/0"
export JWT_SECRET="very-secure-production-secret"
```

## 最佳实践

### 敏感信息管理

1. **永远不要将敏感信息提交到版本控制**
2. **使用环境变量管理密钥**
3. **使用不同的配置文件区分环境**

```yaml
# 不要这样做
datasource:
  postgresql:
    dsn: "postgresql://admin:password123@localhost:5432/graphedu"

# 应该这样做
datasource:
  postgresql:
    dsn: "${DATABASE_URL}"
```

### 环境区分

```bash
# 开发环境
config=dev.config.yaml

# 生产环境
config=prod.config.yaml
```

```bash
# 设置环境配置文件路径
export GE_CONFIG_FILE_ENV="prod.config.yaml"
```

### 配置验证

1. 在应用启动时验证配置完整性
2. 对关键配置项设置合理的约束
3. 提供清晰的错误提示

```python
class PostgresqlConfig(BaseModel):
    dsn: PostgresDsn = Field(...)
    pool_size: int = Field(default=10, gt=0, le=100)
```

### 配置文档化

使用 Pydantic Field 的 `description` 参数为配置项添加文档：

```python
class TokenConfig(BaseModel):
    expire: int = Field(
        default=120,
        gt=0,
        description="Token 过期时间（分钟）"
    )
```

## 相关文件

| 文件 | 说明 |
|------|------|
| `manager.py` | 配置管理器单例 |
| `core/base.py` | 配置基类和 YAML 源 |
| `core/constants.py` | 配置常量 |
| `modes/service.py` | Service 模式主配置 |
| `modules/` | 各功能配置模块 |
| `example.config.yaml` | 配置示例模板 |
