# GraphEdu 前端运行时 Dockerfile（不含构建阶段）
#
# 构建上下文: 项目根目录（需包含 graphedu-ui/dist/）
# 前置条件: graphedu-ui/dist/ 已由 CI 构建
#
# SSL / Gzip / Brotli 等高级功能请在外层代理（宿主机 Nginx / Caddy / Traefik）中配置

FROM nginx:1.25.5-alpine

LABEL maintainer="ZK-Jackie"
LABEL description="GraphEdu Frontend (Runtime)"

ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo "$TZ" > /etc/timezone

COPY graphedu-ui/dist /usr/share/nginx/html
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/ > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
