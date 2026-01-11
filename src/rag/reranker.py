"""
Reranker 모듈

Cross-encoder를 사용하여 검색 결과를 재정렬합니다.
"""

from typing import List, Optional, Tuple
from langchain_core.documents import Document

try:
    from sentence_transformers import CrossEncoder
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    CrossEncoder = None


class KoreanReranker:
    """
    다국어 지원 Reranker

    Cross-encoder 모델을 사용하여 Query-Document 관련성을 재평가합니다.
    영어/한국어 혼용 환경에서 사용할 수 있습니다.
    """

    # 영어 리뷰 + 한국어/영어 질문에 적합한 다국어 모델
    DEFAULT_MODEL = "BAAI/bge-reranker-v2-m3"
    FALLBACK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        top_n: int = 5,
        score_threshold: float = 0.0,
        max_length: int = 512
    ):
        """
        :param model_name: Cross-encoder 모델명 (기본: ko-reranker)
        :param top_n: 반환할 최대 문서 수
        :param score_threshold: 최소 점수 임계값 (이하는 제외)
        :param max_length: 최대 토큰 길이
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers 패키지가 필요합니다: "
                "pip install sentence-transformers"
            )
        
        self.model_name = model_name or self.DEFAULT_MODEL
        self.top_n = top_n
        self.score_threshold = score_threshold
        self.max_length = max_length
        
        self._model: Optional[CrossEncoder] = None
    
    @property
    def model(self) -> CrossEncoder:
        """Cross-encoder 모델 (lazy loading)"""
        if self._model is None:
            try:
                self._model = CrossEncoder(
                    self.model_name,
                    max_length=self.max_length
                )
            except Exception:
                self._model = CrossEncoder(
                    self.FALLBACK_MODEL,
                    max_length=self.max_length
                )
        return self._model
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_n: Optional[int] = None
    ) -> List[Document]:
        """
        문서를 Query와의 관련성에 따라 재정렬합니다.
        
        :param query: 검색 쿼리
        :param documents: 재정렬할 Document 리스트
        :param top_n: 반환할 문서 수 (기본: 초기화 시 설정값)
        :return: 재정렬된 Document 리스트
        """
        if not documents:
            return []
        
        top_n = top_n or self.top_n
        
        pairs = [(query, doc.page_content) for doc in documents]
        scores = self.model.predict(pairs)
        
        scored_docs = sorted(
            zip(scores, documents),
            key=lambda x: x[0],
            reverse=True
        )
        
        result = []
        for score, doc in scored_docs[:top_n]:
            if score >= self.score_threshold:
                doc.metadata["rerank_score"] = float(score)
                result.append(doc)
        
        return result
    
    def rerank_with_scores(
        self,
        query: str,
        documents: List[Document]
    ) -> List[Tuple[Document, float]]:
        """
        문서와 점수를 함께 반환합니다.
        
        :param query: 검색 쿼리
        :param documents: 재정렬할 Document 리스트
        :return: (Document, score) 튜플 리스트
        """
        if not documents:
            return []
        
        pairs = [(query, doc.page_content) for doc in documents]
        scores = self.model.predict(pairs)
        
        scored_docs = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            (doc, float(score))
            for doc, score in scored_docs
            if score >= self.score_threshold
        ]


class RerankerFactory:
    """Reranker 팩토리 클래스"""
    
    @staticmethod
    def create(
        reranker_type: str = "korean",
        **kwargs
    ) -> KoreanReranker:
        """
        Reranker 인스턴스를 생성합니다.
        
        :param reranker_type: 리랭커 타입 ("korean", "multilingual")
        :param kwargs: Reranker 초기화 인자
        :return: Reranker 인스턴스
        """
        model_map = {
            "korean": "Dongjin-kr/ko-reranker",
            "multilingual": "BAAI/bge-reranker-v2-m3",
            "ms-marco": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        }
        
        model_name = model_map.get(reranker_type, model_map["korean"])
        return KoreanReranker(model_name=model_name, **kwargs)
