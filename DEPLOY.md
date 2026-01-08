# 🚀 Review Mind RAG 배포 가이드

NAS 또는 서버에 Docker를 사용하여 Review Mind RAG를 배포하는 방법을 설명합니다.

## 📋 사전 요구사항

| 항목 | 최소 요구사항 |
|------|-------------|
| Docker | 20.10 이상 |
| Docker Compose | 2.0 이상 |
| RAM | 2GB 이상 권장 |
| 저장 공간 | 5GB 이상 (Vector DB 크기에 따라 증가) |
| OpenAI API Key | 필수 |

## 🔧 빠른 시작 (5분 배포)

### 1. 프로젝트 다운로드

```bash
# 프로젝트 클론
git clone https://github.com/your-username/review-mind-rag.git
cd review-mind-rag
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

**필수 설정:**
```bash
# .env 파일 내용
OPENAI_API_KEY=sk-your-api-key-here

# 선택 설정 (기본값 사용 가능)
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
STREAMLIT_PORT=8501
```

### 3. Docker Compose로 실행

```bash
# 컨테이너 빌드 및 실행
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f
```

### 4. 접속 확인

브라우저에서 `http://<NAS-IP>:8501` 접속

---

## 🔒 NAS별 상세 가이드

### Synology NAS

#### Container Manager 사용 (권장)

1. **Container Manager** → **프로젝트** → **생성**
2. 프로젝트 경로: `/volume1/docker/review-mind-rag`
3. `docker-compose.yml` 업로드
4. 환경 변수 설정 (OPENAI_API_KEY)
5. **적용** 클릭

#### SSH로 직접 설치

```bash
# SSH 접속
ssh admin@nas-ip

# 디렉토리 생성
sudo mkdir -p /volume1/docker/review-mind-rag
cd /volume1/docker/review-mind-rag

# 파일 복사 후 실행
docker-compose up -d
```

### QNAP NAS

#### Container Station 사용

1. **Container Station** → **Create** → **Create Application**
2. `docker-compose.yml` 내용 붙여넣기
3. **Create** 클릭

### 일반 Linux 서버

```bash
# Docker 설치 (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo apt install docker-compose-plugin

# 서비스 실행
docker compose up -d
```

---

## 📊 데이터 관리

### 볼륨 위치

| 볼륨 | 용도 | 컨테이너 내 경로 |
|------|------|----------------|
| `review-mind-data` | 리뷰 데이터 (raw/processed) | `/app/data` |
| `review-mind-chroma` | Vector DB | `/app/chroma_db` |

### 데이터 백업

```bash
# 볼륨 백업
docker run --rm \
  -v review-mind-data:/data \
  -v $(pwd):/backup \
  busybox tar cvf /backup/data-backup.tar /data

docker run --rm \
  -v review-mind-chroma:/chroma \
  -v $(pwd):/backup \
  busybox tar cvf /backup/chroma-backup.tar /chroma
```

### 데이터 복원

```bash
# 볼륨 복원
docker run --rm \
  -v review-mind-data:/data \
  -v $(pwd):/backup \
  busybox tar xvf /backup/data-backup.tar -C /

docker run --rm \
  -v review-mind-chroma:/chroma \
  -v $(pwd):/backup \
  busybox tar xvf /backup/chroma-backup.tar -C /
```

### 리뷰 데이터 로드 (컨테이너 내에서)

```bash
# 컨테이너 접속
docker exec -it review-mind-rag bash

# 데이터 로드 (예: Electronics 카테고리 1000개)
python -c "
from src.data.loader import AmazonReviewLoader
from src.data.preprocessor import ReviewPreprocessor
from src.rag.vectorstore import ReviewVectorStore

loader = AmazonReviewLoader()
reviews = loader.load_category('Electronics', limit=1000)

preprocessor = ReviewPreprocessor()
documents = list(preprocessor.process_reviews(reviews))

vectorstore = ReviewVectorStore.from_documents(documents)
print(f'Loaded {len(documents)} documents')
"
```

---

## 🔧 운영 명령어

### 기본 명령어

```bash
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 서비스 재시작
docker-compose restart

# 로그 확인 (실시간)
docker-compose logs -f

# 컨테이너 상태 확인
docker-compose ps
```

### 업데이트

```bash
# 최신 코드 가져오기
git pull origin main

# 이미지 재빌드 및 배포
docker-compose up -d --build
```

### 문제 해결

```bash
# 컨테이너 로그 확인
docker-compose logs review-mind

# 컨테이너 내부 접속
docker exec -it review-mind-rag bash

# 헬스체크 확인
curl http://localhost:8501/_stcore/health
```

---

## ⚙️ 고급 설정

### 리버스 프록시 (Nginx)

```nginx
# /etc/nginx/sites-available/review-mind
server {
    listen 80;
    server_name review-mind.example.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

### HTTPS 설정 (Let's Encrypt)

```bash
# certbot 설치
sudo apt install certbot python3-certbot-nginx

# 인증서 발급
sudo certbot --nginx -d review-mind.example.com
```

### 커스텀 포트 사용

```bash
# .env 파일에서 포트 변경
STREAMLIT_PORT=9501

# 재시작
docker-compose up -d
```

---

## 🐛 트러블슈팅

### "OPENAI_API_KEY 환경 변수가 설정되지 않았습니다" 오류

```bash
# .env 파일 확인
cat .env | grep OPENAI

# 환경 변수 직접 확인
docker exec review-mind-rag env | grep OPENAI
```

### 컨테이너가 계속 재시작되는 경우

```bash
# 로그 확인
docker-compose logs --tail=100

# 메모리 확인
docker stats review-mind-rag
```

### Vector DB 손상 시

```bash
# 볼륨 삭제 후 재생성
docker-compose down -v
docker-compose up -d

# 데이터 재로드 필요
```

### 포트 충돌

```bash
# 사용 중인 포트 확인
netstat -tlnp | grep 8501

# 포트 변경 (.env 수정)
STREAMLIT_PORT=8502
docker-compose up -d
```

---

## 📈 모니터링

### 리소스 사용량 확인

```bash
# 실시간 리소스 모니터링
docker stats review-mind-rag

# 디스크 사용량
docker system df
```

### 로그 관리

로그는 자동으로 최대 10MB × 3개 파일로 제한됩니다. (`docker-compose.yml`의 `logging` 설정)

---

## 📝 환경 변수 전체 목록

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `OPENAI_API_KEY` | (필수) | OpenAI API 키 |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | 임베딩 모델 |
| `LLM_MODEL` | `gpt-4o-mini` | LLM 모델 |
| `STREAMLIT_PORT` | `8501` | 외부 접속 포트 |
| `CHROMA_COLLECTION_NAME` | `reviews` | ChromaDB 컬렉션명 |

---

## 🔗 참고 자료

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 공식 문서](https://docs.docker.com/compose/)
- [Streamlit 배포 가이드](https://docs.streamlit.io/deploy)
- [Synology Container Manager](https://www.synology.com/en-global/dsm/feature/container-manager)
