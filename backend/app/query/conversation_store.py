"""
Conversation Store — IndicRAG-QA

Persists and retrieves multi-turn conversational context in SQLite.
Enables evidence-based answer repair, contextual memory, and provenance tracking.
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from app.core.database import get_db
from app.core.logging_config import logger
from app.models.schemas import Citation, RetrievedPassage


def save_turn(
    session_id: str,
    user_id: Optional[str],
    user_query: str,
    assistant_answer: str,
    evidence_status: str,
    query_type: str = "direct",
    feedback_subtype: Optional[str] = None,
    normalized_query: Optional[str] = None,
    citations: Optional[list[Citation | dict]] = None,
    retrieved_passages: Optional[list[RetrievedPassage | dict]] = None,
    target_cohort: Optional[str] = None,
    target_programme: Optional[str] = None,
    target_academic_year: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """Save a conversation turn to SQLite and return the turn_id."""
    turn_id = f"turn_{uuid.uuid4().hex[:12]}"
    meta = metadata or {}

    # Serialize citations cleanly
    citations_data = []
    if citations:
        for c in citations:
            if hasattr(c, "model_dump"):
                citations_data.append(c.model_dump())
            elif isinstance(c, dict):
                citations_data.append(c)

    # Serialize retrieved passages cleanly
    passages_data = []
    if retrieved_passages:
        for p in retrieved_passages:
            if hasattr(p, "model_dump"):
                passages_data.append(p.model_dump())
            elif isinstance(p, dict):
                passages_data.append(p)

    with get_db() as conn:
        # Determine current turn_index for this session
        row = conn.execute(
            "SELECT COALESCE(MAX(turn_index), 0) + 1 FROM conversation_turns WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        turn_index = row[0] if row else 1

        conn.execute(
            """
            INSERT INTO conversation_turns (
                turn_id, session_id, user_id, turn_index, user_query,
                normalized_query, query_type, feedback_subtype, assistant_answer,
                evidence_status, citations_json, retrieved_passages_json,
                target_cohort, target_programme, target_academic_year, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                turn_id,
                session_id,
                user_id,
                turn_index,
                user_query,
                normalized_query,
                query_type,
                feedback_subtype,
                assistant_answer,
                evidence_status,
                json.dumps(citations_data),
                json.dumps(passages_data),
                target_cohort,
                target_programme,
                target_academic_year,
                json.dumps(meta),
            ),
        )

    logger.debug(
        "Saved turn %s (index %d) for session %s (user: %s)",
        turn_id,
        turn_index,
        session_id,
        user_id,
    )
    return turn_id


def get_last_turn(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Retrieve the immediately preceding conversation turn.
    Tries by session_id first; if not found or session_id is None, tries user_id.
    """
    with get_db() as conn:
        row = None
        if session_id and user_id:
            row = conn.execute(
                """
                SELECT * FROM conversation_turns
                WHERE session_id = ? AND (user_id = ? OR user_id IS NULL)
                ORDER BY turn_index DESC, created_at DESC
                LIMIT 1
                """,
                (session_id, user_id),
            ).fetchone()
        elif session_id:
            row = conn.execute(
                """
                SELECT * FROM conversation_turns
                WHERE session_id = ?
                ORDER BY turn_index DESC, created_at DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()

        if not row and user_id:
            row = conn.execute(
                """
                SELECT * FROM conversation_turns
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

        if not row:
            return None

        # Format turn as dictionary
        return _format_turn_row(row)


def get_recent_turns(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve recent conversation turns in chronological order."""
    with get_db() as conn:
        rows = []
        if session_id:
            rows = conn.execute(
                """
                SELECT * FROM conversation_turns
                WHERE session_id = ?
                ORDER BY turn_index ASC, created_at ASC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        elif user_id:
            rows = conn.execute(
                """
                SELECT * FROM conversation_turns
                WHERE user_id = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

        return [_format_turn_row(r) for r in rows]


def _format_turn_row(row: Any) -> dict[str, Any]:
    """Helper to convert sqlite3.Row to parsed dictionary."""
    d = dict(row)
    try:
        d["citations"] = json.loads(d["citations_json"]) if d.get("citations_json") else []
    except Exception:
        d["citations"] = []
    try:
        d["retrieved_passages"] = (
            json.loads(d["retrieved_passages_json"]) if d.get("retrieved_passages_json") else []
        )
    except Exception:
        d["retrieved_passages"] = []
    try:
        d["metadata"] = json.loads(d["metadata"]) if d.get("metadata") else {}
    except Exception:
        d["metadata"] = {}
    return d
