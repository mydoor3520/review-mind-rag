# 시작하기

Review Mind RAG를 처음 사용하시는 분들을 위한 빠른 시작 가이드입니다.

## 시스템 요구 사항

- **Python**: 3.9 이상
- **API Key**: OpenAI API Key (gpt-4o-mini 및 text-embedding-3-small 모델 사용)
- **메모리**: 최소 4GB 이상의 여유 공간 (데이터 로딩 시 권장)

## 설치

### 1. 저장소 클론

```bash
git clone <repository-url>
cd review-mind-rag
```

### 2. 가상환경 생성

=== "macOS/Linux"

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

=== "Windows"

    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

## 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 설정을 추가해야 합니다.

### 1. .env 파일 생성

```bash
cp .env.example .env
```

### 2. OpenAI API 키 입력

`.env` 파일을 열어 다음과 같이 설정합니다.

```env
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=reviews
```

!!! warning "API 키 보안"
    `.env` 파일은 절대 Git에 커밋하지 마세요. 이미 `.gitignore`에 포함되어 있습니다.

## 데이터 로딩

시스템을 사용하기 전에 리뷰 데이터를 Vector DB(ChromaDB)에 인덱싱해야 합니다.

### 전체 카테고리 로딩

`scripts/load_all_categories.py`를 사용하여 데이터를 로드할 수 있습니다.

```bash
# 기본 실행 (카테고리당 전체 데이터 로드)
python scripts/load_all_categories.py

# 테스트를 위해 카테고리당 개수 제한 (권장)
python scripts/load_all_categories.py --limit-per-category 500

# 특정 컬렉션 이름 지정
python scripts/load_all_categories.py --collection-name my_reviews
```

### 지원 카테고리

- Electronics (전자제품)
- Appliances (가전제품)
- Beauty (뷰티/화장품)
- Home & Kitchen (가구/주방용품)

!!! tip "데이터 로딩 팁"
    처음 사용하시는 경우 `--limit-per-category 500`을 사용하여 빠르게 테스트해보세요.

## 앱 실행

데이터 로딩이 완료되었다면 다음 명령어로 앱을 실행합니다.

```bash
streamlit run app/main.py
```

브라우저에서 자동으로 `http://localhost:8501`이 열립니다.

## 다음 단계

- [사용자 가이드](user-guide.md)에서 각 기능의 상세한 사용법을 확인하세요.
- [API Reference](api/rag.md)에서 코드 레벨의 문서를 확인하세요.

## 트러블슈팅

### API 키 관련 오류

**현상**: `APIKeyNotFoundError` 발생 또는 AI 답변이 생성되지 않음.

**해결**: `.env` 파일에 `OPENAI_API_KEY`가 정확히 입력되었는지 확인하세요. Streamlit 사이드바 설정에서도 직접 입력할 수 있습니다.

### 데이터 로딩 실패

**현상**: 검색 결과나 QA 답변이 "데이터가 없습니다"라고 나옴.

**해결**: `scripts/load_all_categories.py`를 실행했는지 확인하세요. `chroma_db/` 폴더가 생성되었는지 확인하십시오.

### 메모리 부족 오류

**현상**: 데이터 인덱싱 중 프로그램이 종료됨.

**해결**: `--limit-per-category` 인자를 사용하여 로드하는 데이터 양을 줄이거나, `--batch-size`를 작게 설정(예: 50)하여 실행하세요.
