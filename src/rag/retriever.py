"""
리뷰 검색 모듈

메타데이터 필터링과 함께 리뷰를 검색합니다.
HyDE, MMR, Reranking 등 고급 검색 기법을 지원합니다.
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from .vectorstore import ReviewVectorStore

if TYPE_CHECKING:
    from .reranker import KoreanReranker


class HyDEQueryExpander:
    """
    HyDE (Hypothetical Document Embedding) 쿼리 확장기

    질문을 가상의 리뷰 문서로 변환하여 검색 품질을 향상시킵니다.
    """

    HYDE_PROMPT = """You are a helpful assistant that generates hypothetical product review content.
Given a question about a product, generate a short hypothetical review excerpt (2-3 sentences)
that would answer this question. Write in English as the reviews are in English.

IMPORTANT:
- Focus on the ACTUAL PRODUCT mentioned, not accessories or cases
- If asking about "iPhone design", write about the iPhone itself, not iPhone cases
- If asking about "headphone sound quality", write about headphones, not headphone stands
- Be specific about the product type in your response

Question: {question}

Hypothetical review excerpt:"""

    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)

    def expand_query(self, question: str) -> str:
        """
        질문을 가상의 리뷰 텍스트로 확장합니다.

        :param question: 사용자 질문
        :return: 가상의 리뷰 텍스트
        """
        prompt = self.HYDE_PROMPT.format(question=question)
        response = self.llm.invoke(prompt)
        return response.content


class ReviewRetriever:
    """
    리뷰 검색기

    카테고리, 평점 등 메타데이터 필터링을 지원하는 검색기입니다.
    HyDE, MMR, Reranking 등 고급 검색 기법을 지원합니다.
    """

    def __init__(
        self,
        vectorstore: ReviewVectorStore,
        reranker: Optional["KoreanReranker"] = None,
        use_hyde: bool = False
    ):
        """
        :param vectorstore: ReviewVectorStore 인스턴스
        :param reranker: KoreanReranker 인스턴스 (선택)
        :param use_hyde: HyDE 쿼리 확장 사용 여부
        """
        self.vectorstore = vectorstore
        self.reranker = reranker
        self.use_hyde = use_hyde
        self._hyde_expander: Optional[HyDEQueryExpander] = None

    @property
    def hyde_expander(self) -> HyDEQueryExpander:
        """HyDE 쿼리 확장기 (lazy loading)"""
        if self._hyde_expander is None:
            self._hyde_expander = HyDEQueryExpander()
        return self._hyde_expander
    
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
        use_hyde: Optional[bool] = None,
        use_mmr: bool = False,
        fetch_k: Optional[int] = None,
        mmr_lambda: float = 0.5
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
        :param use_hyde: HyDE 쿼리 확장 사용 여부 (None이면 초기화 시 설정 따름)
        :param use_mmr: MMR(Maximum Marginal Relevance) 사용 여부
        :param fetch_k: 1차 검색에서 가져올 문서 수 (reranker/mmr 사용 시)
        :param mmr_lambda: MMR 다양성 파라미터 (0: 최대 다양성, 1: 최대 관련성)
        :return: 검색된 Document 리스트
        """
        filter_dict = self._build_filter(
            category=category,
            min_rating=min_rating,
            max_rating=max_rating,
            sentiment=sentiment,
            product_id=product_id
        )

        # HyDE 쿼리 확장 적용
        should_use_hyde = use_hyde if use_hyde is not None else self.use_hyde
        search_query = query
        if should_use_hyde:
            search_query = self.hyde_expander.expand_query(query)

        # MMR 검색
        if use_mmr:
            search_k = fetch_k or k * 4
            return self.vectorstore.mmr_search(
                query=search_query,
                k=k,
                fetch_k=search_k,
                lambda_mult=mmr_lambda,
                filter=filter_dict if filter_dict else None
            )

        # Reranker 사용
        if self.reranker and use_reranker:
            search_k = fetch_k or k * 4
            candidates = self.vectorstore.similarity_search(
                query=search_query,
                k=search_k,
                filter=filter_dict if filter_dict else None
            )
            # Rerank는 원본 쿼리로 수행 (HyDE 확장 쿼리가 아닌)
            return self.reranker.rerank(query, candidates, top_n=k)

        return self.vectorstore.similarity_search(
            query=search_query,
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
