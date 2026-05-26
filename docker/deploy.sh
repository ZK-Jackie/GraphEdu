#!/usr/bin/env bash
# GraphEdu 生产环境部署脚本
# 用法: ./docker/deploy.sh [-v] [项目根目录]
set -euo pipefail

# 解析参数
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VERBOSE=0
while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--verbose) VERBOSE=1; shift ;;
    -h|--help)
      echo "用法: $0 [-v|--verbose] [项目根目录]"
      echo "  默认项目根目录: $(dirname "$0")/.."
      exit 0 ;;
    *) PROJECT_DIR="$(cd "$1" && pwd)"; shift ;;
  esac
done

DOCKER_DIR="$PROJECT_DIR/docker"
log()  { echo ">>> $*"; }
warn() { echo "::warning::$*"; }
err()  { echo "::error::$*" >&2; }

# ========================================
# 1. 预检
# ========================================
log "Pre-flight checks"

if [ ! -d "$PROJECT_DIR/.git" ]; then
  err "$PROJECT_DIR is not a git repository."
  exit 1
fi

if [ ! -f "$PROJECT_DIR/prod.config.yaml" ]; then
  err "prod.config.yaml not found in $PROJECT_DIR"
  err "Create it from example.config.yaml first."
  exit 1
fi

if [ ! -d "$PROJECT_DIR/graphedu-ui/dist" ]; then
  err "graphedu-ui/dist/ not found."
  err "Frontend must be built by CI before deployment."
  exit 1
fi

# ========================================
# 2. 拉取最新代码（先拉代码，确保 generate-env.py 等为最新）
# ========================================
cd "$PROJECT_DIR"
PREV_COMMIT=$(git rev-parse --short HEAD)
log "Pulling latest code (was: $PREV_COMMIT)"
git pull origin master || true
CURR_COMMIT=$(git rev-parse --short HEAD)
log "Current commit: $CURR_COMMIT"

if [ "$PREV_COMMIT" = "$CURR_COMMIT" ]; then
  echo "No code changes detected."
fi

# ========================================
# 3. 生成 .env（使用最新的 generate-env.py）
# ========================================
cd "$DOCKER_DIR"
log "Generating .env from prod.config.yaml"
docker compose --profile env-gen run --rm env-generator

if [ ! -f ".env" ]; then
  err ".env generation failed."
  exit 1
fi

# ========================================
# 4. 停止现有服务（释放资源）
# ========================================
log "Stopping existing services"
docker compose down --remove-orphans 2>/dev/null || true

# ========================================
# 5. 构建并启动
# ========================================
log "Building and starting services"
docker compose up -d

# ========================================
# 6. 健康检查
# ========================================
HEALTH_TIMEOUT=180
HEALTH_INTERVAL=10
ELAPSED=0

log "Waiting for services (timeout: ${HEALTH_TIMEOUT}s)"
while [ $ELAPSED -lt $HEALTH_TIMEOUT ]; do
  FAILED=$(docker compose ps --format '{{.Status}}' 2>/dev/null | grep -ci 'exited\|unhealthy\|dead' || true)
  if [ "$FAILED" -eq 0 ]; then
    UNHEALTHY=$(docker compose ps --format '{{.Health}}' 2>/dev/null | grep -cv 'healthy\|^$' || true)
    if [ "$UNHEALTHY" -eq 0 ]; then
      log "All services are healthy!"
      break
    fi
  fi

  [ $VERBOSE -eq 1 ] && docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}" 2>/dev/null
  sleep $HEALTH_INTERVAL
  ELAPSED=$((ELAPSED + HEALTH_INTERVAL))
done

if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
  warn "Health check timed out after ${HEALTH_TIMEOUT}s"
  docker compose ps
  docker compose logs --tail=30
  err "Deployment may be unhealthy."
  exit 1
fi

# ========================================
# 7. 清理 & 汇总
# ========================================
docker image prune -f > /dev/null

log "Deployment complete! ($CURR_COMMIT)"
docker compose ps
