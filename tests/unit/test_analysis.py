"""
SentimentAnalyzer, ReviewSummarizer 단위 테스트

분석 모듈의 단위 테스트입니다.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from langchain_core.documents import Document


# =============================================================================
# SentimentAnalyzer 테스트
# =============================================================================

class TestSentimentAnalyzerGetSentimentFromRating:
    """get_sentiment_from_rating() 메서드 테스트"""

    def test_평점_5점_positive(self):
        """평점 5점은 positive로 분류된다"""
        # given
        from src.analysis.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        # when
        result = analyzer.get_sentiment_from_rating(5)

        # then
        assert result == "positive"

    def test_평점_4점_positive(self):
        """평점 4점은 positive로 분류된다"""
        # given
        from src.analysis.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        # when
        result = analyzer.get_sentiment_from_rating(4)

        # then
        assert result == "positive"

    def test_평점_3점_neutral(self):
        """평점 3점은 neutral로 분류된다"""
        # given
        from src.analysis.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        # when
        result = analyzer.get_sentiment_from_rating(3)

        # then
        assert result == "neutral"

    def test_평점_2점_negative(self):
        """평점 2점은 negative로 분류된다"""
        # given
        from src.analysis.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        # when
        result = analyzer.get_sentiment_from_rating(2)

        # then
        assert result == "negative"

    def test_평점_1점_negative(self):
        """평점 1점은 negative로 분류된다"""
        # given
        from src.analysis.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        # when
        result = analyzer.get_sentiment_from_rating(1)

        # then
        assert result == "negative"


class TestSentimentAnalyzerAnalyzeDocuments:
    """analyze_documents() 메서드 테스트"""

    @pytest.fixture
    def sample_documents(self):
        """테스트용 Document 리스트"""
        return [
            Document(page_content="좋아요", metadata={"rating": 5, "sentiment": "positive"}),
            Document(page_content="좋아요", metadata={"rating": 4, "sentiment": "positive"}),
            Document(page_content="보통", metadata={"rating": 3, "sentiment": "neutral"}),
            Document(page_content="별로", metadata={"rating": 2, "sentiment": "negative"}),
            Document(page_content="최악", metadata={"rating": 1, "sentiment": "negative"}),
        ]

    def test_감성_분포_계산(self, sample_documents):
        """감성 분포를 올바르게 계산한다"""
        # given
        from src.analysis.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        # when
        result = analyzer.analyze_documents(sample_documents)

        # then
        assert result["total_reviews"] == 5
        assert result["distribution"]["positive"]["count"] == 2
        assert result["distribution"]["neutral"]["count"] == 1
        assert result["distribution"]["negative"]["count"] == 2

    def test_평균_평점_계산(self, sample_documents):
        """평균 평점을 올바르게 계산한다"""
        # given
        from src.analysis.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        # when
        result = analyzer.analyze_documents(sample_documents)

        # then
        # (5+4+3+2+1) / 5 = 3.0
        assert result["average_rating"] == 3.0

    def test_지배적_감성_판단(self, sample_documents):
        """지배적 감성을 올바르게 판단한다"""
        # given
        from src.analysis.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        
        # positive가 3개로 가장 많은 경우
        positive_docs = [
            Document(page_content="좋아요", metadata={"rating": 5, "sentiment": "positive"}),
            Document(page_content="좋아요", metadata={"rating": 5, "sentiment": "positive"}),
            Document(page_content="좋아요", metadata={"rating": 5, "sentiment": "positive"}),
            Document(page_content="별로", metadata={"rating": 2, "sentiment": "negative"}),
        ]

        # when
        result = analyzer.analyze_documents(positive_docs)

        # then
        assert result["dominant_sentiment"] == "positive"

    def test_빈_문서_리스트(self):
        """빈 문서 리스트를 처리한다"""
        # given
        from src.analysis.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()

        # when
        result = analyzer.analyze_documents([])

        # then
        assert result["total_reviews"] == 0
        assert result["average_rating"] == 0


class TestSentimentAnalyzerGetSentimentSummary:
    """get_sentiment_summary() 메서드 테스트"""

    def test_요약_텍스트_생성(self):
        """감성 분석 요약 텍스트를 생성한다"""
        # given
        from src.analysis.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        
        analysis = {
            "total_reviews": 10,
            "average_rating": 4.2,
            "distribution": {
                "positive": {"percentage": 60.0},
                "neutral": {"percentage": 20.0},
                "negative": {"percentage": 20.0},
            },
            "dominant_sentiment": "positive"
        }

        # when
        result = analyzer.get_sentiment_summary(analysis)

        # then
        assert "10개 리뷰" in result
        assert "4.2점" in result
        assert "60.0%" in result


class TestSentimentAnalyzerGetChartData:
    """get_chart_data() 메서드 테스트"""

    def test_차트_데이터_생성(self):
        """차트 시각화용 데이터를 생성한다"""
        # given
        from src.analysis.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        
        analysis = {
            "total_reviews": 10,
            "average_rating": 4.0,
            "distribution": {
                "positive": {"count": 6, "label_kr": "긍정", "color": "#4CAF50"},
                "neutral": {"count": 2, "label_kr": "중립", "color": "#FFC107"},
                "negative": {"count": 2, "label_kr": "부정", "color": "#F44336"},
            }
        }

        # when
        result = analyzer.get_chart_data(analysis)

        # then
        assert "pie" in result
        assert len(result["pie"]["labels"]) == 3
        assert len(result["pie"]["values"]) == 3
        assert len(result["pie"]["colors"]) == 3


# =============================================================================
# ReviewSummarizer 테스트
# =============================================================================

class TestReviewSummarizerInit:
    """초기화 테스트"""

    def test_기본_초기화(self):
        """기본 파라미터로 초기화된다"""
        # given
        from src.analysis.summarizer import ReviewSummarizer
        
        with patch('src.analysis.summarizer.ChatOpenAI'):
            # when
            summarizer = ReviewSummarizer()

            # then
            assert summarizer.llm is not None

    def test_커스텀_모델_설정(self):
        """커스텀 모델을 설정할 수 있다"""
        # given
        from src.analysis.summarizer import ReviewSummarizer
        
        with patch('src.analysis.summarizer.ChatOpenAI') as mock_llm:
            # when
            summarizer = ReviewSummarizer(
                model_name="gpt-4",
                temperature=0.5
            )

            # then
            mock_llm.assert_called_once_with(
                model="gpt-4",
                temperature=0.5
            )


class TestReviewSummarizerSummarize:
    """summarize() 메서드 테스트"""

    @pytest.fixture
    def sample_documents(self):
        """테스트용 Document 리스트"""
        return [
            Document(page_content="음질이 좋습니다", metadata={"rating": 5}),
            Document(page_content="배터리가 오래가요", metadata={"rating": 4}),
            Document(page_content="가격이 비쌉니다", metadata={"rating": 3}),
        ]

    def test_요약_생성(self, sample_documents):
        """리뷰 요약을 생성한다"""
        # given
        from src.analysis.summarizer import ReviewSummarizer
        
        with patch('src.analysis.summarizer.ChatOpenAI') as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(
                content="## 장점\n- 음질이 좋음\n## 단점\n- 가격이 비쌈"
            )
            mock_llm_class.return_value = mock_llm
            
            summarizer = ReviewSummarizer()

            # when
            result = summarizer.summarize(sample_documents)

            # then
            assert "summary" in result
            assert result["review_count"] == 3
            assert "장점" in result["summary"]

    def test_빈_문서_리스트(self):
        """빈 문서 리스트를 처리한다"""
        # given
        from src.analysis.summarizer import ReviewSummarizer
        
        with patch('src.analysis.summarizer.ChatOpenAI'):
            summarizer = ReviewSummarizer()

            # when
            result = summarizer.summarize([])

            # then
            assert result["review_count"] == 0
            assert "없습니다" in result["summary"]

    def test_max_reviews_제한(self, sample_documents):
        """max_reviews 파라미터가 적용된다"""
        # given
        from src.analysis.summarizer import ReviewSummarizer
        
        with patch('src.analysis.summarizer.ChatOpenAI') as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(content="요약")
            mock_llm_class.return_value = mock_llm
            
            summarizer = ReviewSummarizer()

            # when
            result = summarizer.summarize(sample_documents, max_reviews=2)

            # then
            assert result["review_count"] == 2
            assert result["total_available"] == 3


class TestReviewSummarizerExtractProsCons:
    """extract_pros_cons() 메서드 테스트"""

    @pytest.fixture
    def sample_documents(self):
        """테스트용 Document 리스트"""
        return [
            Document(page_content="음질이 좋습니다", metadata={"rating": 5}),
            Document(page_content="가격이 비쌉니다", metadata={"rating": 2}),
        ]

    def test_장단점_추출(self, sample_documents):
        """장단점을 추출한다"""
        # given
        from src.analysis.summarizer import ReviewSummarizer
        
        with patch('src.analysis.summarizer.ChatOpenAI') as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(
                content='{"pros": ["음질이 좋음"], "cons": ["가격이 비쌈"]}'
            )
            mock_llm_class.return_value = mock_llm
            
            summarizer = ReviewSummarizer()

            # when
            result = summarizer.extract_pros_cons(sample_documents)

            # then
            assert "pros" in result
            assert "cons" in result
            assert len(result["pros"]) > 0
            assert len(result["cons"]) > 0

    def test_빈_문서_리스트(self):
        """빈 문서 리스트를 처리한다"""
        # given
        from src.analysis.summarizer import ReviewSummarizer
        
        with patch('src.analysis.summarizer.ChatOpenAI'):
            summarizer = ReviewSummarizer()

            # when
            result = summarizer.extract_pros_cons([])

            # then
            assert result["pros"] == []
            assert result["cons"] == []


class TestReviewSummarizerGenerateOneLiner:
    """generate_one_liner() 메서드 테스트"""

    @pytest.fixture
    def sample_documents(self):
        """테스트용 Document 리스트"""
        return [
            Document(page_content="좋은 제품입니다", metadata={"rating": 5}),
            Document(page_content="추천합니다", metadata={"rating": 4}),
        ]

    def test_한줄_요약_생성(self, sample_documents):
        """한 줄 요약을 생성한다"""
        # given
        from src.analysis.summarizer import ReviewSummarizer
        
        with patch('src.analysis.summarizer.ChatOpenAI') as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(
                content="만족도 높은 제품"
            )
            mock_llm_class.return_value = mock_llm
            
            summarizer = ReviewSummarizer()

            # when
            result = summarizer.generate_one_liner(sample_documents)

            # then
            assert isinstance(result, str)
            assert len(result) > 0

    def test_빈_문서_리스트(self):
        """빈 문서 리스트를 처리한다"""
        # given
        from src.analysis.summarizer import ReviewSummarizer
        
        with patch('src.analysis.summarizer.ChatOpenAI'):
            summarizer = ReviewSummarizer()

            # when
            result = summarizer.generate_one_liner([])

            # then
            assert "없습니다" in result
