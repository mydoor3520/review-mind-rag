"""
검색 품질 평가 메트릭 단위 테스트

RetrievalMetrics, RetrievalEvaluator 클래스의 기능을 검증합니다.
"""

import pytest
import math
from src.analysis.metrics import (
    RetrievalMetrics,
    RetrievalEvaluator,
    EvaluationResult,
)


class TestReciprocalRank:
    """Reciprocal Rank 테스트"""
    
    def test_첫번째_위치에_관련문서(self):
        """첫 번째 위치에 관련 문서가 있으면 1.0 반환"""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc1"}
        
        rr = RetrievalMetrics.reciprocal_rank(retrieved, relevant)
        
        assert rr == 1.0
    
    def test_두번째_위치에_관련문서(self):
        """두 번째 위치에 관련 문서가 있으면 0.5 반환"""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc2"}
        
        rr = RetrievalMetrics.reciprocal_rank(retrieved, relevant)
        
        assert rr == 0.5
    
    def test_세번째_위치에_관련문서(self):
        """세 번째 위치에 관련 문서가 있으면 1/3 반환"""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc3"}
        
        rr = RetrievalMetrics.reciprocal_rank(retrieved, relevant)
        
        assert rr == pytest.approx(1/3, rel=1e-9)
    
    def test_관련문서_없음(self):
        """관련 문서가 없으면 0.0 반환"""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc4"}
        
        rr = RetrievalMetrics.reciprocal_rank(retrieved, relevant)
        
        assert rr == 0.0
    
    def test_빈_검색_결과(self):
        """검색 결과가 비어있으면 0.0 반환"""
        retrieved = []
        relevant = {"doc1"}
        
        rr = RetrievalMetrics.reciprocal_rank(retrieved, relevant)
        
        assert rr == 0.0


class TestMeanReciprocalRank:
    """MRR 테스트"""
    
    def test_MRR_계산(self):
        """여러 쿼리의 MRR을 정확히 계산한다"""
        results = [
            {"retrieved": ["a", "b", "c"], "relevant": ["a"]},
            {"retrieved": ["a", "b", "c"], "relevant": ["b"]},
            {"retrieved": ["a", "b", "c"], "relevant": ["c"]},
        ]
        
        mrr = RetrievalMetrics.mean_reciprocal_rank(results)
        
        expected = (1.0 + 0.5 + 1/3) / 3
        assert mrr == pytest.approx(expected, rel=1e-9)
    
    def test_빈_결과_리스트(self):
        """결과 리스트가 비어있으면 0.0 반환"""
        mrr = RetrievalMetrics.mean_reciprocal_rank([])
        
        assert mrr == 0.0


class TestHitRate:
    """Hit Rate 테스트"""
    
    def test_적중(self):
        """관련 문서가 있으면 1.0 반환"""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc2"}
        
        hr = RetrievalMetrics.hit_rate(retrieved, relevant)
        
        assert hr == 1.0
    
    def test_미적중(self):
        """관련 문서가 없으면 0.0 반환"""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc4"}
        
        hr = RetrievalMetrics.hit_rate(retrieved, relevant)
        
        assert hr == 0.0
    
    def test_k_제한_적중(self):
        """k 제한 내에 관련 문서가 있으면 1.0 반환"""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc2"}
        
        hr = RetrievalMetrics.hit_rate(retrieved, relevant, k=3)
        
        assert hr == 1.0
    
    def test_k_제한_미적중(self):
        """k 제한 밖에 관련 문서가 있으면 0.0 반환"""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc5"}
        
        hr = RetrievalMetrics.hit_rate(retrieved, relevant, k=3)
        
        assert hr == 0.0


class TestNDCG:
    """NDCG 테스트"""
    
    def test_완벽한_순위(self):
        """완벽한 순위면 1.0 반환"""
        retrieved = ["rel1", "rel2", "irr1"]
        relevant = {"rel1", "rel2"}
        
        ndcg = RetrievalMetrics.ndcg(retrieved, relevant)
        
        assert ndcg == 1.0
    
    def test_역순위(self):
        """역순위면 1.0 미만 반환"""
        retrieved = ["irr1", "rel1", "rel2"]
        relevant = {"rel1", "rel2"}
        
        ndcg = RetrievalMetrics.ndcg(retrieved, relevant)
        
        assert ndcg < 1.0
        assert ndcg > 0.0
    
    def test_관련문서_없음(self):
        """관련 문서가 없으면 0.0 반환"""
        retrieved = ["irr1", "irr2", "irr3"]
        relevant = {"rel1"}
        
        ndcg = RetrievalMetrics.ndcg(retrieved, relevant)
        
        assert ndcg == 0.0
    
    def test_k_제한(self):
        """k 제한이 적용된다"""
        retrieved = ["rel1", "irr1", "irr2", "rel2"]
        relevant = {"rel1", "rel2"}
        
        ndcg_k2 = RetrievalMetrics.ndcg(retrieved, relevant, k=2)
        ndcg_all = RetrievalMetrics.ndcg(retrieved, relevant)
        
        assert ndcg_k2 != ndcg_all


class TestPrecisionAtK:
    """Precision@K 테스트"""
    
    def test_precision_at_1_적중(self):
        """첫 번째가 관련 문서면 P@1 = 1.0"""
        retrieved = ["rel1", "irr1", "irr2"]
        relevant = {"rel1"}
        
        p_at_1 = RetrievalMetrics.precision_at_k(retrieved, relevant, k=1)
        
        assert p_at_1 == 1.0
    
    def test_precision_at_1_미적중(self):
        """첫 번째가 비관련 문서면 P@1 = 0.0"""
        retrieved = ["irr1", "rel1", "irr2"]
        relevant = {"rel1"}
        
        p_at_1 = RetrievalMetrics.precision_at_k(retrieved, relevant, k=1)
        
        assert p_at_1 == 0.0
    
    def test_precision_at_3(self):
        """상위 3개 중 2개가 관련 문서면 P@3 = 2/3"""
        retrieved = ["rel1", "irr1", "rel2", "irr2"]
        relevant = {"rel1", "rel2"}
        
        p_at_3 = RetrievalMetrics.precision_at_k(retrieved, relevant, k=3)
        
        assert p_at_3 == pytest.approx(2/3, rel=1e-9)
    
    def test_k가_0이면_0반환(self):
        """k가 0이면 0.0 반환"""
        retrieved = ["rel1", "rel2"]
        relevant = {"rel1", "rel2"}
        
        p_at_0 = RetrievalMetrics.precision_at_k(retrieved, relevant, k=0)
        
        assert p_at_0 == 0.0


class TestRecallAtK:
    """Recall@K 테스트"""
    
    def test_recall_at_k_전체포함(self):
        """모든 관련 문서가 상위 k개에 포함되면 1.0"""
        retrieved = ["rel1", "rel2", "irr1"]
        relevant = {"rel1", "rel2"}
        
        r_at_3 = RetrievalMetrics.recall_at_k(retrieved, relevant, k=3)
        
        assert r_at_3 == 1.0
    
    def test_recall_at_k_일부포함(self):
        """일부 관련 문서만 상위 k개에 포함"""
        retrieved = ["rel1", "irr1", "irr2", "rel2"]
        relevant = {"rel1", "rel2"}
        
        r_at_2 = RetrievalMetrics.recall_at_k(retrieved, relevant, k=2)
        
        assert r_at_2 == 0.5
    
    def test_관련문서_없으면_0(self):
        """관련 문서가 없으면 0.0"""
        retrieved = ["doc1", "doc2"]
        relevant = set()
        
        r_at_2 = RetrievalMetrics.recall_at_k(retrieved, relevant, k=2)
        
        assert r_at_2 == 0.0


class TestRetrievalEvaluator:
    """RetrievalEvaluator 테스트"""
    
    def test_evaluate_전체메트릭(self):
        """evaluate가 모든 메트릭을 계산한다"""
        results = [
            {"query": "q1", "retrieved": ["rel1", "irr1"], "relevant": ["rel1"]},
            {"query": "q2", "retrieved": ["irr1", "rel1"], "relevant": ["rel1"]},
        ]
        
        evaluator = RetrievalEvaluator(k_values=[1, 3])
        eval_result = evaluator.evaluate(results)
        
        assert eval_result.num_queries == 2
        assert 0 < eval_result.mrr <= 1
        assert 0 <= eval_result.hit_rate <= 1
        assert 0 <= eval_result.ndcg <= 1
        assert 1 in eval_result.precision_at_k
        assert 3 in eval_result.precision_at_k
    
    def test_빈_결과(self):
        """빈 결과 리스트에서도 동작한다"""
        evaluator = RetrievalEvaluator()
        eval_result = evaluator.evaluate([])
        
        assert eval_result.num_queries == 0
        assert eval_result.mrr == 0.0
    
    def test_compare_baseline_reranked(self):
        """baseline과 reranked 결과를 비교한다"""
        baseline = [
            {"retrieved": ["irr1", "rel1"], "relevant": ["rel1"]},
        ]
        reranked = [
            {"retrieved": ["rel1", "irr1"], "relevant": ["rel1"]},
        ]
        
        evaluator = RetrievalEvaluator()
        comparison = evaluator.compare(baseline, reranked)
        
        assert "baseline" in comparison
        assert "reranked" in comparison
        assert "improvement" in comparison
        assert comparison["reranked"]["mrr"] > comparison["baseline"]["mrr"]


class TestEvaluationResult:
    """EvaluationResult 테스트"""
    
    def test_to_dict(self):
        """to_dict가 올바른 형식을 반환한다"""
        result = EvaluationResult(
            mrr=0.75,
            hit_rate=0.8,
            ndcg=0.6,
            precision_at_k={1: 0.5, 3: 0.33},
            recall_at_k={1: 0.25, 3: 0.5},
            num_queries=10
        )
        
        d = result.to_dict()
        
        assert d["mrr"] == 0.75
        assert d["num_queries"] == 10
        assert 1 in d["precision_at_k"]
