# 초기 데이터 로드 가이드

NAS에서 Review Mind RAG의 초기 리뷰 데이터를 로드하는 방법입니다.

## 목차

1. [개요](#개요)
2. [로드 방법](#로드-방법)
3. [배치 크기 조정](#배치-크기-조정)
4. [카테고리별 로드](#카테고리별-로드)
5. [데이터 확인](#데이터-확인)

---

## 개요

Review Mind RAG는 Amazon Reviews 2023 데이터셋을 사용합니다. 첫 배포 시 데이터를 ChromaDB에 인덱싱해야 합니다.

### 주의사항

- **시간 소요**: 카테고리당 1000개 리뷰 기준 약 5-10분
- **리소스**: NAS CPU 사용률이 높아질 수 있음
- **네트워크**: Hugging Face에서 데이터 다운로드 필요

---

## 로드 방법

### 방법 1: docker exec 사용 (권장)

```bash
# NAS SSH 접속 후
docker exec -it review-mind-rag python scripts/load_all_categories.py --limit-per-category 500
```

### 방법 2: 로컬에서 로드 후 볼륨 복사

```bash
# 로컬에서 데이터 로드
python scripts/load_all_categories.py --limit-per-category 1000

# NAS로 볼륨 복사
scp -r chroma_db/ admin@your-nas:/volume1/docker/review-mind-rag/
```

### 방법 3: 일회성 컨테이너 실행

```bash
docker run --rm \
  -v /volume1/docker/review-mind-rag/chroma_db:/app/chroma_db \
  -v /volume1/docker/review-mind-rag/data:/app/data \
  --env-file /volume1/docker/review-mind-rag/.env \
  jeonghopak/review-mind-rag:latest \
  python scripts/load_all_categories.py --limit-per-category 500
```

---

## 배치 크기 조정

NAS CPU (Intel Celeron J4025)의 성능을 고려하여 배치 크기를 조정합니다.

### 권장 설정

| RAM | 배치 크기 | 카테고리당 개수 |
|-----|----------|----------------|
| 2GB | 50 | 200 |
| 4GB | 100 | 500 |
| 8GB+ | 200 | 1000 |
| 24GB | 500 | 2000+ |

### 명령어 예시

```bash
# 메모리가 적은 경우
docker exec -it review-mind-rag python scripts/load_all_categories.py \
  --limit-per-category 200 \
  --batch-size 50

# 메모리가 충분한 경우 (24GB)
docker exec -it review-mind-rag python scripts/load_all_categories.py \
  --limit-per-category 2000 \
  --batch-size 500
```

---

## 카테고리별 로드

특정 카테고리만 선택적으로 로드할 수 있습니다.

### 지원 카테고리

| 카테고리 | 설명 |
|----------|------|
| Electronics | 전자제품 (이어폰, 스피커, 케이블) |
| Appliances | 가전제품 (에어프라이어, 청소기) |
| Beauty_and_Personal_Care | 뷰티/화장품 |
| Home_and_Kitchen | 가구/주방용품 |

### Python 코드로 선택적 로드

```python
# docker exec -it review-mind-rag python
from src.data.loader import AmazonReviewLoader
from src.data.preprocessor import ReviewPreprocessor
from src.rag.vectorstore import ReviewVectorStore

loader = AmazonReviewLoader()
preprocessor = ReviewPreprocessor()

# Electronics만 로드
reviews = list(loader.load_category("Electronics", limit=1000))
documents = list(preprocessor.process_reviews(reviews))

# VectorStore에 추가
vectorstore = ReviewVectorStore()
vectorstore.add_documents(documents, batch_size=100)

print(f"Added {len(documents)} documents")
```

---

## 데이터 확인

### VectorStore 상태 확인

```python
# docker exec -it review-mind-rag python
from src.rag.vectorstore import ReviewVectorStore

vectorstore = ReviewVectorStore()
stats = vectorstore.get_collection_stats()
print(f"문서 수: {stats['document_count']}")
print(f"컬렉션: {stats['collection_name']}")
```

### Streamlit 대시보드에서 확인

1. `https://mydoor.synology.me/review-mind` 접속
2. 사이드바에서 **시스템 상태** 확인
3. 리뷰 수와 카테고리 개수 표시됨

### 검색 테스트

```python
# docker exec -it review-mind-rag python
from src.rag.vectorstore import ReviewVectorStore

vectorstore = ReviewVectorStore()
results = vectorstore.similarity_search("battery life", k=5)

for doc in results:
    print(f"[{doc.metadata.get('category')}] {doc.page_content[:100]}...")
```

---

## 트러블슈팅

### 메모리 부족

```bash
# 배치 크기 줄이기
--batch-size 25

# 카테고리 하나씩 로드
docker exec -it review-mind-rag python -c "
from src.data.loader import AmazonReviewLoader
loader = AmazonReviewLoader()
for review in loader.load_category('Electronics', limit=100):
    print(review['product_id'])
"
```

### 네트워크 오류

```bash
# Hugging Face 캐시 사용
export HF_HOME=/app/data/.cache
```

### 중간에 중단된 경우

데이터 로드는 배치 단위로 저장되므로 중간에 중단되어도 이미 저장된 데이터는 유지됩니다. 다시 실행하면 추가 데이터가 저장됩니다.

```bash
# 기존 데이터 삭제 후 다시 로드하려면
docker exec -it review-mind-rag python -c "
from src.rag.vectorstore import ReviewVectorStore
vs = ReviewVectorStore()
vs.delete_collection()
print('Collection deleted')
"
```

---

## 다음 단계

데이터 로드가 완료되면:

1. Streamlit 대시보드에서 기능 테스트
2. QA Chat에서 질문 테스트
3. 성능 최적화 필요 시 Reranker 활성화
