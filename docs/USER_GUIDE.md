# 📖 Review Mind RAG 사용자 가이드

Review Mind RAG는 이커머스 상품 리뷰를 분석하여 사용자에게 유용한 통찰을 제공하는 RAG(Retrieval-Augmented Generation) 기반 시스템입니다. 이 가이드는 시스템 설치부터 각 기능 활용 방법까지 상세히 설명합니다.

---

## 📑 목차

1. [시스템 요구 사항](#시스템-요구-사항)
2. [설치 가이드](#설치-가이드)
3. [환경 변수 설정](#환경-변수-설정)
4. [데이터 로딩 방법](#데이터-로딩-방법)
5. [주요 기능 사용법](#주요-기능-사용법)
    - [상품 검색 (Search)](#상품-검색-search)
    - [리뷰 QA (QA Chat)](#리뷰-qa-qa-chat)
    - [리뷰 요약 (Summary)](#리뷰-요약-summary)
    - [상품 비교 (Compare)](#상품-비교-compare)
6. [트러블슈팅](#트러블슈팅)
7. [자주 묻는 질문 (FAQ)](#자주-묻는-질문-faq)

---

## 💻 시스템 요구 사항

- **Python**: 3.9 이상
- **API Key**: OpenAI API Key (gpt-4o-mini 및 text-embedding-3-small 모델 사용)
- **메모리**: 최소 4GB 이상의 여유 공간 (데이터 로딩 시 권장)

---

## 🛠️ 설치 가이드

### 1. 저장소 클론 및 이동
```bash
git clone <repository-url>
cd review-mind-rag
```

### 2. 가상환경 생성 및 활성화
**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

---

## ⚙️ 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 설정을 추가해야 합니다.

1. `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.
   ```bash
   cp .env.example .env
   ```

2. `.env` 파일을 열어 OpenAI API 키를 입력합니다.
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   EMBEDDING_MODEL=text-embedding-3-small
   LLM_MODEL=gpt-4o-mini
   CHROMA_PERSIST_DIR=./chroma_db
   CHROMA_COLLECTION_NAME=reviews
   ```

---

## 📥 데이터 로딩 방법

시스템을 사용하기 전에 리뷰 데이터를 Vector DB(ChromaDB)에 인덱싱해야 합니다.

### 전체 카테고리 로딩 스크립트 사용
`scripts/load_all_categories.py`를 사용하여 데이터를 로드할 수 있습니다.

```bash
# 기본 실행 (카테고리당 전체 데이터 로드)
python scripts/load_all_categories.py

# 테스트를 위해 카테고리당 개수 제한 (권장)
python scripts/load_all_categories.py --limit-per-category 500

# 특정 컬렉션 이름 지정
python scripts/load_all_categories.py --collection-name my_reviews
```

**지원 카테고리:**
- Electronics (전자제품)
- Appliances (가전제품)
- Beauty (뷰티/화장품)
- Home & Kitchen (가구/주방용품)

---

## 🚀 주요 기능 사용법

데이터 로딩이 완료되었다면 다음 명령어로 앱을 실행합니다.
```bash
streamlit run app/main.py
```

### 🔍 상품 검색 (Search)
- **위치**: 사이드바 `1_🔍_Search`
- **사용법**: 
  1. 검색어 입력창에 상품명 또는 키워드를 입력합니다.
  2. 원하는 카테고리를 선택합니다.
  3. `검색` 버튼을 클릭하여 관련 상품 리스트와 리뷰 요약을 확인합니다.

### 💬 리뷰 QA (QA Chat)
- **위치**: 사이드바 `2_💬_QA_Chat`
- **사용법**:
  1. 질문 입력창에 궁금한 내용을 자연어로 입력합니다. (예: "이 제품 소음은 어떤가요?")
  2. AI가 관련 리뷰를 검색하여 답변을 생성합니다.
  3. `참고한 리뷰` 확장 섹션을 통해 실제 근거가 된 리뷰 원문을 확인할 수 있습니다.
  4. 사이드바의 `필터 설정`을 통해 특정 카테고리나 최소 평점 조건을 걸 수 있습니다.

### 📊 리뷰 요약 (Summary)
- **위치**: 사이드바 `3_📊_Summary`
- **사용법**:
  1. 분석을 원하는 상품의 ID(ASIN 등)를 입력합니다.
  2. `요약 생성` 버튼을 클릭합니다.
  3. AI가 해당 상품의 리뷰를 분석하여 **장점**, **단점**, **종합 평가**를 제공합니다.
  4. 하단에서 긍정/부정 리뷰의 비율을 나타내는 감성 분석 차트를 확인합니다.

### ⚖️ 상품 비교 (Compare)
- **위치**: 사이드바 `4_⚖️_Compare`
- **사용법**:
  1. 비교할 두 상품의 ID를 각각 입력합니다.
  2. `비교 분석` 버튼을 클릭합니다.
  3. 두 상품의 평균 평점, 리뷰 수, 주요 장단점을 한눈에 비교할 수 있는 표와 분석 리포트가 생성됩니다.

---

## ❓ 트러블슈팅

### 1. API 키 관련 오류
- **현상**: `APIKeyNotFoundError` 발생 또는 AI 답변이 생성되지 않음.
- **해결**: `.env` 파일에 `OPENAI_API_KEY`가 정확히 입력되었는지 확인하세요. Streamlit 사이드바 설정에서도 직접 입력할 수 있습니다.

### 2. 데이터 로딩 실패
- **현상**: 검색 결과나 QA 답변이 "데이터가 없습니다"라고 나옴.
- **해결**: `scripts/load_all_categories.py`를 실행했는지 확인하세요. `chroma_db/` 폴더가 생성되었는지 확인하십시오.

### 3. 메모리 부족 오류
- **현상**: 데이터 인덱싱 중 프로그램이 종료됨.
- **해결**: `--limit-per-category` 인자를 사용하여 로드하는 데이터 양을 줄이거나, `--batch-size`를 작게 설정(예: 50)하여 실행하세요.

---

## 💬 자주 묻는 질문 (FAQ)

**Q: 어떤 데이터를 기반으로 답변하나요?**
A: Amazon Reviews 2023 오픈 데이터를 기반으로 하며, 시스템에 인덱싱된 리뷰만을 근거로 답변합니다.

**Q: 한국어로 질문해도 되나요?**
A: 네, 시스템 프롬프트가 한국어 답변을 지원하도록 설계되어 있어 한국어 질문에 대해 한국어로 답변합니다.

**Q: 새로운 카테고리를 추가할 수 있나요?**
A: `src/config.py`의 `DataConfig` 클래스에서 `categories` 리스트를 수정하여 다른 Amazon 카테고리를 추가할 수 있습니다.
