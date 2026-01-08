"""
설정 관리 모듈

환경 변수와 기본 설정을 관리합니다.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class OpenAIConfig:
    """OpenAI API 설정"""
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    def validate(self) -> bool:
        """API 키가 설정되었는지 확인"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return True


@dataclass
class ChromaConfig:
    """Chroma Vector DB 설정"""
    persist_directory: str = os.getenv("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "chroma_db"))
    collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "reviews")


@dataclass
class DataConfig:
    """데이터 경로 설정"""
    data_dir: Path = PROJECT_ROOT / "data"
    raw_dir: Path = PROJECT_ROOT / "data" / "raw"
    processed_dir: Path = PROJECT_ROOT / "data" / "processed"
    
    # Amazon Reviews 카테고리
    categories: list = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = [
                "Electronics",
                "Appliances", 
                "Beauty_and_Personal_Care",
                "Home_and_Kitchen"  # Furniture 대신 Home_and_Kitchen 사용
            ]
        
        # 디렉토리 생성
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class RAGConfig:
    """RAG 파이프라인 설정"""
    chunk_size: int = 500
    chunk_overlap: int = 50
    retriever_k: int = 5  # 검색 결과 개수
    
    # 프롬프트 템플릿
    qa_prompt_template: str = """다음은 상품 리뷰들입니다. 이 리뷰들을 바탕으로 질문에 답변해주세요.

리뷰:
{context}

질문: {question}

답변 시 주의사항:
- 리뷰에 있는 정보만 사용하세요
- 구체적인 수치나 의견을 인용하세요
- 리뷰에 없는 내용은 "리뷰에서 해당 정보를 찾을 수 없습니다"라고 답하세요

답변:"""

    summary_prompt_template: str = """다음 상품 리뷰들을 분석하여 요약해주세요.

리뷰:
{reviews}

다음 형식으로 요약해주세요:
## 장점
- (리뷰에서 자주 언급되는 긍정적인 점들)

## 단점
- (리뷰에서 자주 언급되는 부정적인 점들)

## 종합 평가
(전반적인 평가와 추천 여부)
"""


class Config:
    """전체 설정 클래스"""
    
    def __init__(self):
        self.openai = OpenAIConfig()
        self.chroma = ChromaConfig()
        self.data = DataConfig()
        self.rag = RAGConfig()
    
    def validate(self) -> bool:
        """모든 필수 설정 검증"""
        self.openai.validate()
        return True


# 전역 설정 인스턴스
config = Config()
