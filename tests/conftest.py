"""
pytest 공통 설정 및 Fixtures

테스트 전반에서 사용되는 공통 fixture와 설정을 정의합니다.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Iterator

import pytest

pytest_plugins = ["pytest_playwright"]

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# 환경 설정 Fixtures
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """테스트 환경 설정 (세션 전체에서 한 번만 실행)"""
    # 테스트용 환경 변수 설정
    os.environ.setdefault("OPENAI_API_KEY", "test-api-key")
    os.environ.setdefault("CHROMA_PERSIST_DIR", "./test_chroma_db")
    os.environ.setdefault("CHROMA_COLLECTION_NAME", "test_reviews")
    yield
    # 테스트 종료 후 정리 (필요시)


@pytest.fixture
def temp_dir(tmp_path) -> Path:
    """임시 디렉토리 제공"""
    return tmp_path


# =============================================================================
# 샘플 데이터 Fixtures
# =============================================================================

@pytest.fixture
def sample_review() -> Dict:
    """단일 샘플 리뷰 데이터"""
    return {
        "review_id": "B001_user123",
        "product_id": "B001",
        "product_name": "테스트 상품",
        "category": "Electronics",
        "rating": 4,
        "review_text": "이 제품은 정말 좋습니다. 배송도 빠르고 품질도 만족스럽습니다. 다만 가격이 조금 비싼 편이에요.",
        "review_title": "만족스러운 구매",
        "helpful_votes": 10,
        "verified_purchase": True,
        "timestamp": "2024-01-15",
        "user_id": "user123",
    }


@pytest.fixture
def sample_reviews() -> List[Dict]:
    """여러 개의 샘플 리뷰 데이터"""
    return [
        {
            "review_id": "B001_user1",
            "product_id": "B001",
            "product_name": "무선 이어폰",
            "category": "Electronics",
            "rating": 5,
            "review_text": "음질이 뛰어나고 노이즈 캔슬링이 훌륭합니다. 배터리도 오래 가요.",
            "helpful_votes": 25,
            "verified_purchase": True,
        },
        {
            "review_id": "B001_user2",
            "product_id": "B001",
            "product_name": "무선 이어폰",
            "category": "Electronics",
            "rating": 4,
            "review_text": "전반적으로 좋은데 연결이 가끔 끊깁니다. 음질은 만족.",
            "helpful_votes": 12,
            "verified_purchase": True,
        },
        {
            "review_id": "B002_user3",
            "product_id": "B002",
            "product_name": "에어프라이어",
            "category": "Appliances",
            "rating": 3,
            "review_text": "보통입니다. 소음이 좀 있고 용량이 작아요.",
            "helpful_votes": 5,
            "verified_purchase": False,
        },
        {
            "review_id": "B002_user4",
            "product_id": "B002",
            "product_name": "에어프라이어",
            "category": "Appliances",
            "rating": 2,
            "review_text": "기대 이하입니다. 음식이 고르게 익지 않아요.",
            "helpful_votes": 8,
            "verified_purchase": True,
        },
        {
            "review_id": "B003_user5",
            "product_id": "B003",
            "product_name": "스킨케어 세트",
            "category": "Beauty",
            "rating": 5,
            "review_text": "피부가 확실히 좋아졌어요! 촉촉하고 자극 없이 순해요.",
            "helpful_votes": 30,
            "verified_purchase": True,
        },
    ]


@pytest.fixture
def sample_review_with_html() -> Dict:
    """HTML 태그가 포함된 리뷰 데이터"""
    return {
        "review_id": "B004_user6",
        "product_id": "B004",
        "category": "Electronics",
        "rating": 4,
        "review_text": "<p>정말 <strong>좋은</strong> 제품입니다!</p><br/>추천해요.",
        "helpful_votes": 5,
        "verified_purchase": True,
    }


@pytest.fixture
def sample_review_with_url() -> Dict:
    """URL이 포함된 리뷰 데이터"""
    return {
        "review_id": "B005_user7",
        "product_id": "B005",
        "category": "Electronics",
        "rating": 5,
        "review_text": "제품 사용법은 https://example.com/manual 에서 확인하세요. 정말 좋아요!",
        "helpful_votes": 3,
        "verified_purchase": True,
    }


@pytest.fixture
def invalid_reviews() -> List[Dict]:
    """유효하지 않은 리뷰 데이터들"""
    return [
        # 빈 리뷰 텍스트
        {"review_id": "invalid1", "review_text": "", "rating": 4},
        # 너무 짧은 리뷰
        {"review_id": "invalid2", "review_text": "좋아요", "rating": 5},
        # 평점 없음
        {"review_id": "invalid3", "review_text": "이 제품은 정말 좋습니다.", "rating": None},
        # 유효하지 않은 평점
        {"review_id": "invalid4", "review_text": "이 제품은 정말 좋습니다.", "rating": 6},
        # 평점 0
        {"review_id": "invalid5", "review_text": "이 제품은 정말 좋습니다.", "rating": 0},
    ]


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API 응답"""
    class MockResponse:
        content = "이 제품은 리뷰에 따르면 음질이 좋고 배터리 수명이 길다고 합니다."
    
    return MockResponse()


@pytest.fixture
def mock_embedding():
    """Mock 임베딩 벡터 (1536차원)"""
    import random
    random.seed(42)
    return [random.random() for _ in range(1536)]
