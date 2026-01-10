# Review Mind RAG

RAG(Retrieval-Augmented Generation) 기반 이커머스 리뷰 분석 시스템

## 개요

Review Mind RAG는 이커머스 상품 리뷰를 Vector DB에 저장하고, 자연어 질문을 통해 리뷰 기반 답변을 제공하는 AI 시스템입니다.

### 주요 기능

- **자연어 QA**: "이 제품 소음 어때?" 같은 질문에 리뷰 기반 답변
- **리뷰 요약**: 상품별 장점/단점 자동 요약
- **감성 분석**: 긍정/부정/중립 비율 시각화
- **상품 비교**: 두 상품의 리뷰 비교 분석

## 기술 스택

| 구분 | 기술 |
|------|------|
| LLM Framework | LangChain |
| Vector DB | Chroma |
| Embedding | OpenAI text-embedding-3-small |
| LLM | OpenAI gpt-4o-mini |
| UI | Streamlit |
| Data | Amazon Reviews 2023 |

## 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
cd review-mind-rag

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일에 OpenAI API 키 설정
OPENAI_API_KEY=your_api_key_here
```

### 3. 데이터 로드 (선택)

```python
from src.data.loader import AmazonReviewLoader
from src.data.preprocessor import ReviewPreprocessor
from src.rag.vectorstore import ReviewVectorStore

# 데이터 로드
loader = AmazonReviewLoader()
reviews = loader.load_category("Electronics", limit=1000)

# 전처리
preprocessor = ReviewPreprocessor()
documents = list(preprocessor.process_reviews(reviews))

# Vector DB 저장
vectorstore = ReviewVectorStore.from_documents(documents)
```

### 4. 앱 실행

```bash
streamlit run app/main.py
```

## 프로젝트 구조

```
review-mind-rag/
├── app/                    # Streamlit 앱
│   ├── main.py
│   └── pages/
├── src/                    # 핵심 로직
│   ├── data/              # 데이터 로딩/전처리
│   ├── rag/               # RAG 파이프라인
│   └── analysis/          # 분석 모듈
├── data/                   # 데이터 저장소
├── chroma_db/             # Vector DB
└── notebooks/             # 탐색용 노트북
```

## 지원 카테고리

- Electronics (전자제품)
- Appliances (가전제품)
- Beauty (뷰티/화장품)
- Home & Kitchen (가구/주방용품)

## 라이선스

MIT License

## 참고 자료

- [LangChain Docs](https://python.langchain.com/docs/)
- [Chroma Docs](https://docs.trychroma.com/)
- [Amazon Reviews 2023](https://amazon-reviews-2023.github.io/)
