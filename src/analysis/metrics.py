"""
검색 품질 평가 메트릭 모듈

RAG 시스템의 검색 품질을 측정하기 위한 메트릭을 제공합니다.
"""

from typing import List, Dict, Any, Optional, Set, Union
from dataclasses import dataclass, field
import math


@dataclass
class EvaluationResult:
    """평가 결과를 담는 데이터 클래스"""
    mrr: float = 0.0
    hit_rate: float = 0.0
    ndcg: float = 0.0
    precision_at_k: Dict[int, float] = field(default_factory=dict)
    recall_at_k: Dict[int, float] = field(default_factory=dict)
    num_queries: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mrr": round(self.mrr, 4),
            "hit_rate": round(self.hit_rate, 4),
            "ndcg": round(self.ndcg, 4),
            "precision_at_k": {k: round(v, 4) for k, v in self.precision_at_k.items()},
            "recall_at_k": {k: round(v, 4) for k, v in self.recall_at_k.items()},
            "num_queries": self.num_queries,
        }


class RetrievalMetrics:
    """검색 품질 평가 메트릭 클래스"""
    
    @staticmethod
    def reciprocal_rank(
        retrieved_ids: List[str],
        relevant_ids: Set[str]
    ) -> float:
        """
        Reciprocal Rank를 계산합니다.
        
        :param retrieved_ids: 검색된 문서 ID 리스트 (순서 유지)
        :param relevant_ids: 관련 문서 ID 집합
        :return: 1/rank (첫 번째 관련 문서의 역순위), 없으면 0
        """
        for i, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in relevant_ids:
                return 1.0 / i
        return 0.0
    
    @staticmethod
    def mean_reciprocal_rank(
        results: List[Dict[str, Any]]
    ) -> float:
        """
        Mean Reciprocal Rank (MRR)를 계산합니다.
        
        :param results: [{"retrieved": [...], "relevant": {...}}, ...] 형식
        :return: MRR 점수 (0~1)
        """
        if not results:
            return 0.0
        
        total_rr = sum(
            RetrievalMetrics.reciprocal_rank(
                r["retrieved"],
                set(r["relevant"])
            )
            for r in results
        )
        return total_rr / len(results)
    
    @staticmethod
    def hit_rate(
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        k: Optional[int] = None
    ) -> float:
        """
        Hit Rate (Recall@1의 일반화)를 계산합니다.
        
        :param retrieved_ids: 검색된 문서 ID 리스트
        :param relevant_ids: 관련 문서 ID 집합
        :param k: 상위 k개만 고려 (None이면 전체)
        :return: 1 (적중) 또는 0 (미적중)
        """
        if k is not None:
            retrieved_ids = retrieved_ids[:k]
        
        for doc_id in retrieved_ids:
            if doc_id in relevant_ids:
                return 1.0
        return 0.0
    
    @staticmethod
    def mean_hit_rate(
        results: List[Dict[str, Any]],
        k: Optional[int] = None
    ) -> float:
        """
        평균 Hit Rate를 계산합니다.
        
        :param results: [{"retrieved": [...], "relevant": {...}}, ...] 형식
        :param k: 상위 k개만 고려
        :return: 평균 Hit Rate (0~1)
        """
        if not results:
            return 0.0
        
        total_hits = sum(
            RetrievalMetrics.hit_rate(
                r["retrieved"],
                set(r["relevant"]),
                k
            )
            for r in results
        )
        return total_hits / len(results)
    
    @staticmethod
    def dcg(relevance_scores: List[float]) -> float:
        """
        Discounted Cumulative Gain을 계산합니다.
        
        :param relevance_scores: 관련성 점수 리스트 (순서대로)
        :return: DCG 점수
        """
        if not relevance_scores:
            return 0.0
        
        return sum(
            rel / math.log2(i + 2)
            for i, rel in enumerate(relevance_scores)
        )
    
    @staticmethod
    def ndcg(
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        k: Optional[int] = None
    ) -> float:
        """
        Normalized Discounted Cumulative Gain을 계산합니다.
        
        :param retrieved_ids: 검색된 문서 ID 리스트
        :param relevant_ids: 관련 문서 ID 집합
        :param k: 상위 k개만 고려
        :return: NDCG 점수 (0~1)
        """
        if k is not None:
            retrieved_ids = retrieved_ids[:k]
        
        relevance_scores = [
            1.0 if doc_id in relevant_ids else 0.0
            for doc_id in retrieved_ids
        ]
        
        dcg = RetrievalMetrics.dcg(relevance_scores)
        
        ideal_scores = sorted(relevance_scores, reverse=True)
        idcg = RetrievalMetrics.dcg(ideal_scores)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    @staticmethod
    def mean_ndcg(
        results: List[Dict[str, Any]],
        k: Optional[int] = None
    ) -> float:
        """
        평균 NDCG를 계산합니다.
        
        :param results: [{"retrieved": [...], "relevant": {...}}, ...] 형식
        :param k: 상위 k개만 고려
        :return: 평균 NDCG (0~1)
        """
        if not results:
            return 0.0
        
        total_ndcg = sum(
            RetrievalMetrics.ndcg(
                r["retrieved"],
                set(r["relevant"]),
                k
            )
            for r in results
        )
        return total_ndcg / len(results)
    
    @staticmethod
    def precision_at_k(
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        k: int
    ) -> float:
        """
        Precision@K를 계산합니다.
        
        :param retrieved_ids: 검색된 문서 ID 리스트
        :param relevant_ids: 관련 문서 ID 집합
        :param k: 상위 k개
        :return: Precision@K (0~1)
        """
        if k <= 0:
            return 0.0
        
        top_k = retrieved_ids[:k]
        if not top_k:
            return 0.0
        
        relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant_ids)
        return relevant_in_top_k / len(top_k)
    
    @staticmethod
    def recall_at_k(
        retrieved_ids: List[str],
        relevant_ids: Set[str],
        k: int
    ) -> float:
        """
        Recall@K를 계산합니다.
        
        :param retrieved_ids: 검색된 문서 ID 리스트
        :param relevant_ids: 관련 문서 ID 집합
        :param k: 상위 k개
        :return: Recall@K (0~1)
        """
        if not relevant_ids or k <= 0:
            return 0.0
        
        top_k = retrieved_ids[:k]
        relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant_ids)
        return relevant_in_top_k / len(relevant_ids)


class RetrievalEvaluator:
    """검색 시스템 평가기"""
    
    def __init__(self, k_values: List[int] = None):
        """
        :param k_values: Precision@K, Recall@K 계산에 사용할 k 값들
        """
        self.k_values = k_values or [1, 3, 5, 10]
        self.metrics = RetrievalMetrics()
    
    def evaluate(
        self,
        results: List[Dict[str, Any]]
    ) -> EvaluationResult:
        """
        전체 평가를 수행합니다.
        
        :param results: 평가 데이터 리스트
            [{"query": "...", "retrieved": ["id1", "id2"], "relevant": ["id1"]}, ...]
        :return: EvaluationResult
        """
        if not results:
            return EvaluationResult()
        
        mrr = self.metrics.mean_reciprocal_rank(results)
        hit_rate = self.metrics.mean_hit_rate(results)
        ndcg = self.metrics.mean_ndcg(results)
        
        precision_at_k = {}
        recall_at_k = {}
        
        for k in self.k_values:
            p_at_k_scores = [
                self.metrics.precision_at_k(
                    r["retrieved"],
                    set(r["relevant"]),
                    k
                )
                for r in results
            ]
            precision_at_k[k] = sum(p_at_k_scores) / len(p_at_k_scores)
            
            r_at_k_scores = [
                self.metrics.recall_at_k(
                    r["retrieved"],
                    set(r["relevant"]),
                    k
                )
                for r in results
            ]
            recall_at_k[k] = sum(r_at_k_scores) / len(r_at_k_scores)
        
        return EvaluationResult(
            mrr=mrr,
            hit_rate=hit_rate,
            ndcg=ndcg,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            num_queries=len(results)
        )
    
    def compare(
        self,
        baseline_results: List[Dict[str, Any]],
        reranked_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Baseline과 Reranked 결과를 비교합니다.
        
        :param baseline_results: 기본 검색 결과
        :param reranked_results: 리랭킹 후 결과
        :return: 비교 결과
        """
        baseline_eval = self.evaluate(baseline_results)
        reranked_eval = self.evaluate(reranked_results)
        
        def calc_improvement(baseline: float, reranked: float) -> float:
            if baseline == 0:
                return 0.0 if reranked == 0 else float('inf')
            return ((reranked - baseline) / baseline) * 100
        
        return {
            "baseline": baseline_eval.to_dict(),
            "reranked": reranked_eval.to_dict(),
            "improvement": {
                "mrr": round(calc_improvement(baseline_eval.mrr, reranked_eval.mrr), 2),
                "hit_rate": round(calc_improvement(baseline_eval.hit_rate, reranked_eval.hit_rate), 2),
                "ndcg": round(calc_improvement(baseline_eval.ndcg, reranked_eval.ndcg), 2),
            }
        }
    
    def generate_report(
        self,
        results: List[Dict[str, Any]],
        title: str = "검색 품질 평가 리포트"
    ) -> str:
        """
        평가 리포트를 생성합니다.
        
        :param results: 평가 데이터
        :param title: 리포트 제목
        :return: 마크다운 형식 리포트
        """
        eval_result = self.evaluate(results)
        
        report = f"""# {title}

## 요약
- **평가 쿼리 수**: {eval_result.num_queries}
- **MRR (Mean Reciprocal Rank)**: {eval_result.mrr:.4f}
- **Hit Rate**: {eval_result.hit_rate:.4f}
- **NDCG**: {eval_result.ndcg:.4f}

## Precision@K
| K | Precision |
|---|-----------|
"""
        for k, p in sorted(eval_result.precision_at_k.items()):
            report += f"| {k} | {p:.4f} |\n"
        
        report += """
## Recall@K
| K | Recall |
|---|--------|
"""
        for k, r in sorted(eval_result.recall_at_k.items()):
            report += f"| {k} | {r:.4f} |\n"
        
        report += """
## 해석
- **MRR**: 첫 번째 관련 문서의 평균 역순위 (1에 가까울수록 좋음)
- **Hit Rate**: 관련 문서가 결과에 포함된 쿼리 비율
- **NDCG**: 순위를 고려한 검색 품질 (1에 가까울수록 좋음)
- **Precision@K**: 상위 K개 중 관련 문서 비율
- **Recall@K**: 전체 관련 문서 중 상위 K개에 포함된 비율
"""
        return report
