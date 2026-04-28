# GraphEdu Docker 快速部署指南

## 文件结构

```
docker/
├── .env                       # 由 generate env 命令生成，包含镜像初始化变量
├── docker-compose.yaml        # 统一的 Compose 配置（通过 profiles 控制启动哪些服务）
├── backend/
│   ├── Dockerfile
│   └── Dockerfile.dockerignore
├── frontend/
│   ├── Dockerfile             # 两阶段: Node 构建 + nginx:stable-alpine 服务
│   ├── Dockerfile.dockerignore
│   └── nginx.conf             # 静态服务 + /api/ 反向代理（无 SSL/压缩，由外层代理处理）
├── pg/
│   ├── Dockerfile             # postgres:18 + pgvector + Apache AGE
│   └── init/                  # 初始化 SQL 脚本（按文件名顺序执行）
└── redis/
    └── conf/redis.conf
```

> **SSL / Gzip / Brotli** 等高级功能请在宿主机的 Nginx / Caddy / Traefik 等外层代理中配置，
> 容器内的 Nginx 只负责静态文件服务和 `/api/` 反向代理。

---

## 服务与 Profiles

`docker-compose.yaml` 通过 Docker Compose Profiles 控制哪些服务启动：

| 服务 | Profile | 说明 |
|------|---------|------|
| postgres | `postgres` | PostgreSQL（含 pgvector、Apache AGE） |
| redis | `redis` | Redis 缓存 |
| backend | `backend` | FastAPI 后端 |
| worker | `backend` | Celery Worker（共用 backend 镜像） |
| beat | `backend` | Celery Beat 定时调度（共用 backend 镜像） |
| frontend | `frontend` | Nginx 网关（SPA + /api/ 反代） |

`deploy.profiles` 配置（在 `dev.config.yaml` / `prod.config.yaml` 中）决定生成哪些 profile 到 `.env` 文件。

---

## 快速开始（生产环境）

所有命令均在**项目根目录**执行。

### 步骤一：配置 `prod.config.yaml`

修改数据库 DSN、Token 密钥等配置，以及决定哪些服务由 Docker 托管：

```yaml
# prod.config.yaml（片段）
datasource:
  postgresql:
    dsn: postgresql://graphedu:password@graphedu-postgres:5432/graphedu
  redis:
    dsn: redis://:password@graphedu-redis:6379/0

deploy:
  profiles:
    - postgres    # 注释此行 → 使用外部 PostgreSQL
    - redis       # 注释此行 → 使用外部 Redis
    - backend
    - frontend
```

### 步骤二：生成 `docker/.env`

```bash
uv run -m graphedu generate env --output docker/.env
```

该命令从 `prod.config.yaml` 读取配置，生成 `COMPOSE_PROFILES` 和镜像初始化变量（数据库密码、镜像版本等）。

### 步骤三：构建并启动

```bash
cd docker
docker compose up -d --build
```

---

## 开发环境（按需启动基础设施）

仅启动需要的数据库服务，应用在本地运行：

```bash
# 仅启动 PostgreSQL 和 Redis
cd docker
docker compose --profile postgres --profile redis up -d

# 或使用 generate env 生成 .env 后直接启动
uv run -m graphedu generate env --output docker/.env
cd docker
docker compose up -d
```

---

## 常用命令

```bash
cd docker

# 查看服务状态
docker compose ps

# 查看后端日志
docker compose logs -f graphedu-backend

# 停止并清理
docker compose down
```

---

## 使用外部数据库

在 `prod.config.yaml` 中将 DSN 修改为外部地址，并在 `deploy.profiles` 中去掉对应的服务，
然后重新执行 `generate env` 即可。容器内服务通过 Docker 网络 `graphedu-network` 互联，
服务名（如 `graphedu-postgres`）作为 hostname 使用。
