# review-mind-rag Dockerfile
# RAG 기반 이커머스 리뷰 분석 시스템
#
# 빌드: docker build -t review-mind-rag .
# 실행: docker run -p 8501:8501 --env-file .env review-mind-rag

FROM python:3.11-slim

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치 (캐싱 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY src/ ./src/
COPY app/ ./app/
COPY pyproject.toml ./

# 데이터 및 DB 디렉토리 생성
RUN mkdir -p data/raw data/processed chroma_db

# Streamlit 설정
RUN mkdir -p .streamlit
COPY <<EOF .streamlit/config.toml
[server]
port = 8501
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1E88E5"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
EOF

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501

# 포트 노출
EXPOSE 8501

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Streamlit 앱 실행
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
