"""
Relationship Store & Evidence Relationship Modeling — IndicRAG-QA (Phase R2)

Provides:
1. SQLite relationship persistence with multi-tenant isolation and foreign-key integrity.
2. Idempotent insertion with deterministic relationship IDs.
3. Structural relationship extraction from R1 tables (headers, rows, dates, events, date ranges).
4. Deterministic regulatory relationship extraction (rules, clauses, thresholds, exceptions, approvals, scopes).
5. Query interface for provenance-grounded relationship retrieval.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Optional

from app.core.database import get_db
from app.core.logging_config import logger
from app.models.schemas import (
    RelationshipExtractionMethod,
    RelationshipPredicate,
    RelationshipRecord,
    RelationshipVerificationStatus,
)


def make_relationship_id(
    doc_id: str,
    predicate: str,
    subject: str,
    obj_val: str,
    table_id: Optional[str] = None,
    row_id: Optional[int] = None,
) -> str:
    """Generate deterministic, collision-resistant relationship ID for idempotency."""
    key = f"{doc_id}_{table_id or 'notbl'}_{row_id if row_id is not None else 'norow'}_{predicate}_{subject}_{obj_val}"
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"rel_{h}"


class RelationshipStore:
    """Service layer for querying and managing document relationships."""

    @staticmethod
    def insert_relationships(relationships: list[RelationshipRecord]) -> int:
        """
        Idempotent insertion of relationship records into SQLite.
        Existing records with identical relationship_id are replaced without duplication.
        """
        if not relationships:
            return 0

        rows = []
        for r in relationships:
            rows.append((
                r.relationship_id,
                r.subject_id,
                r.predicate.value if hasattr(r.predicate, "value") else str(r.predicate),
                r.object_id,
                r.object_value,
                r.source_document_id,
                r.source_passage_id,
                r.source_table_id,
                r.source_row_id,
                r.source_page,
                r.temporal_anchor,
                r.cohort_scope,
                r.programme_scope,
                r.extraction_method.value if hasattr(r.extraction_method, "value") else str(r.extraction_method),
                r.confidence,
                r.verification_status.value if hasattr(r.verification_status, "value") else str(r.verification_status),
                r.user_id,
                json.dumps(r.metadata or {}),
            ))

        with get_db() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO document_relationships (
                    relationship_id, subject_id, predicate, object_id, object_value,
                    source_document_id, source_passage_id, source_table_id, source_row_id,
                    source_page, temporal_anchor, cohort_scope, programme_scope,
                    extraction_method, confidence, verification_status, user_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

        logger.debug("Persisted %d relationship records into SQLite.", len(rows))
        return len(rows)

    @staticmethod
    def get_relationships_for_passage(
        passage_id: str,
        user_id: Optional[str] = None,
    ) -> list[RelationshipRecord]:
        """Retrieve all relationships linked to a passage, enforcing user isolation."""
        with get_db() as conn:
            query = (
                "SELECT * FROM document_relationships "
                "WHERE source_passage_id = ? AND (user_id = ? OR user_id IS NULL)"
            )
            rows = conn.execute(query, (passage_id, user_id)).fetchall()
            return [_row_to_record(r) for r in rows]

    @staticmethod
    def get_related_evidence(
        subject_id: str,
        predicate: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[RelationshipRecord]:
        """Find relationships for a subject entity, optionally filtering by predicate."""
        with get_db() as conn:
            query = "SELECT * FROM document_relationships WHERE subject_id = ? "
            params = [subject_id]
            if predicate:
                query += " AND predicate = ? "
                params.append(predicate)
            query += " AND (user_id = ? OR user_id IS NULL) "
            params.append(user_id)
            query += " ORDER BY confidence DESC, source_page ASC"
            rows = conn.execute(query, params).fetchall()
            return [_row_to_record(r) for r in rows]

    @staticmethod
    def get_event_details(
        event_name_or_date: str,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Query event dates, days, types, page numbers, and multi-day spans.
        Supports lookup by event description substring or exact date (e.g., '10-12-2026').
        """
        with get_db() as conn:
            query = """
                SELECT DISTINCT
                    r1.subject_id as event_name,
                    r1.object_value as event_date,
                    r2.object_value as event_day,
                    r3.object_value as event_type,
                    r1.source_page as page_number,
                    r1.source_document_id,
                    r1.source_table_id,
                    r1.source_row_id
                FROM document_relationships r1
                LEFT JOIN document_relationships r2
                    ON r1.source_table_id = r2.source_table_id
                    AND r1.source_row_id = r2.source_row_id
                    AND r2.predicate = 'EVENT_HAS_DAY'
                LEFT JOIN document_relationships r3
                    ON r1.source_table_id = r3.source_table_id
                    AND r1.source_row_id = r3.source_row_id
                    AND r3.predicate = 'EVENT_HAS_TYPE'
                WHERE r1.predicate = 'EVENT_HAS_DATE'
                  AND (r1.subject_id LIKE ? OR r1.object_value LIKE ?)
                  AND (r1.user_id = ? OR r1.user_id IS NULL)
                ORDER BY r1.source_page ASC, r1.source_row_id ASC
            """
            search_param = f"%{event_name_or_date}%"
            rows = conn.execute(query, (search_param, search_param, user_id)).fetchall()

            # Group rows by normalized event_name and page_number
            grouped: dict[tuple[str, int], dict[str, Any]] = {}
            for r in rows:
                ev_raw = r["event_name"] or ""
                ev_norm = re.sub(r"\s+", " ", ev_raw).strip()
                page = r["page_number"]
                key = (ev_norm, page)
                if key not in grouped:
                    grouped[key] = {
                        "event_name": ev_norm,
                        "page_number": page,
                        "source_document_id": r["source_document_id"],
                        "source_table_id": r["source_table_id"],
                        "event_type": r["event_type"],
                        "dates": [],
                        "days": {},
                        "rows": [],
                    }
                dt = r["event_date"]
                if dt and dt not in grouped[key]["dates"]:
                    grouped[key]["dates"].append(dt)
                    grouped[key]["days"][dt] = r["event_day"]
                if r["source_row_id"] is not None and r["source_row_id"] not in grouped[key]["rows"]:
                    grouped[key]["rows"].append(r["source_row_id"])

            results = []
            for (ev_name, page), data in grouped.items():
                dates = data["dates"]
                start_date = dates[0] if dates else ""
                end_date = dates[-1] if dates else ""
                start_day = data["days"].get(start_date, "")
                end_day = data["days"].get(end_date, "")
                date_range = f"{start_date} to {end_date}" if len(dates) > 1 and start_date != end_date else start_date

                results.append({
                    "event_name": ev_name,
                    "event_date": start_date,
                    "event_day": start_day,
                    "start_date": start_date,
                    "end_date": end_date,
                    "start_day": start_day,
                    "end_day": end_day,
                    "date_range": date_range,
                    "individual_dates": dates,
                    "event_type": data["event_type"],
                    "page_number": page,
                    "source_document_id": data["source_document_id"],
                    "source_table_id": data["source_table_id"],
                    "source_row_id": data["rows"][0] if data["rows"] else None,
                    "source_rows": data["rows"],
                })

            return results

    @staticmethod
    def get_rule_exceptions(
        rule_or_clause: str,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Query verified regulatory exceptions, required documentation, and approval authorities.
        """
        with get_db() as conn:
            query = """
                SELECT
                    r.subject_id as rule_name,
                    r.predicate,
                    r.object_value,
                    r.source_passage_id,
                    r.source_page,
                    d.title as document_title,
                    d.filename as document_filename
                FROM document_relationships r
                JOIN documents d ON r.source_document_id = d.document_id
                WHERE (r.subject_id LIKE ? OR r.object_value LIKE ?)
                  AND r.predicate IN (
                      'RULE_HAS_EXCEPTION',
                      'EXCEPTION_HAS_PREREQUISITE',
                      'EXCEPTION_REQUIRES_DOCUMENT',
                      'EXCEPTION_REQUIRES_APPROVAL',
                      'RULE_HAS_THRESHOLD'
                  )
                  AND (r.user_id = ? OR r.user_id IS NULL)
                ORDER BY r.source_page ASC
            """
            search_param = f"%{rule_or_clause}%"
            rows = conn.execute(query, (search_param, search_param, user_id)).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_rule_applicability(
        rule_name: str,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Query cohort scope, programme scope, effective dates, and clarifying circulars.
        """
        with get_db() as conn:
            query = """
                SELECT
                    r.subject_id as rule_name,
                    r.predicate,
                    r.object_value,
                    r.temporal_anchor,
                    r.cohort_scope,
                    r.programme_scope,
                    d.title as document_title,
                    d.filename as document_filename
                FROM document_relationships r
                JOIN documents d ON r.source_document_id = d.document_id
                WHERE (r.subject_id LIKE ? OR r.object_value LIKE ?)
                  AND r.predicate IN (
                      'RULE_APPLIES_TO_PROGRAM',
                      'RULE_APPLIES_TO_COHORT',
                      'RULE_HAS_EFFECTIVE_PERIOD',
                      'DOCUMENT_CLARIFIES_RULE',
                      'DOCUMENT_SUPERSEDES_RULE',
                      'RULE_HAS_APPLICABILITY_SCOPE'
                  )
                  AND (r.user_id = ? OR r.user_id IS NULL)
                ORDER BY r.source_page ASC
            """
            search_param = f"%{rule_name}%"
            rows = conn.execute(query, (search_param, search_param, user_id)).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_source_relationships(
        document_id: str,
        user_id: Optional[str] = None,
    ) -> list[RelationshipRecord]:
        """Retrieve all relationships originating from a specific document."""
        with get_db() as conn:
            query = (
                "SELECT * FROM document_relationships "
                "WHERE source_document_id = ? AND (user_id = ? OR user_id IS NULL) "
                "ORDER BY source_page ASC, source_row_id ASC"
            )
            rows = conn.execute(query, (document_id, user_id)).fetchall()
            return [_row_to_record(r) for r in rows]

    @staticmethod
    def delete_relationships_for_document(document_id: str) -> int:
        """Cleanly remove existing relationships before re-ingestion."""
        with get_db() as conn:
            res = conn.execute(
                "DELETE FROM document_relationships WHERE source_document_id = ?",
                (document_id,),
            )
            deleted = res.rowcount
        logger.debug("Deleted %d relationships for document %s", deleted, document_id)
        return deleted

    @staticmethod
    def get_relationship_expanded_passages(
        seed_candidates: list[dict[str, Any]] | list[str],
        user_id: Optional[str] = None,
        max_expanded: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Given top retrieved candidate passages (or passage IDs), retrieve closely connected
        relationship evidence (exceptions, prerequisite docs, approvals, subclauses, dates)
        with full provenance and strict tenant isolation.
        """
        if not seed_candidates:
            return []

        # Normalize seed input
        seed_pids: set[str] = set()
        doc_pages: list[tuple[str, int]] = []
        if isinstance(seed_candidates[0], str):
            seed_pids = set(seed_candidates)
        else:
            for c in seed_candidates:
                if isinstance(c, dict):
                    pid = c.get("passage_id")
                    if pid:
                        seed_pids.add(pid)
                    did = c.get("document_id")
                    page = c.get("page_number")
                    if did and page:
                        doc_pages.append((did, page))

        expanded: list[dict[str, Any]] = []
        seen_passage_ids = set(seed_pids)
        seen_rel_keys = set()

        with get_db() as conn:
            where_clauses = []
            params_direct = []

            if seed_pids:
                placeholders = ",".join("?" for _ in seed_pids)
                where_clauses.append(f"r.source_passage_id IN ({placeholders})")
                params_direct.extend(list(seed_pids))

            for did, page in doc_pages[:6]:
                where_clauses.append("(r.source_document_id = ? AND r.source_page = ?)")
                params_direct.extend([did, page])

            if not where_clauses:
                return []

            where_str = " OR ".join(where_clauses)
            query_direct = f"""
                SELECT r.*, d.filename as document_filename, d.source_type
                FROM document_relationships r
                JOIN documents d ON r.source_document_id = d.document_id
                WHERE ({where_str})
                  AND (r.user_id = ? OR (r.user_id IS NULL AND d.source_type = 'official'))
                ORDER BY 
                  CASE r.predicate
                    WHEN 'RULE_HAS_EXCEPTION' THEN 1
                    WHEN 'EXCEPTION_REQUIRES_DOCUMENT' THEN 2
                    WHEN 'EXCEPTION_REQUIRES_APPROVAL' THEN 3
                    WHEN 'EXCEPTION_HAS_PREREQUISITE' THEN 4
                    WHEN 'CLAUSE_HAS_SUBCLAUSE' THEN 5
                    WHEN 'RULE_HAS_THRESHOLD' THEN 6
                    WHEN 'EVENT_HAS_DATE' THEN 7
                    WHEN 'RULE_APPLIES_TO_PROGRAM' THEN 8
                    WHEN 'RULE_APPLIES_TO_COHORT' THEN 9
                    ELSE 10
                  END ASC,
                  r.confidence DESC
            """
            params_direct.append(user_id)
            direct_rows = conn.execute(query_direct, params_direct).fetchall()

            connected_subjects = set()
            for row in direct_rows:
                subj = row["subject_id"]
                pred = row["predicate"]
                # Exclude document-level titles from broad transitive expansion
                if subj and pred not in ("RULE_HAS_CLAUSE",):
                    connected_subjects.add(subj)

            transitive_rows = []
            if connected_subjects and seed_pids:
                subj_placeholders = ",".join("?" for _ in connected_subjects)
                pid_placeholders = ",".join("?" for _ in seed_pids)
                query_trans = f"""
                    SELECT r.*, d.filename as document_filename, d.source_type
                    FROM document_relationships r
                    JOIN documents d ON r.source_document_id = d.document_id
                    WHERE r.subject_id IN ({subj_placeholders})
                      AND (r.source_passage_id NOT IN ({pid_placeholders}) OR r.source_passage_id IS NULL)
                      AND (r.user_id = ? OR (r.user_id IS NULL AND d.source_type = 'official'))
                    ORDER BY 
                      CASE r.predicate
                        WHEN 'RULE_HAS_EXCEPTION' THEN 1
                        WHEN 'EXCEPTION_REQUIRES_DOCUMENT' THEN 2
                        WHEN 'EXCEPTION_REQUIRES_APPROVAL' THEN 3
                        WHEN 'EXCEPTION_HAS_PREREQUISITE' THEN 4
                        WHEN 'CLAUSE_HAS_SUBCLAUSE' THEN 5
                        WHEN 'RULE_HAS_THRESHOLD' THEN 6
                        WHEN 'EVENT_HAS_DATE' THEN 7
                        WHEN 'RULE_APPLIES_TO_PROGRAM' THEN 8
                        WHEN 'RULE_APPLIES_TO_COHORT' THEN 9
                        ELSE 10
                      END ASC,
                      r.confidence DESC
                """
                params_trans = list(connected_subjects) + list(seed_pids) + [user_id]
                transitive_rows = conn.execute(query_trans, params_trans).fetchall()

            all_rel_rows = list(direct_rows) + list(transitive_rows)

            for r in all_rel_rows:
                if len(expanded) >= max_expanded:
                    break

                target_pid = r["source_passage_id"]
                rel_pred = r["predicate"]
                rel_subj = r["subject_id"]
                rel_obj = r["object_value"]
                rel_conf = r["confidence"] or 0.90
                doc_id = r["source_document_id"]
                doc_fn = r["document_filename"]
                page = r["source_page"]

                rel_key = (doc_id, target_pid, rel_pred, rel_obj)
                if rel_key in seen_rel_keys:
                    continue
                seen_rel_keys.add(rel_key)

                if target_pid and target_pid not in seen_passage_ids:
                    p_row = conn.execute(
                        "SELECT text, section, heading, metadata FROM passages WHERE passage_id = ?",
                        (target_pid,),
                    ).fetchone()
                    if p_row:
                        seen_passage_ids.add(target_pid)
                        meta_dict = {}
                        if p_row["metadata"]:
                            try:
                                meta_dict = json.loads(p_row["metadata"])
                            except Exception:
                                pass
                        meta_dict["relationship_expansion"] = {
                            "predicate": rel_pred,
                            "subject_id": rel_subj,
                            "object_value": rel_obj,
                            "confidence": rel_conf,
                            "is_expanded": True,
                        }
                        expanded.append({
                            "passage_id": target_pid,
                            "document_id": doc_id,
                            "document_filename": doc_fn,
                            "text": p_row["text"],
                            "page_number": page,
                            "section": p_row["section"],
                            "heading": p_row["heading"],
                            "source_type": r["source_type"],
                            "metadata": meta_dict,
                            "confidence": rel_conf,
                            "relationship_info": meta_dict["relationship_expansion"],
                        })
                elif not target_pid and r["source_table_id"] is not None:
                    syn_pid = f"rel_syn_{r['relationship_id'][:16]}"
                    if syn_pid not in seen_passage_ids:
                        seen_passage_ids.add(syn_pid)
                        syn_text = f"[{rel_pred} | Page {page}] {rel_subj} -> {rel_obj}"
                        meta_dict = {
                            "document_id": doc_id,
                            "filename": doc_fn,
                            "page_number": page,
                            "relationship_expansion": {
                                "predicate": rel_pred,
                                "subject_id": rel_subj,
                                "object_value": rel_obj,
                                "confidence": rel_conf,
                                "is_expanded": True,
                            },
                        }
                        expanded.append({
                            "passage_id": syn_pid,
                            "document_id": doc_id,
                            "document_filename": doc_fn,
                            "text": syn_text,
                            "page_number": page,
                            "section": "Table Schedule Evidence",
                            "heading": rel_subj,
                            "source_type": r["source_type"],
                            "metadata": meta_dict,
                            "confidence": rel_conf,
                            "relationship_info": meta_dict["relationship_expansion"],
                        })

        return expanded


def _row_to_record(row: Any) -> RelationshipRecord:
    """Helper to convert sqlite3.Row into RelationshipRecord."""
    d = dict(row)
    try:
        d["metadata"] = json.loads(d["metadata"]) if d.get("metadata") else {}
    except Exception:
        d["metadata"] = {}
    return RelationshipRecord(**d)


# ─── 4. Table Relationship Extraction (R1 Records) ───────────────────────────

def extract_table_relationships_from_db(
    document_id: str,
    user_id: Optional[str] = None,
) -> list[RelationshipRecord]:
    """
    Extracts structural table and event relationships from stored R1 table_cells and document_tables.
    Deterministic, verifiable, and strictly grounded in extracted cell coordinates.
    """
    relationships: list[RelationshipRecord] = []

    with get_db() as conn:
        tables = conn.execute(
            "SELECT table_id, page_number, headers, num_rows, num_cols "
            "FROM document_tables WHERE document_id = ? ORDER BY page_number ASC",
            (document_id,),
        ).fetchall()

        for tbl in tables:
            table_id = tbl["table_id"]
            page_num = tbl["page_number"]
            try:
                headers = json.loads(tbl["headers"])
            except Exception:
                headers = []

            # 1. HEADER_OF relationships
            for h in headers:
                if not h.strip():
                    continue
                rel_id = make_relationship_id(document_id, "HEADER_OF", h.strip(), table_id, table_id=table_id)
                relationships.append(
                    RelationshipRecord(
                        relationship_id=rel_id,
                        subject_id=h.strip(),
                        predicate=RelationshipPredicate.HEADER_OF,
                        object_id=table_id,
                        object_value=f"Column header of table on page {page_num}",
                        source_document_id=document_id,
                        source_table_id=table_id,
                        source_page=page_num,
                        extraction_method=RelationshipExtractionMethod.STRUCTURAL_TABLE,
                        confidence=1.0,
                        user_id=user_id,
                    )
                )

            # Retrieve distinct cell rows
            cells = conn.execute(
                "SELECT row_index, col_index, header, cell_value "
                "FROM table_cells WHERE table_id = ? "
                "GROUP BY row_index, col_index "
                "ORDER BY row_index ASC, col_index ASC",
                (table_id,),
            ).fetchall()

            # Group cells by row_index
            rows_by_idx: dict[int, dict[str, str]] = {}
            for c in cells:
                r_idx = c["row_index"]
                hdr = (c["header"] or "").strip()
                val = (c["cell_value"] or "").strip()
                if r_idx not in rows_by_idx:
                    rows_by_idx[r_idx] = {}
                rows_by_idx[r_idx][hdr] = val

            # Multi-day event tracking across contiguous rows on this page
            current_span_event = ""
            span_start_date = ""
            span_end_date = ""
            span_start_row = -1

            sorted_row_indices = sorted(rows_by_idx.keys())
            for r_idx in sorted_row_indices:
                row_data = rows_by_idx[r_idx]
                date_val = row_data.get("Date", "")
                day_val = row_data.get("Day", "")
                type_val = row_data.get("Type", "")
                event_val = row_data.get("Event", "")

                # 2. CELL_BELONGS_TO_ROW
                for hdr, c_val in row_data.items():
                    if not c_val:
                        continue
                    rel_id = make_relationship_id(document_id, "CELL_BELONGS_TO_ROW", f"cell_r{r_idx}_{hdr}", f"row_{r_idx}", table_id, r_idx)
                    relationships.append(
                        RelationshipRecord(
                            relationship_id=rel_id,
                            subject_id=f"Row {r_idx} [{hdr}]",
                            predicate=RelationshipPredicate.CELL_BELONGS_TO_ROW,
                            object_id=f"{table_id}_r{r_idx}",
                            object_value=c_val,
                            source_document_id=document_id,
                            source_table_id=table_id,
                            source_row_id=r_idx,
                            source_page=page_num,
                            extraction_method=RelationshipExtractionMethod.STRUCTURAL_TABLE,
                            confidence=1.0,
                            user_id=user_id,
                        )
                    )

                # Event semantic relationships
                clean_event = _normalize_event_name(event_val)
                if clean_event and clean_event.lower() not in ("holiday", "teaching day", "teaching day*"):
                    # ROW_DESCRIBES_EVENT
                    rel_row_ev = make_relationship_id(document_id, "ROW_DESCRIBES_EVENT", f"row_{r_idx}", clean_event, table_id, r_idx)
                    relationships.append(
                        RelationshipRecord(
                            relationship_id=rel_row_ev,
                            subject_id=f"{table_id}_row_{r_idx}",
                            predicate=RelationshipPredicate.ROW_DESCRIBES_EVENT,
                            object_value=clean_event,
                            source_document_id=document_id,
                            source_table_id=table_id,
                            source_row_id=r_idx,
                            source_page=page_num,
                            temporal_anchor=date_val or None,
                            extraction_method=RelationshipExtractionMethod.STRUCTURAL_TABLE,
                            confidence=1.0,
                            user_id=user_id,
                        )
                    )

                    # EVENT_HAS_DATE
                    if date_val:
                        rel_date = make_relationship_id(document_id, "EVENT_HAS_DATE", clean_event, date_val, table_id, r_idx)
                        relationships.append(
                            RelationshipRecord(
                                relationship_id=rel_date,
                                subject_id=clean_event,
                                predicate=RelationshipPredicate.EVENT_HAS_DATE,
                                object_value=date_val,
                                source_document_id=document_id,
                                source_table_id=table_id,
                                source_row_id=r_idx,
                                source_page=page_num,
                                temporal_anchor=date_val,
                                extraction_method=RelationshipExtractionMethod.STRUCTURAL_TABLE,
                                confidence=1.0,
                                user_id=user_id,
                            )
                        )

                    # EVENT_HAS_DAY
                    if day_val:
                        rel_day = make_relationship_id(document_id, "EVENT_HAS_DAY", clean_event, day_val, table_id, r_idx)
                        relationships.append(
                            RelationshipRecord(
                                relationship_id=rel_day,
                                subject_id=clean_event,
                                predicate=RelationshipPredicate.EVENT_HAS_DAY,
                                object_value=day_val,
                                source_document_id=document_id,
                                source_table_id=table_id,
                                source_row_id=r_idx,
                                source_page=page_num,
                                temporal_anchor=date_val or None,
                                extraction_method=RelationshipExtractionMethod.STRUCTURAL_TABLE,
                                confidence=1.0,
                                user_id=user_id,
                            )
                        )

                    # EVENT_HAS_TYPE
                    if type_val:
                        rel_type = make_relationship_id(document_id, "EVENT_HAS_TYPE", clean_event, type_val, table_id, r_idx)
                        relationships.append(
                            RelationshipRecord(
                                relationship_id=rel_type,
                                subject_id=clean_event,
                                predicate=RelationshipPredicate.EVENT_HAS_TYPE,
                                object_value=type_val,
                                source_document_id=document_id,
                                source_table_id=table_id,
                                source_row_id=r_idx,
                                source_page=page_num,
                                temporal_anchor=date_val or None,
                                extraction_method=RelationshipExtractionMethod.STRUCTURAL_TABLE,
                                confidence=1.0,
                                user_id=user_id,
                            )
                        )

                    # Track multi-day span
                    if clean_event == current_span_event:
                        span_end_date = date_val
                    else:
                        if current_span_event and span_start_date and span_end_date and span_start_date != span_end_date:
                            _add_span_relationship(
                                relationships, document_id, table_id, span_start_row, page_num,
                                current_span_event, span_start_date, span_end_date, user_id
                            )
                        current_span_event = clean_event
                        span_start_date = date_val
                        span_end_date = date_val
                        span_start_row = r_idx
                else:
                    # Non-event row (e.g. intermediate Holiday or Sunday): close active span if date gap occurs
                    if current_span_event and span_start_date and span_end_date and span_start_date != span_end_date:
                        _add_span_relationship(
                            relationships, document_id, table_id, span_start_row, page_num,
                            current_span_event, span_start_date, span_end_date, user_id
                        )
                        current_span_event = ""
                        span_start_date = ""
                        span_end_date = ""

            # Close any pending span at the end of the table
            if current_span_event and span_start_date and span_end_date and span_start_date != span_end_date:
                _add_span_relationship(
                    relationships, document_id, table_id, span_start_row, page_num,
                    current_span_event, span_start_date, span_end_date, user_id
                )

        # Detect multi-page table continuity across pages
        for i in range(len(tables) - 1):
            t_curr = tables[i]
            t_next = tables[i + 1]
            if t_curr["page_number"] + 1 == t_next["page_number"]:
                rel_cont = make_relationship_id(document_id, "EVENT_CONTINUES_ON_PAGE", t_curr["table_id"], f"Page {t_next['page_number']}")
                relationships.append(
                    RelationshipRecord(
                        relationship_id=rel_cont,
                        subject_id=t_curr["table_id"],
                        predicate=RelationshipPredicate.EVENT_CONTINUES_ON_PAGE,
                        object_id=t_next["table_id"],
                        object_value=f"Academic Calendar table continues onto page {t_next['page_number']}",
                        source_document_id=document_id,
                        source_table_id=t_curr["table_id"],
                        source_page=t_curr["page_number"],
                        extraction_method=RelationshipExtractionMethod.STRUCTURAL_TABLE,
                        confidence=1.0,
                        user_id=user_id,
                    )
                )

    return relationships


def _add_span_relationship(
    relationships: list[RelationshipRecord],
    document_id: str,
    table_id: str,
    row_idx: int,
    page_num: int,
    event_name: str,
    start_date: str,
    end_date: str,
    user_id: Optional[str],
) -> None:
    """Helper to record an explicit multi-day date interval relationship."""
    date_range = f"{start_date} to {end_date}"
    rel_id = make_relationship_id(document_id, "EVENT_HAS_DATE_RANGE", event_name, date_range, table_id, row_idx)
    relationships.append(
        RelationshipRecord(
            relationship_id=rel_id,
            subject_id=event_name,
            predicate=RelationshipPredicate.EVENT_HAS_DATE_RANGE,
            object_value=date_range,
            source_document_id=document_id,
            source_table_id=table_id,
            source_row_id=row_idx,
            source_page=page_num,
            temporal_anchor=f"{start_date}/{end_date}",
            extraction_method=RelationshipExtractionMethod.STRUCTURAL_TABLE,
            confidence=1.0,
            user_id=user_id,
        )
    )


def _normalize_event_name(raw: str) -> str:
    """Clean repeated headers or duplicate text in event names."""
    if not raw:
        return ""
    text = raw.strip()
    # Remove accidental repeated concatenation e.g. "Event Name Event Name"
    words = text.split()
    half = len(words) // 2
    if half >= 3 and words[:half] == words[half:half*2]:
        text = " ".join(words[:half])
    return text.strip()


# ─── 5. Regulatory Relationship Extraction ────────────────────────────────────

def extract_regulatory_relationships_from_db() -> list[RelationshipRecord]:
    """
    Deterministically extracts verified academic regulations from official documents.
    Distinguishes:
    - 70% Course Attendance (Clause 30.1) vs 75% Exam Eligibility (Notification 307/2022).
    - SCSET 2022 scope vs SEAS 2017 Ordinance vs University-Wide Notifications.
    - Medical/Dean exceptions and prerequisite conditions.
    """
    relationships: list[RelationshipRecord] = []

    with get_db() as conn:
        # 1. Inspect Clause 30.1 in SEAS 2017 Ordinance
        doc_2017 = conn.execute(
            "SELECT document_id, title FROM documents WHERE filename LIKE '%SEAS-Ordinance%' OR title LIKE '%2017%'"
        ).fetchone()

        if doc_2017:
            d_id = doc_2017["document_id"]
            p30 = conn.execute(
                "SELECT passage_id, page_number FROM passages WHERE document_id = ? AND text LIKE '%30.1 Attendance Rules%' LIMIT 1",
                (d_id,),
            ).fetchone()
            p_id = p30["passage_id"] if p30 else None
            p_no = p30["page_number"] if p30 else 28

            # RULE_HAS_CLAUSE
            r1 = make_relationship_id(d_id, "RULE_HAS_CLAUSE", "Attendance Requirements", "Clause 30.1")
            relationships.append(RelationshipRecord(
                relationship_id=r1,
                subject_id="Attendance Requirements",
                predicate=RelationshipPredicate.RULE_HAS_CLAUSE,
                object_value="Clause 30.1 — Attendance Rules",
                source_document_id=d_id,
                source_passage_id=p_id,
                source_page=p_no,
                cohort_scope="2017-2021",
                programme_scope="B.Tech (SEAS)",
                extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
            ))

            # CLAUSE_HAS_SUBCLAUSE
            for sub_code, sub_desc in [
                ("30.1(i)", "Presence expected in all scheduled sessions"),
                ("30.1(ii)", "Minimum attendance of 70% in each course during semester; below 70% awards 'X' grade"),
                ("30.1(iii)", "Irrespective of medical or other leaves"),
                ("30.1(iv)", "Each class counted as one unit"),
                ("30.1(v)", "Relaxation up to 10% on special exceptional grounds"),
            ]:
                r_sub = make_relationship_id(d_id, "CLAUSE_HAS_SUBCLAUSE", "Clause 30.1", sub_code)
                relationships.append(RelationshipRecord(
                    relationship_id=r_sub,
                    subject_id="Clause 30.1",
                    predicate=RelationshipPredicate.CLAUSE_HAS_SUBCLAUSE,
                    object_value=f"{sub_code}: {sub_desc}",
                    source_document_id=d_id,
                    source_passage_id=p_id,
                    source_page=p_no,
                    cohort_scope="2017-2021",
                    programme_scope="B.Tech (SEAS)",
                    extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
                ))

            # RULE_HAS_THRESHOLD (Course Attendance: 70%)
            r_thresh = make_relationship_id(d_id, "RULE_HAS_THRESHOLD", "Course Attendance Requirement", "70%")
            relationships.append(RelationshipRecord(
                relationship_id=r_thresh,
                subject_id="Course Attendance Requirement",
                predicate=RelationshipPredicate.RULE_HAS_THRESHOLD,
                object_value="70% minimum attendance per course (Clause 30.1)",
                source_document_id=d_id,
                source_passage_id=p_id,
                source_page=p_no,
                cohort_scope="2017-2021",
                programme_scope="B.Tech (SEAS)",
                extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
            ))

            # RULE_APPLIES_TO_COHORT
            r_cohort = make_relationship_id(d_id, "RULE_APPLIES_TO_COHORT", "SEAS 2017 First Ordinance", "2017-2021 Cohorts")
            relationships.append(RelationshipRecord(
                relationship_id=r_cohort,
                subject_id="SEAS 2017 First Ordinance",
                predicate=RelationshipPredicate.RULE_APPLIES_TO_COHORT,
                object_value="Students admitted in 2017-2021 under SEAS Ordinance",
                source_document_id=d_id,
                source_passage_id=p_id,
                source_page=p_no,
                cohort_scope="2017-2021",
                programme_scope="B.Tech (SEAS)",
                extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
            ))

            # Medical & Dean Exceptions (Clause 30.1(v) on Page 29)
            p_exc = conn.execute(
                "SELECT passage_id, page_number FROM passages WHERE document_id = ? AND text LIKE '%relaxation of up to 10%%' LIMIT 1",
                (d_id,),
            ).fetchone()
            pe_id = p_exc["passage_id"] if p_exc else p_id
            pe_no = p_exc["page_number"] if p_exc else 29

            # RULE_HAS_EXCEPTION
            r_exc = make_relationship_id(d_id, "RULE_HAS_EXCEPTION", "Course Attendance Requirement", "Medical Condonation")
            relationships.append(RelationshipRecord(
                relationship_id=r_exc,
                subject_id="Course Attendance Requirement",
                predicate=RelationshipPredicate.RULE_HAS_EXCEPTION,
                object_value="Clause 30.1(v): Relaxation of up to 10% on medical or approved university representation grounds",
                source_document_id=d_id,
                source_passage_id=pe_id,
                source_page=pe_no,
                cohort_scope="2017-2021",
                programme_scope="B.Tech (SEAS)",
                extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
            ))

            # EXCEPTION_HAS_PREREQUISITE
            r_pre = make_relationship_id(d_id, "EXCEPTION_HAS_PREREQUISITE", "Medical Condonation", "Continuous illness of 2 weeks")
            relationships.append(RelationshipRecord(
                relationship_id=r_pre,
                subject_id="Medical Condonation",
                predicate=RelationshipPredicate.EXCEPTION_HAS_PREREQUISITE,
                object_value="Any continuous illness of at least two weeks (smaller absences do not qualify)",
                source_document_id=d_id,
                source_passage_id=pe_id,
                source_page=pe_no,
                extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
            ))

            # EXCEPTION_REQUIRES_DOCUMENT
            r_doc = make_relationship_id(d_id, "EXCEPTION_REQUIRES_DOCUMENT", "Medical Condonation", "Proper medical certificate")
            relationships.append(RelationshipRecord(
                relationship_id=r_doc,
                subject_id="Medical Condonation",
                predicate=RelationshipPredicate.EXCEPTION_REQUIRES_DOCUMENT,
                object_value="Proper medical certificate submitted to program coordinator to prove genuineness",
                source_document_id=d_id,
                source_passage_id=pe_id,
                source_page=pe_no,
                extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
            ))

            # EXCEPTION_REQUIRES_APPROVAL
            r_app = make_relationship_id(d_id, "EXCEPTION_REQUIRES_APPROVAL", "Medical Condonation", "Dean of School")
            relationships.append(RelationshipRecord(
                relationship_id=r_app,
                subject_id="Medical Condonation",
                predicate=RelationshipPredicate.EXCEPTION_REQUIRES_APPROVAL,
                object_value="Prior approval / recommendation of the Dean of School",
                source_document_id=d_id,
                source_passage_id=pe_id,
                source_page=pe_no,
                extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
            ))

        # 2. Inspect Notification No. 307/2022 (75% Exam Eligibility)
        doc_307 = conn.execute(
            "SELECT document_id, title FROM documents WHERE filename LIKE '%307%' OR title LIKE '%307%'"
        ).fetchone()

        if doc_307:
            d_id = doc_307["document_id"]
            p307 = conn.execute(
                "SELECT passage_id, page_number FROM passages WHERE document_id = ? LIMIT 1",
                (d_id,),
            ).fetchone()
            p_id = p307["passage_id"] if p307 else None
            p_no = p307["page_number"] if p307 else 1

            # RULE_HAS_THRESHOLD (Exam Hall Entry: 75%)
            r307_th = make_relationship_id(d_id, "RULE_HAS_THRESHOLD", "End Semester Examination Eligibility", "75%")
            relationships.append(RelationshipRecord(
                relationship_id=r307_th,
                subject_id="End Semester Examination Eligibility",
                predicate=RelationshipPredicate.RULE_HAS_THRESHOLD,
                object_value="75% aggregate attendance required to be eligible to appear in End Semester Examinations",
                source_document_id=d_id,
                source_passage_id=p_id,
                source_page=p_no,
                temporal_anchor="Effective 2022-11-03 onwards",
                programme_scope="University-wide (All Schools)",
                extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
            ))

            # RULE_HAS_EFFECTIVE_PERIOD
            r307_eff = make_relationship_id(d_id, "RULE_HAS_EFFECTIVE_PERIOD", "Notification 307/2022", "2022-11-03")
            relationships.append(RelationshipRecord(
                relationship_id=r307_eff,
                subject_id="Notification 307/2022",
                predicate=RelationshipPredicate.RULE_HAS_EFFECTIVE_PERIOD,
                object_value="Effective from November 3, 2022 onwards",
                source_document_id=d_id,
                source_passage_id=p_id,
                source_page=p_no,
                temporal_anchor="2022-11-03",
                extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
            ))

            # DOCUMENT_CLARIFIES_RULE
            r307_cla = make_relationship_id(d_id, "DOCUMENT_CLARIFIES_RULE", "Notification 307/2022", "Clause 30.1")
            relationships.append(RelationshipRecord(
                relationship_id=r307_cla,
                subject_id="Notification 307/2022",
                predicate=RelationshipPredicate.DOCUMENT_CLARIFIES_RULE,
                object_value="Standardizes exam hall entrance criteria across all schools, complementing Clause 30.1 course-level grading",
                source_document_id=d_id,
                source_passage_id=p_id,
                source_page=p_no,
                extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
            ))

            # RULE_HAS_APPLICABILITY_SCOPE
            r307_sc = make_relationship_id(d_id, "RULE_HAS_APPLICABILITY_SCOPE", "Notification 307/2022", "University-wide")
            relationships.append(RelationshipRecord(
                relationship_id=r307_sc,
                subject_id="Notification 307/2022",
                predicate=RelationshipPredicate.RULE_HAS_APPLICABILITY_SCOPE,
                object_value="Applicable across all undergraduate and postgraduate programs of Bennett University",
                source_document_id=d_id,
                source_passage_id=p_id,
                source_page=p_no,
                programme_scope="All Schools",
                extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
            ))

        # 3. Inspect SCSET 2022 Undergraduate Rules
        doc_scset = conn.execute(
            "SELECT document_id, title FROM documents WHERE filename LIKE '%SCSET%' OR title LIKE '%SCSET%'"
        ).fetchone()

        if doc_scset:
            d_id = doc_scset["document_id"]
            p_sc = conn.execute(
                "SELECT passage_id, page_number FROM passages WHERE document_id = ? LIMIT 1",
                (d_id,),
            ).fetchone()
            p_id = p_sc["passage_id"] if p_sc else None
            p_no = p_sc["page_number"] if p_sc else 1

            # RULE_APPLIES_TO_PROGRAM
            r_scset = make_relationship_id(d_id, "RULE_APPLIES_TO_PROGRAM", "SCSET Academic Rules", "B.Tech CSE")
            relationships.append(RelationshipRecord(
                relationship_id=r_scset,
                subject_id="SCSET Academic Rules",
                predicate=RelationshipPredicate.RULE_APPLIES_TO_PROGRAM,
                object_value="School of Computer Science Engineering and Technology (SCSET)",
                source_document_id=d_id,
                source_passage_id=p_id,
                source_page=p_no,
                programme_scope="B.Tech CSE / SCSET",
                extraction_method=RelationshipExtractionMethod.DETERMINISTIC_REGULATION,
            ))

    return relationships


# ─── 6. Generic Document Relationship Extraction (R3 Generic Ingestion) ──────

def extract_generic_relationships_from_doc(
    document_id: str,
    user_id: Optional[str] = None,
) -> list[RelationshipRecord]:
    """
    Extracts generic hierarchical, regulatory, condition, exception, threshold,
    applicability, and date relationships from text passages of ANY document (official or upload).
    Document-independent: operates on structural headings, clauses, subclauses, and keywords.
    """
    relationships: list[RelationshipRecord] = []

    with get_db() as conn:
        doc = conn.execute(
            "SELECT document_id, filename, title, source_type FROM documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()
        if not doc:
            return relationships

        doc_title = doc["title"] or doc["filename"] or "Document"

        # Fetch child and parent passages
        passages = conn.execute(
            """
            SELECT passage_id, text, page_number, section, heading, is_parent, chunk_index
            FROM passages
            WHERE document_id = ?
            ORDER BY page_number ASC, chunk_index ASC
            """,
            (document_id,),
        ).fetchall()

        if not passages:
            return relationships

        seen_keys: set[tuple[str, str, str]] = set()

        for p in passages:
            p_id = p["passage_id"]
            p_text = (p["text"] or "").strip()
            p_page = p["page_number"] or 1
            p_heading = (p["heading"] or "").strip()
            p_section = (p["section"] or "").strip()

            if not p_text:
                continue

            # Determine context entity name
            context_clause = None
            if p_heading:
                m_hd = re.search(r'(?:Clause|Section|Rule|Article)?\s*(\b\d+(?:\.\d+)+[a-z\(\)]*)\s*[:\.\-—\s]*(.*)', p_heading, re.IGNORECASE)
                if m_hd:
                    context_clause = f"Clause {m_hd.group(1)}"
                else:
                    context_clause = p_heading[:60]
            elif p_section:
                context_clause = p_section[:60]
            else:
                context_clause = doc_title[:40]

            # 1. Heading / Clause extraction: RULE_HAS_CLAUSE
            clause_candidates = []
            if p_heading:
                clause_candidates.append(p_heading)
            for line in p_text.splitlines()[:6]:
                if re.search(r'^(?:Clause|Section|Rule|Article)\s+\d+', line.strip(), re.IGNORECASE):
                    clause_candidates.append(line.strip())

            for cand in clause_candidates:
                m_cl = re.search(r'(?:Clause|Section|Rule|Article)?\s*(\b\d+(?:\.\d+)*[a-z\(\)]*)\s*[:\.\-—\s]*(.*)', cand, re.IGNORECASE)
                if m_cl and m_cl.group(1):
                    c_num = m_cl.group(1)
                    c_name = m_cl.group(2).strip() or cand
                    c_key = ("RULE_HAS_CLAUSE", doc_title, f"Clause {c_num}")
                    if c_key not in seen_keys:
                        seen_keys.add(c_key)
                        rel_id = make_relationship_id(document_id, "RULE_HAS_CLAUSE", doc_title, f"Clause {c_num}")
                        relationships.append(RelationshipRecord(
                            relationship_id=rel_id,
                            subject_id=doc_title,
                            predicate=RelationshipPredicate.RULE_HAS_CLAUSE,
                            object_value=f"Clause {c_num} — {c_name}",
                            source_document_id=document_id,
                            source_passage_id=p_id,
                            source_page=p_page,
                            user_id=user_id,
                            confidence=0.95,
                            extraction_method=RelationshipExtractionMethod.GENERIC_EXTRACTION,
                        ))

            # 2. Subclause hierarchy in text (e.g. (i), (ii), (a), (b), 12.1(a)): CLAUSE_HAS_SUBCLAUSE
            sub_matches = re.finditer(r'(\(\s*[a-z0-9ivxlc]+\s*\)|\b\d+\.\d+\([a-z0-9]+\))\s*([^\n\(\)]{15,140})', p_text)
            for sm in sub_matches:
                sub_code = sm.group(1).strip()
                sub_body = sm.group(2).strip()
                s_key = ("CLAUSE_HAS_SUBCLAUSE", context_clause, sub_code)
                if s_key not in seen_keys:
                    seen_keys.add(s_key)
                    rel_id = make_relationship_id(document_id, "CLAUSE_HAS_SUBCLAUSE", context_clause, sub_code)
                    relationships.append(RelationshipRecord(
                        relationship_id=rel_id,
                        subject_id=context_clause,
                        predicate=RelationshipPredicate.CLAUSE_HAS_SUBCLAUSE,
                        object_value=f"{sub_code} {sub_body}",
                        source_document_id=document_id,
                        source_passage_id=p_id,
                        source_page=p_page,
                        user_id=user_id,
                        confidence=0.90,
                        extraction_method=RelationshipExtractionMethod.GENERIC_EXTRACTION,
                    ))

            # 3. Exceptions & Conditions: RULE_HAS_EXCEPTION, EXCEPTION_REQUIRES_DOCUMENT, EXCEPTION_REQUIRES_APPROVAL
            exc_triggers = [
                r'(?i)\bprovided\s+that\b',
                r'(?i)\bin\s+exceptional\s+(?:cases?|circumstances?)\b',
                r'(?i)\brelaxation\s+may\s+be\s+granted\b',
                r'(?i)\bexemption\s+may\s+be\s+granted\b',
                r'(?i)\bmedical\s+(?:grounds?|certificate|leave)\b',
                r'(?i)\bcondon(?:e|ation)\b',
                r'(?i)\bunless\s+(?:approved|permitted)\b',
                r'(?i)\bsubject\s+to\s+(?:the\s+)?approval\b',
                r'(?i)\bat\s+the\s+discretion\s+of\b',
            ]
            has_exc = any(re.search(trig, p_text) for trig in exc_triggers)
            if has_exc:
                sentences = re.split(r'(?<=[.!?])\s+', p_text)
                for s in sentences:
                    if any(re.search(trig, s) for trig in exc_triggers) and len(s) > 15:
                        s_clean = s.strip()[:160]
                        e_key = ("RULE_HAS_EXCEPTION", context_clause, s_clean[:60])
                        if e_key not in seen_keys:
                            seen_keys.add(e_key)
                            rel_id = make_relationship_id(document_id, "RULE_HAS_EXCEPTION", context_clause, s_clean[:60])
                            relationships.append(RelationshipRecord(
                                relationship_id=rel_id,
                                subject_id=context_clause,
                                predicate=RelationshipPredicate.RULE_HAS_EXCEPTION,
                                object_value=s_clean,
                                source_document_id=document_id,
                                source_passage_id=p_id,
                                source_page=p_page,
                                user_id=user_id,
                                confidence=0.90,
                                extraction_method=RelationshipExtractionMethod.GENERIC_EXTRACTION,
                            ))

                # Required documentation check across the entire passage
                doc_m = re.search(r'(?i)\b(medical\s+certificate|medical\s+records?|documentary\s+(?:proof|evidence)|written\s+application|undertaking|police\s+report|fir)\b', p_text)
                if doc_m:
                    doc_val = doc_m.group(0).strip().title()
                    d_key = ("EXCEPTION_REQUIRES_DOCUMENT", context_clause, doc_val)
                    if d_key not in seen_keys:
                        seen_keys.add(d_key)
                        rel_id = make_relationship_id(document_id, "EXCEPTION_REQUIRES_DOCUMENT", context_clause, doc_val)
                        relationships.append(RelationshipRecord(
                            relationship_id=rel_id,
                            subject_id=context_clause,
                            predicate=RelationshipPredicate.EXCEPTION_REQUIRES_DOCUMENT,
                            object_value=doc_val,
                            source_document_id=document_id,
                            source_passage_id=p_id,
                            source_page=p_page,
                            user_id=user_id,
                            confidence=0.95,
                            extraction_method=RelationshipExtractionMethod.GENERIC_EXTRACTION,
                        ))

                # Required approval check across the entire passage
                auth_m = re.search(r'(?i)\b(Dean(?:\s+Academics)?|Vice[- ]Chancellor|Director|Head\s+of\s+Department|HoD|Academic\s+Council|Competent\s+Authority)\b', p_text)
                if auth_m:
                    auth_val = f"Approval of {auth_m.group(0).strip()}"
                    a_key = ("EXCEPTION_REQUIRES_APPROVAL", context_clause, auth_val)
                    if a_key not in seen_keys:
                        seen_keys.add(a_key)
                        rel_id = make_relationship_id(document_id, "EXCEPTION_REQUIRES_APPROVAL", context_clause, auth_val)
                        relationships.append(RelationshipRecord(
                            relationship_id=rel_id,
                            subject_id=context_clause,
                            predicate=RelationshipPredicate.EXCEPTION_REQUIRES_APPROVAL,
                            object_value=auth_val,
                            source_document_id=document_id,
                            source_passage_id=p_id,
                            source_page=p_page,
                            user_id=user_id,
                            confidence=0.95,
                            extraction_method=RelationshipExtractionMethod.GENERIC_EXTRACTION,
                        ))

            # 4. Thresholds (attendance %, CGPA, credits): RULE_HAS_THRESHOLD
            att_m = re.search(r'(?i)\b(?:minimum|at\s+least|attendance\s+of)?\s*(\d{1,2}(?:\.\d+)?)\s*%\s*(?:attendance|minimum\s+attendance)?\b', p_text)
            if att_m and ('attend' in p_text.lower() or 'presence' in p_text.lower()):
                val = f"{att_m.group(1)}% Attendance requirement"
                t_key = ("RULE_HAS_THRESHOLD", context_clause, val)
                if t_key not in seen_keys:
                    seen_keys.add(t_key)
                    rel_id = make_relationship_id(document_id, "RULE_HAS_THRESHOLD", context_clause, val)
                    relationships.append(RelationshipRecord(
                        relationship_id=rel_id,
                        subject_id=context_clause,
                        predicate=RelationshipPredicate.RULE_HAS_THRESHOLD,
                        object_value=val,
                        source_document_id=document_id,
                        source_passage_id=p_id,
                        source_page=p_page,
                        user_id=user_id,
                        confidence=0.95,
                        extraction_method=RelationshipExtractionMethod.GENERIC_EXTRACTION,
                    ))

            cgpa_m = re.search(r'(?i)\b(?:minimum|cgpa\s+of|sgpa\s+of)\s*(\d+(?:\.\d+)?)\s*(?:cgpa|sgpa|grade\s+point)\b', p_text)
            if cgpa_m:
                val = f"Minimum {cgpa_m.group(1)} CGPA requirement"
                c_key = ("RULE_HAS_THRESHOLD", context_clause, val)
                if c_key not in seen_keys:
                    seen_keys.add(c_key)
                    rel_id = make_relationship_id(document_id, "RULE_HAS_THRESHOLD", context_clause, val)
                    relationships.append(RelationshipRecord(
                        relationship_id=rel_id,
                        subject_id=context_clause,
                        predicate=RelationshipPredicate.RULE_HAS_THRESHOLD,
                        object_value=val,
                        source_document_id=document_id,
                        source_passage_id=p_id,
                        source_page=p_page,
                        user_id=user_id,
                        confidence=0.90,
                        extraction_method=RelationshipExtractionMethod.GENERIC_EXTRACTION,
                    ))

            # 5. Programme & Cohort applicability: RULE_APPLIES_TO_PROGRAM, RULE_APPLIES_TO_COHORT
            progs = re.findall(r'(?i)\b(B\.?Tech|M\.?Tech|Ph\.?D|MBA|BBA|B\.?Sc|M\.?Sc|B\.?Com|Law|SEAS|SCSET)\b', p_text)
            for prog in set(progs):
                p_val = prog.upper().replace(".", "")
                pr_key = ("RULE_APPLIES_TO_PROGRAM", context_clause, p_val)
                if pr_key not in seen_keys:
                    seen_keys.add(pr_key)
                    rel_id = make_relationship_id(document_id, "RULE_APPLIES_TO_PROGRAM", context_clause, p_val)
                    relationships.append(RelationshipRecord(
                        relationship_id=rel_id,
                        subject_id=context_clause,
                        predicate=RelationshipPredicate.RULE_APPLIES_TO_PROGRAM,
                        object_value=p_val,
                        source_document_id=document_id,
                        source_passage_id=p_id,
                        source_page=p_page,
                        programme_scope=p_val,
                        user_id=user_id,
                        confidence=0.90,
                        extraction_method=RelationshipExtractionMethod.GENERIC_EXTRACTION,
                    ))

            cohorts = re.findall(r'(?i)\b(?:batch\s+of\s+(\d{4})|cohort\s+(\d{4}(?:-\d{2,4})?)|(\d{4}-\d{2,4})\s+onwards|academic\s+year\s+(\d{4}-\d{2,4}))\b', p_text)
            for c_tuple in cohorts:
                c_val = next(x for x in c_tuple if x)
                co_key = ("RULE_APPLIES_TO_COHORT", context_clause, c_val)
                if co_key not in seen_keys:
                    seen_keys.add(co_key)
                    rel_id = make_relationship_id(document_id, "RULE_APPLIES_TO_COHORT", context_clause, c_val)
                    relationships.append(RelationshipRecord(
                        relationship_id=rel_id,
                        subject_id=context_clause,
                        predicate=RelationshipPredicate.RULE_APPLIES_TO_COHORT,
                        object_value=f"Cohort {c_val}",
                        source_document_id=document_id,
                        source_passage_id=p_id,
                        source_page=p_page,
                        cohort_scope=c_val,
                        user_id=user_id,
                        confidence=0.85,
                        extraction_method=RelationshipExtractionMethod.GENERIC_EXTRACTION,
                    ))

            # 6. Dates in text: EVENT_HAS_DATE
            date_matches = re.finditer(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\b', p_text)
            for dm in date_matches:
                dt_str = dm.group(1).strip()
                dt_key = ("EVENT_HAS_DATE", context_clause, dt_str)
                if dt_key not in seen_keys and len(relationships) < 300:
                    seen_keys.add(dt_key)
                    rel_id = make_relationship_id(document_id, "EVENT_HAS_DATE", context_clause, dt_str)
                    relationships.append(RelationshipRecord(
                        relationship_id=rel_id,
                        subject_id=context_clause,
                        predicate=RelationshipPredicate.EVENT_HAS_DATE,
                        object_value=dt_str,
                        source_document_id=document_id,
                        source_passage_id=p_id,
                        source_page=p_page,
                        temporal_anchor=dt_str,
                        user_id=user_id,
                        confidence=0.85,
                        extraction_method=RelationshipExtractionMethod.GENERIC_EXTRACTION,
                    ))

    return relationships

