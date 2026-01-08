"""
ReviewVectorStore 통합 테스트

ChromaDB와 연동하는 Vector Store 테스트입니다.
외부 의존성(ChromaDB, OpenAI Embedding)이 필요합니다.
"""

import os
import pytest
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from langchain_core.documents import Document


class TestReviewVectorStoreInit:
    """초기화 테스트"""

    def test_기본_파라미터_초기화(self):
        """기본 파라미터로 초기화된다"""
        # given
        from src.rag.vectorstore import ReviewVectorStore

        # when
        store = ReviewVectorStore(
            persist_directory="./test_chroma",
            collection_name="test_reviews"
        )

        # then
        assert store.persist_directory == "./test_chroma"
        assert store.collection_name == "test_reviews"
        assert store._vectorstore is None  # lazy initialization

    def test_임베딩_모델_설정(self):
        """임베딩 모델을 설정할 수 있다"""
        # given
        from src.rag.vectorstore import ReviewVectorStore

        # when
        store = ReviewVectorStore(
            embedding_model="text-embedding-3-small"
        )

        # then
        assert store.embeddings is not None


@pytest.mark.integration
class TestReviewVectorStoreWithMockEmbedding:
    """Mock 임베딩을 사용한 통합 테스트"""

    @pytest.fixture
    def temp_chroma_dir(self, tmp_path):
        """임시 ChromaDB 디렉토리"""
        chroma_dir = tmp_path / "chroma_db"
        chroma_dir.mkdir()
        yield chroma_dir
        # 정리
        if chroma_dir.exists():
            shutil.rmtree(chroma_dir)

    @pytest.fixture
    def sample_documents(self):
        """테스트용 Document 리스트"""
        return [
            Document(
                page_content="이 이어폰은 음질이 정말 좋습니다. 노이즈 캔슬링도 훌륭해요.",
                metadata={
                    "review_id": "B001_user1",
                    "product_id": "B001",
                    "category": "Electronics",
                    "rating": 5,
                    "sentiment": "positive",
                }
            ),
            Document(
                page_content="배터리가 오래 가고 연결이 안정적입니다. 추천합니다.",
                metadata={
                    "review_id": "B001_user2",
                    "product_id": "B001",
                    "category": "Electronics",
                    "rating": 4,
                    "sentiment": "positive",
                }
            ),
            Document(
                page_content="음질은 괜찮은데 착용감이 별로입니다. 오래 끼면 귀가 아파요.",
                metadata={
                    "review_id": "B001_user3",
                    "product_id": "B001",
                    "category": "Electronics",
                    "rating": 3,
                    "sentiment": "neutral",
                }
            ),
            Document(
                page_content="에어프라이어 용량이 작아서 아쉽습니다. 소음도 좀 있어요.",
                metadata={
                    "review_id": "B002_user1",
                    "product_id": "B002",
                    "category": "Appliances",
                    "rating": 2,
                    "sentiment": "negative",
                }
            ),
        ]

    @pytest.fixture
    def mock_embeddings(self):
        """Mock OpenAI 임베딩"""
        mock = MagicMock()
        # 간단한 벡터 반환 (1536차원 대신 작은 차원 사용)
        mock.embed_documents.return_value = [[0.1] * 384 for _ in range(10)]
        mock.embed_query.return_value = [0.1] * 384
        return mock

    def test_문서_추가(self, temp_chroma_dir, sample_documents, mock_embeddings):
        """문서를 Vector Store에 추가할 수 있다"""
        # given
        from src.rag.vectorstore import ReviewVectorStore
        
        with patch.object(ReviewVectorStore, '__init__', lambda self, **kwargs: None):
            store = ReviewVectorStore()
            store.persist_directory = str(temp_chroma_dir)
            store.collection_name = "test_reviews"
            store.embeddings = mock_embeddings
            store._vectorstore = None

        # Chroma 초기화를 mock
        with patch('src.rag.vectorstore.Chroma') as mock_chroma:
            mock_chroma_instance = MagicMock()
            mock_chroma.return_value = mock_chroma_instance
            
            # vectorstore property 접근 시 mock 반환
            store._vectorstore = mock_chroma_instance
            
            # when
            store.vectorstore.add_documents(sample_documents)

            # then
            mock_chroma_instance.add_documents.assert_called_once_with(sample_documents)

    def test_유사도_검색(self, temp_chroma_dir, sample_documents, mock_embeddings):
        """유사도 검색을 수행할 수 있다"""
        # given
        from src.rag.vectorstore import ReviewVectorStore
        
        with patch.object(ReviewVectorStore, '__init__', lambda self, **kwargs: None):
            store = ReviewVectorStore()
            store.persist_directory = str(temp_chroma_dir)
            store.collection_name = "test_reviews"
            store.embeddings = mock_embeddings
            store._vectorstore = None

        with patch('src.rag.vectorstore.Chroma') as mock_chroma:
            mock_chroma_instance = MagicMock()
            mock_chroma_instance.similarity_search.return_value = sample_documents[:2]
            store._vectorstore = mock_chroma_instance

            # when
            results = store.similarity_search("이어폰 음질", k=2)

            # then
            assert len(results) == 2
            mock_chroma_instance.similarity_search.assert_called_once()

    def test_필터링_검색(self, temp_chroma_dir, sample_documents, mock_embeddings):
        """메타데이터 필터링 검색을 수행할 수 있다"""
        # given
        from src.rag.vectorstore import ReviewVectorStore
        
        with patch.object(ReviewVectorStore, '__init__', lambda self, **kwargs: None):
            store = ReviewVectorStore()
            store.persist_directory = str(temp_chroma_dir)
            store.collection_name = "test_reviews"
            store.embeddings = mock_embeddings
            store._vectorstore = None

        with patch('src.rag.vectorstore.Chroma') as mock_chroma:
            mock_chroma_instance = MagicMock()
            # Electronics만 반환
            mock_chroma_instance.similarity_search.return_value = [
                doc for doc in sample_documents if doc.metadata["category"] == "Electronics"
            ]
            store._vectorstore = mock_chroma_instance

            # when
            filter_dict = {"category": "Electronics"}
            results = store.similarity_search("음질", k=5, filter=filter_dict)

            # then
            assert len(results) == 3
            for doc in results:
                assert doc.metadata["category"] == "Electronics"

    def test_컬렉션_통계(self, temp_chroma_dir, mock_embeddings):
        """컬렉션 통계를 조회할 수 있다"""
        # given
        from src.rag.vectorstore import ReviewVectorStore
        
        with patch.object(ReviewVectorStore, '__init__', lambda self, **kwargs: None):
            store = ReviewVectorStore()
            store.persist_directory = str(temp_chroma_dir)
            store.collection_name = "test_reviews"
            store.embeddings = mock_embeddings
            store._vectorstore = None

        with patch('src.rag.vectorstore.Chroma') as mock_chroma:
            mock_chroma_instance = MagicMock()
            mock_collection = MagicMock()
            mock_collection.count.return_value = 100
            mock_chroma_instance._collection = mock_collection
            store._vectorstore = mock_chroma_instance

            # when
            stats = store.get_collection_stats()

            # then
            assert stats["document_count"] == 100
            assert stats["collection_name"] == "test_reviews"

    def test_retriever_생성(self, temp_chroma_dir, mock_embeddings):
        """Retriever를 생성할 수 있다"""
        # given
        from src.rag.vectorstore import ReviewVectorStore
        
        with patch.object(ReviewVectorStore, '__init__', lambda self, **kwargs: None):
            store = ReviewVectorStore()
            store.persist_directory = str(temp_chroma_dir)
            store.collection_name = "test_reviews"
            store.embeddings = mock_embeddings
            store._vectorstore = None

        with patch('src.rag.vectorstore.Chroma') as mock_chroma:
            mock_chroma_instance = MagicMock()
            mock_retriever = MagicMock()
            mock_chroma_instance.as_retriever.return_value = mock_retriever
            store._vectorstore = mock_chroma_instance

            # when
            retriever = store.get_retriever(k=5)

            # then
            assert retriever is not None
            mock_chroma_instance.as_retriever.assert_called_once()


@pytest.mark.integration
class TestReviewVectorStoreFromDocuments:
    """from_documents 클래스 메서드 테스트"""

    def test_문서로부터_생성(self, tmp_path):
        """문서로부터 새 Vector Store를 생성할 수 있다"""
        # given
        from src.rag.vectorstore import ReviewVectorStore
        
        sample_docs = [
            Document(
                page_content="테스트 리뷰입니다.",
                metadata={"rating": 5}
            )
        ]
        
        with patch('src.rag.vectorstore.OpenAIEmbeddings') as mock_embed_class:
            mock_embeddings = MagicMock()
            mock_embed_class.return_value = mock_embeddings
            
            with patch('src.rag.vectorstore.Chroma') as mock_chroma:
                mock_vectorstore = MagicMock()
                mock_chroma.from_documents.return_value = mock_vectorstore

                # when
                store = ReviewVectorStore.from_documents(
                    documents=sample_docs,
                    persist_directory=str(tmp_path / "chroma"),
                    collection_name="test"
                )

                # then
                assert store is not None
                mock_chroma.from_documents.assert_called_once()


class TestReviewVectorStoreAddDocumentsBatch:
    """add_documents 배치 처리 테스트"""

    def test_배치_추가_진행률(self, tmp_path):
        """배치 추가 시 진행률이 표시된다"""
        # given
        from src.rag.vectorstore import ReviewVectorStore
        
        docs = [
            Document(page_content=f"리뷰 {i}", metadata={"rating": 5})
            for i in range(250)
        ]

        with patch.object(ReviewVectorStore, '__init__', lambda self, **kwargs: None):
            store = ReviewVectorStore()
            store.persist_directory = str(tmp_path)
            store.collection_name = "test"
            store._vectorstore = None

        with patch('src.rag.vectorstore.Chroma') as mock_chroma:
            mock_chroma_instance = MagicMock()
            store._vectorstore = mock_chroma_instance

            # when
            added = store.add_documents(docs, batch_size=100, show_progress=False)

            # then
            assert added == 250
            # 3번 호출 (100, 100, 50)
            assert mock_chroma_instance.add_documents.call_count == 3
