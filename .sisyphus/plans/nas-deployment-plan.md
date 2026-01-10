# NAS 배포 계획서

## 프로젝트 개요

**목표**: Review Mind RAG 애플리케이션을 Synology DS220+ NAS에 Docker 컨테이너로 배포하고, GitHub Webhook을 통한 CD(Continuous Deployment) 파이프라인 구축

**작성일**: 2026-01-10

---

## 요구사항 요약

| 항목 | 내용 |
|------|------|
| NAS 모델 | Synology DS220+ (Intel Celeron J4025, 24GB RAM) |
| 배포 방식 | Docker Container |
| CD 방식 | GitHub Webhook → NAS 스크립트 실행 |
| 외부 접근 | Synology Reverse Proxy (mydoor.synology.me) |
| 포트 | 8510 (Streamlit 내부) |
| API 키 관리 | `.env` 시크릿 파일 (NAS 볼륨) |
| 자동 시작 | 수동 (restart: no) |

---

## 수용 기준 (Acceptance Criteria)

### 필수
- [ ] Dockerfile이 정상적으로 빌드됨
- [ ] Docker Compose로 컨테이너 실행 가능
- [ ] 외부에서 `https://mydoor.synology.me/review-mind` 접근 시 대시보드 표시
- [ ] GitHub main 브랜치 push 시 NAS에서 자동 배포
- [ ] ChromaDB 데이터가 NAS 볼륨에 영구 저장됨
- [ ] `.env` 파일로 API 키 주입 동작

### 선택
- [ ] 헬스체크 엔드포인트 동작
- [ ] 로그 파일 영구 저장
- [ ] 배포 알림 (Slack/Discord)

---

## 구현 단계

### Phase 1: Docker 설정 (MYD-140)

#### 1.1 Dockerfile 작성
```
파일: Dockerfile
위치: 프로젝트 루트
```

**구현 내용**:
- Python 3.11 slim 베이스 이미지
- 의존성 설치 최적화 (레이어 캐싱)
- 비루트 사용자 실행 (보안)
- Streamlit 8510 포트 노출

#### 1.2 .dockerignore 작성
```
파일: .dockerignore
위치: 프로젝트 루트
```

**제외 대상**:
- `.git/`, `venv/`, `__pycache__/`
- `chroma_db/` (런타임에 볼륨 마운트)
- `.env` (보안)
- `tests/`, `docs/`

---

### Phase 2: Docker Compose 설정 (MYD-141)

#### 2.1 docker-compose.yml 작성
```
파일: docker-compose.yml
위치: 프로젝트 루트
```

**구현 내용**:
- 서비스: review-mind-rag
- 포트: 8510:8501
- 볼륨:
  - `./chroma_db:/app/chroma_db` (데이터 영속성)
  - `./.env:/app/.env:ro` (시크릿)
- 환경변수: PYTHONUNBUFFERED=1
- restart: "no"
- 네트워크: bridge

#### 2.2 docker-compose.prod.yml (프로덕션 오버라이드)
```
파일: docker-compose.prod.yml
위치: 프로젝트 루트
```

**추가 설정**:
- 로그 드라이버 설정
- 메모리 제한 (2GB)
- 헬스체크

---

### Phase 3: GitHub Actions 수정 (MYD-142)

#### 3.1 Docker 이미지 빌드 & 푸시 워크플로우
```
파일: .github/workflows/docker-build.yml
```

**트리거**: main 브랜치 push
**작업**:
1. Docker Hub 로그인
2. 이미지 빌드 (태그: latest, SHA)
3. Docker Hub 푸시
4. NAS Webhook 호출

#### 3.2 GitHub Secrets 설정 필요
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `NAS_WEBHOOK_URL`
- `NAS_WEBHOOK_SECRET`

---

### Phase 4: NAS 배포 스크립트 (MYD-143)

#### 4.1 배포 스크립트 작성
```
파일: scripts/deploy-nas.sh
```

**기능**:
- Docker Hub에서 최신 이미지 pull
- 기존 컨테이너 중지 및 제거
- 새 컨테이너 시작
- 헬스체크 확인
- 결과 로깅

#### 4.2 NAS Webhook 설정 가이드
```
파일: docs/deployment/nas-setup.md
```

**내용**:
- Synology Container Manager 설치
- Webhook 수신 설정 (Task Scheduler)
- Reverse Proxy 설정 방법
- SSL 인증서 설정

---

### Phase 5: Synology Reverse Proxy 설정 (MYD-144)

#### 5.1 Reverse Proxy 규칙
```
소스: https://mydoor.synology.me/review-mind
대상: http://localhost:8510
```

**설정**:
- WebSocket 지원 활성화 (Streamlit 필요)
- 커스텀 헤더 설정
- HTTPS 강제

#### 5.2 설정 문서화
```
파일: docs/deployment/reverse-proxy.md
```

---

### Phase 6: 환경 설정 템플릿 (MYD-145)

#### 6.1 프로덕션 환경변수 템플릿
```
파일: .env.production.example
```

**내용**:
```env
OPENAI_API_KEY=your_api_key_here
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
CHROMA_PERSIST_DIR=/app/chroma_db
CHROMA_COLLECTION_NAME=reviews
```

#### 6.2 NAS 초기 데이터 로드 가이드
```
파일: docs/deployment/initial-data-load.md
```

---

## 파일 구조 (최종)

```
review-mind-rag/
├── Dockerfile                      # Phase 1
├── .dockerignore                   # Phase 1
├── docker-compose.yml              # Phase 2
├── docker-compose.prod.yml         # Phase 2
├── .env.production.example         # Phase 6
├── .github/
│   └── workflows/
│       ├── ci.yml                  # 기존
│       └── docker-build.yml        # Phase 3 (신규)
├── scripts/
│   ├── load_all_categories.py      # 기존
│   └── deploy-nas.sh               # Phase 4 (신규)
└── docs/
    └── deployment/                 # Phase 4-6 (신규)
        ├── nas-setup.md
        ├── reverse-proxy.md
        └── initial-data-load.md
```

---

## Linear 이슈 계획

| 이슈 ID | 제목 | 우선순위 | 예상 작업 |
|---------|------|----------|----------|
| MYD-140 | Docker 설정: Dockerfile 및 .dockerignore 작성 | High | Dockerfile, .dockerignore 생성 |
| MYD-141 | Docker Compose 설정 | High | docker-compose.yml, docker-compose.prod.yml |
| MYD-142 | GitHub Actions: Docker 빌드 & Webhook 워크플로우 | High | docker-build.yml 워크플로우 |
| MYD-143 | NAS 배포 스크립트 및 설정 가이드 | Medium | deploy-nas.sh, nas-setup.md |
| MYD-144 | Synology Reverse Proxy 설정 문서화 | Medium | reverse-proxy.md |
| MYD-145 | 프로덕션 환경 설정 템플릿 | Low | .env.production.example, initial-data-load.md |

---

## 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| NAS CPU 성능 한계 | 임베딩 생성 느림 | 사전 데이터 로드, 배치 크기 조정 |
| Docker Hub rate limit | 배포 실패 | GHCR 대안 고려 |
| Webhook 보안 | 무단 배포 | 시크릿 토큰 검증 |
| 볼륨 권한 문제 | 데이터 접근 불가 | UID/GID 매핑 문서화 |

---

## 검증 체크리스트

### 로컬 테스트
- [ ] `docker build -t review-mind-rag .` 성공
- [ ] `docker-compose up` 으로 8510 포트 접근 가능
- [ ] ChromaDB 데이터 볼륨 마운트 확인

### NAS 테스트
- [ ] Docker Hub에서 이미지 pull 성공
- [ ] 컨테이너 실행 및 로그 확인
- [ ] Reverse Proxy 통해 외부 접근 확인
- [ ] Webhook 트리거 시 자동 배포 확인

---

## 실행 명령

계획 승인 후 다음 명령으로 실행:
```
/sisyphus NAS 배포 계획 실행
```

또는 이슈별로:
```
/sisyphus MYD-140 Docker 설정
```
