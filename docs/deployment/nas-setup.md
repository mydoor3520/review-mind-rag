# Synology NAS 설정 가이드

Review Mind RAG를 Synology NAS (DS220+)에 배포하기 위한 설정 가이드입니다.

## 목차

1. [사전 요구사항](#사전-요구사항)
2. [Container Manager 설치](#container-manager-설치)
3. [디렉토리 구조 설정](#디렉토리-구조-설정)
4. [환경 변수 설정](#환경-변수-설정)
5. [Webhook 설정](#webhook-설정)
6. [수동 배포](#수동-배포)
7. [자동 배포 (GitHub CD)](#자동-배포-github-cd)
8. [트러블슈팅](#트러블슈팅)

---

## 사전 요구사항

- Synology NAS (DS220+ 또는 호환 모델)
- DSM 7.0 이상
- Container Manager (구 Docker) 패키지
- SSH 접근 권한 (고급 설정용)

---

## Container Manager 설치

1. **패키지 센터** 열기
2. **Container Manager** 검색 및 설치
3. 설치 완료 후 **Container Manager** 실행

---

## 디렉토리 구조 설정

SSH 또는 File Station에서 다음 디렉토리 구조를 생성합니다:

```bash
# SSH 접속
ssh admin@your-nas-ip

# 디렉토리 생성
sudo mkdir -p /volume1/docker/review-mind-rag/{chroma_db,data,logs}
sudo chown -R 1000:1000 /volume1/docker/review-mind-rag
```

### 디렉토리 구조

```
/volume1/docker/review-mind-rag/
├── docker-compose.yml      # Docker Compose 설정
├── docker-compose.prod.yml # 프로덕션 오버라이드
├── .env                    # 환경 변수 (시크릿)
├── chroma_db/              # Vector DB 데이터
├── data/                   # 리뷰 데이터
│   ├── raw/
│   └── processed/
├── logs/                   # 배포 로그
└── scripts/
    └── deploy-nas.sh       # 배포 스크립트
```

---

## 환경 변수 설정

`.env` 파일을 생성하고 API 키를 설정합니다:

```bash
# /volume1/docker/review-mind-rag/.env
cat > /volume1/docker/review-mind-rag/.env << 'EOF'
# OpenAI API 설정
OPENAI_API_KEY=sk-your-api-key-here

# 모델 설정
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini

# ChromaDB 설정
CHROMA_PERSIST_DIR=/app/chroma_db
CHROMA_COLLECTION_NAME=reviews
EOF

# 권한 설정 (보안)
chmod 600 /volume1/docker/review-mind-rag/.env
```

---

## Webhook 설정

GitHub Actions에서 NAS로 배포를 트리거하기 위한 Webhook 설정입니다.

### 방법 1: Task Scheduler + HTTP 서버 (권장)

1. **제어판 > 작업 스케줄러** 열기
2. **생성 > 트리거된 작업 > 사용자 정의 스크립트** 선택
3. 설정:
   - 작업: `review-mind-deploy`
   - 사용자: `root`
   - 이벤트: **부트업** (또는 Webhook 트리거 시)

### 방법 2: 간단한 Webhook 수신 스크립트

NAS에서 간단한 HTTP 서버를 실행하여 Webhook을 수신합니다:

```bash
# webhook-server.py
# /volume1/docker/review-mind-rag/webhook-server.py

#!/usr/bin/env python3
import http.server
import subprocess
import json
import os

WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-secret-here')
DEPLOY_SCRIPT = '/volume1/docker/review-mind-rag/scripts/deploy-nas.sh'

class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        # 시크릿 검증
        secret = self.headers.get('X-Webhook-Secret', '')
        if secret != WEBHOOK_SECRET:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'Forbidden')
            return

        # 배포 스크립트 실행
        try:
            result = subprocess.run(
                ['bash', DEPLOY_SCRIPT],
                capture_output=True,
                text=True
            )

            self.send_response(200)
            self.end_headers()
            self.wfile.write(f'Deploy executed: {result.returncode}'.encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'Error: {str(e)}'.encode())

if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', 9000), WebhookHandler)
    print('Webhook server running on port 9000')
    server.serve_forever()
```

---

## 수동 배포

### Docker Compose 파일 복사

```bash
# 로컬에서 NAS로 파일 복사
scp docker-compose.yml admin@your-nas:/volume1/docker/review-mind-rag/
scp docker-compose.prod.yml admin@your-nas:/volume1/docker/review-mind-rag/
scp scripts/deploy-nas.sh admin@your-nas:/volume1/docker/review-mind-rag/scripts/

# 스크립트 실행 권한
ssh admin@your-nas "chmod +x /volume1/docker/review-mind-rag/scripts/deploy-nas.sh"
```

### 첫 배포 실행

```bash
# NAS SSH 접속 후
cd /volume1/docker/review-mind-rag
./scripts/deploy-nas.sh
```

### Container Manager UI에서 확인

1. Container Manager 열기
2. **컨테이너** 탭에서 `review-mind-rag` 확인
3. 상태가 **실행 중**인지 확인
4. **로그** 탭에서 시작 로그 확인

---

## 자동 배포 (GitHub CD)

### GitHub Secrets 설정

GitHub 저장소 > Settings > Secrets and variables > Actions에서:

| Secret 이름 | 값 |
|------------|-----|
| `DOCKERHUB_USERNAME` | Docker Hub 사용자명 |
| `DOCKERHUB_TOKEN` | Docker Hub 액세스 토큰 |
| `NAS_WEBHOOK_URL` | `http://your-nas:9000/deploy` |
| `NAS_WEBHOOK_SECRET` | Webhook 시크릿 (자체 생성) |

### 배포 흐름

```
1. main 브랜치 push
   ↓
2. GitHub Actions 트리거
   ↓
3. Docker 이미지 빌드 & Docker Hub 푸시
   ↓
4. NAS Webhook 호출
   ↓
5. NAS에서 deploy-nas.sh 실행
   ↓
6. 새 이미지 Pull & 컨테이너 재시작
```

---

## 트러블슈팅

### 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker logs review-mind-rag

# 리소스 확인
docker stats review-mind-rag
```

### 포트 충돌

```bash
# 8510 포트 사용 확인
netstat -tlnp | grep 8510

# 다른 포트로 변경 (docker-compose.yml)
ports:
  - "8520:8501"
```

### 권한 문제

```bash
# chroma_db 디렉토리 권한 확인
ls -la /volume1/docker/review-mind-rag/chroma_db

# 권한 수정
sudo chown -R 1000:1000 /volume1/docker/review-mind-rag/chroma_db
```

### Webhook이 작동하지 않음

1. NAS 방화벽에서 9000 포트 열기
2. 라우터 포트 포워딩 확인 (외부 접근 시)
3. Webhook 서버 로그 확인

---

## 다음 단계

- [Reverse Proxy 설정](./reverse-proxy.md)
- [초기 데이터 로드](./initial-data-load.md)
