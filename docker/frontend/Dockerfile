# GraphEdu 前端生产环境 Dockerfile
#
# 构建上下文: 项目根目录（prod.docker-compose.yaml 中 context: ..）
# 职责: 构建 Vue 3 SPA → 用 nginx:alpine 提供静态服务 + /api/ 反向代理
#
# ⚠️  SSL / Gzip / Brotli 等高级功能请在外层代理（宿主机 Nginx / Caddy / Traefik）中配置

# ========================================
# 阶段 1: 构建前端
# ========================================
FROM node:22-alpine AS builder

ARG NPM_REGISTRY=https://registry.npmmirror.com

LABEL maintainer="ZK-Jackie"
LABEL version="0.0.1"
LABEL description="GraphEdu Frontend"

# 配置 npm 全局镜像源（corepack 下载 pnpm 时也会使用此源）
RUN if [ -n "$NPM_REGISTRY" ]; then \
      npm config set registry "$NPM_REGISTRY"; \
    fi

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
COPY graphedu-ui/ /app
WORKDIR /app

RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    if [ -n "$NPM_REGISTRY" ]; then \
      pnpm install --frozen-lockfile --registry "$NPM_REGISTRY"; \
    else \
      pnpm install --frozen-lockfile; \
    fi
RUN pnpm run build-only

# ========================================
# 阶段 2: 运行时（官方 nginx:alpine，轻量）
# SSL / Gzip / Brotli 等高级功能请在外层代理（宿主机 Nginx / Caddy / Traefik）中配置
# ========================================
FROM nginx:1.25.5-alpine

# 设置时区
ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo "$TZ" > /etc/timezone

# nginx 1.25.x 的 mime.types 不含 .mjs，补上 ES Module MIME 映射
RUN sed -i 's|application/javascript  js;|application/javascript  js mjs;|' /etc/nginx/mime.types

# 复制静态文件
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 站点配置（静态服务 + /api/ 反代，无 SSL/压缩配置）
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
