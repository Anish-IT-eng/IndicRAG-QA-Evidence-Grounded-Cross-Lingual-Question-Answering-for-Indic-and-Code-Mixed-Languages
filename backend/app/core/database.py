"""SQLite database initialization and session management."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from app.core.config import settings
from app.core.logging_config import logger


def get_db_path() -> Path:
    return settings.db_path


def init_db() -> None:
    """Create all tables if they do not exist."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Initialising SQLite database at %s", db_path)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(_SCHEMA)
        conn.commit()
    logger.info("Database ready.")


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield a WAL-mode SQLite connection with row_factory set."""
    conn = sqlite3.connect(str(get_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── Schema ───────────────────────────────────────────────────────────────────
_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    document_id          TEXT PRIMARY KEY,
    filename             TEXT NOT NULL,
    source_url           TEXT,
    source_type          TEXT NOT NULL CHECK(source_type IN ('official','upload')),
    file_hash            TEXT NOT NULL,
    ingestion_timestamp  TEXT NOT NULL,
    ingestion_status     TEXT NOT NULL DEFAULT 'pending',
    page_count           INTEGER,
    title                TEXT,
    description          TEXT,
    effective_date       TEXT,
    academic_year        TEXT,
    program_applicability TEXT,           -- JSON array stored as text
    superseded_by        TEXT,
    supersedes           TEXT,
    is_current           INTEGER,         -- 0/1/NULL
    version_notes        TEXT,
    metadata             TEXT,            -- JSON blob
    error_message        TEXT,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS passages (
    passage_id          TEXT PRIMARY KEY,
    document_id         TEXT NOT NULL REFERENCES documents(document_id),
    parent_passage_id   TEXT,
    is_parent           INTEGER NOT NULL DEFAULT 0,
    text                TEXT NOT NULL,
    page_number         INTEGER,
    section             TEXT,
    heading             TEXT,
    clause              TEXT,
    table_ref           TEXT,
    chunk_index         INTEGER NOT NULL DEFAULT 0,
    total_chunks        INTEGER NOT NULL DEFAULT 1,
    source_type         TEXT NOT NULL,
    metadata            TEXT,            -- JSON blob
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_passages_document ON passages(document_id);
CREATE INDEX IF NOT EXISTS idx_passages_parent   ON passages(parent_passage_id);
CREATE INDEX IF NOT EXISTS idx_documents_hash    ON documents(file_hash);

CREATE TABLE IF NOT EXISTS qa_instances (
    question_id          TEXT PRIMARY KEY,
    original_question    TEXT NOT NULL,
    normalized_question  TEXT,
    translated_question  TEXT,
    query_language       TEXT NOT NULL,
    query_script         TEXT,
    question_type        TEXT NOT NULL,
    answerability        TEXT NOT NULL,
    reference_answer     TEXT,
    gold_passage_ids     TEXT,           -- JSON array
    source_document_id   TEXT,
    page_number          INTEGER,
    section              TEXT,
    source_version       TEXT,
    effective_date       TEXT,
    program_applicability TEXT,          -- JSON array
    expected_response_language TEXT,
    validation_status    TEXT DEFAULT 'pending',
    review_status        TEXT NOT NULL DEFAULT 'pending',
    reviewer_notes       TEXT,
    gold_evidence_quotes TEXT,           -- JSON array
    split                TEXT,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS evaluation_runs (
    run_id         TEXT PRIMARY KEY,
    run_name       TEXT NOT NULL,
    timestamp      TEXT NOT NULL,
    config_json    TEXT,
    metrics_json   TEXT,
    notes          TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS document_tables (
    table_id            TEXT PRIMARY KEY,
    document_id         TEXT NOT NULL REFERENCES documents(document_id),
    page_number         INTEGER NOT NULL,
    headers             TEXT NOT NULL,   -- JSON array of column headers
    num_rows            INTEGER NOT NULL,
    num_cols            INTEGER NOT NULL,
    confidence          REAL NOT NULL DEFAULT 1.0,
    status              TEXT NOT NULL DEFAULT 'extracted',
    structured_text     TEXT,
    raw_markdown        TEXT,
    metadata            TEXT,            -- JSON blob
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS table_cells (
    cell_id             TEXT PRIMARY KEY,
    table_id            TEXT NOT NULL REFERENCES document_tables(table_id),
    document_id         TEXT NOT NULL REFERENCES documents(document_id),
    page_number         INTEGER NOT NULL,
    row_index           INTEGER NOT NULL,
    col_index           INTEGER NOT NULL,
    header              TEXT,
    cell_value          TEXT NOT NULL,
    original_text       TEXT,
    confidence          REAL NOT NULL DEFAULT 1.0,
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_doc_tables_doc ON document_tables(document_id);
CREATE INDEX IF NOT EXISTS idx_table_cells_table ON table_cells(table_id);
CREATE INDEX IF NOT EXISTS idx_table_cells_header ON table_cells(header);

CREATE TABLE IF NOT EXISTS conversation_turns (
    turn_id                 TEXT PRIMARY KEY,
    session_id              TEXT NOT NULL,
    user_id                 TEXT,
    turn_index              INTEGER NOT NULL,
    user_query              TEXT NOT NULL,
    normalized_query        TEXT,
    query_type              TEXT NOT NULL,
    feedback_subtype        TEXT,
    assistant_answer        TEXT NOT NULL,
    evidence_status         TEXT NOT NULL,
    citations_json          TEXT,
    retrieved_passages_json TEXT,
    target_cohort           TEXT,
    target_programme        TEXT,
    target_academic_year    TEXT,
    metadata                TEXT,
    created_at              TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_conv_session ON conversation_turns(session_id, turn_index);
CREATE INDEX IF NOT EXISTS idx_conv_user ON conversation_turns(user_id, created_at);

CREATE TABLE IF NOT EXISTS document_relationships (
    relationship_id     TEXT PRIMARY KEY,
    subject_id          TEXT NOT NULL,
    predicate           TEXT NOT NULL,
    object_id           TEXT,
    object_value        TEXT NOT NULL,
    source_document_id  TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    source_passage_id   TEXT,
    source_table_id     TEXT,
    source_row_id       INTEGER,
    source_page         INTEGER NOT NULL,
    temporal_anchor     TEXT,
    cohort_scope        TEXT,
    programme_scope     TEXT,
    extraction_method   TEXT NOT NULL,
    confidence          REAL NOT NULL DEFAULT 1.0,
    verification_status TEXT NOT NULL DEFAULT 'VERIFIED',
    user_id             TEXT,
    metadata            TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_rel_subject ON document_relationships(subject_id, predicate);
CREATE INDEX IF NOT EXISTS idx_rel_doc ON document_relationships(source_document_id);
CREATE INDEX IF NOT EXISTS idx_rel_passage ON document_relationships(source_passage_id);
CREATE INDEX IF NOT EXISTS idx_rel_table ON document_relationships(source_table_id);
CREATE INDEX IF NOT EXISTS idx_rel_user ON document_relationships(user_id);
CREATE INDEX IF NOT EXISTS idx_rel_predicate ON document_relationships(predicate);
"""
