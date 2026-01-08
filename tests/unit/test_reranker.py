"""
Reranker 단위 테스트

KoreanReranker 클래스의 기능을 검증합니다.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys


class MockDocument:
    """테스트용 Document Mock"""
    def __init__(self, page_content: str, metadata: dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}


class TestKoreanRerankerInit:
    """KoreanReranker 초기화 테스트"""
    
    def test_sentence_transformers_미설치시_ImportError(self):
        """sentence-transformers가 없으면 ImportError 발생"""
        with patch.dict('sys.modules', {'sentence_transformers': None}):
            with patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', False):
                from src.rag.reranker import KoreanReranker
                
                with pytest.raises(ImportError) as exc_info:
                    KoreanReranker()
                
                assert "sentence-transformers" in str(exc_info.value)
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_기본_모델명_설정(self, mock_cross_encoder):
        """기본 모델명이 ko-reranker로 설정된다"""
        from src.rag.reranker import KoreanReranker
        
        reranker = KoreanReranker()
        
        assert reranker.model_name == "Dongjin-kr/ko-reranker"
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_커스텀_모델명_설정(self, mock_cross_encoder):
        """커스텀 모델명을 설정할 수 있다"""
        from src.rag.reranker import KoreanReranker
        
        custom_model = "BAAI/bge-reranker-v2-m3"
        reranker = KoreanReranker(model_name=custom_model)
        
        assert reranker.model_name == custom_model
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_기본_파라미터_설정(self, mock_cross_encoder):
        """기본 파라미터가 올바르게 설정된다"""
        from src.rag.reranker import KoreanReranker
        
        reranker = KoreanReranker()
        
        assert reranker.top_n == 5
        assert reranker.score_threshold == 0.0
        assert reranker.max_length == 512


class TestKoreanRerankerRerank:
    """KoreanReranker.rerank 테스트"""
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_빈_문서_리스트_처리(self, mock_cross_encoder):
        """빈 문서 리스트는 빈 리스트 반환"""
        from src.rag.reranker import KoreanReranker
        
        reranker = KoreanReranker()
        result = reranker.rerank("test query", [])
        
        assert result == []
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_문서_점수순_정렬(self, mock_cross_encoder):
        """문서가 점수 내림차순으로 정렬된다"""
        from src.rag.reranker import KoreanReranker
        
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.3, 0.9, 0.5]
        mock_cross_encoder.return_value = mock_model
        
        reranker = KoreanReranker()
        reranker._model = mock_model
        
        docs = [
            MockDocument(page_content="문서1", metadata={}),
            MockDocument(page_content="문서2", metadata={}),
            MockDocument(page_content="문서3", metadata={}),
        ]
        
        result = reranker.rerank("test query", docs)
        
        assert result[0].page_content == "문서2"
        assert result[1].page_content == "문서3"
        assert result[2].page_content == "문서1"
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_top_n_제한(self, mock_cross_encoder):
        """top_n 개수만큼만 반환한다"""
        from src.rag.reranker import KoreanReranker
        
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.9, 0.8, 0.7, 0.6, 0.5]
        mock_cross_encoder.return_value = mock_model
        
        reranker = KoreanReranker(top_n=3)
        reranker._model = mock_model
        
        docs = [
            MockDocument(page_content=f"문서{i}", metadata={})
            for i in range(5)
        ]
        
        result = reranker.rerank("test query", docs)
        
        assert len(result) == 3
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_score_threshold_적용(self, mock_cross_encoder):
        """score_threshold 이하 점수는 제외한다"""
        from src.rag.reranker import KoreanReranker
        
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.8, 0.2, 0.1]
        mock_cross_encoder.return_value = mock_model
        
        reranker = KoreanReranker(top_n=5, score_threshold=0.3)
        reranker._model = mock_model
        
        docs = [
            MockDocument(page_content=f"문서{i}", metadata={})
            for i in range(3)
        ]
        
        result = reranker.rerank("test query", docs)
        
        assert len(result) == 1
        assert result[0].page_content == "문서0"
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_rerank_score_메타데이터_추가(self, mock_cross_encoder):
        """리랭킹 점수가 메타데이터에 추가된다"""
        from src.rag.reranker import KoreanReranker
        
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.85]
        mock_cross_encoder.return_value = mock_model
        
        reranker = KoreanReranker()
        reranker._model = mock_model
        
        docs = [MockDocument(page_content="테스트 문서", metadata={"rating": 5})]
        
        result = reranker.rerank("test query", docs)
        
        assert "rerank_score" in result[0].metadata
        assert result[0].metadata["rerank_score"] == 0.85
        assert result[0].metadata["rating"] == 5


class TestKoreanRerankerRerankWithScores:
    """KoreanReranker.rerank_with_scores 테스트"""
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_문서와_점수_함께_반환(self, mock_cross_encoder):
        """문서와 점수를 튜플로 반환한다"""
        from src.rag.reranker import KoreanReranker
        
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.7, 0.9]
        mock_cross_encoder.return_value = mock_model
        
        reranker = KoreanReranker()
        reranker._model = mock_model
        
        docs = [
            MockDocument(page_content="문서1", metadata={}),
            MockDocument(page_content="문서2", metadata={}),
        ]
        
        result = reranker.rerank_with_scores("test query", docs)
        
        assert len(result) == 2
        assert result[0][0].page_content == "문서2"
        assert result[0][1] == 0.9
        assert result[1][0].page_content == "문서1"
        assert result[1][1] == 0.7


class TestRerankerFactory:
    """RerankerFactory 테스트"""
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_korean_타입_생성(self, mock_cross_encoder):
        """korean 타입은 ko-reranker 모델 사용"""
        from src.rag.reranker import RerankerFactory
        
        reranker = RerankerFactory.create("korean")
        
        assert reranker.model_name == "Dongjin-kr/ko-reranker"
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_multilingual_타입_생성(self, mock_cross_encoder):
        """multilingual 타입은 bge-reranker 모델 사용"""
        from src.rag.reranker import RerankerFactory
        
        reranker = RerankerFactory.create("multilingual")
        
        assert reranker.model_name == "BAAI/bge-reranker-v2-m3"
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_기본_타입_korean(self, mock_cross_encoder):
        """알 수 없는 타입은 korean으로 기본 설정"""
        from src.rag.reranker import RerankerFactory
        
        reranker = RerankerFactory.create("unknown_type")
        
        assert reranker.model_name == "Dongjin-kr/ko-reranker"
    
    @patch('src.rag.reranker.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    @patch('src.rag.reranker.CrossEncoder')
    def test_추가_파라미터_전달(self, mock_cross_encoder):
        """추가 파라미터가 전달된다"""
        from src.rag.reranker import RerankerFactory
        
        reranker = RerankerFactory.create("korean", top_n=10, score_threshold=0.5)
        
        assert reranker.top_n == 10
        assert reranker.score_threshold == 0.5
