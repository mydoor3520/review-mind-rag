"""
리뷰 데이터 전처리 모듈

리뷰 텍스트를 정제하고 LangChain Document 형식으로 변환합니다.
"""

import re
from typing import List, Dict, Iterator, Optional
from langchain_core.documents import Document


class ReviewPreprocessor:
    """
    리뷰 데이터 전처리기
    
    리뷰 텍스트를 정제하고 LangChain Document로 변환합니다.
    """
    
    def __init__(
        self,
        min_length: int = 20,
        max_length: int = 2000,
        remove_html: bool = True,
        remove_urls: bool = True
    ):
        """
        :param min_length: 최소 리뷰 길이 (이보다 짧으면 필터링)
        :param max_length: 최대 리뷰 길이 (이보다 길면 잘라냄)
        :param remove_html: HTML 태그 제거 여부
        :param remove_urls: URL 제거 여부
        """
        self.min_length = min_length
        self.max_length = max_length
        self.remove_html = remove_html
        self.remove_urls = remove_urls
    
    def clean_text(self, text: str) -> str:
        """
        리뷰 텍스트를 정제합니다.
        
        :param text: 원본 텍스트
        :return: 정제된 텍스트
        """
        if not text:
            return ""
        
        # HTML 태그 제거
        if self.remove_html:
            text = re.sub(r'<[^>]+>', '', text)
        
        # URL 제거
        if self.remove_urls:
            text = re.sub(r'http[s]?://\S+', '', text)
        
        # 연속 공백 정리
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        # 최대 길이 제한
        if len(text) > self.max_length:
            text = text[:self.max_length] + "..."
        
        return text
    
    def is_valid_review(self, review: Dict) -> bool:
        """
        리뷰가 유효한지 검사합니다.
        
        :param review: 리뷰 딕셔너리
        :return: 유효 여부
        """
        text = review.get("review_text", "")
        
        # 빈 리뷰 필터링
        if not text:
            return False
        
        # 최소 길이 검사
        if len(text) < self.min_length:
            return False
        
        # 평점이 있는지 검사
        rating = review.get("rating", 0)
        if not rating or rating < 1 or rating > 5:
            return False
        
        return True
    
    def review_to_document(self, review: Dict) -> Document:
        """
        리뷰를 LangChain Document로 변환합니다.

        :param review: 리뷰 딕셔너리
        :return: LangChain Document
        """
        # 텍스트 정제
        clean_review_text = self.clean_text(review.get("review_text", ""))

        # 메타데이터 구성
        metadata = {
            "review_id": review.get("review_id", ""),
            "product_id": review.get("product_id", ""),
            "product_name": review.get("product_name", "Unknown Product"),
            "brand": review.get("brand", ""),
            "price": review.get("price"),
            "category": review.get("category", ""),
            "review_title": review.get("review_title", ""),
            "rating": review.get("rating", 0),
            "helpful_votes": review.get("helpful_votes", 0),
            "verified_purchase": review.get("verified_purchase", False),
            "sentiment": self._get_sentiment(review.get("rating", 0)),
        }

        # Document 생성
        return Document(
            page_content=clean_review_text,
            metadata=metadata
        )
    
    def process_reviews(
        self,
        reviews: Iterator[Dict],
        limit: Optional[int] = None
    ) -> Iterator[Document]:
        """
        리뷰 스트림을 처리하여 Document 스트림으로 변환합니다.
        
        :param reviews: 리뷰 딕셔너리 이터레이터
        :param limit: 처리할 최대 리뷰 수
        :return: Document 이터레이터
        """
        count = 0
        for review in reviews:
            if limit and count >= limit:
                break
            
            # 유효성 검사
            if not self.is_valid_review(review):
                continue
            
            # Document로 변환
            yield self.review_to_document(review)
            count += 1
    
    def _get_sentiment(self, rating: int) -> str:
        """
        평점을 기반으로 감성을 결정합니다.
        
        :param rating: 평점 (1-5)
        :return: 감성 레이블 (positive, negative, neutral)
        """
        if rating >= 4:
            return "positive"
        elif rating <= 2:
            return "negative"
        else:
            return "neutral"
    
    def get_stats(self, reviews: List[Dict]) -> Dict:
        """
        리뷰 통계를 계산합니다.
        
        :param reviews: 리뷰 리스트
        :return: 통계 딕셔너리
        """
        total = len(reviews)
        valid = sum(1 for r in reviews if self.is_valid_review(r))
        
        ratings = [r.get("rating", 0) for r in reviews if r.get("rating")]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        categories = {}
        for r in reviews:
            cat = r.get("category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_reviews": total,
            "valid_reviews": valid,
            "invalid_reviews": total - valid,
            "average_rating": round(avg_rating, 2),
            "category_distribution": categories,
        }
