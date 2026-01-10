# Analysis 모듈

리뷰 분석 기능을 제공하는 모듈입니다.

## 모듈 구조

- `sentiment.py`: 감성 분석
- `summarizer.py`: 리뷰 요약
- `metrics.py`: 통계 및 메트릭

## SentimentAnalyzer

리뷰의 감성을 분석하는 클래스입니다.

### 주요 메서드

#### `analyze_sentiment(text)`

텍스트의 감성을 분석합니다.

**Parameters:**

- `text` (str): 분석할 텍스트

**Returns:**

- `dict`: 감성 분석 결과
    - `label` (str): "positive", "negative", "neutral"
    - `score` (float): 신뢰도 점수 (0.0 ~ 1.0)

**Example:**

```python
from src.analysis.sentiment import SentimentAnalyzer

analyzer = SentimentAnalyzer()
result = analyzer.analyze_sentiment("This product is amazing!")
print(result)  # {"label": "positive", "score": 0.95}
```

#### `analyze_reviews(reviews)`

여러 리뷰의 감성을 일괄 분석합니다.

**Parameters:**

- `reviews` (List[str]): 리뷰 텍스트 리스트

**Returns:**

- `dict`: 감성 분포
    - `positive` (int): 긍정 리뷰 개수
    - `negative` (int): 부정 리뷰 개수
    - `neutral` (int): 중립 리뷰 개수
    - `percentages` (dict): 각 감성의 백분율

**Example:**

```python
reviews = ["Great!", "Terrible", "It's okay"]
distribution = analyzer.analyze_reviews(reviews)
print(distribution)
# {
#   "positive": 1,
#   "negative": 1,
#   "neutral": 1,
#   "percentages": {"positive": 33.3, "negative": 33.3, "neutral": 33.3}
# }
```

## ReviewSummarizer

리뷰를 요약하는 클래스입니다.

### 주요 메서드

#### `summarize(reviews, product_id=None)`

리뷰 목록을 요약합니다.

**Parameters:**

- `reviews` (List[str] or List[Document]): 요약할 리뷰
- `product_id` (str, optional): 상품 ID

**Returns:**

- `dict`: 요약 결과
    - `summary` (str): 전체 요약
    - `pros` (List[str]): 장점 목록
    - `cons` (List[str]): 단점 목록
    - `rating_summary` (str): 평점 요약

**Example:**

```python
from src.analysis.summarizer import ReviewSummarizer

summarizer = ReviewSummarizer()
summary = summarizer.summarize(reviews, product_id="B001")
print(summary["summary"])
print("장점:", summary["pros"])
print("단점:", summary["cons"])
```

## ReviewMetrics

리뷰 통계 및 메트릭을 계산하는 클래스입니다.

### 주요 메서드

#### `calculate_basic_stats(reviews)`

기본 통계를 계산합니다.

**Parameters:**

- `reviews` (List[dict]): 리뷰 데이터 (rating, text 포함)

**Returns:**

- `dict`: 통계 정보
    - `total_reviews` (int): 전체 리뷰 수
    - `average_rating` (float): 평균 평점
    - `rating_distribution` (dict): 평점별 분포
    - `median_rating` (float): 중앙값 평점

**Example:**

```python
from src.analysis.metrics import ReviewMetrics

metrics = ReviewMetrics()
reviews = [
    {"rating": 5, "text": "Great!"},
    {"rating": 4, "text": "Good"},
    {"rating": 3, "text": "OK"}
]
stats = metrics.calculate_basic_stats(reviews)
print(f"평균 평점: {stats['average_rating']}")
print(f"총 리뷰 수: {stats['total_reviews']}")
```

#### `calculate_sentiment_metrics(reviews)`

감성 분석 기반 메트릭을 계산합니다.

**Parameters:**

- `reviews` (List[str]): 리뷰 텍스트 리스트

**Returns:**

- `dict`: 감성 메트릭
    - `sentiment_distribution` (dict): 감성 분포
    - `sentiment_score` (float): 전체 감성 점수 (-1.0 ~ 1.0)

**Example:**

```python
sentiment_metrics = metrics.calculate_sentiment_metrics(review_texts)
print(sentiment_metrics["sentiment_score"])
```

#### `compare_products(product_a_reviews, product_b_reviews)`

두 상품의 리뷰를 비교합니다.

**Parameters:**

- `product_a_reviews` (List[dict]): 상품 A의 리뷰
- `product_b_reviews` (List[dict]): 상품 B의 리뷰

**Returns:**

- `dict`: 비교 결과
    - `product_a_stats` (dict): 상품 A 통계
    - `product_b_stats` (dict): 상품 B 통계
    - `comparison` (dict): 비교 요약

**Example:**

```python
comparison = metrics.compare_products(reviews_a, reviews_b)
print(comparison["product_a_stats"]["average_rating"])
print(comparison["product_b_stats"]["average_rating"])
print(comparison["comparison"]["better_product"])
```

## 시각화

분석 결과를 시각화하는 유틸리티 함수들입니다.

### `plot_sentiment_distribution(sentiment_data)`

감성 분포를 파이 차트로 시각화합니다.

**Parameters:**

- `sentiment_data` (dict): 감성 분석 결과

**Returns:**

- `matplotlib.figure.Figure`: 차트 객체

**Example:**

```python
from src.analysis.metrics import plot_sentiment_distribution

distribution = analyzer.analyze_reviews(reviews)
fig = plot_sentiment_distribution(distribution)
fig.savefig("sentiment.png")
```

### `plot_rating_distribution(stats)`

평점 분포를 막대 차트로 시각화합니다.

**Parameters:**

- `stats` (dict): 통계 데이터

**Returns:**

- `matplotlib.figure.Figure`: 차트 객체

**Example:**

```python
from src.analysis.metrics import plot_rating_distribution

stats = metrics.calculate_basic_stats(reviews)
fig = plot_rating_distribution(stats)
```

## 참고 자료

- [Sentiment Analysis Guide](https://huggingface.co/docs/transformers/tasks/sequence_classification)
- [Text Summarization](https://python.langchain.com/docs/use_cases/summarization)
