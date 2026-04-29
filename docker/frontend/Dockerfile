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

LABEL maintainer="ZK-Jackie"
LABEL version="0.0.1"
LABEL description="GraphEdu Frontend"

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
COPY graphedu-ui/ /app
WORKDIR /app

RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
RUN pnpm run build-only

# ========================================
# 阶段 2: 运行时（官方 nginx:stable-alpine，轻量、无需手工编译）
# ========================================
FROM nginx:1.25.5-alpine

# 设置时区
ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo "$TZ" > /etc/timezone

# 复制静态文件
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 站点配置（静态服务 + /api/ 反代，无 SSL/压缩配置）
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]