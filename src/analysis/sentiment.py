"""
감성 분석 모듈

리뷰의 감성을 분석합니다.
"""

from typing import List, Dict, Any
from collections import Counter
from langchain_core.documents import Document


class SentimentAnalyzer:
    """
    리뷰 감성 분석기
    
    평점 기반 감성 분류 및 통계를 제공합니다.
    """
    
    SENTIMENT_LABELS = {
        "positive": "긍정",
        "negative": "부정",
        "neutral": "중립"
    }
    
    SENTIMENT_COLORS = {
        "positive": "#4CAF50",  # 녹색
        "negative": "#F44336",  # 빨간색
        "neutral": "#FFC107"    # 노란색
    }
    
    def __init__(self):
        pass
    
    def get_sentiment_from_rating(self, rating: int) -> str:
        """
        평점에서 감성을 추출합니다.
        
        :param rating: 평점 (1-5)
        :return: 감성 레이블
        """
        if rating >= 4:
            return "positive"
        elif rating <= 2:
            return "negative"
        else:
            return "neutral"
    
    def analyze_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """
        문서 리스트의 감성을 분석합니다.
        
        :param documents: LangChain Document 리스트
        :return: 감성 분석 결과
        """
        sentiments = []
        ratings = []
        
        for doc in documents:
            sentiment = doc.metadata.get("sentiment", "neutral")
            rating = doc.metadata.get("rating", 3)
            
            sentiments.append(sentiment)
            ratings.append(rating)
        
        # 감성 분포 계산
        sentiment_counts = Counter(sentiments)
        total = len(sentiments)
        
        distribution = {
            label: {
                "count": sentiment_counts.get(label, 0),
                "percentage": round(sentiment_counts.get(label, 0) / total * 100, 1) if total > 0 else 0,
                "label_kr": self.SENTIMENT_LABELS.get(label, label),
                "color": self.SENTIMENT_COLORS.get(label, "#999999")
            }
            for label in ["positive", "neutral", "negative"]
        }
        
        # 평균 평점
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        dominant = "neutral"
        if sentiment_counts:
            dominant = max(sentiment_counts.keys(), key=lambda k: sentiment_counts[k])
        
        return {
            "total_reviews": total,
            "average_rating": round(avg_rating, 2),
            "distribution": distribution,
            "dominant_sentiment": dominant
        }
    
    def get_sentiment_summary(self, analysis: Dict[str, Any]) -> str:
        """
        감성 분석 결과를 텍스트 요약으로 반환합니다.
        
        :param analysis: analyze_documents 결과
        :return: 요약 텍스트
        """
        dist = analysis["distribution"]
        dominant = analysis["dominant_sentiment"]
        
        summary_parts = [
            f"총 {analysis['total_reviews']}개 리뷰 분석 결과:",
            f"- 평균 평점: {analysis['average_rating']}점",
            f"- 긍정: {dist['positive']['percentage']}%",
            f"- 중립: {dist['neutral']['percentage']}%",
            f"- 부정: {dist['negative']['percentage']}%",
            f"- 전반적 감성: {self.SENTIMENT_LABELS[dominant]}"
        ]
        
        return "\n".join(summary_parts)
    
    def get_chart_data(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        차트 시각화용 데이터를 반환합니다.
        
        :param analysis: analyze_documents 결과
        :return: 차트 데이터
        """
        dist = analysis["distribution"]
        
        # Pie 차트용 데이터
        pie_data = {
            "labels": [dist[s]["label_kr"] for s in ["positive", "neutral", "negative"]],
            "values": [dist[s]["count"] for s in ["positive", "neutral", "negative"]],
            "colors": [dist[s]["color"] for s in ["positive", "neutral", "negative"]]
        }
        
        return {
            "pie": pie_data,
            "average_rating": analysis["average_rating"],
            "total_reviews": analysis["total_reviews"]
        }
