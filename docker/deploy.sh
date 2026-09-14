#!/usr/bin/env bash
# GraphEdu 生产环境部署脚本
# 用法: ./docker/deploy.sh [-v] [--target frontend|backend|all] [项目根目录]
#
# 选择性部署（前端/后端互不牵连，不停数据库）：
#   --target frontend  仅部署前端 (frontend)
#   --target backend   仅部署后端 (backend worker1 beat，三者共享同一镜像)
#   --target all       部署所有应用服务 (frontend backend worker1 beat)，不含 postgres/redis
#
# 默认 --target all。
# postgres / redis 不在本脚本自动重启范围内（涉及数据卷，需手动处理）。
set -euo pipefail

# 解析参数
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VERBOSE=0
TARGET="all"
while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--verbose) VERBOSE=1; shift ;;
    --target)
      [[ $# -ge 2 ]] || { echo "::error::--target 缺少参数" >&2; exit 1; }
      TARGET="$2"; shift 2 ;;
    --target=*) TARGET="${1#*=}"; shift ;;
    -h|--help)
      echo "用法: $0 [-v|--verbose] [--target frontend|backend|all] [项目根目录]"
      echo "  默认项目根目录: $(dirname "$0")/.."
      echo "  默认 --target all"
      exit 0 ;;
    *) PROJECT_DIR="$(cd "$1" && pwd)"; shift ;;
  esac
done

DOCKER_DIR="$PROJECT_DIR/docker"
log()  { echo ">>> $*"; }
warn() { echo "::warning::$*"; }
err()  { echo "::error::$*" >&2; }

# target → 服务集合
case "$TARGET" in
  frontend) SERVICES=(frontend) ;;
  backend)  SERVICES=(backend worker1 beat) ;;
  all)      SERVICES=(frontend backend worker1 beat) ;;
  *) err "unknown --target: $TARGET (可选: frontend|backend|all)"; exit 1 ;;
esac

# ========================================
# 1. 预检
# ========================================
log "Pre-flight checks (target: $TARGET)"

if [ ! -d "$PROJECT_DIR/.git" ]; then
  err "$PROJECT_DIR is not a git repository."
  exit 1
fi

if [ ! -f "$PROJECT_DIR/prod.config.yaml" ]; then
  err "prod.config.yaml not found in $PROJECT_DIR"
  err "Create it from example.config.yaml first."
  exit 1
fi

# ========================================
# 2. 拉取最新代码（先拉代码，确保 compose / generate-env.py 等为最新）
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
# 3. 生成 .env（一次性容器，不影响其他在运行的服务）
# ========================================
cd "$DOCKER_DIR"
log "Generating .env from prod.config.yaml"
docker compose --profile env-gen run --rm env-generator

if [ ! -f ".env" ]; then
  err ".env generation failed."
  exit 1
fi

# ========================================
# 4. 拉取最新镜像并重启目标服务
#    --no-deps：不启动/重启依赖（postgres/redis 及未变更服务原状不动）
#    注意：不再执行 docker compose down，避免中断所有服务。
# ========================================
log "Pulling images for: ${SERVICES[*]}"
docker compose pull "${SERVICES[@]}"

log "Starting services (no-deps): ${SERVICES[*]}"
docker compose up -d --no-deps "${SERVICES[@]}"

# ========================================
# 5. 健康检查（仅针对本次部署的服务）
# ========================================
HEALTH_TIMEOUT=180
HEALTH_INTERVAL=10
ELAPSED=0

log "Waiting for services (timeout: ${HEALTH_TIMEOUT}s)"
while [ $ELAPSED -lt $HEALTH_TIMEOUT ]; do
  FAILED=$(docker compose ps --format '{{.Status}}' "${SERVICES[@]}" 2>/dev/null | grep -ci 'exited\|unhealthy\|dead' || true)
  if [ "$FAILED" -eq 0 ]; then
    UNHEALTHY=$(docker compose ps --format '{{.Health}}' "${SERVICES[@]}" 2>/dev/null | grep -cv 'healthy\|^$' || true)
    if [ "$UNHEALTHY" -eq 0 ]; then
      log "Target services are healthy!"
      break
    fi
  fi

  [ $VERBOSE -eq 1 ] && docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}" "${SERVICES[@]}" 2>/dev/null
  sleep $HEALTH_INTERVAL
  ELAPSED=$((ELAPSED + HEALTH_INTERVAL))
done

if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
  warn "Health check timed out after ${HEALTH_TIMEOUT}s"
  docker compose ps "${SERVICES[@]}"
  docker compose logs --tail=30 "${SERVICES[@]}"
  err "Deployment may be unhealthy."
  exit 1
fi

# ========================================
# 6. 清理 & 汇总
# ========================================
docker image prune -f > /dev/null

log "Deployment complete! ($CURR_COMMIT, target: $TARGET)"
docker compose ps "${SERVICES[@]}"
