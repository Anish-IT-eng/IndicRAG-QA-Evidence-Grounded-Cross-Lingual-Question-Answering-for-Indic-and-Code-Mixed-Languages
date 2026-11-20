"""
Tests for M4 retrieval baselines: BM25, Dense FAISS, Hybrid RRF,
multilingual retrieval, duplicate handling, and regulatory version awareness.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from app.core.config import settings
from app.models.schemas import DocumentSource, QueryAnalysis, QueryLanguage
from app.retrieval.engine import (
    RetrieverIndex,
    _deduplicate,
    _rrf_fuse,
    get_official_index,
    retrieve,
)


@pytest.fixture(scope="module")
def official_index() -> RetrieverIndex:
    from app.retrieval import engine as _eng
    _eng._indexes.clear()
    idx = get_official_index()
    assert idx.is_ready(), "Official index must be loaded and ready"
    return idx


class TestRetrievalBaselines:
    """Baseline retrieval tests for BM25, Dense FAISS, and Hybrid RRF."""

    def test_bm25_retrieval_exact_terminology(self, official_index: RetrieverIndex):
        """BM25 successfully retrieves passages containing exact technical keywords."""
        query = "supplementary examination C+ grade"
        hits = official_index.bm25_search(query, top_k=5)
        assert len(hits) > 0
        pids = [pid for pid, score, meta in hits]
        # Candidate b0a1c007 gold passage
        assert "5f9028f1-69ee-4e2d-9aa0-68ca2f510deb" in pids
        # Scores must be positive and descending
        scores = [score for pid, score, meta in hits]
        assert all(s > 0 for s in scores)
        assert scores == sorted(scores, reverse=True)

    def test_dense_faiss_retrieval(self, official_index: RetrieverIndex):
        """Dense FAISS returns embeddings-based top-k with valid cosine similarities."""
        query = "What are the options for final semester internship or startup?"
        hits = official_index.dense_search(query, top_k=5)
        assert len(hits) == 5
        scores = [score for pid, score, meta in hits]
        # Cosine similarity on normalized vectors should be bounded in [-1, 1]
        assert all(-1.0 <= s <= 1.0 for s in scores)
        assert scores == sorted(scores, reverse=True)
        # Gold passage for final semester options
        pids = [pid for pid, score, meta in hits]
        assert "1731cce9-583a-44b6-a7e4-e4dda7776056" in pids

    def test_hybrid_rrf_fusion(self, official_index: RetrieverIndex):
        """Hybrid RRF mathematically fuses lexical and dense rankings."""
        query = "B.Tech minimum duration"
        bm25_hits = official_index.bm25_search(query, top_k=10)
        dense_hits = official_index.dense_search(query, top_k=10)
        fused = _rrf_fuse(bm25_hits, dense_hits, k=60, bm25_weight=1.0, dense_weight=1.0)
        assert len(fused) > 0
        fused_scores = [score for pid, score, meta in fused]
        # RRF scores must be monotonically non-increasing
        assert fused_scores == sorted(fused_scores, reverse=True)
        # Verify first item score calculation
        top_pid, top_score, _ = fused[0]
        # RRF score is sum of 1/(60+rank)
        assert 0.0 < top_score <= (1.0 / 61 + 1.0 / 61)

    def test_ranking_correctness(self, official_index: RetrieverIndex):
        """All retrieval modes return results strictly ordered by rank score descending."""
        query = "Academic Calendar 2026-27 attendance condonation"
        for search_fn in [official_index.bm25_search, official_index.dense_search]:
            hits = search_fn(query, top_k=5)
            scores = [s for _, s, _ in hits]
            assert scores == sorted(scores, reverse=True)


class TestMultilingualRetrieval:
    """Multilingual query coverage across Devanagari, Code-mixed, and Romanized Hindi."""

    def test_devanagari_hindi_retrieval(self, official_index: RetrieverIndex):
        """Devanagari Hindi query successfully retrieves the relevant calendar passage in Hybrid RRF."""
        query = "शैक्षणिक कैलेंडर 2026-27 के अनुसार विषम सेमेस्टर (Odd Semester) में उपस्थिति माफी (Attendance Condonation) के लिए आवेदन करने की अंतिम तिथि क्या है?"
        bm25_hits = official_index.bm25_search(query, top_k=10)
        dense_hits = official_index.dense_search(query, top_k=10)
        fused = _rrf_fuse(bm25_hits, dense_hits, k=60)[:5]
        pids = [pid for pid, score, meta in fused]
        # Academic calendar passage (Page 4, Odd Semester Condonation)
        assert "bbaac776-23eb-4535-85f9-6f181b238d3f" in pids

    def test_code_mixed_hinglish_retrieval(self, official_index: RetrieverIndex):
        """Code-mixed Hinglish query retrieves course withdrawal passage."""
        query = "Semester khatam hone se kitne hafte pehle tak course withdraw karne ki permission milti hai?"
        bm25_hits = official_index.bm25_search(query, top_k=10)
        pids = [pid for pid, score, meta in bm25_hits]
        # Gold passage for withdrawal
        assert "5fce6f7d-77a5-4f39-a240-072d84c12334" in pids

    def test_romanized_hindi_retrieval(self, official_index: RetrieverIndex):
        """Romanized Hindi query retrieves grade threshold passage via dense similarity."""
        query = "Courses ke liye D grade ki range kitne marks se shuru hoti hai?"
        dense_hits = official_index.dense_search(query, top_k=5)
        pids = [pid for pid, score, meta in dense_hits]
        # Gold passage for D grade (30 marks)
        assert "505e552e-35e0-4b5d-98ba-10dff85f4eab" in pids


class TestEdgeCasesAndDeduplication:
    """Robustness tests for empty queries, unanswerable queries, and duplicates."""

    def test_empty_query_returns_gracefully(self, official_index: RetrieverIndex):
        """Empty or whitespace-only queries do not crash."""
        hits_bm25 = official_index.bm25_search("", top_k=5)
        assert hits_bm25 == []

    def test_unanswerable_query_low_confidence(self, official_index: RetrieverIndex):
        """Out-of-scope query yields lower dense similarity compared to in-scope query."""
        unans_query = "What is the fee for submitting a PhD dissertation thesis in SCSET UG?"
        ans_query = "What is the minimum duration of the B.Tech program?"
        unans_hits = official_index.dense_search(unans_query, top_k=1)
        ans_hits = official_index.dense_search(ans_query, top_k=1)
        assert ans_hits[0][1] > unans_hits[0][1]

    def test_deduplicate_removes_redundant_passages(self):
        """Deduplication preserves rank order while dropping duplicate passage IDs."""
        raw = [
            ("p1", 0.9, {"doc": "d1"}),
            ("p2", 0.8, {"doc": "d1"}),
            ("p1", 0.7, {"doc": "d1"}),
            ("p3", 0.6, {"doc": "d2"}),
        ]
        deduped = _deduplicate(raw)
        assert len(deduped) == 3
        assert [pid for pid, _, _ in deduped] == ["p1", "p2", "p3"]
        assert deduped[0][1] == 0.9  # Preserves highest score


class TestRegulatoryVersionAwareness:
    """Controlled tests for historical vs. current attendance regulations."""

    def test_notification_307_retrieval_for_current_attendance(self, official_index: RetrieverIndex):
        """Query for 2022-23 attendance criteria retrieves Notification 307/2022 at Rank 1."""
        query = "What is the minimum attendance required to appear in the end semester examination for academic year 2022-23?"
        dense_hits = official_index.dense_search(query, top_k=1)
        assert len(dense_hits) == 1
        top_pid, top_score, meta = dense_hits[0]
        assert top_pid == "0280358a-ff3c-4964-88ab-419a9147b1f0"
        assert meta["effective_date"] == "2022-09-08"
        assert meta["is_current"] is True

    def test_clause_30_historical_retrievability(self, official_index: RetrieverIndex):
        """Clause 30.1(ii) (70% attendance) remains in index and retrievable."""
        clause_30_pid = "c31d716d-bcfe-4011-a3f6-f4a2d5f1f22b"
        assert clause_30_pid in official_index.passage_ids
        idx = official_index.passage_ids.index(clause_30_pid)
        text = official_index.passage_texts[idx]
        assert "70%" in text
        assert "Clause 30" in text or "30 Attendance Requirements" in text


class TestAdaptiveRouting:
    """Controlled unit tests for Candidate E6b Adaptive Bi-Encoder Routing."""

    def test_adaptive_devanagari_routes_to_bi_encoder(self):
        """Devanagari query under adaptive_e6b routes to dense bi-encoder and retrieves Notification 307."""
        from app.query.processor import process_query
        qa = process_query("एंड सेमेस्टर परीक्षा में बैठने के लिए न्यूनतम कितनी उपस्थिति आवश्यक है?")
        res = retrieve(qa, [DocumentSource.OFFICIAL], top_k=5, rerank_strategy="adaptive_e6b")
        pids = [p.passage_id for p in res.retrieved_passages]
        assert "0280358a-ff3c-4964-88ab-419a9147b1f0" in pids
        assert pids[0] == "0280358a-ff3c-4964-88ab-419a9147b1f0"

    def test_adaptive_preserves_english_cross_encoder(self):
        """English query under adaptive_e6b preserves production cross-encoder ranking."""
        from app.query.processor import process_query
        qa = process_query("What is the minimum attendance required to appear in the End Semester Examination?")
        res = retrieve(qa, [DocumentSource.OFFICIAL], top_k=5, rerank_strategy="adaptive_e6b")
        pids = [p.passage_id for p in res.retrieved_passages]
        assert "0280358a-ff3c-4964-88ab-419a9147b1f0" in pids
        assert pids[0] == "0280358a-ff3c-4964-88ab-419a9147b1f0"

    def test_default_rerank_strategy_is_production(self):
        """Default strategy is production without modifying caller signatures."""
        from app.query.processor import process_query
        qa = process_query("What is the minimum attendance required to appear in the End Semester Examination?")
        res_default = retrieve(qa, [DocumentSource.OFFICIAL], top_k=5)
        res_prod = retrieve(qa, [DocumentSource.OFFICIAL], top_k=5, rerank_strategy="production")
        assert [p.passage_id for p in res_default.retrieved_passages] == [p.passage_id for p in res_prod.retrieved_passages]


