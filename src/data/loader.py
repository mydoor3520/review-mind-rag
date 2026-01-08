"""
Amazon Reviews 데이터 로더

Hugging Face datasets를 사용하여 Amazon Reviews 2023 데이터를 로드합니다.
"""

from typing import List, Dict, Optional, Iterator
from pathlib import Path
import json
from tqdm import tqdm


class AmazonReviewLoader:
    """
    Amazon Reviews 2023 데이터셋 로더
    
    Hugging Face의 McAuley-Lab/Amazon-Reviews-2023 데이터셋을 사용합니다.
    https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023
    """
    
    DATASET_NAME = "McAuley-Lab/Amazon-Reviews-2023"
    
    # 사용 가능한 카테고리 매핑
    CATEGORY_MAP = {
        "Electronics": "Electronics",
        "Appliances": "Appliances",
        "Beauty": "Beauty_and_Personal_Care",
        "Furniture": "Home_and_Kitchen",
        "Home": "Home_and_Kitchen",
    }
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        :param cache_dir: 데이터 캐시 디렉토리
        """
        self.cache_dir = cache_dir
    
    def load_category(
        self,
        category: str,
        split: str = "full",
        limit: Optional[int] = None,
        streaming: bool = True
    ) -> Iterator[Dict]:
        """
        특정 카테고리의 리뷰를 로드합니다.
        
        :param category: 카테고리 이름 (Electronics, Appliances, Beauty, Furniture)
        :param split: 데이터셋 스플릿 (full, 5-core 등)
        :param limit: 로드할 최대 리뷰 수 (None이면 전체)
        :param streaming: 스트리밍 모드 사용 여부 (메모리 효율)
        :return: 리뷰 딕셔너리 이터레이터
        """
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError("datasets 패키지를 설치해주세요: pip install datasets")
        
        # 카테고리 이름 정규화
        hf_category = self.CATEGORY_MAP.get(category, category)
        
        print(f"Loading {hf_category} reviews (streaming={streaming})...")
        
        # 데이터셋 로드
        dataset = load_dataset(
            self.DATASET_NAME,
            f"raw_review_{hf_category}",
            split=split,
            streaming=streaming,
            cache_dir=str(self.cache_dir) if self.cache_dir else None
        )
        
        count = 0
        for item in tqdm(dataset, desc=f"Loading {category}"):
            if limit and count >= limit:
                break
            
            yield self._normalize_review(item, category)
            count += 1
        
        print(f"Loaded {count} reviews from {category}")
    
    def load_multiple_categories(
        self,
        categories: List[str],
        limit_per_category: Optional[int] = None
    ) -> Iterator[Dict]:
        """
        여러 카테고리의 리뷰를 로드합니다.
        
        :param categories: 카테고리 리스트
        :param limit_per_category: 카테고리당 최대 리뷰 수
        :return: 리뷰 딕셔너리 이터레이터
        """
        for category in categories:
            yield from self.load_category(
                category,
                limit=limit_per_category
            )
    
    def _normalize_review(self, item: Dict, category: str) -> Dict:
        """
        리뷰 데이터를 정규화된 형식으로 변환합니다.
        
        :param item: 원본 리뷰 데이터
        :param category: 카테고리
        :return: 정규화된 리뷰 딕셔너리
        """
        return {
            "review_id": item.get("asin", "") + "_" + str(item.get("user_id", "")),
            "product_id": item.get("asin", ""),
            "product_name": item.get("title", "Unknown Product"),
            "category": category,
            "rating": item.get("rating", 0),
            "review_text": item.get("text", ""),
            "review_title": item.get("title", ""),
            "helpful_votes": item.get("helpful_vote", 0),
            "verified_purchase": item.get("verified_purchase", False),
            "timestamp": item.get("timestamp", None),
            "user_id": item.get("user_id", ""),
        }
    
    def save_to_jsonl(
        self,
        reviews: Iterator[Dict],
        output_path: Path,
        limit: Optional[int] = None
    ) -> int:
        """
        리뷰를 JSONL 파일로 저장합니다.
        
        :param reviews: 리뷰 이터레이터
        :param output_path: 출력 파일 경로
        :param limit: 저장할 최대 리뷰 수
        :return: 저장된 리뷰 수
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for review in tqdm(reviews, desc="Saving reviews"):
                if limit and count >= limit:
                    break
                f.write(json.dumps(review, ensure_ascii=False) + "\n")
                count += 1
        
        print(f"Saved {count} reviews to {output_path}")
        return count
    
    @staticmethod
    def load_from_jsonl(input_path: Path) -> Iterator[Dict]:
        """
        JSONL 파일에서 리뷰를 로드합니다.
        
        :param input_path: 입력 파일 경로
        :return: 리뷰 딕셔너리 이터레이터
        """
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)
