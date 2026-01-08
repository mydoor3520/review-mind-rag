"""
ReviewPreprocessor 단위 테스트

리뷰 데이터 전처리 모듈의 테스트 코드입니다.
"""

import pytest
from src.data.preprocessor import ReviewPreprocessor


class TestReviewPreprocessorCleanText:
    """clean_text() 메서드 테스트"""

    def test_HTML태그_제거(self, sample_review_with_html):
        """HTML 태그가 포함된 텍스트에서 태그를 제거한다"""
        # given
        preprocessor = ReviewPreprocessor()
        text = sample_review_with_html["review_text"]

        # when
        result = preprocessor.clean_text(text)

        # then
        assert "<p>" not in result
        assert "<strong>" not in result
        assert "</p>" not in result
        assert "<br/>" not in result
        assert "좋은" in result
        assert "제품" in result

    def test_URL_제거(self, sample_review_with_url):
        """URL이 포함된 텍스트에서 URL을 제거한다"""
        # given
        preprocessor = ReviewPreprocessor()
        text = sample_review_with_url["review_text"]

        # when
        result = preprocessor.clean_text(text)

        # then
        assert "https://" not in result
        assert "example.com" not in result
        assert "정말 좋아요" in result

    def test_연속_공백_정리(self):
        """연속된 공백을 하나로 정리한다"""
        # given
        preprocessor = ReviewPreprocessor()
        text = "좋은    제품입니다.    추천해요."

        # when
        result = preprocessor.clean_text(text)

        # then
        assert "    " not in result
        assert "좋은 제품입니다. 추천해요." == result

    def test_앞뒤_공백_제거(self):
        """텍스트 앞뒤의 공백을 제거한다"""
        # given
        preprocessor = ReviewPreprocessor()
        text = "   좋은 제품입니다.   "

        # when
        result = preprocessor.clean_text(text)

        # then
        assert result == "좋은 제품입니다."

    def test_최대_길이_제한(self):
        """최대 길이를 초과하는 텍스트를 잘라낸다"""
        # given
        preprocessor = ReviewPreprocessor(max_length=20)
        text = "이 제품은 정말 좋습니다. 강력히 추천합니다!"

        # when
        result = preprocessor.clean_text(text)

        # then
        assert len(result) <= 23  # 20 + "..." = 23
        assert result.endswith("...")

    def test_빈_텍스트_처리(self):
        """빈 텍스트를 처리한다"""
        # given
        preprocessor = ReviewPreprocessor()

        # when
        result = preprocessor.clean_text("")

        # then
        assert result == ""

    def test_None_텍스트_처리(self):
        """None 텍스트를 처리한다"""
        # given
        preprocessor = ReviewPreprocessor()

        # when
        result = preprocessor.clean_text(None)

        # then
        assert result == ""


class TestReviewPreprocessorIsValidReview:
    """is_valid_review() 메서드 테스트"""

    def test_유효한_리뷰_True_반환(self, sample_review):
        """유효한 리뷰는 True를 반환한다"""
        # given
        preprocessor = ReviewPreprocessor(min_length=10)

        # when
        result = preprocessor.is_valid_review(sample_review)

        # then
        assert result is True

    def test_빈_리뷰_텍스트_False_반환(self):
        """빈 리뷰 텍스트는 False를 반환한다"""
        # given
        preprocessor = ReviewPreprocessor()
        review = {"review_text": "", "rating": 5}

        # when
        result = preprocessor.is_valid_review(review)

        # then
        assert result is False

    def test_최소_길이_미달_False_반환(self):
        """최소 길이 미만의 리뷰는 False를 반환한다"""
        # given
        preprocessor = ReviewPreprocessor(min_length=20)
        review = {"review_text": "짧은 리뷰", "rating": 5}

        # when
        result = preprocessor.is_valid_review(review)

        # then
        assert result is False

    def test_평점_없음_False_반환(self):
        """평점이 없는 리뷰는 False를 반환한다"""
        # given
        preprocessor = ReviewPreprocessor()
        review = {"review_text": "이 제품은 정말 좋습니다.", "rating": None}

        # when
        result = preprocessor.is_valid_review(review)

        # then
        assert result is False

    def test_평점_범위_초과_False_반환(self):
        """평점이 1-5 범위를 벗어나면 False를 반환한다"""
        # given
        preprocessor = ReviewPreprocessor()
        review = {"review_text": "이 제품은 정말 좋습니다.", "rating": 6}

        # when
        result = preprocessor.is_valid_review(review)

        # then
        assert result is False

    def test_평점_0_False_반환(self):
        """평점이 0인 리뷰는 False를 반환한다"""
        # given
        preprocessor = ReviewPreprocessor()
        review = {"review_text": "이 제품은 정말 좋습니다.", "rating": 0}

        # when
        result = preprocessor.is_valid_review(review)

        # then
        assert result is False


class TestReviewPreprocessorReviewToDocument:
    """review_to_document() 메서드 테스트"""

    def test_Document_객체_생성(self, sample_review):
        """리뷰를 Document 객체로 변환한다"""
        # given
        preprocessor = ReviewPreprocessor()

        # when
        document = preprocessor.review_to_document(sample_review)

        # then
        assert document is not None
        assert document.page_content is not None
        assert len(document.page_content) > 0

    def test_메타데이터_포함(self, sample_review):
        """Document에 메타데이터가 포함된다"""
        # given
        preprocessor = ReviewPreprocessor()

        # when
        document = preprocessor.review_to_document(sample_review)

        # then
        metadata = document.metadata
        assert metadata["review_id"] == sample_review["review_id"]
        assert metadata["product_id"] == sample_review["product_id"]
        assert metadata["category"] == sample_review["category"]
        assert metadata["rating"] == sample_review["rating"]

    def test_감성_분류_포함(self, sample_review):
        """Document 메타데이터에 감성 분류가 포함된다"""
        # given
        preprocessor = ReviewPreprocessor()

        # when
        document = preprocessor.review_to_document(sample_review)

        # then
        assert "sentiment" in document.metadata
        assert document.metadata["sentiment"] in ["positive", "negative", "neutral"]


class TestReviewPreprocessorGetSentiment:
    """_get_sentiment() 메서드 테스트"""

    def test_평점_5점_positive(self):
        """평점 5점은 positive로 분류된다"""
        # given
        preprocessor = ReviewPreprocessor()

        # when
        result = preprocessor._get_sentiment(5)

        # then
        assert result == "positive"

    def test_평점_4점_positive(self):
        """평점 4점은 positive로 분류된다"""
        # given
        preprocessor = ReviewPreprocessor()

        # when
        result = preprocessor._get_sentiment(4)

        # then
        assert result == "positive"

    def test_평점_3점_neutral(self):
        """평점 3점은 neutral로 분류된다"""
        # given
        preprocessor = ReviewPreprocessor()

        # when
        result = preprocessor._get_sentiment(3)

        # then
        assert result == "neutral"

    def test_평점_2점_negative(self):
        """평점 2점은 negative로 분류된다"""
        # given
        preprocessor = ReviewPreprocessor()

        # when
        result = preprocessor._get_sentiment(2)

        # then
        assert result == "negative"

    def test_평점_1점_negative(self):
        """평점 1점은 negative로 분류된다"""
        # given
        preprocessor = ReviewPreprocessor()

        # when
        result = preprocessor._get_sentiment(1)

        # then
        assert result == "negative"


class TestReviewPreprocessorProcessReviews:
    """process_reviews() 메서드 테스트"""

    def test_유효한_리뷰만_처리(self, sample_reviews, invalid_reviews):
        """유효한 리뷰만 Document로 변환한다"""
        # given
        preprocessor = ReviewPreprocessor(min_length=10)
        all_reviews = sample_reviews + invalid_reviews

        # when
        documents = list(preprocessor.process_reviews(iter(all_reviews)))

        # then
        assert len(documents) == len(sample_reviews)

    def test_limit_적용(self, sample_reviews):
        """limit 파라미터가 적용된다"""
        # given
        preprocessor = ReviewPreprocessor(min_length=10)
        limit = 2

        # when
        documents = list(preprocessor.process_reviews(iter(sample_reviews), limit=limit))

        # then
        assert len(documents) == limit

    def test_빈_리뷰_리스트_처리(self):
        """빈 리뷰 리스트를 처리한다"""
        # given
        preprocessor = ReviewPreprocessor()

        # when
        documents = list(preprocessor.process_reviews(iter([])))

        # then
        assert len(documents) == 0
