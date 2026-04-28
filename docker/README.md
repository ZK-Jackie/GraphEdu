# GraphEdu Docker 部署指南

[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-Ready-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![PostgreSQL 18](https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis 8](https://img.shields.io/badge/Redis-8-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Nginx](https://img.shields.io/badge/Nginx-1.25-009639?logo=nginx&logoColor=white)](https://nginx.org/)

基于 Docker Compose 的生产环境部署方案，通过 Profiles 灵活控制启动哪些服务。

---

## 架构拓扑

```mermaid
graph TB
    Browser["Browser"] --> Frontend["graphedu-frontend\nNginx :11334 → :80"]

    subgraph Network["graphedu-network (bridge)"]
        Frontend -->|"/api/ 反向代理"| Backend["graphedu-backend\nFastAPI :8000"]
        Backend --> PG["graphedu-postgres\nPostgreSQL :5432\npgvector + Apache AGE"]
        Backend --> Redis["graphedu-redis\nRedis :6379"]
        Worker["graphedu-worker\nCelery Worker"] --> PG
        Worker --> Redis
        Beat["graphedu-beat\nCelery Beat"] --> Redis
    end

    Config["prod.config.yaml :ro"] -.-> Backend
    Config -.-> Worker
    Config -.-> Beat
    Init["pg/init/ :ro"] -.-> PG

    classDef gateway fill:#e8f5e9,stroke:#43a047
    classDef app fill:#fff3e0,stroke:#fb8c00
    classDef data fill:#fce4ec,stroke:#e53935
    classDef config fill:#e3f2fd,stroke:#1e88e5

    class Frontend gateway
    class Backend,Worker,Beat app
    class PG,Redis data
    class Config,Init config
```

- 仅 `frontend` 暴露端口到宿主机（`11334:80`），其余服务仅在 `graphedu-network` 内部通信
- `backend`、`worker`、`beat` 共享同一镜像，通过不同启动命令区分
- `prod.config.yaml` 以只读方式挂载到应用容器，由配置系统自动发现加载

---

## 文件结构

```
docker/
├── .env                          # 由 generate env 自动生成，手动编辑将在下次生成时被覆盖
├── .gitignore                    # 忽略 dev.*、oss/、dify/、neo4j/
├── docker-compose.yaml           # 生产环境 Compose 配置
│
├── backend/
│   ├── Dockerfile                # Python 3.13 + uv，backend/worker/beat 共用
│   └── Dockerfile.dockerignore
│
├── frontend/
│   ├── Dockerfile                # 两阶段：Node 22 构建 → nginx:1.25-alpine 服务
│   ├── Dockerfile.dockerignore
│   └── nginx.conf                # SPA 静态服务 + /api/ 反向代理 + WebSocket
│
├── pg/
│   ├── Dockerfile                # postgres:18 + pgvector 0.8.2 + Apache AGE
│   ├── postgresql.conf           # 自定义配置：shared_preload_libraries, auth_delay
│   ├── dev.docker-compose.yaml   # 开发用独立 PostgreSQL（暴露 5432 到宿主机）
│   ├── utils/
│   │   └── drop_create_database.sql
│   └── init/                     # 初始化脚本（首次创建数据库时按文件名字典序执行）
│       ├── 1.extensions.sql      # 启用 pgvector、Apache AGE 扩展
│       ├── 2.1system.sql         # 系统核心表（sys_user, sys_role, sys_dept ...）
│       ├── 2.2upload.sql         # 文件上传表
│       ├── 2.3dict_data.sql      # 字典数据表
│       ├── 2.4system_data.sql    # 系统种子数据
│       ├── 2.5gen.sql            # 代码生成器表
│       ├── 2.6job.sql            # 定时任务表
│       ├── 3.1education.sql      # 教育域表（学生/教师/课程）
│       ├── 3.2course_data.sql    # 课程种子数据
│       ├── 3.3study.sql          # 学习分析表
│       ├── 3.4graph.sql          # 知识图谱 + 向量嵌入表（HNSW 索引）
│       ├── 4.function_summary.sql # 功能权限树
│       ├── 5.user.sql            # 初始账户（admin, student001, teacher001）
│       ├── 6.students.sql        # 演示学生数据
│       ├── 7.age_graph.sh        # 创建 AGE 图 edu_visualized_graph
│       ├── 9.final.sql           # 验证查询
│       └── 9.users/              # 数据库用户和权限（gitignored）
│
├── redis/
│   ├── conf/
│   │   ├── redis.conf            # 生产配置（RDB 持久化）
│   │   └── dev.redis.conf        # 开发配置
│   └── dev.docker-compose.yaml   # 开发用独立 Redis（暴露 6379 到宿主机）
│
└── volumes/                      # 运行时数据持久化（gitignored）
    ├── pg/                       # PostgreSQL 数据文件
    ├── redis/                    # Redis RDB 快照
    ├── backend-data/             # 后端日志、上传文件
    ├── worker-data/              # Worker 缓存（tiktoken, NLTK）
    └── beat-data/                # Beat 调度数据
```

---

## 服务与 Profiles

通过 Docker Compose Profiles 控制启动哪些服务：

| 服务 | Profile | 镜像 | 端口 | 说明 |
|------|---------|------|------|------|
| postgres | `postgres` | `jackiey101/graphedu-postgres` | 5432（内部） | PostgreSQL 18 + pgvector + Apache AGE |
| redis | `redis` | `redis:8-alpine` | 6379（内部） | 缓存 + Celery broker |
| backend | `backend` | `jackiey101/graphedu-backend` | 8000（内部） | FastAPI 应用 |
| worker | `worker` | `jackiey101/graphedu-backend`（共享镜像） | - | Celery Worker |
| beat | `beat` | `jackiey101/graphedu-backend`（共享镜像） | - | Celery Beat 定时调度 |
| frontend | `frontend` | `jackiey101/graphedu-frontend` | 11334→80（宿主机） | Nginx 网关 |

**补充说明**：

- `backend`、`worker`、`beat` 共用 `docker/backend/Dockerfile` 构建的同一镜像，通过不同 `command` 区分
- 三个应用服务均以只读方式挂载 `../prod.config.yaml`
- `depends_on` 使用 `required: false`，即使 postgres/redis 不在 Compose 中（使用外部数据库时），应用服务仍可正常启动
- 所有服务配置了 `restart: unless-stopped` 和健康检查

`deploy.profiles`（在 `prod.config.yaml` 中）决定哪些 profile 写入 `.env` 的 `COMPOSE_PROFILES`：

```yaml
# prod.config.yaml
deploy:
  profiles:
    - postgres    # 注释此行 → 使用外部 PostgreSQL
    - redis       # 注释此行 → 使用外部 Redis
    - backend
    - worker      # Celery Worker
    - beat        # Celery Beat 定时调度
    - frontend
```

---

## 网络与端口

所有服务连接到 `graphedu-network` 桥接网络，服务名即 hostname：

```yaml
# prod.config.yaml 中 DSN 使用 Docker 服务名
datasource:
  postgresql:
    dsn: postgresql://graphedu:password@graphedu-postgres:5432/graphedu
  redis:
    dsn: redis://:password@graphedu-redis:6379/0
```

| 宿主机端口 | 容器 | 容器端口 | 说明 |
|-----------|------|---------|------|
| `${FRONTEND_PORT:-11334}` | graphedu-frontend | 80 | 唯一暴露到宿主机的端口 |
| - | graphedu-backend | 8000 | 仅内部网络 |
| - | graphedu-postgres | 5432 | 仅内部网络 |
| - | graphedu-redis | 6379 | 仅内部网络 |

---

## 环境变量参考

`docker/.env` 由 `uv run -m graphedu generate env` 自动生成，不建议手动编辑：

| 变量 | 说明 | docker-compose 默认值 |
|------|------|---------------------|
| `COMPOSE_PROFILES` | 启用的 Profile 列表（逗号分隔） | - |
| `POSTGRES_USER` | PostgreSQL 超级用户 | `graphedu` |
| `POSTGRES_PASSWORD` | PostgreSQL 密码 | `graphedu_password` |
| `POSTGRES_DB` | 首次启动创建的默认数据库 | `graphedu` |
| `FRONTEND_PORT` | 前端宿主机端口 | `11334` |
| `POSTGRES_VERSION` | PostgreSQL 镜像标签 | `18.3.0` |
| `REDIS_VERSION` | Redis 镜像标签 | `8.6.2-alpine` |
| `BACKEND_VERSION` | Backend/Worker/Beat 镜像标签 | `latest` |
| `FRONTEND_VERSION` | Frontend 镜像标签 | `latest` |

> 实际值从 `prod.config.yaml` 的 `datasource.postgresql.dsn` 和 `deploy.images` 中提取，`generate env` 会覆盖手动修改。

---

## 部署指南

所有命令在**项目根目录**执行。

### 步骤一：配置后端

```bash
cp example.config.yaml prod.config.yaml
# 编辑 prod.config.yaml，配置数据库 DSN、Token 密钥、AI 模型 API Key 等
```

关键配置项：

```yaml
# prod.config.yaml
datasource:
  postgresql:
    dsn: postgresql://graphedu:your_password@graphedu-postgres:5432/graphedu
  redis:
    dsn: redis://:your_password@graphedu-redis:6379/0

security:
  token:
    secret: "your-strong-secret-key"

deploy:
  profiles:
    - postgres
    - redis
    - backend
    - worker
    - beat
    - frontend
  images:
    postgres: '18.3.0'
    redis: '8.6.2-alpine'
    backend: '0.1.0'
    frontend: '0.1.0'
```

> DSN 中使用 Docker 服务名（如 `graphedu-postgres`、`graphedu-redis`），而非 `localhost`。

### 步骤二：配置前端

```bash
cd graphedu-ui
cp .env.development .env.production
# 编辑 .env.production
```

关键配置：`VITE_API_BASE_URL=/api`（Nginx 容器内已配置 `/api/` 到后端的反向代理）。

### 步骤三：生成 Docker 环境变量

```bash
uv run -m graphedu generate env --output docker/.env
```

该命令从 `prod.config.yaml` 读取配置，生成 `COMPOSE_PROFILES` 和数据库密码、镜像版本等变量。

### 步骤四：构建并启动

```bash
cd docker
docker compose up -d --build
```

- `--build`：强制重新构建镜像；省略则优先使用本地已有镜像（`pull_policy: missing`）
- PostgreSQL 初始化脚本仅在**首次创建数据库**时执行

### 步骤五：验证

```bash
cd docker
docker compose ps

# 查看后端启动日志（健康检查 start_period 为 60s）
docker compose logs -f graphedu-backend
```

所有服务显示 `healthy` 即表示启动成功。

---

## 数据持久化

| 宿主路径 | 容器路径 | 服务 | 模式 | 用途 |
|----------|----------|------|------|------|
| `./volumes/pg` | `/var/lib/postgresql` | postgres | rw | PostgreSQL 数据文件 |
| `./pg/init` | `/docker-entrypoint-initdb.d` | postgres | ro | 初始化脚本（仅首次） |
| `./volumes/redis` | `/data` | redis | rw | Redis RDB 持久化 |
| `./redis/conf` | `/usr/local/etc/redis` | redis | ro | Redis 配置文件 |
| `./volumes/backend-data` | `/app/data` | backend | rw | 日志、上传文件 |
| `../prod.config.yaml` | `/app/prod.config.yaml` | backend/worker/beat | ro | 应用配置 |
| `./volumes/worker-data` | `/app/data` | worker | rw | Worker 缓存（tiktoken, NLTK） |
| `./volumes/beat-data` | `/app/data` | beat | rw | Beat 调度数据 |

> `pg/init` 中的初始化脚本仅在数据库**首次创建**时执行。如需重新初始化：`docker compose down` → 删除 `volumes/pg/` → `docker compose up -d`。

---

## 数据库初始化

`pg/init/` 中的脚本在 PostgreSQL 首次启动时按文件名字典序执行：

| 阶段 | 脚本 | 用途 |
|------|------|------|
| 扩展 | `1.extensions.sql` | 启用 `pgvector`、`age` 扩展 |
| 系统表 | `2.1system.sql` | 核心表：`sys_user`, `sys_role`, `sys_dept` 等 |
| 文件上传 | `2.2upload.sql` | 文件上传和存储表 |
| 字典 | `2.3dict_data.sql` | 系统字典类型和数据 |
| 系统数据 | `2.4system_data.sql` | 种子数据：角色、部门、管理员配置 |
| 生成器 | `2.5gen.sql` | 代码生成器业务表 |
| 定时任务 | `2.6job.sql` | 定时任务调度表 |
| 教育域 | `3.1education.sql` | 教育域表：学生、教师、课程 |
| 课程数据 | `3.2course_data.sql` | 演示课程（离散数学） |
| 学习分析 | `3.3study.sql` | 学习事件、掌握度追踪 |
| 图谱/向量 | `3.4graph.sql` | 知识点嵌入表 + HNSW 向量索引 |
| 权限 | `4.function_summary.sql` | 功能权限树 |
| 用户账户 | `5.user.sql` | `admin/admin123`, `student001/student123`, `teacher001/teacher123` |
| 演示学生 | `6.students.sql` | 演示学生数据 |
| AGE 图 | `7.age_graph.sh` | 在 AGE 中创建 `edu_visualized_graph` 图 |
| 验证 | `9.final.sql` | 表创建验证查询 |

> 自定义 PostgreSQL 配置（`pg/postgresql.conf`）通过 `shared_preload_libraries = 'auth_delay,age'` 加载 AGE 扩展，并设置 2 秒登录延迟防止暴力破解。

---

## 开发环境

仅启动数据库等基础设施，应用在本地运行。提供两种方式：

**方式一：使用独立 dev compose 文件**（推荐，端口暴露到宿主机）

```bash
# 仅启动 PostgreSQL（暴露 5432）
docker compose -f docker/pg/dev.docker-compose.yaml up -d

# 仅启动 Redis（暴露 6379）
docker compose -f docker/redis/dev.docker-compose.yaml up -d
```

**方式二：使用主 compose 的 profile**

```bash
cd docker
docker compose --profile postgres --profile redis up -d
```

> 注意：主 compose 的 PostgreSQL 和 Redis **不暴露端口**到宿主机，仅内部网络可达。开发时推荐使用方式一。

---

## 使用外部数据库

1. 在 `prod.config.yaml` 中将 DSN 修改为外部地址
2. 从 `deploy.profiles` 中移除对应服务
3. 重新执行 `generate env`

```yaml
# 示例：使用外部 PostgreSQL，仅 Docker 托管 Redis + 应用
deploy:
  profiles:
    # - postgres    # 已注释，使用外部 PostgreSQL
    - redis
    - backend
    - worker
    - beat
    - frontend
```

由于 `depends_on` 设置了 `required: false`，backend/worker/beat 在 postgres/redis 不在 Compose 栈中时仍可正常启动。

---

## 常用命令

```bash
cd docker

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f graphedu-backend    # 后端日志
docker compose logs -f graphedu-worker     # Worker 日志

# 重启单个服务
docker compose restart graphedu-backend

# 重新构建并启动单个服务
docker compose up -d --build graphedu-backend

# 拉取最新镜像
docker compose pull

# 停止所有服务
docker compose down

# 停止并删除数据卷（⚠️ 会清除所有持久化数据）
docker compose down -v
```

---

## 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Backend 健康检查持续失败 | PostgreSQL 尚未就绪 | 等待 `start_period: 60s`；检查 `docker compose logs graphedu-postgres` |
| `AGE extension not found` | `postgresql.conf` 未加载 AGE | 确认镜像构建正确，`shared_preload_libraries` 包含 `age` |
| 初始化脚本未执行 | `volumes/pg/` 已存在 | 删除 `volumes/pg/` 后重启：`docker compose down && rm -rf volumes/pg && docker compose up -d` |
| 前端白屏 | `.env.production` 未配置 | 确认 `VITE_API_BASE_URL=/api` 后重新构建前端 |
| Worker/Beat 未启动 | Profile 未添加到 `COMPOSE_PROFILES` | 在 `prod.config.yaml` 的 `deploy.profiles` 中添加 `worker`/`beat`，重新 `generate env` |
| `COMPOSE_PROFILES` 缺少服务 | `.env` 文件过期 | 重新运行 `uv run -m graphedu generate env --output docker/.env` |
| 无法连接外部数据库 | DSN 使用了 Docker 服务名 | 使用外部 IP/hostname，而非 `graphedu-postgres` |

---

## SSL 与反向代理

容器内的 Nginx 仅负责静态文件服务和 `/api/` 反向代理。**SSL / Gzip / Brotli** 等高级功能请在宿主机的 Nginx / Caddy / Traefik 等外层代理中配置，将请求转发到 `localhost:11334`。

示例（宿主机 Nginx）：

```nginx
server {
    listen 443 ssl http2;
    server_name graphedu.example.com;

    ssl_certificate     /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:11334;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
