#!/bin/bash
# deploy-nas.sh
# Synology NAS 배포 스크립트
# GitHub Webhook에서 호출되거나 수동으로 실행

set -e

# === 설정 ===
DOCKER_IMAGE="jeonghopak/review-mind-rag"
CONTAINER_NAME="review-mind-rag"
DEPLOY_DIR="/volume1/docker/review-mind-rag"
LOG_FILE="${DEPLOY_DIR}/logs/deploy.log"
COMPOSE_FILE="${DEPLOY_DIR}/docker-compose.yml"
COMPOSE_PROD_FILE="${DEPLOY_DIR}/docker-compose.prod.yml"

# === 함수 ===

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] $1" | tee -a "${LOG_FILE}"
}

check_health() {
    local max_attempts=30
    local attempt=1

    log "헬스체크 시작 (최대 ${max_attempts}회 시도)"

    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://localhost:8510/_stcore/health > /dev/null 2>&1; then
            log "✅ 헬스체크 성공 (${attempt}회 시도)"
            return 0
        fi

        log "   시도 ${attempt}/${max_attempts}..."
        sleep 5
        attempt=$((attempt + 1))
    done

    log "❌ 헬스체크 실패"
    return 1
}

# === 메인 스크립트 ===

log "=========================================="
log "🚀 Review Mind RAG 배포 시작"
log "=========================================="

# 디렉토리 확인
if [ ! -d "${DEPLOY_DIR}" ]; then
    log "❌ 배포 디렉토리가 존재하지 않습니다: ${DEPLOY_DIR}"
    exit 1
fi

cd "${DEPLOY_DIR}"

# 로그 디렉토리 생성
mkdir -p "${DEPLOY_DIR}/logs"

# 1. 최신 이미지 Pull
log "1. Docker 이미지 Pull: ${DOCKER_IMAGE}:latest"
docker pull "${DOCKER_IMAGE}:latest"

# 2. 기존 컨테이너 중지 및 제거
log "2. 기존 컨테이너 중지"
if docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
    docker stop "${CONTAINER_NAME}" || true
    docker rm "${CONTAINER_NAME}" || true
    log "   기존 컨테이너 제거 완료"
else
    log "   실행 중인 컨테이너 없음"
fi

# 3. 새 컨테이너 시작
log "3. 새 컨테이너 시작"
if [ -f "${COMPOSE_PROD_FILE}" ]; then
    docker-compose -f "${COMPOSE_FILE}" -f "${COMPOSE_PROD_FILE}" up -d
else
    docker-compose -f "${COMPOSE_FILE}" up -d
fi

# 4. 헬스체크
log "4. 헬스체크 수행"
if check_health; then
    log "=========================================="
    log "✅ 배포 완료!"
    log "   URL: http://localhost:8510"
    log "=========================================="
    exit 0
else
    log "=========================================="
    log "❌ 배포 실패 - 컨테이너 로그 확인 필요"
    log "   docker logs ${CONTAINER_NAME}"
    log "=========================================="

    # 실패 시 롤백 (이전 이미지가 있다면)
    # docker-compose down
    # docker run ... 이전 버전

    exit 1
fi
