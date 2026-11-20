"""Tests for the database initialization and schema."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

# We need to override the DB path before importing the module
import os

@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Use a temporary DB for all database tests."""
    db_file = tmp_path / "test_indicrag.db"
    monkeypatch.setenv("DB_PATH", str(db_file))
    # Also patch the settings object
    from app.core import config as cfg_module
    monkeypatch.setattr(cfg_module.settings, "db_path", db_file)
    # Ensure parent exists
    db_file.parent.mkdir(parents=True, exist_ok=True)
    yield db_file


class TestDatabaseInit:

    def test_init_creates_tables(self, temp_db):
        from app.core.database import init_db, get_db
        init_db()
        with get_db() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {r[0] for r in tables}
        assert "documents" in table_names
        assert "passages" in table_names
        assert "qa_instances" in table_names
        assert "evaluation_runs" in table_names

    def test_double_init_is_idempotent(self, temp_db):
        from app.core.database import init_db
        init_db()
        init_db()  # should not raise

    def test_document_insert_and_fetch(self, temp_db):
        from app.core.database import init_db, get_db
        init_db()
        with get_db() as conn:
            conn.execute("""
                INSERT INTO documents (
                    document_id, filename, source_type, file_hash,
                    ingestion_timestamp, ingestion_status
                ) VALUES (?, ?, ?, ?, datetime('now'), 'completed')
            """, ("doc-001", "test.pdf", "official", "abc123"))

        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE document_id = ?", ("doc-001",)
            ).fetchone()
        assert row is not None
        assert row["filename"] == "test.pdf"
        assert row["source_type"] == "official"

    def test_passage_insert_and_fetch(self, temp_db):
        from app.core.database import init_db, get_db
        init_db()
        with get_db() as conn:
            conn.execute("""
                INSERT INTO documents (
                    document_id, filename, source_type, file_hash,
                    ingestion_timestamp, ingestion_status
                ) VALUES ('doc-002', 'test2.pdf', 'official', 'def456', datetime('now'), 'completed')
            """)
            conn.execute("""
                INSERT INTO passages (
                    passage_id, document_id, is_parent, text,
                    page_number, chunk_index, total_chunks, source_type
                ) VALUES ('pass-001', 'doc-002', 0, 'Test passage text.', 1, 0, 1, 'official')
            """)

        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM passages WHERE passage_id = ?", ("pass-001",)
            ).fetchone()
        assert row is not None
        assert row["text"] == "Test passage text."
        assert row["page_number"] == 1
