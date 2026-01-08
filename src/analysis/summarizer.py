"""
리뷰 요약 모듈

LLM을 사용하여 리뷰를 요약합니다.
"""

from typing import List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.schema import Document


class ReviewSummarizer:
    """
    리뷰 요약 생성기
    
    LLM을 사용하여 리뷰 요약, 장단점 추출 등을 수행합니다.
    """
    
    DEFAULT_SUMMARY_PROMPT = """다음 상품 리뷰들을 분석하여 요약해주세요.

리뷰:
{reviews}

다음 형식으로 한국어로 요약해주세요:

## 장점
- (리뷰에서 자주 언급되는 긍정적인 점들, 3-5개)

## 단점
- (리뷰에서 자주 언급되는 부정적인 점들, 3-5개)

## 자주 언급되는 키워드
- (리뷰에서 반복적으로 나타나는 주요 키워드들)

## 종합 평가
(전반적인 평가와 어떤 사용자에게 추천하는지)
"""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.3
    ):
        """
        :param model_name: OpenAI 모델 이름
        :param temperature: 생성 temperature
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature
        )
    
    def summarize(
        self,
        documents: List[Document],
        max_reviews: int = 20,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        리뷰 문서들을 요약합니다.
        
        :param documents: LangChain Document 리스트
        :param max_reviews: 요약에 사용할 최대 리뷰 수
        :param custom_prompt: 커스텀 프롬프트
        :return: 요약 결과
        """
        if not documents:
            return {
                "summary": "요약할 리뷰가 없습니다.",
                "review_count": 0
            }
        
        # 리뷰 수 제한
        docs_to_use = documents[:max_reviews]
        
        # 리뷰 텍스트 합치기
        reviews_text = "\n\n---\n\n".join([
            f"[평점: {doc.metadata.get('rating', 'N/A')}점]\n{doc.page_content}"
            for doc in docs_to_use
        ])
        
        # 프롬프트 구성
        prompt = (custom_prompt or self.DEFAULT_SUMMARY_PROMPT).format(
            reviews=reviews_text
        )
        
        # LLM 호출
        response = self.llm.invoke(prompt)
        
        return {
            "summary": response.content,
            "review_count": len(docs_to_use),
            "total_available": len(documents)
        }
    
    def extract_pros_cons(
        self,
        documents: List[Document],
        max_reviews: int = 15
    ) -> Dict[str, List[str]]:
        """
        리뷰에서 장단점을 추출합니다.
        
        :param documents: LangChain Document 리스트
        :param max_reviews: 분석할 최대 리뷰 수
        :return: 장단점 리스트
        """
        if not documents:
            return {"pros": [], "cons": []}
        
        docs_to_use = documents[:max_reviews]
        
        reviews_text = "\n\n".join([
            f"[{doc.metadata.get('rating', 3)}점] {doc.page_content[:300]}"
            for doc in docs_to_use
        ])
        
        prompt = f"""다음 리뷰들에서 장점과 단점을 추출해주세요.

리뷰:
{reviews_text}

JSON 형식으로 응답해주세요:
{{
    "pros": ["장점1", "장점2", "장점3"],
    "cons": ["단점1", "단점2", "단점3"]
}}

중요: 반드시 위 JSON 형식만 출력하세요. 다른 텍스트는 포함하지 마세요.
"""
        
        response = self.llm.invoke(prompt)
        
        # JSON 파싱 시도
        try:
            import json
            result = json.loads(response.content)
            return {
                "pros": result.get("pros", []),
                "cons": result.get("cons", [])
            }
        except json.JSONDecodeError:
            # 파싱 실패 시 기본값 반환
            return {
                "pros": ["파싱 오류 - 원본 응답을 확인하세요"],
                "cons": [response.content[:200]]
            }
    
    def generate_one_liner(
        self,
        documents: List[Document],
        max_reviews: int = 10
    ) -> str:
        """
        한 줄 요약을 생성합니다.
        
        :param documents: LangChain Document 리스트
        :param max_reviews: 분석할 최대 리뷰 수
        :return: 한 줄 요약
        """
        if not documents:
            return "리뷰가 없습니다."
        
        docs_to_use = documents[:max_reviews]
        avg_rating = sum(
            doc.metadata.get("rating", 3) for doc in docs_to_use
        ) / len(docs_to_use)
        
        reviews_text = " | ".join([
            doc.page_content[:100] for doc in docs_to_use[:5]
        ])
        
        prompt = f"""다음 리뷰들을 한 문장으로 요약해주세요 (30자 이내).

평균 평점: {avg_rating:.1f}점
리뷰 샘플: {reviews_text}

한 줄 요약:"""
        
        response = self.llm.invoke(prompt)
        return response.content.strip()
