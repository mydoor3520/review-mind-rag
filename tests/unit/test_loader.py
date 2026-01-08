"""
AmazonReviewLoader 단위 테스트

Amazon Reviews 데이터 로더 모듈의 테스트 코드입니다.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.data.loader import AmazonReviewLoader


class TestAmazonReviewLoaderInit:
    """__init__() 메서드 테스트"""

    def test_기본_초기화(self):
        """기본 파라미터로 초기화된다"""
        # when
        loader = AmazonReviewLoader()

        # then
        assert loader.cache_dir is None

    def test_cache_dir_설정(self, temp_dir):
        """cache_dir을 설정할 수 있다"""
        # when
        loader = AmazonReviewLoader(cache_dir=temp_dir)

        # then
        assert loader.cache_dir == temp_dir


class TestAmazonReviewLoaderCategoryMap:
    """카테고리 매핑 테스트"""

    def test_Electronics_매핑(self):
        """Electronics 카테고리가 올바르게 매핑된다"""
        # given
        loader = AmazonReviewLoader()

        # then
        assert loader.CATEGORY_MAP["Electronics"] == "Electronics"

    def test_Beauty_매핑(self):
        """Beauty 카테고리가 Beauty_and_Personal_Care로 매핑된다"""
        # given
        loader = AmazonReviewLoader()

        # then
        assert loader.CATEGORY_MAP["Beauty"] == "Beauty_and_Personal_Care"

    def test_Furniture_매핑(self):
        """Furniture 카테고리가 Home_and_Kitchen으로 매핑된다"""
        # given
        loader = AmazonReviewLoader()

        # then
        assert loader.CATEGORY_MAP["Furniture"] == "Home_and_Kitchen"


class TestAmazonReviewLoaderNormalizeReview:
    """_normalize_review() 메서드 테스트"""

    def test_필드_매핑(self):
        """원본 리뷰 데이터가 올바르게 정규화된다"""
        # given
        loader = AmazonReviewLoader()
        raw_item = {
            "asin": "B001ABC123",
            "user_id": "USER001",
            "title": "좋은 제품",
            "rating": 5,
            "text": "정말 만족합니다.",
            "helpful_vote": 10,
            "verified_purchase": True,
            "timestamp": 1704067200,
        }

        # when
        result = loader._normalize_review(raw_item, "Electronics")

        # then
        assert result["review_id"] == "B001ABC123_USER001"
        assert result["product_id"] == "B001ABC123"
        assert result["category"] == "Electronics"
        assert result["rating"] == 5
        assert result["review_text"] == "정말 만족합니다."
        assert result["helpful_votes"] == 10
        assert result["verified_purchase"] is True

    def test_빈_필드_기본값(self):
        """빈 필드에 기본값이 적용된다"""
        # given
        loader = AmazonReviewLoader()
        raw_item = {}

        # when
        result = loader._normalize_review(raw_item, "Electronics")

        # then
        assert result["review_id"] == "_"
        assert result["product_id"] == ""
        assert result["rating"] == 0
        assert result["review_text"] == ""
        assert result["helpful_votes"] == 0
        assert result["verified_purchase"] is False


class TestAmazonReviewLoaderSaveToJsonl:
    """save_to_jsonl() 메서드 테스트"""

    def test_JSONL_파일_저장(self, temp_dir, sample_reviews):
        """리뷰를 JSONL 파일로 저장한다"""
        # given
        loader = AmazonReviewLoader()
        output_path = temp_dir / "reviews.jsonl"

        # when
        count = loader.save_to_jsonl(iter(sample_reviews), output_path)

        # then
        assert output_path.exists()
        assert count == len(sample_reviews)

    def test_limit_적용(self, temp_dir, sample_reviews):
        """limit 파라미터가 적용된다"""
        # given
        loader = AmazonReviewLoader()
        output_path = temp_dir / "reviews.jsonl"
        limit = 2

        # when
        count = loader.save_to_jsonl(iter(sample_reviews), output_path, limit=limit)

        # then
        assert count == limit

    def test_저장된_내용_검증(self, temp_dir, sample_reviews):
        """저장된 JSONL 파일의 내용을 검증한다"""
        # given
        loader = AmazonReviewLoader()
        output_path = temp_dir / "reviews.jsonl"
        loader.save_to_jsonl(iter(sample_reviews), output_path)

        # when
        with open(output_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # then
        assert len(lines) == len(sample_reviews)
        first_review = json.loads(lines[0])
        assert first_review["review_id"] == sample_reviews[0]["review_id"]


class TestAmazonReviewLoaderLoadFromJsonl:
    """load_from_jsonl() 메서드 테스트"""

    def test_JSONL_파일_로드(self, temp_dir, sample_reviews):
        """JSONL 파일에서 리뷰를 로드한다"""
        # given
        loader = AmazonReviewLoader()
        input_path = temp_dir / "reviews.jsonl"
        
        # 먼저 저장
        loader.save_to_jsonl(iter(sample_reviews), input_path)

        # when
        loaded_reviews = list(AmazonReviewLoader.load_from_jsonl(input_path))

        # then
        assert len(loaded_reviews) == len(sample_reviews)
        assert loaded_reviews[0]["review_id"] == sample_reviews[0]["review_id"]

    def test_빈_줄_무시(self, temp_dir):
        """빈 줄은 무시한다"""
        # given
        input_path = temp_dir / "reviews.jsonl"
        with open(input_path, "w", encoding="utf-8") as f:
            f.write('{"review_id": "1", "text": "test"}\n')
            f.write('\n')
            f.write('{"review_id": "2", "text": "test2"}\n')

        # when
        loaded_reviews = list(AmazonReviewLoader.load_from_jsonl(input_path))

        # then
        assert len(loaded_reviews) == 2


class TestAmazonReviewLoaderLoadCategory:
    """load_category() 메서드 테스트 (Mock 사용)"""

    @patch("datasets.load_dataset")
    def test_카테고리_로드_호출(self, mock_load_dataset):
        """load_dataset이 올바른 파라미터로 호출된다"""
        # given
        loader = AmazonReviewLoader()
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = Mock(return_value=iter([]))
        mock_load_dataset.return_value = mock_dataset

        # when
        list(loader.load_category("Electronics", limit=10))

        # then
        mock_load_dataset.assert_called_once()
        call_args = mock_load_dataset.call_args
        assert "McAuley-Lab/Amazon-Reviews-2023" in str(call_args)
        assert "raw_review_Electronics" in str(call_args)

    @patch("datasets.load_dataset")
    def test_limit_적용(self, mock_load_dataset):
        """limit 파라미터가 적용된다"""
        # given
        loader = AmazonReviewLoader()
        mock_items = [
            {"asin": f"B00{i}", "user_id": f"user{i}", "rating": 5, "text": "good"}
            for i in range(10)
        ]
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = Mock(return_value=iter(mock_items))
        mock_load_dataset.return_value = mock_dataset

        # when
        reviews = list(loader.load_category("Electronics", limit=3))

        # then
        assert len(reviews) == 3

    @patch("datasets.load_dataset")
    def test_카테고리_매핑_적용(self, mock_load_dataset):
        """카테고리 매핑이 적용된다"""
        # given
        loader = AmazonReviewLoader()
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = Mock(return_value=iter([]))
        mock_load_dataset.return_value = mock_dataset

        # when
        list(loader.load_category("Beauty", limit=1))

        # then
        call_args = mock_load_dataset.call_args
        assert "Beauty_and_Personal_Care" in str(call_args)


class TestAmazonReviewLoaderLoadMultipleCategories:
    """load_multiple_categories() 메서드 테스트"""

    @patch.object(AmazonReviewLoader, "load_category")
    def test_여러_카테고리_로드(self, mock_load_category):
        """여러 카테고리의 리뷰를 로드한다"""
        # given
        loader = AmazonReviewLoader()
        mock_load_category.side_effect = [
            iter([{"category": "Electronics"}]),
            iter([{"category": "Appliances"}]),
        ]

        # when
        reviews = list(loader.load_multiple_categories(
            ["Electronics", "Appliances"],
            limit_per_category=1
        ))

        # then
        assert len(reviews) == 2
        assert mock_load_category.call_count == 2
