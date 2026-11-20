"""
Adaptive Retrieval Budget Module (E11 Baseline & Adaptive Budget Comparison).

Dynamically selects retrieval depth k in [min_k, max_k] (bounded between 3 and 10)
based on:
1. Query complexity score and multi-part requirements.
2. Cross-lingual / language difficulty signals.
3. Post-retrieval score slope / elbow drop-off detection.

Preserves fixed k=5 as the control baseline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from app.models.schemas import QueryAnalysis, QueryLanguage, QuestionType


@dataclass
class BudgetDecision:
    selected_k: int
    reason: str
    features: dict[str, Any] = field(default_factory=dict)
    fixed_k_baseline: int = 5

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_k": self.selected_k,
            "reason": self.reason,
            "features": self.features,
            "fixed_k_baseline": self.fixed_k_baseline,
        }


class AdaptiveBudgetRetriever:
    """
    Selects retrieval depth k adaptively bounded between min_k (3) and max_k (10).
    """

    def __init__(
        self,
        min_k: int = 3,
        max_k: int = 10,
        fixed_k: int = 5,
        elbow_drop_threshold: float = 0.35,  # 35% drop from previous candidate indicates elbow
    ):
        self.min_k = min_k
        self.max_k = max_k
        self.fixed_k = fixed_k
        self.elbow_drop_threshold = elbow_drop_threshold

    def determine_candidate_budget(self, query_analysis: QueryAnalysis) -> BudgetDecision:
        """
        Pre-retrieval heuristic budget based on query complexity and language.
        """
        complexity = query_analysis.complexity_score or 0.0
        lang = query_analysis.detected_language
        is_multi_part = query_analysis.is_multi_part
        q_type = query_analysis.query_type

        features = {
            "complexity_score": complexity,
            "is_multi_part": is_multi_part,
            "language": lang.value if hasattr(lang, "value") else str(lang),
            "question_type": q_type.value if hasattr(q_type, "value") else str(q_type),
        }

        # High complexity multi-part: expand budget to max_k
        if is_multi_part or complexity >= 0.7:
            k = min(self.max_k, 8)
            return BudgetDecision(
                selected_k=k,
                reason=f"Multi-part/high-complexity query (complexity={complexity:.2f}): expanded budget to {k}.",
                features=features,
                fixed_k_baseline=self.fixed_k,
            )

        # Cross-lingual Devanagari Hindi or Code-mixed: moderate expansion
        if lang in (QueryLanguage.HINDI, QueryLanguage.CODE_MIXED):
            k = 6
            return BudgetDecision(
                selected_k=k,
                reason=f"Cross-lingual query ({lang.value}): expanded budget to {k} to ensure candidate coverage.",
                features=features,
                fixed_k_baseline=self.fixed_k,
            )

        # Simple direct English query
        if lang == QueryLanguage.ENGLISH and q_type == QuestionType.DIRECT and complexity <= 0.2 and not is_multi_part:
            k = max(self.min_k, 3)
            return BudgetDecision(
                selected_k=k,
                reason=f"Simple English query (complexity={complexity:.2f}): tightened budget to {k}.",
                features=features,
                fixed_k_baseline=self.fixed_k,
            )

        # Standard default
        return BudgetDecision(
            selected_k=self.fixed_k,
            reason="Standard query profile: maintained default budget k=5.",
            features=features,
            fixed_k_baseline=self.fixed_k,
        )

    def prune_by_score_elbow(
        self,
        candidates: List[Tuple[str, float, dict]],
        initial_budget: int,
    ) -> Tuple[List[Tuple[str, float, dict]], BudgetDecision]:
        """
        Post-retrieval truncation using score drop-off / elbow detection.
        If a steep drop in similarity occurs between adjacent ranks, prune early.
        """
        pool = candidates[:initial_budget]
        if len(pool) <= self.min_k:
            return pool, BudgetDecision(
                selected_k=len(pool),
                reason=f"Candidate pool size ({len(pool)}) at or below min_k ({self.min_k}).",
                fixed_k_baseline=self.fixed_k,
            )

        # Look for score drop-off
        scores = [score for pid, score, meta in pool]
        pruned_k = len(pool)
        elbow_index = None

        for idx in range(self.min_k, len(scores)):
            prev_s = scores[idx - 1]
            curr_s = scores[idx]
            if prev_s > 0:
                rel_drop = (prev_s - curr_s) / prev_s
                if rel_drop >= self.elbow_drop_threshold:
                    elbow_index = idx
                    pruned_k = idx
                    break

        pruned_candidates = pool[:pruned_k]
        reason = (
            f"Elbow detected at rank {elbow_index} with relative score drop >= {self.elbow_drop_threshold:.0%}: pruned from {len(pool)} to {pruned_k}."
            if elbow_index is not None
            else f"No steep drop-off detected: retained full budget k={pruned_k}."
        )

        return pruned_candidates, BudgetDecision(
            selected_k=pruned_k,
            reason=reason,
            features={"initial_budget": initial_budget, "final_k": pruned_k, "scores": [round(s, 4) for s in scores[:pruned_k]]},
            fixed_k_baseline=self.fixed_k,
        )


_adaptive_budget_retriever = AdaptiveBudgetRetriever()


def get_adaptive_budget_retriever() -> AdaptiveBudgetRetriever:
    return _adaptive_budget_retriever

