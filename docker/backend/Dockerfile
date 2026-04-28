# GraphEdu 后端生产环境 Dockerfile
# 此镜像被 backend / worker / beat 三个服务共用
# EXPOSE / HEALTHCHECK / CMD 在 docker-compose.yaml 中按服务分别配置

FROM astral/uv:python3.13-trixie-slim

# 设置标签
LABEL maintainer="ZK-Jackie"
LABEL version="0.0.1"
LABEL description="GraphEdu Backend Service"

# 设置工作目录
WORKDIR /app

# 复制整个项目（依赖文件、应用代码等）
COPY . .

# 安装依赖（使用 uv，缓存挂载持久化下载缓存）
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --all-extras

# 创建必要的目录
RUN mkdir -p /app/logs /app/uploads /app/oss

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app
