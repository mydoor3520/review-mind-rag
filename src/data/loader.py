from typing import List, Dict, Optional, Iterator
from pathlib import Path
import json
from tqdm import tqdm
import pandas as pd

from ..exceptions import CategoryNotFoundError, DatasetLoadError


class ProductMetadataStore:
    """
    상품 메타데이터 저장소

    ASIN을 키로 하여 상품명, 브랜드, 가격 등의 메타데이터를 저장합니다.
    """

    def __init__(self):
        self._metadata: Dict[str, Dict] = {}

    def load_from_parquet(self, parquet_path: Path) -> int:
        """
        Parquet 파일에서 메타데이터를 로드합니다.

        :param parquet_path: Parquet 파일 경로
        :return: 로드된 상품 수
        """
        df = pd.read_parquet(parquet_path)
        count = 0

        for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading metadata"):
            asin = row.get("parent_asin", "")
            if asin:
                self._metadata[asin] = {
                    "product_name": row.get("title", "Unknown Product"),
                    "brand": row.get("store", ""),
                    "price": row.get("price", None),
                    "average_rating": row.get("average_rating", None),
                    "rating_number": row.get("rating_number", 0),
                    "main_category": row.get("main_category", ""),
                    "categories": list(row.get("categories", [])) if row.get("categories") is not None else [],
                    "features": list(row.get("features", [])) if row.get("features") is not None else [],
                    "description": list(row.get("description", [])) if row.get("description") is not None else [],
                }
                count += 1

        print(f"Loaded {count} product metadata from {parquet_path}")
        return count

    def load_from_multiple_parquets(self, parquet_paths: List[Path]) -> int:
        """
        여러 Parquet 파일에서 메타데이터를 로드합니다.
        """
        total = 0
        for path in parquet_paths:
            total += self.load_from_parquet(path)
        return total

    def load_from_jsonl(self, jsonl_path: Path) -> int:
        """
        JSONL 파일에서 메타데이터를 로드합니다.

        :param jsonl_path: JSONL 파일 경로
        :return: 로드된 상품 수
        """
        count = 0
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in tqdm(f, desc=f"Loading metadata from {jsonl_path.name}"):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    asin = item.get("parent_asin", "")
                    if asin:
                        self._metadata[asin] = {
                            "product_name": item.get("title", "Unknown Product"),
                            "brand": item.get("store", ""),
                            "price": item.get("price", None),
                            "average_rating": item.get("average_rating", None),
                            "rating_number": item.get("rating_number", 0),
                            "main_category": item.get("main_category", ""),
                            "categories": item.get("categories", []) or [],
                            "features": item.get("features", []) or [],
                            "description": item.get("description", []) or [],
                        }
                        count += 1
                except json.JSONDecodeError:
                    continue

        print(f"Loaded {count} product metadata from {jsonl_path}")
        return count

    def load_from_directory(self, meta_dir: Path) -> int:
        """
        디렉토리에서 모든 메타데이터 파일(parquet, jsonl)을 로드합니다.

        :param meta_dir: 메타데이터 디렉토리
        :return: 로드된 총 상품 수
        """
        total = 0

        # Parquet 파일 로드
        for parquet_file in meta_dir.glob("*.parquet"):
            if parquet_file.stat().st_size > 100:  # 빈 파일 제외
                total += self.load_from_parquet(parquet_file)

        # JSONL 파일 로드
        for jsonl_file in meta_dir.glob("*.jsonl"):
            if jsonl_file.stat().st_size > 100:  # 빈 파일 제외
                total += self.load_from_jsonl(jsonl_file)

        print(f"Total metadata loaded: {len(self._metadata)} products")
        return total

    def get(self, asin: str) -> Optional[Dict]:
        """
        ASIN으로 상품 메타데이터를 조회합니다.
        """
        return self._metadata.get(asin)

    def get_product_name(self, asin: str, default: str = "Unknown Product") -> str:
        """
        ASIN으로 상품명을 조회합니다.
        """
        meta = self._metadata.get(asin)
        if meta:
            return meta.get("product_name", default)
        return default

    def __len__(self) -> int:
        return len(self._metadata)

    def __contains__(self, asin: str) -> bool:
        return asin in self._metadata


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
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        metadata_store: Optional[ProductMetadataStore] = None
    ):
        """
        :param cache_dir: 데이터 캐시 디렉토리
        :param metadata_store: 상품 메타데이터 저장소 (상품명 조회용)
        """
        self.cache_dir = cache_dir
        self.metadata_store = metadata_store
    
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
            raise DatasetLoadError("datasets 패키지를 설치해주세요: pip install datasets")
        
        hf_category = self.CATEGORY_MAP.get(category)
        if hf_category is None and category not in self.CATEGORY_MAP.values():
            available = list(self.CATEGORY_MAP.keys())
            raise CategoryNotFoundError(
                f"지원하지 않는 카테고리: {category}. 사용 가능: {available}"
            )
        hf_category = hf_category or category
        
        print(f"Loading {hf_category} reviews (streaming={streaming})...")
        
        try:
            dataset = load_dataset(
                self.DATASET_NAME,
                f"raw_review_{hf_category}",
                split=split,
                streaming=streaming,
                trust_remote_code=True,
                cache_dir=str(self.cache_dir) if self.cache_dir else None
            )
        except Exception as e:
            raise DatasetLoadError(f"데이터셋 로드 실패: {e}") from e
        
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
        asin = item.get("parent_asin") or item.get("asin", "")
        review_title = item.get("title", "")

        # 상품명 결정 (Fallback 체인: 메타데이터 → 리뷰 제목 → ASIN)
        product_name = None
        brand = ""
        price = None

        # 1. 메타데이터 스토어에서 조회
        if self.metadata_store and asin:
            meta = self.metadata_store.get(asin)
            if meta:
                product_name = meta.get("product_name")
                brand = meta.get("brand", "")
                price = meta.get("price")

        # 2. 메타데이터 없으면 리뷰 제목 사용 (상품 힌트가 될 수 있음)
        if not product_name and review_title:
            # 리뷰 제목이 너무 짧거나 일반적이지 않으면 사용
            if len(review_title) > 10:
                product_name = f"[Review] {review_title[:80]}"

        # 3. 최종 fallback: ASIN 표시
        if not product_name:
            product_name = f"Product ({asin})" if asin else "Unknown Product"

        return {
            "review_id": asin + "_" + str(item.get("user_id", "")),
            "product_id": asin,
            "product_name": product_name,
            "brand": brand,
            "price": price,
            "category": category,
            "rating": item.get("rating", 0),
            "review_text": item.get("text", ""),
            "review_title": review_title,
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
