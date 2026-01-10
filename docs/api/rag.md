# RAG 모듈

RAG(Retrieval-Augmented Generation) 파이프라인을 구현하는 핵심 모듈입니다.

## 모듈 구조

- `vectorstore.py`: Vector DB 관리
- `retriever.py`: 문서 검색
- `reranker.py`: 검색 결과 재정렬
- `chain.py`: RAG 체인 구성

## ReviewVectorStore

Vector DB(ChromaDB)를 관리하는 클래스입니다.

### 주요 메서드

#### `from_documents(documents, **kwargs)`

문서 목록으로부터 VectorStore를 생성합니다.

**Parameters:**

- `documents` (List[Document]): LangChain Document 객체 리스트
- `**kwargs`: 추가 설정 파라미터

**Returns:**

- `ReviewVectorStore`: 초기화된 VectorStore 인스턴스

**Example:**

```python
from src.rag.vectorstore import ReviewVectorStore
from langchain.schema import Document

documents = [
    Document(page_content="Great product!", metadata={"product_id": "B001"}),
    Document(page_content="Not bad", metadata={"product_id": "B002"})
]

vectorstore = ReviewVectorStore.from_documents(documents)
```

#### `search(query, k=5, **kwargs)`

유사도 검색을 수행합니다.

**Parameters:**

- `query` (str): 검색 쿼리
- `k` (int): 반환할 문서 개수
- `**kwargs`: 추가 필터링 옵션

**Returns:**

- `List[Document]`: 검색된 문서 리스트

**Example:**

```python
results = vectorstore.search("battery life", k=10)
for doc in results:
    print(doc.page_content)
```

#### `delete_collection()`

전체 컬렉션을 삭제합니다.

**Example:**

```python
vectorstore.delete_collection()
```

## ReviewRetriever

고급 검색 기능을 제공하는 Retriever 클래스입니다.

### 주요 메서드

#### `get_relevant_documents(query, **kwargs)`

쿼리에 관련된 문서를 검색합니다.

**Parameters:**

- `query` (str): 검색 쿼리
- `**kwargs`: 필터링 옵션 (category, min_rating 등)

**Returns:**

- `List[Document]`: 관련 문서 리스트

**Example:**

```python
from src.rag.retriever import ReviewRetriever

retriever = ReviewRetriever(vectorstore)
docs = retriever.get_relevant_documents(
    "How is the noise level?",
    category="Electronics",
    min_rating=4.0
)
```

## CrossEncoderReranker

검색 결과를 재정렬하여 정확도를 향상시키는 클래스입니다.

### 주요 메서드

#### `rerank(query, documents, top_k=None)`

문서를 재정렬합니다.

**Parameters:**

- `query` (str): 원본 쿼리
- `documents` (List[Document]): 재정렬할 문서 리스트
- `top_k` (int, optional): 반환할 상위 문서 개수

**Returns:**

- `List[Document]`: 재정렬된 문서 리스트

**Example:**

```python
from src.rag.reranker import CrossEncoderReranker

reranker = CrossEncoderReranker()
reranked_docs = reranker.rerank("battery life", initial_docs, top_k=5)
```

## ReviewRAGChain

QA를 위한 전체 RAG 체인을 구성하는 클래스입니다.

### 주요 메서드

#### `ask(question, **kwargs)`

자연어 질문에 답변합니다.

**Parameters:**

- `question` (str): 사용자 질문
- `**kwargs`: 검색 필터 및 옵션

**Returns:**

- `dict`: 답변 및 소스 문서 정보

**Example:**

```python
from src.rag.chain import ReviewRAGChain

chain = ReviewRAGChain(vectorstore)
result = chain.ask("What do people say about the battery?")
print(result["answer"])
print(result["source_documents"])
```

## 설정

RAG 모듈의 주요 설정은 `src/config.py`의 `RAGConfig`에서 관리됩니다.

```python
from src.config import RAGConfig

config = RAGConfig()
print(config.embedding_model)  # text-embedding-3-small
print(config.llm_model)  # gpt-4o-mini
print(config.chunk_size)  # 500
```

## 참고 자료

- [LangChain Documentation](https://python.langchain.com/docs/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
