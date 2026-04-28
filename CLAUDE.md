# CLAUDE.md

> 本文件为 Claude Code 在本仓库工作时提供指导。

## 项目简介

GraphEdu 是一个基于知识图谱的教育平台，使用前后端分离设计。

- **后端**：FastAPI + SQLAlchemy 2.0（异步）
- **数据库**：PostgreSQL + Redis
- **AI**：LangChain/LangGraph
- **前端**：Vue 3.5 + TypeScript（见 `graphedu-ui/CLAUDE.md`）

## 快速参考

| 场景                     | 命令                                                 |
|------------------------|----------------------------------------------------|
| 安装依赖                   | `uv sync --extra service --extra test --extra dev` |
| 启动开发服务                 | `uv run -m graphedu service dev`                   |
| 运行测试                   | `uv run -m graphedu test run`                      |
| 代码检查和修复                | `uv run ruff check` / `uv run ruff check --fix`    |
| 代码格式化                  | `uv run ruff format`                               |
| 生成 CRUD                | `uv run -m graphedu generate code crud <table>`    |
| 生成 Docker .env         | `uv run -m graphedu generate env`                  |
| 以 Celery Worker 方式启动应用 | `uv run -m graphedu worker`                        |

## 🚨 必须遵从

### 任何 python 命令执行

**始终使用 `uv run`**，禁止直接调用 `python`：

```bash
# ✅ 正确
uv run -m graphedu service dev
uv run python -c "print('hello world')"

# ❌ 错误
python -m graphedu service dev
```

### 架构约束

- **异步优先**：IO 操作使用 async/await
- **分层严格**：Controller → Service → Mapper，禁止跨层调用
- **边界验证**：API 边界必须使用 Pydantic 模型作为参数和返回值，不允许使用 dict 作为参数或返回值
- **权限控制**：所有接口必须添加权限装饰器

### 禁止事项

- 禁止在 Controller 层编写业务逻辑
- 禁止在 Service 层直接操作数据库（使用 Mapper 层函数操作数据库）
- 禁止硬编码 SQL
- 禁止绕过异常体系直接抛出通用异常

## 架构

### 分层结构

```
api/services/     → Controller：HTTP 处理、参数验证（薄层）
services/         → Service：业务逻辑（厚层，核心）
mapper/           → Mapper：数据访问（SQLAlchemy 查询）
common/models/    → Model：数据模型定义
```

**数据流**：`Request → Controller → Service → Mapper → Database`

### 模型分类

| 类型  | 用途            | 命名约定    |
|-----|---------------|---------|
| BO  | 业务数据封装        | 无       |
| DTO | API 请求验证      | `*DTO`  |
| VO  | API 响应封装      | `*VO`   |
| ORM | SQLAlchemy 实体 | 表名的驼峰命名 |

详见 `graphedu/common/models/` 目录结构。

## 权限系统

### 获取当前用户

使用 FastAPI 的依赖注入 `Depends`，结合 `SecurityService.get_current_user`：

```python
@router.post("", dependencies=[Depends(SecurityService.get_current_user)])
async def add_user(current_user: User = Depends(SecurityService.get_current_user)): ...
```

### 接口权限

使用 `CheckUserInterfacePermit` 装饰器，详见 `graphedu/security/aspect/interface_auth.py`：

```python
@router.post("", dependencies=[Depends(CheckUserInterfacePermit("system:user:add"))])
async def add_user(): ...
```

### 数据权限

支持 5 种数据范围（全部/自定义/本部门/本部门及子部门/仅本人）。

详见 `graphedu/security/aspect/data_scope.py`。

### 动态路由与菜单

#### 场景划分

| 场景         | 用途      |
|------------|---------|
| `web`      | 学生学习    |
| `admin`    | 后台管理    |
| `userInfo` | 用户中心    |
| `mobile`   | 移动端（预留） |

#### 核心流程

```
登录 → JWT Token → GET /info → GET /menus?scene=xxx → 前端动态注册路由/动态渲染菜单
```

功能类型（DIR/MENU/BUTTON/INTERFACE 等）参见 `sys_function` 表设计。

## 异常处理

使用带错误码的自定义异常体系，错误码格式：`MODULE.NUMBER`

```python
raise RegisterUsernameExistsException()  # 自动返回 AUTH.11002 和对应语言的错误信息
```

**自定义异常及使用**：参见 `graphedu/common/exceptions/README.md`。

## 项目配置

### 配置文件

**配置文件**：YAML 格式

- `example.config.yaml`: 配置模板（不含敏感信息，提交到版本控制）
- `dev.config.yaml`: 开发环境（本地使用，不提交）
- `prod.config.yaml`: 生产环境（服务器使用，不提交）
- `tests/test.config.yaml`: 测试环境配置

### 配置优先级

从高到低：环境变量 > 环境配置文件 > 本地配置文件 > 默认值

### 环境变量覆盖

使用 `GRAPHEDU_` 前缀和 `__` 分隔符：

```bash
# 数据库连接
export GRAPHEDU__DATASOURCE__POSTGRESQL__DSN="postgresql://..."

# JWT 密钥
export GRAPHEDU__SECURITY__TOKEN__SECRET="your-secret"

# LLM API Key
export GRAPHEDU__MODEL__CHAT__API_KEY="sk-..."
```

### 配置文件路径

通过环境变量指定配置文件路径：

```bash
# 本地配置文件（默认）
export GE_CONFIG_FILE_LOCAL="dev.config.yaml"

# 环境配置文件（优先级高于本地）
export GE_CONFIG_FILE_ENV="/etc/graphedu/prod.config.yaml"
```

### 配置模块结构

```yaml
app:                    # 应用元数据（名称、版本、仓库）
model:                  # AI 模型配置（chat、think、long、embeddings）
datasource:             # 数据源配置
  postgresql:          # PostgreSQL 连接和连接池
  redis:               # Redis 连接
  oss:                 # 对象存储（MinIO/阿里云）
security:               # 安全配置
  token:               # JWT Token 配置
  login:               # 登录配置（单点登录、验证码）
  turnstile:           # Cloudflare Turnstile
agent:                  # AI Agent 配置（检查点存储）
logging:                # 日志配置（控制台、文件、飞书）
system:                 # 系统配置（时区、位置查询）
scheduler:              # 调度器配置（APScheduler）
celery:                 # Celery Worker 配置
deploy:                 # 部署配置
  profiles:            # Docker Compose Profiles（控制启动哪些服务）
  images:              # Docker 镜像版本标签
```

**详见**：`graphedu/common/config/README.md`

### 开发前检查清单

在开始开发前，确保以下配置已正确设置：

- [ ] 复制 `example.config.yaml` 为 `dev.config.yaml`
- [ ] 配置数据库连接（PostgreSQL、Redis）
- [ ] 配置 AI 模型 API Key（智谱 GLM、阿里云等）
- [ ] 配置 JWT 密钥（生产环境使用强密钥）
- [ ] 配置对象存储（s3）
- [ ] 检查日志目录权限（`./data/logs/`）

## Docker 部署

### 配置职责分离

项目使用两套配置，职责明确分离：

| 配置来源 | 文件 | 职责 |
|---------|------|------|
| `docker/.env` | 由 `generate env` 生成 | **镜像初始化**：数据库密码、镜像版本、Compose Profiles |
| `prod.config.yaml` | 手动编写 | **应用运行时**：DSN、API Key、JWT 密钥等全部业务配置 |

`.env` 仅服务于 docker-compose 的变量替换（`${VAR:-default}` 语法）和镜像初始化（如 `POSTGRES_PASSWORD`）。
应用运行时配置通过 volume 将 `prod.config.yaml` 挂载到容器内，由配置系统自动发现加载。

### Docker Compose Profiles

通过 `deploy.profiles` 控制 docker-compose 启动哪些服务：

```yaml
# prod.config.yaml
deploy:
  profiles:
    - postgres    # 注释此行 → 使用外部 PostgreSQL
    - redis       # 注释此行 → 使用外部 Redis
    - backend
    - frontend
```

服务与 Profile 对应关系：

| 服务 | Profile | 说明 |
|------|---------|------|
| postgres | `postgres` | 可选，使用外部 PG 时去掉 |
| redis | `redis` | 可选，使用外部 Redis 时去掉 |
| backend / worker / beat | `backend` | 核心应用服务 |
| frontend | `frontend` | Nginx 网关 |

### 部署流程

```bash
# 1. 配置 prod.config.yaml（DSN 使用 Docker 服务名，如 graphedu-postgres:5432）
# 2. 生成 docker/.env
uv run -m graphedu generate env --output docker/.env

# 3. 构建并启动
cd docker
docker compose up -d --build
```

### env 生成命令

```bash
uv run -m graphedu generate env                    # 生成 docker/.env
uv run -m graphedu generate env --mask             # 脱敏输出（用于分享）
uv run -m graphedu generate env --list             # 列出模板变量
```

从配置文件的 DSN 中提取数据库凭据用于 PostgreSQL 镜像初始化，从 `deploy` 段提取镜像版本和 profiles。

**详见**：`docker/README.md`、`graphedu/cli/README.md`

## 项目结构

```
graphedu/
├── api/services/        # Controller 层
├── services/            # Service 层（核心）
├── mapper/              # Mapper 层
├── common/
│   ├── models/          # PO/DTO/VO/ORM
│   ├── exceptions/      # 异常体系
│   └── resource/        # DB/Redis 客户端
├── security/aspect/     # 权限切面
├── generator/           # 代码生成器
└── cli/                 # CLI 命令

graphedu-ui/             # 前端（见 graphedu-ui/CLAUDE.md）
tests/                   # pytest 测试
```

## 开发检查清单

### 每次提交代码前

- [ ] **代码风格**：运行 `uv run ruff check --fix` 检查并自动修复问题
- [ ] **代码格式化**：运行 `uv run ruff format` 格式化代码
- [ ] **类型检查**：确保没有明显的类型错误
- [ ] **测试通过**：运行 `uv run -m graphedu test run` 确保测试通过
- [ ] **敏感信息**：确认没有将密钥、密码等敏感信息提交到代码库

### API 开发检查清单

创建新 API 接口时：

- [ ] **Controller 层**：
  - [ ] 使用 Pydantic DTO/VO 作为参数和返回值（不使用 dict）
  - [ ] 添加 `CheckUserInterfacePermit` 权限装饰器
  - [ ] 添加 `SystemLog` 日志装饰器（非查询操作）
  - [ ] 使用 `Depends(get_db)` 获取数据库会话
  - [ ] 使用 `Depends(get_redis)` 获取 Redis 连接

- [ ] **Service 层**：
  - [ ] 使用 Pydantic DTO/VO 作为参数和返回值（不使用 dict）
  - [ ] 业务逻辑写在 Service 层（不写在 Controller）
  - [ ] 使用 Mapper 层函数访问数据库（不直接操作 ORM）
  - [ ] 使用自定义异常处理错误（不抛出通用 Exception）
  - [ ] 需要缓存时使用 Redis 工具类

- [ ] **Mapper 层**：
  - [ ] 使用 SQLAlchemy 2.0 异步语法（`select().where()`）
  - [ ] 过滤已删除数据（`status != SystemConstants.Status.DELETED`）
  - [ ] 复杂查询使用 `@staticmethod` 静态方法

- [ ] **模型层**：
  - [ ] ORM：使用 `Mapped` 类型注解，所有字段添加 `comment`
  - [ ] DTO：继承 `DTO` 基类，添加字段验证和 `description`
  - [ ] VO：继承 `VO` 基类，使用 `Field(description=...)`

### 数据库操作检查清单

- [ ] **异步操作**：所有数据库操作使用 `async/await`
- [ ] **事务管理**：需要事务时使用 `AsyncSession.transaction()`
- [ ] **N+1 查询**：使用 `selectinload()` 或 `joinedload()` 预加载关联数据
- [ ] **索引使用**：查询条件字段确保有索引
- [ ] **软删除**：查询时过滤已删除数据（`status != '2'`）

### 权限控制检查清单

- [ ] **认证**：使用 `SecurityService.get_current_user` 获取当前用户
- [ ] **接口权限**：添加 `CheckUserInterfacePermit("module:entity:action")`
- [ ] **数据权限**：需要时使用 `GetDataScope()` 生成数据范围 SQL

### 异常处理检查清单

- [ ] **业务异常**：使用预定义的 `ServiceException` 子类
- [ ] **参数验证**：使用 Pydantic 的 Field 验证和 `field_validator`
- [ ] **错误码**：遵循错误码规范（`MODULE.NUMBER` 格式）
- [ ] **错误消息**：使用多语言消息（添加到 `messages/zh_cn.py`）

## 代码质量工具

```bash
# Ruff（Linter + Formatter）
uv run ruff check                              # 检查
uv run ruff check --fix                        # 自动修复
uv run ruff format                             # 格式化

# Pytest
uv run -m graphedu test run                    # 运行所有测试
pytest tests/unit/test_config.py::test_func    # 运行特定测试
pytest --cov=graphedu --cov-report=html        # 覆盖率报告
```

## 相关文档

| 主题                   | 文档路径                                      |
|----------------------|-------------------------------------------|
| 配置系统详解               | `graphedu/common/config/README.md`         |
| 数据模型设计规范             | `graphedu/common/models/README.md`         |
| 异常处理体系               | `graphedu/common/exceptions/README.md`     |
| 测试框架使用               | `tests/README.md`                          |
| Docker 部署指南           | `docker/README.md`                         |
| CLI 命令参考              | `graphedu/cli/README.md`                   |
| 前端开发指南               | `graphedu-ui/CLAUDE.md`                    |
