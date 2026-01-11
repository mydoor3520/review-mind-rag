"""
RAG Chain 모듈

LangChain을 사용하여 리뷰 기반 QA 체인을 구성합니다.
"""

from typing import Optional, Dict, Any, List
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_classic.chains import RetrievalQA
from langchain_openai import ChatOpenAI

from .retriever import ReviewRetriever
from .vectorstore import ReviewVectorStore


class ReviewQAChain:
    """
    리뷰 기반 QA 체인
    
    RAG 파이프라인을 사용하여 리뷰 기반 질문에 답변합니다.
    """
    
    DEFAULT_QA_PROMPT = """다음은 상품 리뷰들입니다. 이 리뷰들을 바탕으로 질문에 답변해주세요.

리뷰:
{context}

질문: {question}

답변 시 주의사항:
- 리뷰에 있는 정보만 사용하세요
- 구체적인 수치나 의견을 인용하세요
- 리뷰에 없는 내용은 "리뷰에서 해당 정보를 찾을 수 없습니다"라고 답하세요
- 한국어로 답변해주세요

답변:"""

    DEFAULT_CONVERSATIONAL_PROMPT = """당신은 상품 리뷰 분석 전문가입니다.
사용자의 질문에 리뷰 데이터를 기반으로 답변해주세요.

이전 대화:
{chat_history}

관련 리뷰:
{context}

현재 질문: {question}

답변 시 주의사항:
- 이전 대화의 맥락을 고려하세요
- 리뷰에 있는 정보만 사용하세요
- 구체적인 수치나 의견을 인용하세요
- "그 제품", "위에서 언급한" 등 이전 대화를 참조할 수 있습니다
- 한국어로 답변해주세요

답변:"""

    DEFAULT_SUMMARY_PROMPT = """다음 상품 리뷰들을 분석하여 요약해주세요.

리뷰:
{reviews}

다음 형식으로 한국어로 요약해주세요:

## 장점
- (리뷰에서 자주 언급되는 긍정적인 점들)

## 단점
- (리뷰에서 자주 언급되는 부정적인 점들)

## 종합 평가
(전반적인 평가와 추천 여부)
"""

    def __init__(
        self,
        vectorstore: ReviewVectorStore,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.3,
        qa_prompt: Optional[str] = None,
        use_reranker: bool = True,
        use_hyde: bool = True
    ):
        """
        :param vectorstore: ReviewVectorStore 인스턴스
        :param model_name: OpenAI 모델 이름
        :param temperature: 생성 temperature
        :param qa_prompt: 커스텀 QA 프롬프트
        :param use_reranker: Reranker 사용 여부 (기본: True)
        :param use_hyde: HyDE 쿼리 확장 사용 여부 (기본: True)
        """
        self.vectorstore = vectorstore
        self.use_reranker = use_reranker
        self.use_hyde = use_hyde

        reranker = None
        if use_reranker:
            try:
                from .reranker import KoreanReranker
                reranker = KoreanReranker()
            except ImportError:
                pass

        self.retriever = ReviewRetriever(
            vectorstore,
            reranker=reranker,
            use_hyde=use_hyde
        )
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature
        )
        
        # QA 프롬프트
        self.qa_prompt = PromptTemplate(
            template=qa_prompt or self.DEFAULT_QA_PROMPT,
            input_variables=["context", "question"]
        )
        
        # QA 체인 (lazy initialization)
        self._qa_chain = None
    
    @property
    def qa_chain(self) -> RetrievalQA:
        """QA 체인 반환 (없으면 생성)"""
        if self._qa_chain is None:
            self._qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.retriever.get_langchain_retriever(),
                chain_type_kwargs={"prompt": self.qa_prompt},
                return_source_documents=True
            )
        return self._qa_chain
    
    def ask(
        self,
        question: str,
        category: Optional[str] = None,
        product_id: Optional[str] = None,
        min_rating: Optional[int] = None,
        use_reranker: Optional[bool] = None,
        use_hyde: Optional[bool] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        질문에 대해 리뷰 기반 답변을 생성합니다.

        :param question: 사용자 질문
        :param category: 카테고리 필터
        :param product_id: 상품 ID 필터
        :param min_rating: 최소 평점 필터
        :param use_reranker: Reranker 사용 여부 (None이면 초기화 시 설정 따름)
        :param use_hyde: HyDE 쿼리 확장 사용 여부 (None이면 초기화 시 설정 따름)
        :param chat_history: 이전 대화 히스토리 [{"role": "user/assistant", "content": "..."}]
        :return: 답변과 소스 문서
        """
        should_rerank = use_reranker if use_reranker is not None else self.use_reranker
        should_use_hyde = use_hyde if use_hyde is not None else self.use_hyde

        # 대화 맥락이 있으면 검색 쿼리 확장
        search_query = question
        if chat_history:
            # 최근 대화에서 맥락 추출하여 검색 쿼리에 추가
            search_query = self._build_contextual_query(question, chat_history)

        # 고급 검색 사용 (HyDE + Reranker)
        source_docs = self.retriever.search(
            query=search_query,
            k=5,
            fetch_k=20,
            category=category,
            min_rating=min_rating,
            product_id=product_id,
            use_reranker=should_rerank,
            use_hyde=should_use_hyde
        )

        # 컨텍스트 구성 (상품명 포함, fallback: product_id)
        context = "\n\n---\n\n".join([
            f"[상품: {self._get_product_display_name(doc)[:50]}] "
            f"[평점: {doc.metadata.get('rating', 'N/A')}점]\n{doc.page_content}"
            for doc in source_docs
        ])

        # 대화 히스토리가 있으면 대화형 프롬프트 사용
        if chat_history:
            history_text = self._format_chat_history(chat_history)
            prompt_text = self.DEFAULT_CONVERSATIONAL_PROMPT.format(
                chat_history=history_text,
                context=context,
                question=question
            )
        else:
            prompt_text = self.qa_prompt.format(context=context, question=question)

        response = self.llm.invoke(prompt_text)

        return {
            "answer": response.content,
            "source_documents": source_docs,
            "question": question
        }

    def _format_chat_history(
        self,
        chat_history: List[Dict[str, str]],
        max_turns: int = 5
    ) -> str:
        """대화 히스토리를 텍스트로 포맷합니다."""
        # 최근 N개 턴만 사용
        recent_history = chat_history[-(max_turns * 2):]

        formatted = []
        for msg in recent_history:
            role = "사용자" if msg["role"] == "user" else "AI"
            content = msg["content"][:500]  # 길이 제한
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted) if formatted else "(이전 대화 없음)"

    def _build_contextual_query(
        self,
        question: str,
        chat_history: List[Dict[str, str]]
    ) -> str:
        """대화 맥락을 포함한 검색 쿼리를 생성합니다."""
        if not chat_history:
            return question

        # 최근 사용자 질문에서 주제 추출
        recent_topics = []
        for msg in chat_history[-6:]:  # 최근 3턴
            if msg["role"] == "user":
                recent_topics.append(msg["content"])

        if not recent_topics:
            return question

        # LLM을 사용하여 맥락 기반 쿼리 생성
        context_prompt = f"""이전 대화의 주제를 고려하여 현재 질문에 대한 검색 쿼리를 생성하세요.

이전 질문들:
{chr(10).join(f'- {q}' for q in recent_topics[-3:])}

현재 질문: {question}

규칙:
- 현재 질문이 이전 주제와 연관된 경우, 주제를 포함한 검색 쿼리를 생성
- 현재 질문이 완전히 새로운 주제인 경우, 현재 질문만 반환
- 검색 쿼리만 출력 (설명 없이)

검색 쿼리:"""

        try:
            response = self.llm.invoke(context_prompt)
            expanded_query = response.content.strip()
            # 너무 길면 자르기
            if len(expanded_query) > 200:
                expanded_query = expanded_query[:200]
            return expanded_query
        except Exception:
            # 실패 시 기본 동작: 최근 주제 + 현재 질문
            last_topic = recent_topics[-1] if recent_topics else ""
            # 간단한 키워드 추출 (첫 몇 단어)
            topic_keywords = " ".join(last_topic.split()[:5])
            return f"{question} {topic_keywords}"

    def _get_product_display_name(self, doc) -> str:
        """
        문서에서 표시할 상품명을 결정합니다.
        Fallback 체인: product_name → product_id → 'Unknown'
        """
        product_name = doc.metadata.get("product_name", "")
        product_id = doc.metadata.get("product_id", "")

        # product_name이 유효하면 사용
        if product_name and product_name not in ("Unknown Product", "Unknown", ""):
            return product_name

        # product_id(ASIN)가 있으면 표시
        if product_id:
            return f"Product ({product_id})"

        return "Unknown"

    def summarize_product(
        self,
        product_id: str,
        max_reviews: int = 20
    ) -> Dict[str, Any]:
        """
        특정 상품의 리뷰를 요약합니다.
        
        :param product_id: 상품 ID
        :param max_reviews: 요약에 사용할 최대 리뷰 수
        :return: 요약 결과
        """
        # 상품 리뷰 검색
        reviews = self.retriever.search_by_product(
            product_id=product_id,
            k=max_reviews
        )
        
        if not reviews:
            return {
                "summary": "해당 상품의 리뷰를 찾을 수 없습니다.",
                "review_count": 0
            }
        
        # 리뷰 텍스트 합치기
        reviews_text = "\n\n---\n\n".join([
            f"[평점: {doc.metadata.get('rating', 'N/A')}점]\n{doc.page_content}"
            for doc in reviews
        ])
        
        # 요약 생성
        prompt = self.DEFAULT_SUMMARY_PROMPT.format(reviews=reviews_text)
        response = self.llm.invoke(prompt)
        
        return {
            "summary": response.content,
            "review_count": len(reviews),
            "product_id": product_id
        }
    
    def compare_products(
        self,
        product_id_1: str,
        product_id_2: str,
        max_reviews_per_product: int = 10
    ) -> Dict[str, Any]:
        """
        두 상품의 리뷰를 비교합니다.
        
        :param product_id_1: 첫 번째 상품 ID
        :param product_id_2: 두 번째 상품 ID
        :param max_reviews_per_product: 상품당 최대 리뷰 수
        :return: 비교 결과
        """
        # 각 상품 요약
        summary_1 = self.summarize_product(product_id_1, max_reviews_per_product)
        summary_2 = self.summarize_product(product_id_2, max_reviews_per_product)
        
        # 비교 프롬프트
        compare_prompt = f"""다음 두 상품의 리뷰 요약을 비교해주세요.

## 상품 1
{summary_1['summary']}

## 상품 2
{summary_2['summary']}

다음 형식으로 비교해주세요:

## 비교 분석
- 상품 1의 강점:
- 상품 2의 강점:
- 주요 차이점:

## 추천
(어떤 사용자에게 어떤 상품이 더 적합한지)
"""
        
        response = self.llm.invoke(compare_prompt)
        
        return {
            "comparison": response.content,
            "product_1": summary_1,
            "product_2": summary_2
        }
