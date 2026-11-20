"""
Unit and integration tests for M5 Advanced RAG Phase 2 components:
- Adaptive Router (E2)
- Translation-Assisted Retrieval & Fallbacks (E3)
- Fixed-Window Chunking Comparison & Provenance (E5)
- Adaptive Retrieval Budget (E11)
- Version-Aware Academic Year Filtering (E8)
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from app.core.config import settings
from app.models.schemas import QueryAnalysis, QueryLanguage, QueryScript, QuestionType
from app.query.processor import (
    TranslationResult,
    process_query,
    translate_query_to_english,
)
from app.retrieval.adaptive_budget import (
    AdaptiveBudgetRetriever,
    BudgetDecision,
    get_adaptive_budget_retriever,
)
from app.retrieval.engine import (
    RetrieverIndex,
    get_official_index,
    validate_versions,
)
from app.retrieval.router import (
    AdaptiveRouter,
    RoutingDecision,
    RoutingStrategy,
    route_query,
)


# ─── 1. Adaptive Router Tests (E2) ─────────────────────────────────────────────

class TestAdaptiveRouter:

    def test_english_with_exact_anchors_routes_to_lexical(self):
        """English queries with explicit clauses/percentages route to BM25 lexical precision."""
        analysis = process_query("What is the attendance requirement in Clause 30.1 of SCSET UG?")
        decision = route_query(analysis)
        assert decision.strategy == RoutingStrategy.BM25_LEXICAL
        assert "exact regulatory anchors" in decision.reason
        assert decision.features["has_exact_anchor"] is True

    def test_devanagari_hindi_without_translation_routes_to_mqr(self):
        """Devanagari queries without prior translation route to dense cross-lingual MQR."""
        analysis = process_query("कक्षाएं शुरू होने के बाद छात्र कितने समय में विषय जोड़ सकते हैं?")
        decision = route_query(analysis)
        assert decision.strategy == RoutingStrategy.CROSS_LINGUAL_MQR
        assert "Devanagari query with English corpus" in decision.reason

    def test_devanagari_hindi_with_translation_routes_to_translation(self):
        """Devanagari query with translated text routes to translation-assisted hybrid."""
        analysis = process_query("कक्षाएं शुरू होने के बाद छात्र कितने समय में विषय जोड़ सकते हैं?")
        analysis.translated_query = "Within how much time can students add a course after classes start?"
        decision = route_query(analysis)
        assert decision.strategy == RoutingStrategy.TRANSLATION_ASSISTED
        assert "available English translation" in decision.reason

    def test_romanized_hindi_routes_to_dense(self):
        """Conversational Romanized Hindi queries without rule numbers route to dense semantic search."""
        analysis = process_query("semester khatam hone se kitne hafte pehle tak course se withdraw kar sakte hain?")
        decision = route_query(analysis)
        assert decision.strategy == RoutingStrategy.DENSE_SEMANTIC
        assert "Romanized Hindi conversational query" in decision.reason

    def test_safe_fallback_to_hybrid(self):
        """Standard queries default safely to fixed Hybrid RRF."""
        analysis = process_query("Tell me about university degree award conditions.")
        decision = route_query(analysis)
        assert decision.strategy == RoutingStrategy.HYBRID_RRF
        assert decision.fallback_strategy == RoutingStrategy.HYBRID_RRF


# ─── 2. Translation-Assisted Retrieval Tests (E3) ──────────────────────────────

class TestTranslationAssistedRetrieval:

    def test_translation_english_noop(self):
        """English queries are not translated, returning immediately with zero overhead."""
        res = translate_query_to_english("What is the duration of B.Tech?", QueryLanguage.ENGLISH)
        assert res.fallback_occurred is False
        assert res.translated_query == "What is the duration of B.Tech?"
        assert res.latency_ms == 0.0

    def test_translation_mock_success(self):
        """Non-English query translates successfully, preserving original query unchanged."""
        original = "कक्षाएं कब शुरू होंगी?"
        mock_caller = MagicMock(return_value="When will classes start?")
        res = translate_query_to_english(
            original,
            QueryLanguage.HINDI,
            custom_caller=mock_caller,
        )
        assert res.fallback_occurred is False
        assert res.translated_query == "When will classes start?"
        assert res.original_query == original
        mock_caller.assert_called_once()

    def test_translation_timeout_fallback(self):
        """Ollama timeout triggers graceful fallback without raising unhandled exception."""
        def timeout_caller(prompt, system):
            raise httpx.TimeoutException("Ollama timed out after 30s")

        original = "उपस्थिति माफी के नियम क्या हैं?"
        res = translate_query_to_english(
            original,
            QueryLanguage.HINDI,
            custom_caller=timeout_caller,
        )
        assert res.fallback_occurred is True
        assert res.translated_query is None
        assert res.original_query == original
        assert "timed out" in (res.error_message or "")

    def test_translation_unavailable_model_fallback(self):
        """Unavailable model or HTTP error falls back to direct retrieval."""
        def error_caller(prompt, system):
            req = httpx.Request("POST", "http://localhost:11434/api/generate")
            raise httpx.HTTPStatusError("Model not found", request=req, response=httpx.Response(404, request=req))

        original = "attendance kitni chahiye?"
        res = translate_query_to_english(
            original,
            QueryLanguage.ROMANIZED_HINDI,
            custom_caller=error_caller,
        )
        assert res.fallback_occurred is True
        assert res.translated_query is None
        assert res.original_query == original

    def test_original_query_preserved_in_process_query(self):
        """Original user query is strictly preserved in QueryAnalysis under all translation modes."""
        raw = "परीक्षा के नियम क्या हैं?"
        analysis = process_query(raw, enable_translation=False)
        assert analysis.original_query == raw
        assert analysis.detected_language == QueryLanguage.HINDI


# ─── 3. Adaptive Retrieval Budget Tests (E11) ──────────────────────────────────

class TestAdaptiveBudgetRetriever:

    def test_budget_bounds_enforced(self):
        """Budget k is strictly bounded within [min_k, max_k] = [3, 10]."""
        retriever = get_adaptive_budget_retriever()
        for complexity in [0.0, 0.2, 0.5, 0.8, 1.0]:
            analysis = process_query("Sample question")
            analysis.complexity_score = complexity
            decision = retriever.determine_candidate_budget(analysis)
            assert retriever.min_k <= decision.selected_k <= retriever.max_k

    def test_simple_english_tight_budget(self):
        """Simple English query receives minimal budget (k=3) for low-latency retrieval."""
        retriever = get_adaptive_budget_retriever()
        analysis = process_query("What is B.Tech?")
        decision = retriever.determine_candidate_budget(analysis)
        assert decision.selected_k == 3
        assert "tightened budget" in decision.reason

    def test_complex_multipart_expanded_budget(self):
        """Multi-part / complex queries expand budget (k=8) to guarantee candidate recall."""
        retriever = get_adaptive_budget_retriever()
        analysis = process_query("What are the conditions for degree award and how many credits are needed for Honors?")
        analysis.is_multi_part = True
        analysis.complexity_score = 0.8
        decision = retriever.determine_candidate_budget(analysis)
        assert decision.selected_k >= 6
        assert "expanded budget" in decision.reason

    def test_score_elbow_pruning(self):
        """Score drop-off >= 35% triggers elbow pruning before max_k."""
        retriever = AdaptiveBudgetRetriever(min_k=3, max_k=8, elbow_drop_threshold=0.35)
        # Mock candidates with sharp drop at rank 4 (0.80 -> 0.40)
        candidates = [
            ("p1", 0.95, {}),
            ("p2", 0.90, {}),
            ("p3", 0.85, {}),
            ("p4", 0.45, {}),  # > 40% drop from 0.85
            ("p5", 0.40, {}),
            ("p6", 0.35, {}),
        ]
        pruned, decision = retriever.prune_by_score_elbow(candidates, initial_budget=6)
        assert len(pruned) == 3
        assert decision.selected_k == 3
        assert "Elbow detected" in decision.reason

    def test_fixed_k_baseline_recorded(self):
        """Fixed k=5 is preserved in BudgetDecision as experimental control baseline."""
        retriever = get_adaptive_budget_retriever()
        analysis = process_query("General regulations question")
        decision = retriever.determine_candidate_budget(analysis)
        assert decision.fixed_k_baseline == 5


# ─── 4. Fixed-Window Chunking Provenance Tests (E5) ────────────────────────────

class TestFixedWindowChunkingProvenance:

    def test_fixed_window_index_exists(self):
        """Fixed-window comparison index exists with FAISS vectors and metadata."""
        idx_dir = settings.indexes_dir / "fixed_window"
        assert (idx_dir / "faiss.index").exists(), "fixed_window faiss.index must exist"
        assert (idx_dir / "meta.pkl").exists(), "fixed_window meta.pkl must exist"

    def test_fixed_window_provenance_and_metadata(self):
        """Fixed-window index contains valid passage provenance without missing metadata."""
        idx = RetrieverIndex("fixed_window")
        assert idx.load() is True
        assert len(idx.passage_ids) == 165
        assert len(idx.passage_texts) == 165
        assert len(idx.passage_meta) == 165

        # Check first passage provenance
        meta0 = idx.passage_meta[0]
        assert meta0["chunking_strategy"] == "fixed_window"
        assert meta0["document_id"] == "b787fd22-eb2f-42ed-9ef7-ef098e5ff8b6"
        assert meta0["page_number"] >= 1
        assert "text" in meta0

    def test_official_structure_aware_corpus_untouched(self):
        """Official structure-aware corpus remains at least 142 passages with valid SHA-256."""
        official_idx = get_official_index()
        assert official_idx.is_ready()
        assert len(official_idx.passage_ids) >= 142

        # Verify hash
        conn = sqlite3.connect(str(settings.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT passage_id, text FROM passages WHERE parent_passage_id IS NOT NULL ORDER BY passage_id")
        rows = cursor.fetchall()
        conn.close()

        hasher = hashlib.sha256()
        for pid, text in rows:
            hasher.update(pid.encode("utf-8"))
            hasher.update(text.encode("utf-8"))
        h = hasher.hexdigest()
        assert h in (
            "8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d",
            "c414cee2c2ce35b6c628f4fb4ada50804dd96d574ea9b373f68c53f29f35f111",
        )


# ─── 5. Version-Aware Academic Year Filtering Tests (E8) ───────────────────────

class TestVersionValidationAcademicYear:

    def test_version_validation_ay_mismatch_demoted(self):
        """Passages from conflicting academic years are demoted and flagged without silent deletion."""
        candidates = [
            ("p_current", 0.9, {"academic_year": "2022-23 onwards", "is_current": True}),
            ("p_historical", 0.85, {"academic_year": "2017-18", "is_current": False}),
        ]
        # Query specifies academic year 2026-27
        validated = validate_versions(candidates, academic_year="2026-27")
        assert len(validated) == 2
        # p_current covers onwards, so retains full score
        assert validated[0][0] == "p_current"
        assert validated[0][1] == pytest.approx(0.9)
        # p_historical is demoted by 0.5x
        assert validated[1][0] == "p_historical"
        assert validated[1][1] == pytest.approx(0.85 * 0.5)
        assert validated[1][2]["_version_flag"] == "academic_year_mismatch"

