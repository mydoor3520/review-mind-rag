# AGENTS.md - Review Mind RAG

이커머스 리뷰 분석을 위한 RAG(Retrieval-Augmented Generation) 기반 시스템입니다.

## 프로젝트 관리

| 항목 | 링크 |
|------|------|
| **Notion 계획서** | [review-mind-rag: RAG 기반 이커머스 리뷰 분석 시스템](https://www.notion.so/review-mind-rag-RAG-2e1d921d671e81978b8ddc6c7c1a0c7e) |
| **Linear 프로젝트** | review-mind-rag (이슈 접두사: `MYD`) |

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 언어 | Python 3.9+ |
| 프레임워크 | LangChain, Streamlit |
| Vector DB | ChromaDB |
| LLM | OpenAI GPT-4o-mini |
| Embedding | OpenAI text-embedding-3-small |

## 빌드 및 실행 명령어

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Streamlit 앱 실행
streamlit run app/main.py
```

## 테스트

### 테스트 도구

- **단위 테스트**: pytest
- **E2E 테스트**: Playwright (Streamlit UI 테스트 시)

### 테스트 명령어

```bash
# 전체 테스트
pytest tests/

# 단일 파일
pytest tests/test_preprocessor.py

# 단일 함수
pytest tests/test_preprocessor.py::test_clean_text -v

# 커버리지
pytest --cov=src tests/

# 키워드 매칭
pytest -k "sentiment" -v
```

### 테스트 코드 작성 규칙

```python
"""
테스트 파일은 tests/ 디렉토리에 위치
파일명: test_{모듈명}.py
"""

import pytest
from src.data.preprocessor import ReviewPreprocessor


class TestReviewPreprocessor:
    """ReviewPreprocessor 테스트"""
    
    def test_clean_text_HTML태그_제거(self):
        """HTML 태그가 포함된 텍스트에서 태그를 제거한다"""
        # given
        preprocessor = ReviewPreprocessor()
        text = "<p>좋은 제품입니다</p>"
        
        # when
        result = preprocessor.clean_text(text)
        
        # then
        assert result == "좋은 제품입니다"
    
    def test_is_valid_review_최소길이_미달시_False(self):
        """리뷰 텍스트가 최소 길이 미만이면 False를 반환한다"""
        # given
        preprocessor = ReviewPreprocessor(min_length=20)
        review = {"review_text": "짧은 리뷰", "rating": 5}
        
        # when
        result = preprocessor.is_valid_review(review)
        
        # then
        assert result is False
```

## 환경 변수

`.env` 파일 필수 (`.env.example` 참조):

```bash
OPENAI_API_KEY=your_api_key_here
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=reviews
```

## 프로젝트 구조

```
review-mind-rag/
├── app/                    # Streamlit UI
│   ├── main.py            # 메인 대시보드
│   └── pages/             # 서브 페이지들
├── src/                    # 핵심 비즈니스 로직
│   ├── config.py          # 전역 설정
│   ├── data/              # 데이터 로딩/전처리
│   ├── rag/               # RAG 파이프라인
│   └── analysis/          # 분석 모듈
├── tests/                  # 테스트 코드
├── data/                   # 데이터 저장소 (git 제외)
└── chroma_db/             # Vector DB (git 제외)
```

## 코드 스타일

### 모듈 구조

```python
"""
모듈 설명 (한국어)

모듈의 역할을 간략히 설명합니다.
"""

from typing import List, Optional, Dict, Any
from langchain.schema import Document

# 상대 임포트 사용
from .vectorstore import ReviewVectorStore
```

### 타입 힌트 및 Docstring

```python
def search(
    self,
    query: str,
    k: int = 5,
    category: Optional[str] = None
) -> List[Document]:
    """
    필터 조건과 함께 리뷰를 검색합니다.
    
    :param query: 검색 쿼리
    :param k: 반환할 결과 수
    :param category: 카테고리 필터
    :return: 검색된 Document 리스트
    """
```

### 클래스 설계 패턴

- 생성자에서 기본값 제공
- Lazy initialization 패턴 (`_instance: Optional[T] = None`)
- `@property` 데코레이터로 lazy 접근

```python
def __init__(self, persist_directory: str = "./chroma_db"):
    self._vectorstore: Optional[Chroma] = None

@property
def vectorstore(self) -> Chroma:
    if self._vectorstore is None:
        self._vectorstore = Chroma(...)
    return self._vectorstore
```

### 에러 처리

```python
# 명시적 예외 발생
if not self.api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

# Import 에러 처리
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("datasets 패키지를 설치해주세요: pip install datasets")
```

### 네이밍 컨벤션

| 항목 | 스타일 | 예시 |
|------|--------|------|
| 클래스 | PascalCase | `ReviewVectorStore` |
| 함수/메서드 | snake_case | `add_documents` |
| 상수 | UPPER_SNAKE | `DEFAULT_QA_PROMPT` |
| Private | `_prefix` | `_vectorstore` |

### 임포트 순서

```python
# 1. 표준 라이브러리
import re
from typing import List, Dict, Optional

# 2. 서드파티 라이브러리
from langchain.schema import Document
from langchain_openai import ChatOpenAI

# 3. 로컬 모듈 (상대 임포트)
from .vectorstore import ReviewVectorStore
```

## LangChain 패턴

- `Document` 객체에 메타데이터 포함
- `RetrievalQA` 체인에서 `return_source_documents=True`
- 프롬프트는 클래스 상수로 정의

```python
Document(
    page_content=clean_review_text,
    metadata={
        "review_id": review.get("review_id", ""),
        "product_id": review.get("product_id", ""),
        "rating": review.get("rating", 0),
        "sentiment": self._get_sentiment(rating),
    }
)
```

## Streamlit 페이지 구조

```python
"""페이지 설명"""

import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="페이지명 - Review Mind RAG",
    page_icon="🔍",
    layout="wide"
)
```

## 기술 문서화 규칙

중요한 개념, 구조, 기술 선택이 발생할 경우 **반드시 Notion에 문서화**하여 공유한다.

### 문서화 대상

| 상황 | 예시 |
|------|------|
| **중요 개념** | RAG 파이프라인 흐름, 임베딩 전략, 프롬프트 설계 철학 |
| **중요 구조** | 모듈 아키텍처, 데이터 흐름, 클래스 설계 |
| **중요 선택** | ChromaDB vs Qdrant 선택 이유, Reranker 도입 결정, 모델 선정 근거 |

### 문서 작성 시점

- 새로운 아키텍처 결정 시
- 기술 스택 선택/변경 시
- 트레이드오프가 있는 설계 결정 시
- 향후 참고가 필요한 핵심 개념 정리 시

### 게시 위치

- **Notion 프로젝트 페이지**: [review-mind-rag](https://www.notion.so/review-mind-rag-2e2d921d671e806bba7ceb72813d9cf2)
- 전역 CLAUDE.md의 "Notion 문서 작성 컨벤션" 참조

## 주의사항

- `.env` 파일은 절대 커밋하지 않음
- `data/raw/`, `data/processed/`, `chroma_db/`는 git 제외
- OpenAI API 키 없이는 RAG 기능 동작 불가
- 대용량 데이터 로드 시 `streaming=True` 사용 권장
