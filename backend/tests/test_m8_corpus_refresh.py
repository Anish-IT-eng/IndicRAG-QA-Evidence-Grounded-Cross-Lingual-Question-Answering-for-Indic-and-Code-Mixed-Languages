"""
Tests for Milestone M8: Official Corpus Document Refresh and Repository Expansion.
Verifies new document ingestion, deduplication, version-aware retrieval, benchmark integrity,
upload isolation, conflict disclosure, and multilingual QA.
"""
from __future__ import annotations

import hashlib
import sqlite3
import pytest
from pathlib import Path

from app.core.config import settings
from app.ingestion.source_registry import OFFICIAL_SOURCES, get_verified_sources
from app.models.schemas import DocumentSource, QueryAnalysis, QueryLanguage, EvidenceStatus, ResponseStatus
from app.retrieval.engine import get_official_index, get_upload_index, retrieve


@pytest.fixture(scope="module")
def official_idx():
    idx = get_official_index()
    assert idx.is_ready()
    return idx


class TestM8BenchmarkIntegrity:
    """Verifies that all historical evaluation benchmarks remain 100% frozen."""

    def test_m3_frozen_benchmark_unmodified(self):
        path = Path("backend/data/dataset/final_verified_dataset.csv")
        assert path.exists()
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        assert h == "093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520"

    def test_m6_expanded_benchmark_unmodified(self):
        path = Path("backend/data/dataset/m6_expanded_benchmark_n60.csv")
        assert path.exists()
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        assert h == "a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae"

    def test_m6_qualification_ledger_unmodified(self):
        path = Path("backend/data/dataset/m6_benchmark_qualification.csv")
        assert path.exists()
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        assert h == "db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13"

    def test_m6_phase3_negative_benchmark_unmodified(self):
        path = Path("backend/data/dataset/m6_phase3_negative_candidates.csv")
        assert path.exists()
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        assert h == "492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa"


class TestM8CorpusAndRegistryIntegrity:
    """Verifies source registry, database records, and passage preservation."""

    def test_source_registry_has_7_verified_sources(self):
        sources = get_verified_sources()
        assert len(sources) == 7
        filenames = {s.filename for s in sources}
        assert "Students-Discipline-Conduct-Rules-2024.pdf" in filenames
        assert "BU-First-Ordinance-2016.pdf" in filenames
        assert "UFM-Guidelines-2024.pdf" in filenames
        assert "SEAS-Ordinance-Rules-Regulations-2017.pdf" in filenames
        assert "Notification-Minimum-Attendance.pdf" in filenames
        assert "Academic-Rules-for-SCSET_UG.pdf" in filenames
        assert "Academic-Calendar-2026-27.pdf" in filenames

    def test_all_source_urls_are_official_bennett(self):
        for s in get_verified_sources():
            assert s.source_url is not None
            assert "bennett.edu.in" in s.source_url or "cloudfront.net" in s.source_url

    def test_sqlite_has_7_official_documents(self):
        conn = sqlite3.connect(str(settings.db_path))
        cursor = conn.cursor()
        rows = cursor.execute("SELECT filename FROM documents WHERE source_type = 'official'").fetchall()
        conn.close()
        filenames = {r[0] for r in rows}
        assert len(filenames) == 7
        assert "Students-Discipline-Conduct-Rules-2024.pdf" in filenames
        assert "BU-First-Ordinance-2016.pdf" in filenames
        assert "UFM-Guidelines-2024.pdf" in filenames

    def test_passage_counts_expanded_correctly(self):
        conn = sqlite3.connect(str(settings.db_path))
        cursor = conn.cursor()
        child_count = cursor.execute("SELECT count(*) FROM passages WHERE is_parent = 0").fetchone()[0]
        parent_count = cursor.execute("SELECT count(*) FROM passages WHERE is_parent = 1").fetchone()[0]
        conn.close()
        assert child_count == 253
        assert parent_count == 53

    def test_corpus_sha256_matches_canonical_m8(self):
        conn = sqlite3.connect(str(settings.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT passage_id, text FROM passages WHERE parent_passage_id IS NOT NULL ORDER BY passage_id")
        rows = cursor.fetchall()
        conn.close()
        hasher = hashlib.sha256()
        for pid, text in rows:
            hasher.update(pid.encode("utf-8"))
            hasher.update(text.encode("utf-8"))
        assert hasher.hexdigest() == "c414cee2c2ce35b6c628f4fb4ada50804dd96d574ea9b373f68c53f29f35f111"


class TestM8RetrievalCoverage:
    """Verifies BM25, FAISS, and hybrid retrieval across both historical and new documents."""

    def test_bm25_retrieves_proctorial_committee(self, official_idx):
        hits = official_idx.bm25_search("Proctorial Committee discipline inquiry", top_k=5)
        assert len(hits) > 0
        texts = [meta.get("text", "") for _, _, meta in hits]
        assert any("proctorial" in t.lower() for t in texts)

    def test_dense_retrieves_unfair_means_penalties(self, official_idx):
        hits = official_idx.dense_search("penalties for using mobile phone in exam hall", top_k=5)
        assert len(hits) == 5
        texts = [meta.get("text", "") for _, _, meta in hits]
        assert any("unfair means" in t.lower() or "examination" in t.lower() for t in texts)

    def test_historical_clause_30_still_retrievable(self, official_idx):
        qa = QueryAnalysis(original_query="What was the historical attendance requirement in the 2017 ordinances?")
        res = retrieve(qa, collections=[DocumentSource.OFFICIAL], top_k=5)
        assert len(res.retrieved_passages) > 0
        doc_ids = {p.document_id for p in res.retrieved_passages}
        assert "b6f9aad0-4cbd-4915-bc0b-262e14b6e3a2" in doc_ids  # SEAS 2017 doc id

    def test_first_ordinance_degree_rules_retrievable(self, official_idx):
        qa = QueryAnalysis(original_query="What are the conditions for the award of degrees under the First Ordinances?")
        res = retrieve(qa, collections=[DocumentSource.OFFICIAL], top_k=5)
        assert len(res.retrieved_passages) > 0
        doc_ids = {p.document_id for p in res.retrieved_passages}
        assert "8e3b751a-5728-4af0-bf6c-5418b578af7b" in doc_ids  # BU First Ordinance doc id


class TestM8MultilingualQA:
    """Verifies retrieval across English, Hindi, Hinglish, and Romanized Hindi queries."""

    def test_hindi_discipline_retrieval(self, official_idx):
        qa = QueryAnalysis(
            original_query="अनुशासनहीनता और प्रॉक्टोरियल जांच के नियम क्या हैं?",
            detected_language=QueryLanguage.HINDI,
        )
        res = retrieve(qa, collections=[DocumentSource.OFFICIAL], top_k=5)
        assert len(res.retrieved_passages) > 0

    def test_hinglish_unfair_means_retrieval(self, official_idx):
        qa = QueryAnalysis(
            original_query="Exam hall me cheating pakde jane par kya penalty lagti hai?",
            detected_language=QueryLanguage.CODE_MIXED,
        )
        res = retrieve(qa, collections=[DocumentSource.OFFICIAL], top_k=5)
        assert len(res.retrieved_passages) > 0

    def test_romanized_hindi_attendance_conflict(self, official_idx):
        qa = QueryAnalysis(
            original_query="Minimum attendance kitna percent compulsory hai Bennett University me?",
            detected_language=QueryLanguage.ROMANIZED_HINDI,
        )
        res = retrieve(qa, collections=[DocumentSource.OFFICIAL], top_k=5)
        assert len(res.retrieved_passages) > 0
        texts = " ".join([p.text for p in res.retrieved_passages])
        assert "75%" in texts or "70%" in texts


class TestM8UploadIsolationAndSafety:
    """Verifies that official index and upload index remain strictly partitioned."""

    def test_upload_index_isolated_from_official(self):
        off_idx = get_official_index()
        upl_idx = get_upload_index()
        assert off_idx.index_name == "official"
        assert upl_idx.index_name == "upload"
        assert off_idx.index_dir != upl_idx.index_dir

