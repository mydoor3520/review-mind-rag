"""
ReviewQAChain 통합 테스트

RAG QA 체인의 통합 테스트입니다.
LLM 호출은 Mock으로 대체합니다.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from langchain.schema import Document


class TestReviewQAChainInit:
    """초기화 테스트"""

    def test_기본_파라미터_초기화(self):
        """기본 파라미터로 초기화된다"""
        # given
        from src.rag.chain import ReviewQAChain
        
        mock_vectorstore = MagicMock()

        # when
        with patch('src.rag.chain.ChatOpenAI'):
            chain = ReviewQAChain(vectorstore=mock_vectorstore)

        # then
        assert chain.vectorstore == mock_vectorstore
        assert chain._qa_chain is None  # lazy initialization

    def test_커스텀_모델_설정(self):
        """커스텀 모델과 temperature를 설정할 수 있다"""
        # given
        from src.rag.chain import ReviewQAChain
        
        mock_vectorstore = MagicMock()

        with patch('src.rag.chain.ChatOpenAI') as mock_llm_class:
            # when
            chain = ReviewQAChain(
                vectorstore=mock_vectorstore,
                model_name="gpt-4",
                temperature=0.5
            )

            # then
            mock_llm_class.assert_called_once_with(
                model="gpt-4",
                temperature=0.5
            )


class TestReviewQAChainAsk:
    """ask() 메서드 테스트"""

    @pytest.fixture
    def mock_chain_setup(self):
        """Mock 체인 설정"""
        from src.rag.chain import ReviewQAChain
        
        mock_vectorstore = MagicMock()
        
        with patch('src.rag.chain.ChatOpenAI') as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm_class.return_value = mock_llm
            
            chain = ReviewQAChain(vectorstore=mock_vectorstore)
            yield chain, mock_llm

    def test_기본_질문_응답(self, mock_chain_setup):
        """기본 질문에 대해 응답을 생성한다"""
        # given
        chain, mock_llm = mock_chain_setup
        
        with patch('src.rag.chain.RetrievalQA') as mock_qa_class:
            mock_qa = MagicMock()
            mock_qa.invoke.return_value = {
                "result": "이 제품은 음질이 매우 좋다는 평가가 많습니다.",
                "source_documents": [
                    Document(page_content="음질 좋음", metadata={"rating": 5})
                ]
            }
            mock_qa_class.from_chain_type.return_value = mock_qa

            # when
            result = chain.ask("이 제품 음질이 어때?")

            # then
            assert "answer" in result
            assert "source_documents" in result
            assert "question" in result
            assert result["question"] == "이 제품 음질이 어때?"

    def test_필터_적용_질문(self, mock_chain_setup):
        """카테고리 필터를 적용한 질문"""
        # given
        chain, mock_llm = mock_chain_setup
        
        with patch('src.rag.chain.RetrievalQA') as mock_qa_class:
            mock_qa = MagicMock()
            mock_qa.invoke.return_value = {
                "result": "전자제품 리뷰에서는...",
                "source_documents": []
            }
            mock_qa_class.from_chain_type.return_value = mock_qa

            # when
            result = chain.ask(
                "배터리 수명은?",
                category="Electronics"
            )

            # then
            assert "answer" in result
            # RetrievalQA.from_chain_type이 두 번 호출됨 (필터 있을 때 새로 생성)
            assert mock_qa_class.from_chain_type.call_count >= 1


class TestReviewQAChainSummarizeProduct:
    """summarize_product() 메서드 테스트"""

    def test_상품_요약_생성(self):
        """특정 상품의 리뷰를 요약한다"""
        # given
        from src.rag.chain import ReviewQAChain
        
        mock_vectorstore = MagicMock()
        
        with patch('src.rag.chain.ChatOpenAI') as mock_llm_class:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(
                content="## 장점\n- 음질이 좋음\n## 단점\n- 가격이 비쌈"
            )
            mock_llm_class.return_value = mock_llm
            
            chain = ReviewQAChain(vectorstore=mock_vectorstore)
            
            # Mock retriever
            chain.retriever = MagicMock()
            chain.retriever.search_by_product.return_value = [
                Document(page_content="음질이 좋습니다", metadata={"rating": 5}),
                Document(page_content="가격이 비싸요", metadata={"rating": 3}),
            ]

            # when
            result = chain.summarize_product("B001")

            # then
            assert "summary" in result
            assert "review_count" in result
            assert result["review_count"] == 2
            assert "장점" in result["summary"]

    def test_리뷰_없는_상품_요약(self):
        """리뷰가 없는 상품 요약 시 적절한 메시지 반환"""
        # given
        from src.rag.chain import ReviewQAChain
        
        mock_vectorstore = MagicMock()
        
        with patch('src.rag.chain.ChatOpenAI'):
            chain = ReviewQAChain(vectorstore=mock_vectorstore)
            chain.retriever = MagicMock()
            chain.retriever.search_by_product.return_value = []

            # when
            result = chain.summarize_product("NONEXISTENT")

            # then
            assert result["review_count"] == 0
            assert "찾을 수 없습니다" in result["summary"]


class TestReviewQAChainCompareProducts:
    """compare_products() 메서드 테스트"""

    def test_두_상품_비교(self):
        """두 상품의 리뷰를 비교한다"""
        # given
        from src.rag.chain import ReviewQAChain
        
        mock_vectorstore = MagicMock()
        
        with patch('src.rag.chain.ChatOpenAI') as mock_llm_class:
            mock_llm = MagicMock()
            # 요약 호출
            mock_llm.invoke.side_effect = [
                MagicMock(content="## 장점\n- 상품1 좋음"),  # 첫 번째 상품 요약
                MagicMock(content="## 장점\n- 상품2 좋음"),  # 두 번째 상품 요약
                MagicMock(content="## 비교 분석\n상품1이 더 좋습니다")  # 비교
            ]
            mock_llm_class.return_value = mock_llm
            
            chain = ReviewQAChain(vectorstore=mock_vectorstore)
            chain.retriever = MagicMock()
            chain.retriever.search_by_product.return_value = [
                Document(page_content="좋은 제품", metadata={"rating": 5})
            ]

            # when
            result = chain.compare_products("B001", "B002")

            # then
            assert "comparison" in result
            assert "product_1" in result
            assert "product_2" in result


class TestReviewQAChainPromptTemplate:
    """프롬프트 템플릿 테스트"""

    def test_기본_QA_프롬프트_포함_내용(self):
        """기본 QA 프롬프트에 필수 지시사항이 포함되어 있다"""
        # given
        from src.rag.chain import ReviewQAChain

        # then
        prompt = ReviewQAChain.DEFAULT_QA_PROMPT
        assert "리뷰" in prompt
        assert "context" in prompt
        assert "question" in prompt
        assert "한국어" in prompt

    def test_기본_요약_프롬프트_포함_내용(self):
        """기본 요약 프롬프트에 필수 섹션이 포함되어 있다"""
        # given
        from src.rag.chain import ReviewQAChain

        # then
        prompt = ReviewQAChain.DEFAULT_SUMMARY_PROMPT
        assert "장점" in prompt
        assert "단점" in prompt
        assert "종합 평가" in prompt
