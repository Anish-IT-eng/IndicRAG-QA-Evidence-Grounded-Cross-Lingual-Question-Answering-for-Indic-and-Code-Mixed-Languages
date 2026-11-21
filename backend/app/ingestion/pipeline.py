"""
Document ingestion pipeline.

Orchestrates:
  1. Hash check (skip unchanged files)
  2. PDF text extraction
  3. Structure-aware chunking (parent + child)
  4. Embedding and indexing
  5. Metadata persistence to SQLite
  6. Source-provenance tracking
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.logging_config import logger
from app.ingestion.pdf_extractor import (
    RawChunk,
    chunk_pages,
    compute_file_hash,
    extract_pages,
)
from app.models.schemas import (
    DocumentRecord,
    DocumentSource,
    DocumentVersionInfo,
    IngestionStatus,
    PassageRecord,
)
from app.retrieval.engine import get_official_index, get_upload_index


# ─── Database helpers ──────────────────────────────────────────────────────────

def _upsert_document(doc: DocumentRecord) -> None:
    vi = doc.version_info
    with get_db() as conn:
        conn.execute("""
            INSERT INTO documents (
                document_id, filename, source_url, source_type,
                file_hash, ingestion_timestamp, ingestion_status,
                page_count, title, description,
                effective_date, academic_year, program_applicability,
                superseded_by, supersedes, is_current, version_notes,
                metadata, error_message, created_at, updated_at
            ) VALUES (
                :document_id, :filename, :source_url, :source_type,
                :file_hash, :ingestion_timestamp, :ingestion_status,
                :page_count, :title, :description,
                :effective_date, :academic_year, :program_applicability,
                :superseded_by, :supersedes, :is_current, :version_notes,
                :metadata, :error_message, :created_at, :updated_at
            )
            ON CONFLICT(document_id) DO UPDATE SET
                title            = excluded.title,
                description      = excluded.description,
                effective_date   = excluded.effective_date,
                academic_year    = excluded.academic_year,
                program_applicability = excluded.program_applicability,
                superseded_by    = excluded.superseded_by,
                supersedes       = excluded.supersedes,
                is_current       = excluded.is_current,
                version_notes    = excluded.version_notes,
                metadata         = excluded.metadata,
                ingestion_status = excluded.ingestion_status,
                page_count       = excluded.page_count,
                error_message    = excluded.error_message,
                updated_at       = excluded.updated_at
        """, {
            "document_id": doc.document_id,
            "filename": doc.filename,
            "source_url": str(doc.source_url) if doc.source_url else None,
            "source_type": doc.source_type.value,
            "file_hash": doc.file_hash,
            "ingestion_timestamp": doc.ingestion_timestamp.isoformat(),
            "ingestion_status": doc.ingestion_status.value,
            "page_count": doc.page_count,
            "title": doc.title,
            "description": doc.description,
            "effective_date": vi.effective_date,
            "academic_year": vi.academic_year,
            "program_applicability": json.dumps(vi.program_applicability or []),
            "superseded_by": vi.superseded_by,
            "supersedes": vi.supersedes,
            "is_current": (1 if vi.is_current else 0) if vi.is_current is not None else None,
            "version_notes": vi.notes,
            "metadata": json.dumps(doc.metadata),
            "error_message": doc.error_message,
            "created_at": doc.ingestion_timestamp.isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })


def _insert_passages(passages: list[PassageRecord]) -> None:
    with get_db() as conn:
        conn.executemany("""
            INSERT OR IGNORE INTO passages (
                passage_id, document_id, parent_passage_id,
                is_parent, text, page_number, section,
                heading, clause, table_ref, chunk_index,
                total_chunks, source_type, metadata, created_at
            ) VALUES (
                :passage_id, :document_id, :parent_passage_id,
                :is_parent, :text, :page_number, :section,
                :heading, :clause, :table_ref, :chunk_index,
                :total_chunks, :source_type, :metadata, :created_at
            )
        """, [
            {
                "passage_id": p.passage_id,
                "document_id": p.document_id,
                "parent_passage_id": p.parent_passage_id,
                "is_parent": int(p.is_parent),
                "text": p.text,
                "page_number": p.page_number,
                "section": p.section,
                "heading": p.heading,
                "clause": p.clause,
                "table_ref": p.table_ref,
                "chunk_index": p.chunk_index,
                "total_chunks": p.total_chunks,
                "source_type": p.source_type.value,
                "metadata": json.dumps(p.metadata),
                "created_at": datetime.utcnow().isoformat(),
            }
            for p in passages
        ])


def _insert_document_tables(document_id: str, pages: list[RawPage]) -> None:
    table_rows = []
    cell_rows = []
    for page in pages:
        for tbl in page.tables:
            tid = tbl.get("table_id") or str(uuid.uuid4())
            headers = tbl.get("headers", [])
            rows = tbl.get("rows", [])
            cells = tbl.get("cells", [])
            table_rows.append({
                "table_id": tid,
                "document_id": document_id,
                "page_number": page.page_number,
                "headers": json.dumps(headers),
                "num_rows": len(rows),
                "num_cols": len(headers),
                "confidence": tbl.get("confidence", 1.0),
                "status": tbl.get("status", "extracted"),
                "structured_text": tbl.get("structured_text", ""),
                "raw_markdown": tbl.get("raw_markdown", ""),
                "metadata": json.dumps(tbl.get("metadata", {})),
                "created_at": datetime.utcnow().isoformat(),
            })
            for c in cells:
                cell_rows.append({
                    "cell_id": str(uuid.uuid4()),
                    "table_id": tid,
                    "document_id": document_id,
                    "page_number": page.page_number,
                    "row_index": c.get("row_index", 0),
                    "col_index": c.get("col_index", 0),
                    "header": c.get("header", ""),
                    "cell_value": c.get("cell_value", ""),
                    "original_text": c.get("original_text", ""),
                    "confidence": c.get("confidence", 1.0),
                    "created_at": datetime.utcnow().isoformat(),
                })

    if table_rows:
        with get_db() as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO document_tables (
                    table_id, document_id, page_number, headers,
                    num_rows, num_cols, confidence, status,
                    structured_text, raw_markdown, metadata, created_at
                ) VALUES (
                    :table_id, :document_id, :page_number, :headers,
                    :num_rows, :num_cols, :confidence, :status,
                    :structured_text, :raw_markdown, :metadata, :created_at
                )
            """, table_rows)
            if cell_rows:
                conn.executemany("""
                    INSERT OR REPLACE INTO table_cells (
                        cell_id, table_id, document_id, page_number,
                        row_index, col_index, header, cell_value,
                        original_text, confidence, created_at
                    ) VALUES (
                        :cell_id, :table_id, :document_id, :page_number,
                        :row_index, :col_index, :header, :cell_value,
                        :original_text, :confidence, :created_at
                    )
                """, cell_rows)
            logger.info("Persisted %d tables and %d cells for document %s", len(table_rows), len(cell_rows), document_id)


def _find_by_hash(file_hash: str, source_type: DocumentSource, user_id: Optional[str] = None) -> Optional[str]:
    """Return existing document_id if this file was already ingested in this scope."""
    with get_db() as conn:
        if source_type == DocumentSource.UPLOAD:
            if user_id:
                row = conn.execute(
                    "SELECT document_id FROM documents WHERE file_hash = ? AND source_type = ? AND json_extract(metadata, '$.user_id') = ?",
                    (file_hash, source_type.value, user_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT document_id FROM documents WHERE file_hash = ? AND source_type = ? AND json_extract(metadata, '$.user_id') IS NULL",
                    (file_hash, source_type.value),
                ).fetchone()
        else:
            row = conn.execute(
                "SELECT document_id FROM documents WHERE file_hash = ? AND source_type = ?",
                (file_hash, source_type.value),
            ).fetchone()
        return row["document_id"] if row else None


# ─── Core ingestion logic ──────────────────────────────────────────────────────

def ingest_pdf(
    pdf_path: Path,
    source_type: DocumentSource,
    source_url: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    version_info: Optional[DocumentVersionInfo] = None,
    force: bool = False,
    user_id: Optional[str] = None,
) -> DocumentRecord:
    """
    Ingest a single PDF file into the system.

    Returns the DocumentRecord (with final status set).
    Does NOT re-ingest an unchanged file unless force=True.
    """
    pdf_path = Path(pdf_path)
    logger.info("Ingesting %s (source_type=%s, user_id=%s)", pdf_path.name, source_type.value, user_id)

    # 1. Hash check
    file_hash = compute_file_hash(pdf_path)
    existing_id = _find_by_hash(file_hash, source_type=source_type, user_id=user_id)
    if not force:
        if existing_id:
            logger.info(
                "File %s already ingested as %s — skipping.",
                pdf_path.name, existing_id,
            )
            # Return minimal record indicating skip
            return DocumentRecord(
                document_id=existing_id,
                filename=pdf_path.name,
                source_type=source_type,
                file_hash=file_hash,
                ingestion_status=IngestionStatus.SKIPPED,
                version_info=version_info or DocumentVersionInfo(),
            )
    elif existing_id:
        with get_db() as conn:
            conn.execute("DELETE FROM passages WHERE document_id = ?", (existing_id,))
            conn.execute("DELETE FROM table_cells WHERE document_id = ?", (existing_id,))
            conn.execute("DELETE FROM document_tables WHERE document_id = ?", (existing_id,))
            conn.execute("DELETE FROM document_relationships WHERE source_document_id = ?", (existing_id,))
        idx = get_official_index() if source_type == DocumentSource.OFFICIAL else get_upload_index()
        idx.remove_document_passages(existing_id)
        logger.info("Force re-ingest: cleared existing passages and tables for document %s", existing_id)

    doc_id = existing_id if (force and existing_id) else str(uuid.uuid4())
    doc_metadata = {"user_id": user_id} if user_id else {}
    doc = DocumentRecord(
        document_id=doc_id,
        filename=pdf_path.name,
        source_url=source_url,
        source_type=source_type,
        file_hash=file_hash,
        ingestion_status=IngestionStatus.PROCESSING,
        title=title or pdf_path.stem,
        description=description,
        version_info=version_info or DocumentVersionInfo(),
        metadata=doc_metadata,
    )
    _upsert_document(doc)

    try:
        # 2. Extract pages
        pages = extract_pages(pdf_path)
        doc.page_count = len(pages)

        # 3. Chunk
        raw_chunks: list[RawChunk] = chunk_pages(pages)

        # 4. Build passage records
        # Assign parent passage IDs first (parents are first in the list)
        parent_records: dict[int, PassageRecord] = {}
        child_passages: list[PassageRecord] = []

        for chunk in raw_chunks:
            if chunk.is_parent:
                pr = PassageRecord(
                    passage_id=str(uuid.uuid4()),
                    document_id=doc.document_id,
                    parent_passage_id=None,
                    is_parent=True,
                    text=chunk.text,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    heading=chunk.heading,
                    clause=chunk.clause,
                    table_ref=chunk.table_ref,
                    chunk_index=chunk.chunk_index,
                    total_chunks=len([c for c in raw_chunks if c.is_parent]),
                    source_type=source_type,
                    metadata={
                        "document_id": doc.document_id,
                        "filename": pdf_path.name,
                        "document_filename": pdf_path.name,
                        "source_type": source_type.value,
                        "user_id": user_id,
                        "effective_date": version_info.effective_date if version_info else None,
                        "academic_year": version_info.academic_year if version_info else None,
                        "is_current": version_info.is_current if version_info else None,
                        "superseded_by": version_info.superseded_by if version_info else None,
                    },
                )
                parent_records[chunk.chunk_index] = pr
            else:
                child_passages.append(chunk)

        # Create child PassageRecords with parent links
        all_passages: list[PassageRecord] = list(parent_records.values())
        child_total = len(child_passages)
        for chunk in child_passages:
            parent_pr = parent_records.get(
                chunk.parent_chunk_index if chunk.parent_chunk_index is not None else -1
            )
            cr = PassageRecord(
                passage_id=str(uuid.uuid4()),
                document_id=doc.document_id,
                parent_passage_id=parent_pr.passage_id if parent_pr else None,
                is_parent=False,
                text=chunk.text,
                page_number=chunk.page_number,
                section=chunk.section,
                heading=chunk.heading,
                clause=chunk.clause,
                table_ref=chunk.table_ref,
                chunk_index=chunk.chunk_index,
                total_chunks=child_total,
                source_type=source_type,
                metadata={
                    "document_id": doc.document_id,
                    "filename": pdf_path.name,
                    "document_filename": pdf_path.name,
                    "source_type": source_type.value,
                    "user_id": user_id,
                    "effective_date": version_info.effective_date if version_info else None,
                    "academic_year": version_info.academic_year if version_info else None,
                    "is_current": version_info.is_current if version_info else None,
                    "superseded_by": version_info.superseded_by if version_info else None,
                    "parent_passage_id": parent_pr.passage_id if parent_pr else None,
                    "table_ref": chunk.table_ref,
                    "page_number": chunk.page_number,
                    "section": chunk.section,
                    "heading": chunk.heading,
                    "text": chunk.text,   # pre-stored for reranker
                },
            )
            all_passages.append(cr)

        # 5. Persist passages to DB
        _insert_passages(all_passages)
        logger.info("Stored %d passages for %s.", len(all_passages), pdf_path.name)

        # 5b. Persist structured tables and cells to DB
        _insert_document_tables(doc.document_id, pages)

        # 5c. Extract and store structural table relationships
        try:
            from app.retrieval.relationship_store import extract_table_relationships_from_db, RelationshipStore
            table_rels = extract_table_relationships_from_db(doc.document_id, user_id=user_id)
            if table_rels:
                RelationshipStore.insert_relationships(table_rels)
                logger.info("Extracted and stored %d table relationships for %s.", len(table_rels), pdf_path.name)
        except Exception as _rele:
            logger.warning("Failed to extract table relationships for %s: %s", pdf_path.name, _rele)

        # 5d. Extract and store generic hierarchical & regulatory text relationships (R3)
        try:
            from app.retrieval.relationship_store import extract_generic_relationships_from_doc, RelationshipStore
            generic_rels = extract_generic_relationships_from_doc(doc.document_id, user_id=user_id)
            if generic_rels:
                RelationshipStore.insert_relationships(generic_rels)
                logger.info("Extracted and stored %d generic relationships for %s.", len(generic_rels), pdf_path.name)
        except Exception as _genrele:
            logger.warning("Failed to extract generic relationships for %s: %s", pdf_path.name, _genrele)

        # 6. Update retrieval index (child passages only, as retrieval units)
        child_recs = [p for p in all_passages if not p.is_parent]
        idx = get_official_index() if source_type == DocumentSource.OFFICIAL else get_upload_index()
        idx.add_passages(
            passage_ids=[p.passage_id for p in child_recs],
            texts=[p.text for p in child_recs],
            meta=[p.metadata for p in child_recs],
        )
        idx.build()

        doc.ingestion_status = IngestionStatus.COMPLETED
        _upsert_document(doc)
        logger.info("Ingestion complete for %s.", pdf_path.name)

    except Exception as exc:
        logger.exception("Ingestion failed for %s: %s", pdf_path.name, exc)
        doc.ingestion_status = IngestionStatus.FAILED
        doc.error_message = str(exc)
        _upsert_document(doc)

    return doc


def get_all_documents(source_type: Optional[DocumentSource] = None, user_id: Optional[str] = None) -> list[dict]:
    """Return all document records from DB, optionally filtered by source_type and user_id."""
    with get_db() as conn:
        if source_type:
            if source_type == DocumentSource.UPLOAD and user_id:
                rows = conn.execute(
                    "SELECT * FROM documents WHERE source_type = ? AND (json_extract(metadata, '$.user_id') = ? OR json_extract(metadata, '$.user_id') IS NULL OR json_extract(metadata, '$.user_id') = '') ORDER BY ingestion_timestamp DESC",
                    (source_type.value, user_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM documents WHERE source_type = ? ORDER BY ingestion_timestamp DESC",
                    (source_type.value,),
                ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY ingestion_timestamp DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def get_passages_for_document(document_id: str) -> list[dict]:
    """Return all passages for a given document."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM passages WHERE document_id = ? ORDER BY chunk_index",
            (document_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_document(document_id: str, user_id: Optional[str] = None) -> bool:
    """
    Cascading delete of a document, its passages, tables, cells, relationships, and index entries.
    Respects user_id scoping for uploaded documents.
    """
    with get_db() as conn:
        doc = conn.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,)).fetchone()
        if not doc:
            return False

        # Tenant isolation check if user_id is provided
        if user_id and doc["source_type"] == DocumentSource.UPLOAD.value:
            meta = json.loads(doc["metadata"]) if doc["metadata"] else {}
            if meta.get("user_id") != user_id:
                raise PermissionError(f"User {user_id} cannot delete document belonging to another tenant")

        conn.execute("DELETE FROM passages WHERE document_id = ?", (document_id,))
        conn.execute("DELETE FROM table_cells WHERE document_id = ?", (document_id,))
        conn.execute("DELETE FROM document_tables WHERE document_id = ?", (document_id,))
        conn.execute("DELETE FROM document_relationships WHERE source_document_id = ?", (document_id,))
        conn.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))

    # Remove from index
    try:
        source_type = DocumentSource(doc["source_type"])
        idx = get_official_index() if source_type == DocumentSource.OFFICIAL else get_upload_index()
        idx.remove_document_passages(document_id)
    except Exception as exc:
        logger.warning("Could not remove document %s from retriever index: %s", document_id, exc)

    logger.info("Successfully deleted document %s and all associated records/relationships.", document_id)
    return True

