"""
리뷰 검색 모듈

메타데이터 필터링과 함께 리뷰를 검색합니다.
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from langchain_core.documents import Document
from .vectorstore import ReviewVectorStore

if TYPE_CHECKING:
    from .reranker import KoreanReranker


class ReviewRetriever:
    """
    리뷰 검색기
    
    카테고리, 평점 등 메타데이터 필터링을 지원하는 검색기입니다.
    """
    
    def __init__(
        self,
        vectorstore: ReviewVectorStore,
        reranker: Optional["KoreanReranker"] = None
    ):
        """
        :param vectorstore: ReviewVectorStore 인스턴스
        :param reranker: KoreanReranker 인스턴스 (선택)
        """
        self.vectorstore = vectorstore
        self.reranker = reranker
    
    def search(
        self,
        query: str,
        k: int = 5,
        category: Optional[str] = None,
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None,
        sentiment: Optional[str] = None,
        product_id: Optional[str] = None,
        use_reranker: bool = True,
        fetch_k: Optional[int] = None
    ) -> List[Document]:
        """
        필터 조건과 함께 리뷰를 검색합니다.
        
        :param query: 검색 쿼리
        :param k: 반환할 결과 수
        :param category: 카테고리 필터
        :param min_rating: 최소 평점
        :param max_rating: 최대 평점
        :param sentiment: 감성 필터 (positive, negative, neutral)
        :param product_id: 특정 상품 ID
        :param use_reranker: Reranker 사용 여부 (기본: True)
        :param fetch_k: 1차 검색에서 가져올 문서 수 (reranker 사용 시)
        :return: 검색된 Document 리스트
        """
        filter_dict = self._build_filter(
            category=category,
            min_rating=min_rating,
            max_rating=max_rating,
            sentiment=sentiment,
            product_id=product_id
        )
        
        if self.reranker and use_reranker:
            search_k = fetch_k or k * 4
            candidates = self.vectorstore.similarity_search(
                query=query,
                k=search_k,
                filter=filter_dict if filter_dict else None
            )
            return self.reranker.rerank(query, candidates, top_n=k)
        
        return self.vectorstore.similarity_search(
            query=query,
            k=k,
            filter=filter_dict if filter_dict else None
        )
    
    def search_by_product(
        self,
        product_id: str,
        query: Optional[str] = None,
        k: int = 10
    ) -> List[Document]:
        """
        특정 상품의 리뷰를 검색합니다.
        
        :param product_id: 상품 ID
        :param query: 추가 검색 쿼리 (선택)
        :param k: 반환할 결과 수
        :return: 검색된 Document 리스트
        """
        if query:
            return self.search(
                query=query,
                k=k,
                product_id=product_id
            )
        else:
            # 쿼리 없이 상품 ID로만 검색
            return self.vectorstore.similarity_search(
                query="product review",  # 기본 쿼리
                k=k,
                filter={"product_id": product_id}
            )
    
    def search_positive_reviews(
        self,
        query: str,
        k: int = 5,
        category: Optional[str] = None
    ) -> List[Document]:
        """
        긍정적인 리뷰만 검색합니다.
        
        :param query: 검색 쿼리
        :param k: 반환할 결과 수
        :param category: 카테고리 필터
        :return: 검색된 Document 리스트
        """
        return self.search(
            query=query,
            k=k,
            category=category,
            sentiment="positive"
        )
    
    def search_negative_reviews(
        self,
        query: str,
        k: int = 5,
        category: Optional[str] = None
    ) -> List[Document]:
        """
        부정적인 리뷰만 검색합니다.
        
        :param query: 검색 쿼리
        :param k: 반환할 결과 수
        :param category: 카테고리 필터
        :return: 검색된 Document 리스트
        """
        return self.search(
            query=query,
            k=k,
            category=category,
            sentiment="negative"
        )
    
    def get_langchain_retriever(
        self,
        k: int = 5,
        category: Optional[str] = None,
        min_rating: Optional[int] = None
    ):
        """
        LangChain 체인에서 사용할 수 있는 Retriever를 반환합니다.
        
        :param k: 반환할 결과 수
        :param category: 카테고리 필터
        :param min_rating: 최소 평점
        :return: LangChain Retriever
        """
        filter_dict = self._build_filter(
            category=category,
            min_rating=min_rating
        )
        
        return self.vectorstore.get_retriever(
            k=k,
            filter=filter_dict if filter_dict else None
        )
    
    def _build_filter(
        self,
        category: Optional[str] = None,
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None,
        sentiment: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Chroma 필터 딕셔너리를 구성합니다.
        
        :return: 필터 딕셔너리 또는 None
        """
        conditions = []
        
        if category:
            conditions.append({"category": category})
        
        if sentiment:
            conditions.append({"sentiment": sentiment})
        
        if product_id:
            conditions.append({"product_id": product_id})
        
        if min_rating is not None:
            conditions.append({"rating": {"$gte": min_rating}})
        
        if max_rating is not None:
            conditions.append({"rating": {"$lte": max_rating}})
        
        if not conditions:
            return None
        
        if len(conditions) == 1:
            return conditions[0]
        
        return {"$and": conditions}
    
    def search_with_rerank(
        self,
        query: str,
        k: int = 5,
        fetch_k: int = 20,
        **filter_kwargs
    ) -> List[Document]:
        """
        Reranker를 사용하여 검색합니다 (Two-Stage Retrieval).
        
        :param query: 검색 쿼리
        :param k: 최종 반환할 문서 수
        :param fetch_k: 1차 검색에서 가져올 문서 수
        :param filter_kwargs: 필터 조건 (category, min_rating 등)
        :return: 재정렬된 Document 리스트
        """
        if not self.reranker:
            from .reranker import KoreanReranker
            self.reranker = KoreanReranker()
        
        return self.search(
            query=query,
            k=k,
            use_reranker=True,
            fetch_k=fetch_k,
            **filter_kwargs
        )
    
    def set_reranker(self, reranker: "KoreanReranker") -> None:
        """Reranker를 설정합니다."""
        self.reranker = reranker
