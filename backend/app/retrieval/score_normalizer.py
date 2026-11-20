"""
Transparent Score Normalization Module for IndicRAG-QA.

RESEARCH & GOVERNANCE SPECIFICATION:
- This module implements heuristic, theory-anchored score normalizers across distinct
  retrieval modalities (BM25, Dense Cosine, Cross-Encoder, and RRF Rank Fusion).
- CRITICAL RESEARCH RULE: These transformations are HEURISTIC NORMALIZERS designed to
  map disparate score scales into the bounded interval [0, 1] without silent mixing.
- They are NOT empirically fitted calibration parameters, NOT empirical Platt scaling,
  and their outputs MUST NEVER be interpreted or claimed as calibrated probabilities of relevance.
- Every transformation preserves the original raw retrieval score in execution traces.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


class RetrievalModality(str, Enum):
    BM25 = "bm25"
    DENSE = "dense"
    CROSS_ENCODER = "cross_encoder"
    RRF = "rrf"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class NormalizedScore:
    """
    Holds both raw score and transformed score with explicit provenance.
    Never claims probability calibration.
    """
    raw_score: float
    normalized_score: float
    modality: RetrievalModality
    is_empirically_calibrated: bool = False
    transformation_notes: str = ""

    def __post_init__(self):
        # Validate that normalized score is finite and strictly within [0.0, 1.0]
        if not math.isfinite(self.normalized_score):
            raise ValueError(f"Normalized score must be finite, got {self.normalized_score}")
        if not (0.0 <= self.normalized_score <= 1.0):
            raise ValueError(f"Normalized score must be in [0.0, 1.0], got {self.normalized_score}")


def _sigmoid(x: float) -> float:
    """Stable sigmoid implementation with boundary clamping for extreme values."""
    if not math.isfinite(x):
        return 0.0
    if x > 35.0:
        return 1.0
    if x < -35.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


# ─── 1. BM25 Provisional Corpus-Anchored Sigmoid ─────────────────────────────

# Provisional operating parameters based on corpus size and median term match scores
BM25_PROVISIONAL_CENTER: float = 15.0
BM25_PROVISIONAL_SCALE: float = 3.0


def normalize_bm25_score(
    raw_score: float,
    center: float = BM25_PROVISIONAL_CENTER,
    scale: float = BM25_PROVISIONAL_SCALE,
) -> NormalizedScore:
    """
    Transforms raw BM25 score to [0, 1] via corpus-anchored sigmoid:
        sigmoid((bm25_score - 15.0) / 3.0)

    NOTE: center=15.0 and scale=3.0 are provisional operating parameters,
    NOT empirically fitted calibration parameters.
    """
    if not math.isfinite(raw_score) or raw_score < 0.0:
        norm_val = 0.0
    else:
        norm_val = _sigmoid((raw_score - center) / scale)
        norm_val = max(0.0, min(1.0, norm_val))

    return NormalizedScore(
        raw_score=raw_score if math.isfinite(raw_score) else -1.0,
        normalized_score=norm_val,
        modality=RetrievalModality.BM25,
        is_empirically_calibrated=False,
        transformation_notes=f"Provisional sigmoid(center={center}, scale={scale}); heuristic normalizer.",
    )


# ─── 2. Dense Cosine Prior-Anchored Logistic ─────────────────────────────────

def normalize_dense_score(
    raw_score: float,
    a: float = 1.0,
    b: float = 0.0,
) -> NormalizedScore:
    """
    Transforms dense cosine similarity (typically [-1, 1], observed in [0.3, 0.85])
    to [0, 1] using an un-shifted prior-anchored bounded logistic with A=1.0, B=0.0:
        sigmoid(1.0 * score + 0.0)

    NOTE: This is a bounded monotonic score normalizer, NOT a probability of relevance.
    """
    if math.isnan(raw_score):
        norm_val = 0.0
    elif math.isinf(raw_score):
        norm_val = 1.0 if raw_score > 0 else 0.0
    else:
        norm_val = _sigmoid(a * raw_score + b)
        norm_val = max(0.0, min(1.0, norm_val))

    return NormalizedScore(
        raw_score=raw_score if math.isfinite(raw_score) else 0.0,
        normalized_score=norm_val,
        modality=RetrievalModality.DENSE,
        is_empirically_calibrated=False,
        transformation_notes="Prior-anchored logistic(A=1.0, B=0.0); heuristic normalizer, not probability.",
    )


# ─── 3. Cross-Encoder Logit Logistic Transformation ──────────────────────────

def normalize_cross_encoder_score(
    raw_score: float,
    a: float = 1.0,
    b: float = 0.0,
) -> NormalizedScore:
    """
    Transforms raw cross-encoder logit (-inf, +inf) to [0, 1] using bounded logistic:
        sigmoid(1.0 * logit + 0.0)

    NOTE: Preserves original cross-encoder logit in raw_score. Does not claim probability calibration.
    """
    if math.isnan(raw_score):
        norm_val = 0.0
    elif math.isinf(raw_score):
        norm_val = 1.0 if raw_score > 0 else 0.0
    else:
        norm_val = _sigmoid(a * raw_score + b)
        norm_val = max(0.0, min(1.0, norm_val))

    return NormalizedScore(
        raw_score=raw_score if math.isfinite(raw_score) else 0.0,
        normalized_score=norm_val,
        modality=RetrievalModality.CROSS_ENCODER,
        is_empirically_calibrated=False,
        transformation_notes="Prior-anchored logistic(A=1.0, B=0.0); heuristic normalizer, not probability.",
    )


# ─── 4. RRF Rank-Based Normalization ─────────────────────────────────────────

def normalize_rrf_ranks(
    ranked_items: Sequence[Any],
    get_score_fn: Optional[Any] = None,
) -> List[NormalizedScore]:
    """
    Transforms an ordered list of RRF candidates into a normalized rank-based feature in [0, 1].

    Formula:
        For candidate at 1-based rank r in a pool of depth K:
            normalized_rrf(r) = (K - r + 1) / K

    Boundary conditions & tie handling:
        - If K == 1: normalized_rrf = 1.0.
        - If K == 0: returns empty list.
        - Ties: Candidates with identical raw RRF scores receive the average fractional rank
          of their tied group, ensuring strict determinism and fairness.
    """
    k = len(ranked_items)
    if k == 0:
        return []
    if k == 1:
        raw_val = get_score_fn(ranked_items[0]) if get_score_fn else 1.0
        return [
            NormalizedScore(
                raw_score=raw_val,
                normalized_score=1.0,
                modality=RetrievalModality.RRF,
                is_empirically_calibrated=False,
                transformation_notes="Single candidate pool; normalized rank = 1.0.",
            )
        ]

    # Extract raw scores
    raw_scores = []
    for item in ranked_items:
        val = get_score_fn(item) if get_score_fn else getattr(item, "score", 0.0)
        raw_scores.append(float(val) if math.isfinite(val) else 0.0)

    # Detect tied score groups
    # Group indices by raw score (with floating point tolerance 1e-9)
    tied_groups: Dict[float, List[int]] = {}
    for idx, sc in enumerate(raw_scores):
        rounded_sc = round(sc, 9)
        tied_groups.setdefault(rounded_sc, []).append(idx)

    normalized_scores: List[Optional[NormalizedScore]] = [None] * k

    # Assign fractional rank for each tied group
    for rounded_sc, indices in tied_groups.items():
        # 1-based ranks for these positions: e.g. indices [0, 1] -> ranks 1, 2 -> avg rank 1.5
        avg_rank = sum(i + 1 for i in indices) / len(indices)
        norm_val = (k - avg_rank + 1.0) / k
        norm_val = max(0.0, min(1.0, norm_val))

        for idx in indices:
            normalized_scores[idx] = NormalizedScore(
                raw_score=raw_scores[idx],
                normalized_score=norm_val,
                modality=RetrievalModality.RRF,
                is_empirically_calibrated=False,
                transformation_notes=f"RRF rank-based feature (pool depth K={k}, avg rank={avg_rank:.2f}).",
            )

    return [s for s in normalized_scores if s is not None]


# ─── 5. Unified Dispatcher ───────────────────────────────────────────────────

def normalize_retrieval_score(
    raw_score: float,
    modality: Union[str, RetrievalModality],
) -> NormalizedScore:
    """
    Unified entry point for score normalization.
    Preserves raw scale and logs transformations.
    """
    if isinstance(modality, str):
        try:
            modality = RetrievalModality(modality.lower())
        except ValueError:
            modality = RetrievalModality.UNKNOWN

    if modality == RetrievalModality.BM25:
        return normalize_bm25_score(raw_score)
    elif modality == RetrievalModality.DENSE:
        return normalize_dense_score(raw_score)
    elif modality == RetrievalModality.CROSS_ENCODER:
        return normalize_cross_encoder_score(raw_score)
    elif modality == RetrievalModality.RRF:
        # For single score without rank context, assume conservative normalized rank 0.5
        return NormalizedScore(
            raw_score=raw_score,
            normalized_score=0.5 if math.isfinite(raw_score) else 0.0,
            modality=RetrievalModality.RRF,
            is_empirically_calibrated=False,
            transformation_notes="Isolated RRF score without pool depth; assigned neutral median 0.5.",
        )
    else:
        # Unknown modality: if already in [0, 1] clip, else sigmoid
        if math.isfinite(raw_score) and 0.0 <= raw_score <= 1.0:
            norm_val = raw_score
        else:
            norm_val = _sigmoid(raw_score) if math.isfinite(raw_score) else 0.0
        return NormalizedScore(
            raw_score=raw_score if math.isfinite(raw_score) else 0.0,
            normalized_score=norm_val,
            modality=RetrievalModality.UNKNOWN,
            is_empirically_calibrated=False,
            transformation_notes="Unknown modality fallback normalizer.",
        )
