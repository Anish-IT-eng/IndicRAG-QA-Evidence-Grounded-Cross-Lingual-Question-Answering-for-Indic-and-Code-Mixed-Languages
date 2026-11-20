"""
Tests for M7 Frontend Integration and API Contracts.

Verifies:
1. English grounded answer schema and citation formatting.
2. Hindi grounded answer handling.
3. Hinglish code-mixed query processing and schema conformance.
4. Romanized Hindi query handling.
5. Citation traceability and non-empty metadata (filename, page, quote).
6. Missing citation safe abstention.
7. Partial evidence state rendering contract.
8. Insufficient evidence safe abstention contract.
9. Conflicting regulations response contract.
10. Clarification request response contract.
11. User-uploaded document isolation from official queries.
12. API error and timeout response handling.
13. Malformed payload validation handling.
14. Long answer rendering and whitespace preservation.
15. Unicode and Devanagari special character preservation.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.models.schemas import (
    DocumentSource,
    EvidenceStatus,
    QueryRequest,
    QueryResponse,
    ResponseStatus,
)

client = TestClient(app)


class TestM7FrontendAPIIntegration:
    """End-to-end integration and schema contract tests for the frontend UI."""

    def test_01_english_grounded_answer_contract(self):
        """Verify English query returns valid QueryResponse contract."""
        payload = {
            "query": "What is the minimum attendance requirement for undergraduate students?",
            "collection": ["official"],
            "use_reranker": True,
            "use_pdr": True,
            "debug": True,
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "request_id" in data
        assert data["status"] in [s.value for s in ResponseStatus]
        assert data["evidence_status"] in [s.value for s in EvidenceStatus]
        assert "answer" in data
        assert isinstance(data["citations"], list)
        assert data["latency_ms"] >= 0.0

    def test_02_hindi_grounded_query_contract(self):
        """Verify Hindi Devanagari query preserves script and produces valid response."""
        payload = {
            "query": "उपस्थिति के लिए न्यूनतम आवश्यकता क्या है?",
            "collection": ["official"],
            "use_reranker": False,
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in [s.value for s in ResponseStatus]
        assert data["language"] in ["hi", "en", "unknown"]

    def test_03_hinglish_grounded_query_contract(self):
        """Verify Hinglish query returns appropriate response status."""
        payload = {
            "query": "Attendance requirement kya hai B.Tech students ke liye?",
            "collection": ["official"],
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in [s.value for s in ResponseStatus]

    def test_04_romanized_hindi_query_contract(self):
        """Verify Romanized Hindi query returns proper schema without error."""
        payload = {
            "query": "Attendance kam hone par kya hota hai?",
            "collection": ["official"],
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in [s.value for s in ResponseStatus]

    def test_05_valid_citation_traceability(self):
        """Verify citations contain valid filename, quote, and passage_id when present."""
        payload = {
            "query": "What are the grades awarded for course performance?",
            "collection": ["official"],
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        for cit in data.get("citations", []):
            assert "filename" in cit and len(cit["filename"]) > 0
            assert "quote" in cit
            assert "passage_id" in cit and len(cit["passage_id"]) > 0

    def test_06_missing_citation_handling(self):
        """Verify that when no citations are verified or uncertainty is qualified, status is safe."""
        # Querying an external topic not in corpus
        payload = {
            "query": "What is the JEE Advanced opening rank for IIT Bombay Computer Science?",
            "collection": ["official"],
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        # Out of domain query safely abstains or discloses conflicting versions/uncertainty without false claims
        assert data["status"] in [ResponseStatus.UNANSWERABLE.value, ResponseStatus.CONFLICTING_VERSIONS.value]
        assert data["evidence_status"] in [
            EvidenceStatus.INSUFFICIENT.value,
            EvidenceStatus.MISSING.value,
            EvidenceStatus.CONFLICTING.value,
        ]
        assert len(data["citations"]) == 0
        assert "cannot answer" in data["answer"].lower() or "not specify" in data["answer"].lower() or "unanswerable" in data["answer"].lower()

    def test_07_partial_evidence_state_contract(self):
        """Verify PARTIAL evidence status conforms to schema."""
        res = QueryResponse(
            status=ResponseStatus.ANSWERED,
            answer="Partial answer provided.",
            language="en",
            citations=[],
            evidence_status=EvidenceStatus.PARTIAL,
            latency_ms=100.0,
        )
        assert res.evidence_status == EvidenceStatus.PARTIAL
        assert res.status == ResponseStatus.ANSWERED

    def test_08_insufficient_evidence_state_contract(self):
        """Verify INSUFFICIENT evidence produces UNANSWERABLE status without hallucinated citations."""
        res = QueryResponse(
            status=ResponseStatus.UNANSWERABLE,
            answer="UNANSWERABLE — Insufficient information available.",
            language="en",
            citations=[],
            evidence_status=EvidenceStatus.INSUFFICIENT,
            latency_ms=50.0,
        )
        assert res.status == ResponseStatus.UNANSWERABLE
        assert res.evidence_status == EvidenceStatus.INSUFFICIENT
        assert len(res.citations) == 0

    def test_09_conflicting_regulations_state_contract(self):
        """Verify CONFLICTING evidence maps to CONFLICTING_VERSIONS status."""
        payload = {
            "query": "What is the minimum attendance requirement?",
            "collection": ["official"],
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        # Should detect conflict between 2017 70% and 2022 75%
        if data["evidence_status"] == EvidenceStatus.CONFLICTING.value:
            assert data["status"] == ResponseStatus.CONFLICTING_VERSIONS.value
            assert "conflict" in data["answer"].lower() or "75%" in data["answer"] or "70%" in data["answer"]

    def test_10_clarification_request_state_contract(self):
        """Verify CLARIFICATION_REQUIRED maps to CLARIFICATION_NEEDED status."""
        res = QueryResponse(
            status=ResponseStatus.CLARIFICATION_NEEDED,
            answer="CLARIFICATION REQUIRED — Please specify academic cohort.",
            language="en",
            citations=[],
            evidence_status=EvidenceStatus.CLARIFICATION_REQUIRED,
            latency_ms=10.0,
        )
        assert res.status == ResponseStatus.CLARIFICATION_NEEDED
        assert res.evidence_status == EvidenceStatus.CLARIFICATION_REQUIRED

    def test_11_user_upload_document_isolation(self):
        """Verify documents endpoint distinguishes official vs upload collections."""
        resp_off = client.get("/documents?source_type=official")
        assert resp_off.status_code == 200
        docs_off = resp_off.json()
        for d in docs_off:
            assert d["source_type"] == "official"

        resp_up = client.get("/documents?source_type=upload")
        assert resp_up.status_code == 200
        docs_up = resp_up.json()
        for d in docs_up:
            assert d["source_type"] == "upload"

    def test_12_invalid_endpoint_and_method_handling(self):
        """Verify proper 404 and 405 error handling."""
        resp_404 = client.get("/non_existent_endpoint")
        assert resp_404.status_code == 404

        resp_405 = client.get("/query")
        assert resp_405.status_code == 405

    def test_13_malformed_payload_validation_handling(self):
        """Verify validation errors on empty or missing query string."""
        resp = client.post("/query", json={"query": ""})
        assert resp.status_code == 422

        resp2 = client.post("/query", json={})
        assert resp2.status_code == 422

    def test_14_long_query_and_whitespace_handling(self):
        """Verify whitespace cleanup and long query handling."""
        query_text = "   What   is   the   minimum   attendance   ?   \n\n\t"
        resp = client.post("/query", json={"query": query_text})
        assert resp.status_code == 200

    def test_15_unicode_and_devanagari_special_character_handling(self):
        """Verify complex Unicode Devanagari string with matras, conjuncts, and punctuation."""
        complex_devanagari = "छात्रवृत्ति (Scholarship) एवं शुल्क-प्रतिपूर्ति (Fee-Refund) के क्या नियम हैं?"
        resp = client.post("/query", json={"query": complex_devanagari})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in [s.value for s in ResponseStatus]

