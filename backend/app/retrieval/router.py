"""
Adaptive Query Routing Module (E2 Baseline & Adaptive Comparison).

Routes incoming queries to optimal retrieval strategies based on:
1. Detected language and script (English, Devanagari Hindi, Hinglish, Romanized Hindi).
2. Query complexity score (0.0 to 1.0).
3. Presence of exact numerical anchors, clause identifiers, percentages, and dates.
4. Multi-part structure and multi-evidence needs.

Deterministic, machine-readable routing decisions with safe fallback to Hybrid RRF.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.core.logging_config import logger
from app.models.schemas import QueryAnalysis, QueryLanguage, QueryScript, QuestionType


class RoutingStrategy(str, Enum):
    HYBRID_RRF = "hybrid_rrf"                       # Standard BM25 + Dense (Fixed baseline)
    BM25_LEXICAL = "bm25_lexical"                   # Pure lexical for exact clauses/numbers
    DENSE_SEMANTIC = "dense_semantic"               # Semantic vector for conceptual/paraphrased
    CROSS_LINGUAL_MQR = "cross_lingual_mqr"         # Dense + MQR for Devanagari/Hinglish
    TRANSLATION_ASSISTED = "translation_assisted"   # Translation path + Hybrid


@dataclass
class RoutingDecision:
    strategy: RoutingStrategy
    reason: str
    features: dict[str, Any] = field(default_factory=dict)
    fallback_strategy: RoutingStrategy = RoutingStrategy.HYBRID_RRF

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "reason": self.reason,
            "features": self.features,
            "fallback_strategy": self.fallback_strategy.value,
        }


# Exact regulatory anchors: clause numbers, percentages, dates, course codes
_EXACT_ANCHOR_PATTERNS = [
    r"\bclause\s*\d+(\.\d+)*\b",
    r"\b\d+(\.\d+)?%\b",
    r"\b(70%|75%|60%|65%|10%|30%)\b",
    r"\b(grade\s*[oabcdfx]|'x'|'i'|\"x\"|\"i\")\b",
    r"\b(cgpa|sgpa|gpa)\b",
    r"\b(2022-23|2026-27|2017-18|2023-24)\b",
    r"\bnotification\s*(307|307/2022)\b",
    r"\b\d{2}-\d{2}-\d{4}\b",  # DD-MM-YYYY dates
]
_EXACT_ANCHOR_RE = re.compile("|".join(_EXACT_ANCHOR_PATTERNS), re.IGNORECASE)


class AdaptiveRouter:
    """
    Deterministic adaptive router comparing fixed hybrid RRF with
    feature-conditioned dynamic retrieval routing.
    """

    def __init__(self, default_strategy: RoutingStrategy = RoutingStrategy.HYBRID_RRF):
        self.default_strategy = default_strategy

    def route(self, query_analysis: QueryAnalysis) -> RoutingDecision:
        """
        Evaluate query features and return deterministic RoutingDecision.
        """
        query_text = query_analysis.normalized_query or query_analysis.original_query
        lang = query_analysis.detected_language
        script = query_analysis.detected_script
        q_type = query_analysis.query_type
        complexity = query_analysis.complexity_score or 0.0
        is_multi_part = query_analysis.is_multi_part

        # 1. Feature extraction
        has_exact_anchor = bool(_EXACT_ANCHOR_RE.search(query_text))
        has_devanagari = (script == QueryScript.DEVANAGARI) or (lang == QueryLanguage.HINDI)
        has_translation = bool(query_analysis.translated_query)

        features = {
            "language": lang.value if hasattr(lang, "value") else str(lang),
            "script": script.value if hasattr(script, "value") else str(script),
            "complexity_score": complexity,
            "is_multi_part": is_multi_part,
            "has_exact_anchor": has_exact_anchor,
            "has_translation": has_translation,
            "question_type": q_type.value if hasattr(q_type, "value") else str(q_type),
        }

        # 2. Decision Tree Policy

        # Policy Rule 1: Devanagari Script with translation available
        if has_devanagari and has_translation:
            return RoutingDecision(
                strategy=RoutingStrategy.TRANSLATION_ASSISTED,
                reason="Devanagari query with available English translation: routes to translation-assisted hybrid.",
                features=features,
            )

        # Policy Rule 2: Devanagari Script without translation
        if has_devanagari:
            return RoutingDecision(
                strategy=RoutingStrategy.CROSS_LINGUAL_MQR,
                reason="Devanagari query with English corpus: routes to dense multilingual retrieval with MQR.",
                features=features,
            )

        # Policy Rule 3: Complex Multi-part or decomposed query
        if is_multi_part or complexity >= 0.6:
            return RoutingDecision(
                strategy=RoutingStrategy.CROSS_LINGUAL_MQR,
                reason="High-complexity or multi-part query: routes to MQR for multi-evidence coverage.",
                features=features,
            )

        # Policy Rule 4: English with exact regulatory anchors (clauses, grades, percentages)
        if lang == QueryLanguage.ENGLISH and has_exact_anchor:
            return RoutingDecision(
                strategy=RoutingStrategy.BM25_LEXICAL,
                reason="English query with exact regulatory anchors: routes to BM25 lexical precision.",
                features=features,
            )

        # Policy Rule 5: Romanized Hindi without exact English anchors
        if lang == QueryLanguage.ROMANIZED_HINDI and not has_exact_anchor:
            return RoutingDecision(
                strategy=RoutingStrategy.DENSE_SEMANTIC,
                reason="Romanized Hindi conversational query: routes to dense semantic matching.",
                features=features,
            )

        # Default / Safe Fallback: Standard Hybrid RRF
        return RoutingDecision(
            strategy=RoutingStrategy.HYBRID_RRF,
            reason="Standard balanced query: routes to fixed Hybrid RRF baseline.",
            features=features,
        )


# Global singleton
_router = AdaptiveRouter()


def route_query(query_analysis: QueryAnalysis) -> RoutingDecision:
    """Entry point for adaptive query routing."""
    return _router.route(query_analysis)

