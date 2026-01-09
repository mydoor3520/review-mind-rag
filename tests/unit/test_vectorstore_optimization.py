"""VectorStore 인덱싱 최적화 테스트"""

import asyncio
import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from typing import List

from langchain_core.documents import Document


class TestBatchIndexingOptimization:
    """배치 인덱싱 최적화 테스트"""

    @pytest.fixture
    def large_documents(self) -> List[Document]:
        """대량 테스트 문서 (1000개)"""
        return [
            Document(
                page_content=f"리뷰 내용 {i}. 이 제품은 정말 좋습니다. 품질이 우수하고 가격도 적당합니다.",
                metadata={
                    "review_id": f"review_{i}",
                    "product_id": f"product_{i % 100}",
                    "category": ["Electronics", "Appliances", "Beauty"][i % 3],
                    "rating": (i % 5) + 1,
                    "sentiment": ["positive", "neutral", "negative"][i % 3],
                }
            )
            for i in range(1000)
        ]

    @pytest.fixture
    def mock_vectorstore(self):
        """Mock VectorStore 인스턴스"""
        from src.rag.vectorstore import ReviewVectorStore
        
        with patch.object(ReviewVectorStore, '__init__', lambda self, **kwargs: None):
            store = ReviewVectorStore()
            store.persist_directory = "./test_chroma"
            store.collection_name = "test_reviews"
            store.embeddings = MagicMock()
            store._vectorstore = MagicMock()
            return store

    def test_배치_크기_파라미터로_호출_횟수_결정(self, mock_vectorstore, large_documents):
        """batch_size=200으로 500개 문서 처리 시 3번 호출 (200+200+100)"""
        # given
        batch_size = 200
        
        # when
        mock_vectorstore.add_documents(
            documents=large_documents[:500],
            batch_size=batch_size,
            show_progress=False
        )
        
        # then
        assert mock_vectorstore._vectorstore.add_documents.call_count == 3

    def test_진행률_콜백_매_배치마다_호출(self, mock_vectorstore, large_documents):
        """batch_size=25로 100개 처리 시 콜백 4번 호출"""
        # given
        progress_callback = Mock()
        
        # when
        mock_vectorstore.add_documents_with_progress(
            documents=large_documents[:100],
            batch_size=25,
            progress_callback=progress_callback
        )
        
        # then
        assert progress_callback.call_count == 4
        last_call = progress_callback.call_args_list[-1][0]
        assert last_call[0] == 100
        assert last_call[1] == 100

    def test_인덱싱_통계_반환(self, mock_vectorstore, large_documents):
        """처리 완료 후 통계 정보 반환"""
        # when
        stats = mock_vectorstore.add_documents_with_stats(
            documents=large_documents[:100],
            batch_size=50
        )
        
        # then
        assert "total_documents" in stats
        assert "processed_documents" in stats
        assert "elapsed_time" in stats
        assert "documents_per_second" in stats
        assert stats["total_documents"] == 100
        assert stats["processed_documents"] == 100

    def test_실패한_배치_재시도(self, mock_vectorstore, large_documents):
        """첫 번째 배치 실패 시 재시도하여 성공"""
        # given
        call_count = 0
        
        def fail_first_call(batch):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("임시 오류")
            return None
        
        mock_vectorstore._vectorstore.add_documents.side_effect = fail_first_call
        
        # when
        result = mock_vectorstore.add_documents_with_retry(
            documents=large_documents[:50],
            batch_size=50,
            max_retries=3
        )
        
        # then
        assert result["success"] is True
        assert result["retry_count"] == 1

    def test_메모리_사용량_추적(self, mock_vectorstore, large_documents):
        """track_memory=True 시 메모리 정보 포함"""
        # when
        stats = mock_vectorstore.add_documents_with_stats(
            documents=large_documents[:100],
            batch_size=50,
            track_memory=True
        )
        
        # then
        assert "memory_usage_mb" in stats
        assert "peak_memory_mb" in stats
        assert stats["memory_usage_mb"] >= 0


class TestIndexingProgress:
    """진행률 추적 클래스 테스트"""

    def test_ETA_계산(self):
        """진행률 기반 예상 완료 시간 계산"""
        # given
        from src.rag.vectorstore import IndexingProgress  # noqa: F401
        
        progress = IndexingProgress(total=1000)
        progress.start()
        progress.update(100)
        
        # when
        eta = progress.get_eta()
        
        # then
        assert eta is not None
        assert eta > 0

    def test_처리_속도_계산(self):
        """10초간 500개 처리 시 50 docs/sec 반환"""
        # given
        from src.rag.vectorstore import IndexingProgress
        
        progress = IndexingProgress(total=1000)
        progress.start()
        progress._start_time = time.time() - 10
        progress.update(500)
        
        # when
        speed = progress.get_speed()
        
        # then
        assert speed == pytest.approx(50.0, rel=0.1)

    def test_진행률_퍼센트_계산(self):
        """200개 중 50개 처리 시 25% 반환"""
        # given
        from src.rag.vectorstore import IndexingProgress
        
        progress = IndexingProgress(total=200)
        progress.update(50)
        
        # when
        percent = progress.get_percent()
        
        # then
        assert percent == 25.0


class TestAsyncIndexing:
    """비동기 인덱싱 테스트"""

    @pytest.fixture
    def mock_async_vectorstore(self):
        """비동기 지원 Mock VectorStore"""
        from src.rag.vectorstore import ReviewVectorStore
        
        with patch.object(ReviewVectorStore, '__init__', lambda self, **kwargs: None):
            store = ReviewVectorStore()
            store.persist_directory = "./test_chroma"
            store.collection_name = "test_reviews"
            store.embeddings = MagicMock()
            store._vectorstore = MagicMock()
            return store

    @pytest.fixture
    def large_documents(self) -> List[Document]:
        """테스트용 문서"""
        return [
            Document(
                page_content=f"리뷰 {i}",
                metadata={"review_id": f"review_{i}", "rating": 5}
            )
            for i in range(100)
        ]

    @pytest.mark.asyncio
    async def test_비동기_배치_처리(self, mock_async_vectorstore, large_documents):
        """비동기로 100개 문서 처리 성공"""
        # when
        result = await mock_async_vectorstore.add_documents_async(
            documents=large_documents,
            batch_size=25,
            max_concurrent=4
        )
        
        # then
        assert result["processed"] == 100
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_동시_배치_수_제한(self, mock_async_vectorstore, large_documents):
        """max_concurrent=2 시 세마포어로 동시 처리 제한"""
        # given
        max_concurrent = 2
        
        # when
        result = await mock_async_vectorstore.add_documents_async(
            documents=large_documents,
            batch_size=25,
            max_concurrent=max_concurrent
        )
        
        # then
        assert result["success"] is True
        assert result["processed"] == len(large_documents)


class TestDynamicBatchSize:
    """동적 배치 크기 조절 테스트"""

    def test_메모리_기반_배치_크기_계산(self):
        """1024MB 메모리 + 1KB 문서 기준 배치 크기 계산"""
        # given
        from src.rag.vectorstore import calculate_optimal_batch_size
        
        # when
        batch_size = calculate_optimal_batch_size(
            available_memory_mb=1024,
            avg_doc_size_bytes=1000
        )
        
        # then
        assert batch_size > 0
        assert batch_size <= 1000

    def test_최소_배치_크기_보장(self):
        """메모리 부족 시에도 min_batch_size 보장"""
        # given
        from src.rag.vectorstore import calculate_optimal_batch_size
        
        # when
        batch_size = calculate_optimal_batch_size(
            available_memory_mb=1,
            avg_doc_size_bytes=1000000,
            min_batch_size=10
        )
        
        # then
        assert batch_size >= 10

    def test_최대_배치_크기_제한(self):
        """메모리 충분해도 max_batch_size 제한"""
        # given
        from src.rag.vectorstore import calculate_optimal_batch_size
        
        # when
        batch_size = calculate_optimal_batch_size(
            available_memory_mb=100000,
            avg_doc_size_bytes=100,
            max_batch_size=500
        )
        
        # then
        assert batch_size <= 500
