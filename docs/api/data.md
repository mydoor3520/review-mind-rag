# Data 모듈

데이터 로딩 및 전처리를 담당하는 모듈입니다.

## 모듈 구조

- `loader.py`: 데이터 로딩
- `preprocessor.py`: 데이터 전처리

## AmazonReviewLoader

Amazon Reviews 2023 데이터셋을 로드하는 클래스입니다.

### 주요 메서드

#### `load_category(category, limit=None)`

특정 카테고리의 리뷰를 로드합니다.

**Parameters:**

- `category` (str): 카테고리 이름
    - "Electronics"
    - "Appliances"
    - "Beauty_and_Personal_Care"
    - "Home_and_Kitchen"
- `limit` (int, optional): 로드할 최대 개수

**Returns:**

- `List[dict]`: 리뷰 데이터 리스트

**Example:**

```python
from src.data.loader import AmazonReviewLoader

loader = AmazonReviewLoader()

# 전자제품 카테고리 전체 로드
reviews = loader.load_category("Electronics")

# 1000개로 제한
reviews = loader.load_category("Electronics", limit=1000)
```

#### `load_all_categories(limit_per_category=None)`

모든 카테고리의 리뷰를 로드합니다.

**Parameters:**

- `limit_per_category` (int, optional): 카테고리당 최대 개수

**Returns:**

- `dict`: 카테고리별 리뷰 데이터

**Example:**

```python
all_reviews = loader.load_all_categories(limit_per_category=500)
for category, reviews in all_reviews.items():
    print(f"{category}: {len(reviews)} reviews")
```

#### `get_available_categories()`

사용 가능한 카테고리 목록을 반환합니다.

**Returns:**

- `List[str]`: 카테고리 이름 리스트

**Example:**

```python
categories = loader.get_available_categories()
print(categories)  # ['Electronics', 'Appliances', ...]
```

## ReviewPreprocessor

리뷰 데이터를 전처리하고 LangChain Document로 변환하는 클래스입니다.

### 주요 메서드

#### `process_reviews(reviews, batch_size=100)`

리뷰를 전처리하여 Document로 변환합니다.

**Parameters:**

- `reviews` (List[dict]): 원본 리뷰 데이터
- `batch_size` (int): 배치 크기

**Yields:**

- `Document`: LangChain Document 객체

**Example:**

```python
from src.data.preprocessor import ReviewPreprocessor

preprocessor = ReviewPreprocessor()
documents = list(preprocessor.process_reviews(reviews))

for doc in documents:
    print(doc.page_content)
    print(doc.metadata)
```

#### `clean_text(text)`

텍스트를 정제합니다.

**Parameters:**

- `text` (str): 원본 텍스트

**Returns:**

- `str`: 정제된 텍스트

**Example:**

```python
clean = preprocessor.clean_text("  Great product!!!  ")
print(clean)  # "Great product!"
```

#### `extract_metadata(review)`

리뷰에서 메타데이터를 추출합니다.

**Parameters:**

- `review` (dict): 리뷰 데이터

**Returns:**

- `dict`: 메타데이터
    - `product_id` (str): 상품 ID
    - `rating` (float): 평점
    - `category` (str): 카테고리
    - `title` (str): 리뷰 제목
    - `verified_purchase` (bool): 구매 확인 여부

**Example:**

```python
metadata = preprocessor.extract_metadata(review)
print(metadata["product_id"])
print(metadata["rating"])
```

## 데이터 스키마

### Review 데이터 구조

원본 Amazon Reviews 데이터의 주요 필드입니다.

```python
{
    "rating": 5.0,
    "title": "Great product!",
    "text": "This is an excellent product...",
    "parent_asin": "B001XXXXX",
    "user_id": "AXXX",
    "timestamp": 1234567890,
    "verified_purchase": True,
    "helpful_vote": 10
}
```

### Document 메타데이터

LangChain Document의 메타데이터 구조입니다.

```python
{
    "product_id": "B001XXXXX",
    "category": "Electronics",
    "rating": 5.0,
    "title": "Great product!",
    "verified_purchase": True,
    "helpful_vote": 10,
    "timestamp": "2023-01-15"
}
```

## 데이터 로딩 예제

### 기본 사용법

```python
from src.data.loader import AmazonReviewLoader
from src.data.preprocessor import ReviewPreprocessor
from src.rag.vectorstore import ReviewVectorStore

# 1. 데이터 로드
loader = AmazonReviewLoader()
reviews = loader.load_category("Electronics", limit=1000)

# 2. 전처리
preprocessor = ReviewPreprocessor()
documents = list(preprocessor.process_reviews(reviews))

# 3. Vector DB 저장
vectorstore = ReviewVectorStore.from_documents(documents)
```

### 여러 카테고리 로딩

```python
all_reviews = loader.load_all_categories(limit_per_category=500)
all_documents = []

for category, reviews in all_reviews.items():
    docs = list(preprocessor.process_reviews(reviews))
    all_documents.extend(docs)

vectorstore = ReviewVectorStore.from_documents(all_documents)
```

### 필터링된 데이터 로딩

```python
# 높은 평점의 리뷰만 로드
reviews = loader.load_category("Electronics", limit=5000)
high_rated = [r for r in reviews if r.get("rating", 0) >= 4.0]
documents = list(preprocessor.process_reviews(high_rated))
```

## 참고 자료

- [Amazon Reviews 2023 Dataset](https://amazon-reviews-2023.github.io/)
- [LangChain Documents](https://python.langchain.com/docs/modules/data_connection/document_loaders/)
