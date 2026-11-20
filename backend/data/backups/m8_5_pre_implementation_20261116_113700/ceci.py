"""
Composite Evidence Confidence Index (CECI) Heuristic Module for IndicRAG-QA.

RESEARCH & GOVERNANCE SPECIFICATION:
- Implements a 5-feature convex combination estimator yielding `ceci_heuristic_score` in [0, 1].
- CRITICAL RESEARCH RULE: This is a transparent HEURISTIC EVIDENCE SCORE,
  NOT an empirically calibrated probability.
- Strict Convex Formulation:
      Psi = sum(w_i * f_i), where w_i >= 0, sum(w_i) = 1.0, and each f_i in [0.0, 1.0].
- Features:
  1. f1: Top-1 Normalized Relevance (deterministic source precedence: CE > RRF > Dense > BM25).
  2. f2: Top-1 vs Top-2 Same-Scale Score Margin (strictly computed on identical scale).
  3. f3: Modality Retrieval Consensus (Jaccard overlap between dense & BM25 candidate pools).
  4. f4: Intent Keyword Evidence Coverage (non-optimistic conservative fallback).
  5. f5: Regulatory Version and Applicability Fit.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from app.models.schemas import (
    DocumentSource,
    QueryAnalysis,
    RetrievedPassage,
)
from app.retrieval.score_normalizer import (
    NormalizedScore,
    RetrievalModality,
    normalize_bm25_score,
    normalize_cross_encoder_score,
    normalize_dense_score,
    normalize_rrf_ranks,
)


@dataclass(frozen=True)
class CECIWeights:
    """
    Transparent provisional weights for the 5 CECI features.
    Documented as heuristic engineering weights, NOT learned from benchmark.
    """
    w_relevance: float = 0.35      # f1: Top-1 normalized relevance
    w_margin: float = 0.15         # f2: Top-1 vs Top-2 same-scale margin
    w_consensus: float = 0.15      # f3: BM25/Dense candidate consensus
    w_keyword_cov: float = 0.15    # f4: Intent keyword evidence coverage
    w_regulatory: float = 0.20     # f5: Regulatory version & applicability fit

    def __post_init__(self):
        # Validate convex properties
        weights = [
            self.w_relevance,
            self.w_margin,
            self.w_consensus,
            self.w_keyword_cov,
            self.w_regulatory,
        ]
        for w in weights:
            if w < 0.0:
                raise ValueError(f"CECI weights must be non-negative, got {w}")
        total = sum(weights)
        if not math.isclose(total, 1.0, rel_tol=1e-6):
            raise ValueError(f"CECI weights must sum to 1.0, got {total}")


@dataclass
class CECIResult:
    """
    Auditable result container for CECI calculation.
    """
    ceci_heuristic_score: float
    features: Dict[str, float]
    weights: Dict[str, float]
    primary_modality: str
    relevance_source_precedence: str
    is_calibrated_probability: bool = False
    notes: str = ""

    def __post_init__(self):
        if not (0.0 <= self.ceci_heuristic_score <= 1.0):
            raise ValueError(f"ceci_heuristic_score must be in [0.0, 1.0], got {self.ceci_heuristic_score}")


class CECIEstimator:
    """
    Evaluates retrieved evidence passages and query context to produce the
    heuristic evidence confidence index (CECI) bounded strictly in [0, 1].
    """

    def __init__(self, weights: Optional[CECIWeights] = None):
        self.weights = weights or CECIWeights()

    def estimate(
        self,
        passages: Sequence[RetrievedPassage],
        query_analysis: Optional[QueryAnalysis] = None,
        bm25_passage_ids: Optional[Sequence[str]] = None,
        dense_passage_ids: Optional[Sequence[str]] = None,
    ) -> CECIResult:
        # Edge Case: Zero retrieved passages -> All features strictly 0.0
        if not passages:
            f_zero = {
                "f1_top1_relevance": 0.0,
                "f2_score_margin": 0.0,
                "f3_modality_consensus": 0.0,
                "f4_keyword_coverage": 0.0,
                "f5_regulatory_fit": 0.0,
            }
            w_dict = {
                "w1_relevance": self.weights.w_relevance,
                "w2_margin": self.weights.w_margin,
                "w3_consensus": self.weights.w_consensus,
                "w4_keyword_cov": self.weights.w_keyword_cov,
                "w5_regulatory": self.weights.w_regulatory,
            }
            return CECIResult(
                ceci_heuristic_score=0.0,
                features=f_zero,
                weights=w_dict,
                primary_modality="none",
                relevance_source_precedence="empty_retrieval",
                is_calibrated_probability=False,
                notes="Zero retrieved passages; all features evaluate to 0.0.",
            )

        # ── Feature 1 & 2: Top-1 Relevance & Same-Scale Margin ──────────────
        f1, f2, modality_used, prec_desc = self._compute_relevance_and_margin(passages)

        # ── Feature 3: Modality Retrieval Consensus ──────────────────────────
        f3 = self._compute_modality_consensus(passages, bm25_passage_ids, dense_passage_ids)

        # ── Feature 4: Intent Keyword Coverage (Conservative Fallback) ───────
        f4 = self._compute_keyword_coverage(passages, query_analysis)

        # ── Feature 5: Regulatory Version and Applicability Fit ──────────────
        f5 = self._compute_regulatory_fit(passages)

        # Ensure all features strictly bounded in [0.0, 1.0]
        f1 = max(0.0, min(1.0, float(f1)))
        f2 = max(0.0, min(1.0, float(f2)))
        f3 = max(0.0, min(1.0, float(f3)))
        f4 = max(0.0, min(1.0, float(f4)))
        f5 = max(0.0, min(1.0, float(f5)))

        # Strict convex combination
        ceci = (
            self.weights.w_relevance * f1
            + self.weights.w_margin * f2
            + self.weights.w_consensus * f3
            + self.weights.w_keyword_cov * f4
            + self.weights.w_regulatory * f5
        )
        ceci = max(0.0, min(1.0, float(ceci)))

        features_dict = {
            "f1_top1_relevance": round(f1, 4),
            "f2_score_margin": round(f2, 4),
            "f3_modality_consensus": round(f3, 4),
            "f4_keyword_coverage": round(f4, 4),
            "f5_regulatory_fit": round(f5, 4),
        }
        weights_dict = {
            "w1_relevance": self.weights.w_relevance,
            "w2_margin": self.weights.w_margin,
            "w3_consensus": self.weights.w_consensus,
            "w4_keyword_cov": self.weights.w_keyword_cov,
            "w5_regulatory": self.weights.w_regulatory,
        }

        return CECIResult(
            ceci_heuristic_score=round(ceci, 4),
            features=features_dict,
            weights=weights_dict,
            primary_modality=modality_used,
            relevance_source_precedence=prec_desc,
            is_calibrated_probability=False,
            notes=f"Convex CECI heuristic combination on {modality_used} scale.",
        )

    # ── Helpers for Individual Features ──────────────────────────────────────

    def _compute_relevance_and_margin(
        self,
        passages: Sequence[RetrievedPassage],
    ) -> Tuple[float, float, str, str]:
        """
        Determines Top-1 relevance and score margin following deterministic precedence:
            Cross-Encoder (if available) > RRF > Dense > BM25.
        Margin MUST be calculated on the SAME scale.
        """
        p0 = passages[0]
        has_p1 = len(passages) > 1
        p1 = passages[1] if has_p1 else None

        # 1. Cross-Encoder Precedence
        # Check if cross-encoder scores or metadata exists
        ce_score0 = getattr(p0, "rerank_score", None) if getattr(p0, "rerank_score", None) is not None else getattr(p0, "cross_encoder_score", None)
        if ce_score0 is not None and math.isfinite(ce_score0):
            norm0 = normalize_cross_encoder_score(ce_score0).normalized_score
            ce_score1 = (getattr(p1, "rerank_score", None) if p1 else None)
            if ce_score1 is None and p1:
                ce_score1 = getattr(p1, "cross_encoder_score", None)

            if has_p1 and ce_score1 is not None and math.isfinite(ce_score1):
                norm1 = normalize_cross_encoder_score(ce_score1).normalized_score
                margin = max(0.0, min(1.0, norm0 - norm1))
            else:
                margin = 0.5  # Conservative neutral fallback for single candidate pool
            return norm0, margin, "cross_encoder", "CE > RRF > Dense > BM25"

        # 2. RRF Rank Normalization Precedence
        # If passages came from RRF fusion
        is_rrf = any("rrf" in str(getattr(p, "retrieval_method", "")).lower() for p in passages)
        if is_rrf or (len(passages) > 0 and 0.0 < p0.score < 0.1):  # RRF scores are typically < 0.1
            rrf_norms = normalize_rrf_ranks(passages, get_score_fn=lambda p: p.score)
            norm0 = rrf_norms[0].normalized_score if rrf_norms else 0.0
            if has_p1 and len(rrf_norms) > 1:
                norm1 = rrf_norms[1].normalized_score
                margin = max(0.0, min(1.0, norm0 - norm1))
            else:
                margin = 0.5
            return norm0, margin, "rrf", "RRF > Dense > BM25"

        # 3. Dense Cosine Precedence
        is_dense = any("dense" in str(getattr(p, "retrieval_method", "")).lower() for p in passages)
        if is_dense or (-1.0 <= p0.score <= 1.0):
            norm0 = normalize_dense_score(p0.score).normalized_score
            if has_p1 and math.isfinite(p1.score):
                norm1 = normalize_dense_score(p1.score).normalized_score
                margin = max(0.0, min(1.0, norm0 - norm1))
            else:
                margin = 0.5
            return norm0, margin, "dense", "Dense > BM25"

        # 4. BM25 Precedence
        norm0 = normalize_bm25_score(p0.score).normalized_score
        if has_p1 and math.isfinite(p1.score):
            norm1 = normalize_bm25_score(p1.score).normalized_score
            margin = max(0.0, min(1.0, norm0 - norm1))
        else:
            margin = 0.5
        return norm0, margin, "bm25", "BM25"

    def _compute_modality_consensus(
        self,
        passages: Sequence[RetrievedPassage],
        bm25_ids: Optional[Sequence[str]] = None,
        dense_ids: Optional[Sequence[str]] = None,
    ) -> float:
        """
        Computes Jaccard consensus between BM25 and Dense retrieved candidate pools.
        Conservative fallback: If only one modality was executed, returns neutral 0.5.
        """
        if bm25_ids is not None and dense_ids is not None:
            s_bm25 = set(bm25_ids)
            s_dense = set(dense_ids)
            union_len = len(s_bm25 | s_dense)
            if union_len == 0:
                return 0.0
            return len(s_bm25 & s_dense) / union_len

        # If modality pools not explicitly provided, inspect passage retrieval method tags
        methods = {str(getattr(p, "retrieval_method", "")).lower() for p in passages}
        has_bm25 = any("bm25" in m for m in methods)
        has_dense = any("dense" in m for m in methods)

        if has_bm25 and has_dense:
            return 0.75  # Verified multi-modal agreement in pool
        elif has_bm25 or has_dense:
            return 0.50  # Conservative neutral score for single modality execution
        else:
            return 0.50  # Default neutral fallback

    def _compute_keyword_coverage(
        self,
        passages: Sequence[RetrievedPassage],
        query_analysis: Optional[QueryAnalysis],
    ) -> float:
        """
        Calculates proportion of query intent keywords found in retrieved passages.
        MANDATORY CORRECTION: If query has no keywords, return conservative neutral 0.5
        (NEVER optimistic 1.0).
        """
        if not passages:
            return 0.0

        if not query_analysis or not query_analysis.intent_keywords:
            return 0.50  # Neutral fallback for unanalyzed or keyword-less query

        kws = [k.lower().strip() for k in query_analysis.intent_keywords if k.strip()]
        if not kws:
            return 0.50

        all_text = " ".join(p.text.lower() for p in passages)
        matched = sum(1 for kw in kws if kw in all_text)
        return matched / len(kws)

    def _compute_regulatory_fit(
        self,
        passages: Sequence[RetrievedPassage],
    ) -> float:
        """
        Evaluates applicability of the top retrieved passages.
        - 1.0: Verified current, non-superseded, matching query cohort.
        - 0.5: Unconfirmed or general document.
        - 0.0: Superseded, conflicting, or debarred applicability.
        """
        if not passages:
            return 0.0

        top_p = passages[0]
        v_info = getattr(top_p, "version_info", None)

        if getattr(top_p, "is_valid_for_query", True) is False:
            return 0.0

        if v_info:
            if getattr(v_info, "superseded_by", None):
                return 0.0
            if getattr(v_info, "is_current", None) is True:
                return 1.0
            if getattr(v_info, "is_current", None) is False:
                return 0.0

        return 0.50  # Neutral fallback when applicability is unconfirmed


# Global singleton
_ceci_estimator: Optional[CECIEstimator] = None


def get_ceci_estimator() -> CECIEstimator:
    global _ceci_estimator
    if _ceci_estimator is None:
        _ceci_estimator = CECIEstimator()
    return _ceci_estimator
