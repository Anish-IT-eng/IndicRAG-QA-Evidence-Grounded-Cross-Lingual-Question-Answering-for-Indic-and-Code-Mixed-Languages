"""API integration tests using FastAPI TestClient."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """Set up a test client with a temporary database and indexes."""
    tmp = tmp_path_factory.mktemp("data")

    # Patch settings before importing the app
    from app.core import config as cfg
    orig_settings = {
        "db_path": cfg.settings.db_path,
        "data_dir": cfg.settings.data_dir,
        "official_docs_dir": cfg.settings.official_docs_dir,
        "uploads_dir": cfg.settings.uploads_dir,
        "indexes_dir": cfg.settings.indexes_dir,
        "dataset_dir": cfg.settings.dataset_dir,
        "db_dir": cfg.settings.db_dir,
    }
    cfg.settings.db_path = tmp / "test.db"
    cfg.settings.data_dir = tmp
    cfg.settings.official_docs_dir = tmp / "official"
    cfg.settings.uploads_dir = tmp / "uploads"
    cfg.settings.indexes_dir = tmp / "indexes"
    cfg.settings.dataset_dir = tmp / "dataset"
    cfg.settings.db_dir = tmp / "db"

    for d in [
        cfg.settings.official_docs_dir,
        cfg.settings.uploads_dir,
        cfg.settings.indexes_dir,
        cfg.settings.dataset_dir,
        cfg.settings.db_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)

    from app.core.database import init_db
    init_db()

    from app.api.main import app
    with TestClient(app) as c:
        yield c

    # Restore settings and reset index cache
    for k, v in orig_settings.items():
        setattr(cfg.settings, k, v)
    try:
        from app.retrieval import engine as _eng
        _eng._indexes.clear()
    except Exception:
        pass


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_schema(self, client):
        data = client.get("/health").json()
        assert "status" in data
        assert "version" in data
        assert "document_count" in data
        assert "passage_count" in data


class TestDocumentEndpoints:

    def test_list_documents_empty(self, client):
        resp = client.get("/documents")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_documents_invalid_source(self, client):
        resp = client.get("/documents?source_type=invalid")
        assert resp.status_code == 400

    def test_ingest_official_raises_501(self, client):
        resp = client.post(
            "/documents/ingest",
            json={"source_url": "http://example.com/doc.pdf"},
        )
        assert resp.status_code == 501

    def test_ingest_file_not_found(self, client):
        resp = client.post(
            "/documents/ingest-file",
            json={"filename": "nonexistent.pdf"},
        )
        assert resp.status_code == 404


class TestUploadEndpoint:

    def test_upload_rejects_non_pdf(self, client):
        resp = client.post(
            "/uploads",
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert resp.status_code == 400

    def test_upload_accepts_pdf(self, client):
        # Create a minimal valid PDF header
        minimal_pdf = b"%PDF-1.4\n%%EOF"
        resp = client.post(
            "/uploads",
            files={"file": ("test_upload.pdf", minimal_pdf, "application/pdf")},
        )
        # Should accept (200 or 200 with background task message)
        assert resp.status_code in (200, 202)


class TestQueryEndpoint:

    @patch("app.api.main.generate_answer")
    @patch("app.api.main.retrieve")
    def test_query_no_index(self, mock_retrieve, mock_generate, client):
        """Query with no index returns UNANSWERABLE gracefully."""
        from app.models.schemas import (
            EvidenceDecision,
            EvidenceStatus,
            QueryAnalysis,
            QueryLanguage,
            QueryScript,
            QuestionType,
            RetrievalResult,
            ResponseStatus,
            QueryResponse,
        )
        mock_retrieve.return_value = RetrievalResult(
            query_analysis=QueryAnalysis(
                original_query="test",
                detected_language=QueryLanguage.ENGLISH,
                detected_script=QueryScript.LATIN,
                query_type=QuestionType.DIRECT,
            ),
            retrieved_passages=[],
            total_candidates=0,
        )

        import asyncio
        from datetime import datetime

        mock_generate.return_value = QueryResponse(
            status=ResponseStatus.UNANSWERABLE,
            answer="UNANSWERABLE — Insufficient information available in the provided documents.",
            language="en",
            citations=[],
            evidence_status=EvidenceStatus.MISSING,
            timestamp=datetime.utcnow(),
        )

        resp = client.post(
            "/query",
            json={"query": "What is the attendance requirement?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data


class TestPassagesEndpoint:

    def test_passages_not_found(self, client):
        resp = client.get("/documents/nonexistent-doc-id/passages")
        assert resp.status_code == 404


class TestFrontendRoot:

    def test_root_serves_frontend_or_fallback(self, client):
        resp = client.get("/")
        assert resp.status_code == 200


class TestDocumentManagementEndpoints:

    def test_delete_nonexistent_document_returns_404(self, client):
        resp = client.delete("/documents/nonexistent-doc-id")
        assert resp.status_code == 404

    def test_get_status_nonexistent_returns_404(self, client):
        resp = client.get("/documents/nonexistent-doc-id/status")
        assert resp.status_code == 404
