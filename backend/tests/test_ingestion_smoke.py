"""
Ingestion smoke test — Milestone 1.

Generates a well-formed synthetic PDF entirely in Python (no reportlab,
no internet download) and verifies every stage of the ingestion pipeline:

  1. PDF creation               — produces a byte-valid PDF
  2. hash computation           — SHA-256 is stable across calls
  3. page extraction            — at least one page returned, text preserved
  4. structure-aware chunking   — at least one child passage produced
  5. full pipeline              — DocumentRecord written to DB, passages stored
  6. deduplication              — re-ingesting the same file is a no-op (SKIPPED)
  7. page numbers               — passage page_number ≥ 1 (1-indexed)
  8. metadata provenance        — version_info fields round-trip through DB
  9. passage text integrity     — key phrase from synthetic doc is retrievable
 10. parent–child linkage       — every child points to a parent in the same doc

The synthetic PDF contains realistic university-regulation-style text so the
chunker exercises heading detection, clause parsing, and multi-paragraph splits.
"""
from __future__ import annotations

import io
import json
import struct
import tempfile
import textwrap
import uuid
from pathlib import Path

import pytest

# ── Synthetic PDF builder ──────────────────────────────────────────────────────

SYNTHETIC_TEXT_PAGES = [
    # Page 1 — cover-style text
    textwrap.dedent("""\
        Bennett University — School of Computer Science Engineering and Technology
        B.Tech Academic Regulations — Academic Year 2023-24
        Effective Date: 01 August 2023
        These regulations supersede the 2022-23 edition.
    """),
    # Page 2 — attendance rules (the kind of text QA will query)
    textwrap.dedent("""\
        3. ATTENDANCE REQUIREMENTS

        3.1 Minimum Attendance
        A student must maintain a minimum attendance of 75 percent in each course
        in order to be eligible to appear in the End-Semester Examination.

        3.2 Medical Condonation
        On medical grounds, attendance may be condoned up to 65 percent subject
        to submission of a valid medical certificate within seven days.

        3.3 Shortage of Attendance
        A student falling below 65 percent attendance in any course shall be
        debarred from appearing in the End-Semester Examination for that course
        and shall be required to repeat the course.
    """),
    # Page 3 — examination rules
    textwrap.dedent("""\
        4. EXAMINATION RULES

        4.1 End-Semester Examination
        The End-Semester Examination shall carry 50 percent of the total marks
        for each course. The remaining 50 percent shall be allocated to
        Continuous Assessment (CA) components.

        4.2 Passing Criteria
        A student must secure a minimum of 40 percent marks in the
        End-Semester Examination and 40 percent marks in CA independently
        to pass a course.

        4.3 Re-examination
        A student who fails a course is entitled to appear in the
        supplementary examination conducted at the end of the academic year.
    """),
    # Page 4 — grading
    textwrap.dedent("""\
        5. GRADING SCHEME

        Grade  Grade Points  Range (%)
        O      10            90 – 100
        A+      9            80 –  89
        A       8            70 –  79
        B+      7            60 –  69
        B       6            55 –  59
        C       5            50 –  54
        P       4            40 –  49
        F       0            Below 40

        5.1 SGPA and CGPA
        SGPA is computed as the ratio of the sum of credit-weighted grade
        points earned in a semester to the total credits registered.
        CGPA is the cumulative average across all completed semesters.
    """),
]


def _build_pdf_bytes(pages: list[str]) -> bytes:
    """
    Produce a minimal but fully valid PDF 1.4 file containing the supplied
    text pages.  No external library required — uses only the standard
    library (struct, io).

    Each page uses the PDF Helvetica base font so there is no font embedding
    dependency.  Text is encoded as ISO-8859-1 (latin-1) after replacing
    characters outside that range with '?'.
    """
    buf = io.BytesIO()
    offsets: list[int] = []

    def w(data: bytes) -> int:
        pos = buf.tell()
        buf.write(data)
        return pos

    def wb(s: str) -> int:
        return w(s.encode("latin-1", errors="replace"))

    # Header
    wb("%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    # Track object byte offsets; object IDs are 1-based
    obj_offsets: dict[int, int] = {}

    def begin_obj(oid: int) -> None:
        obj_offsets[oid] = buf.tell()
        wb(f"{oid} 0 obj\n")

    def end_obj() -> None:
        wb("endobj\n")

    # Object plan:
    # 1   Catalog
    # 2   Pages (parent)
    # 3   Font (Helvetica shared)
    # 4 + 2*i   Page dict for page i
    # 5 + 2*i   Content stream for page i

    n_pages = len(pages)
    page_obj_ids   = [4 + 2 * i for i in range(n_pages)]
    content_obj_ids = [5 + 2 * i for i in range(n_pages)]
    font_obj_id = 3
    pages_obj_id = 2
    catalog_obj_id = 1

    # 1 — Catalog (forward ref to Pages, written last in update)
    # We write a placeholder and patch it after we know offsets.
    # Simpler: write all objects in order.

    # Build all content streams first (so we know lengths)
    streams: list[bytes] = []
    for text in pages:
        lines = text.strip().splitlines()
        ops = ["BT", "/F1 10 Tf", "10 TL"]
        y = 750
        ops.append(f"50 {y} Td")
        for line in lines:
            clean = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            ops.append(f"({clean}) Tj T*")
        ops.append("ET")
        stream_bytes = "\n".join(ops).encode("latin-1", errors="replace")
        streams.append(stream_bytes)

    # 1 — Catalog
    begin_obj(catalog_obj_id)
    wb(f"<< /Type /Catalog /Pages {pages_obj_id} 0 R >>\n")
    end_obj()

    # 2 — Pages
    page_refs = " ".join(f"{oid} 0 R" for oid in page_obj_ids)
    begin_obj(pages_obj_id)
    wb(f"<< /Type /Pages /Kids [{page_refs}] /Count {n_pages} >>\n")
    end_obj()

    # 3 — Font
    begin_obj(font_obj_id)
    wb("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\n")
    end_obj()

    # 4+, 5+ — Page dicts and content streams
    for i, (stream, page_oid, content_oid) in enumerate(
        zip(streams, page_obj_ids, content_obj_ids)
    ):
        begin_obj(page_oid)
        wb(
            f"<< /Type /Page /Parent {pages_obj_id} 0 R "
            f"/MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_obj_id} 0 R >> >> "
            f"/Contents {content_oid} 0 R >>\n"
        )
        end_obj()

        begin_obj(content_oid)
        wb(f"<< /Length {len(stream)} >>\n")
        wb("stream\n")
        w(stream)
        wb("\nendstream\n")
        end_obj()

    # Cross-reference table
    xref_pos = buf.tell()
    n_objs = max(obj_offsets) + 1
    wb(f"xref\n0 {n_objs}\n")
    wb("0000000000 65535 f \n")
    for oid in range(1, n_objs):
        off = obj_offsets.get(oid, 0)
        wb(f"{off:010d} 00000 n \n")

    # Trailer
    wb(f"trailer\n<< /Size {n_objs} /Root {catalog_obj_id} 0 R >>\n")
    wb(f"startxref\n{xref_pos}\n%%EOF\n")

    return buf.getvalue()


def make_synthetic_pdf(path: Path) -> None:
    """Write a multi-page synthetic university-regulations PDF to *path*."""
    pdf_bytes = _build_pdf_bytes(SYNTHETIC_TEXT_PAGES)
    path.write_bytes(pdf_bytes)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def synthetic_pdf(tmp_path_factory) -> Path:
    """One synthetic PDF reused across the whole test module."""
    p = tmp_path_factory.mktemp("smoke") / "synthetic_regulations.pdf"
    make_synthetic_pdf(p)
    assert p.stat().st_size > 200, "Synthetic PDF must be non-trivial"
    return p


@pytest.fixture(scope="module")
def isolated_db(tmp_path_factory):
    """
    Isolated DB so the smoke tests never touch the real database.
    Patches settings.db_path and settings.indexes_dir to temp directories,
    then initialises a fresh schema.

    Uses pytest.MonkeyPatch (class API) which supports module scope.
    """
    mp = pytest.MonkeyPatch()
    base = tmp_path_factory.mktemp("smoke_db")
    db_path = base / "db" / "indicrag.db"
    idx_dir = base / "indexes"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    idx_dir.mkdir(parents=True, exist_ok=True)

    from app.core import config as _cfg
    mp.setattr(_cfg.settings, "db_path",    db_path, raising=True)
    mp.setattr(_cfg.settings, "indexes_dir", idx_dir, raising=True)

    # Reset cached retrieval-engine singletons so they pick up the new indexes_dir
    try:
        from app.retrieval import engine as _eng
        _eng._indexes.clear()
    except Exception:
        pass

    from app.core.database import init_db
    init_db()

    yield base

    mp.undo()
    try:
        from app.retrieval import engine as _eng
        _eng._indexes.clear()
    except Exception:
        pass


# ── Test 1 — PDF byte validity ─────────────────────────────────────────────────

class TestSyntheticPDFCreation:
    def test_pdf_starts_with_header(self, synthetic_pdf):
        header = synthetic_pdf.read_bytes()[:8]
        assert header == b"%PDF-1.4", f"Bad header: {header!r}"

    def test_pdf_ends_with_eof(self, synthetic_pdf):
        tail = synthetic_pdf.read_bytes()[-10:]
        assert b"%%EOF" in tail, f"Missing %%EOF in tail: {tail!r}"

    def test_pdf_size_reasonable(self, synthetic_pdf):
        size = synthetic_pdf.stat().st_size
        assert 500 < size < 200_000, f"Unexpected size: {size}"


# ── Test 2 — Hash computation ──────────────────────────────────────────────────

class TestHashComputation:
    def test_hash_is_hex_string(self, synthetic_pdf):
        from app.ingestion.pdf_extractor import compute_file_hash
        h = compute_file_hash(synthetic_pdf)
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex
        assert all(c in "0123456789abcdef" for c in h)

    def test_hash_is_deterministic(self, synthetic_pdf):
        from app.ingestion.pdf_extractor import compute_file_hash
        h1 = compute_file_hash(synthetic_pdf)
        h2 = compute_file_hash(synthetic_pdf)
        assert h1 == h2, "Hash must be deterministic"

    def test_different_content_different_hash(self, synthetic_pdf, tmp_path):
        from app.ingestion.pdf_extractor import compute_file_hash
        alt = tmp_path / "alt.pdf"
        make_synthetic_pdf(alt)
        # Same content → same hash
        h1 = compute_file_hash(synthetic_pdf)
        h2 = compute_file_hash(alt)
        assert h1 == h2, "Identical content must hash identically"

        # Corrupt a byte → different hash
        data = bytearray(alt.read_bytes())
        data[50] ^= 0xFF
        alt.write_bytes(bytes(data))
        h3 = compute_file_hash(alt)
        assert h1 != h3, "Different content must hash differently"


# ── Test 3 — Page extraction ───────────────────────────────────────────────────

class TestPageExtraction:
    def test_extracts_expected_page_count(self, synthetic_pdf):
        from app.ingestion.pdf_extractor import extract_pages
        pages = extract_pages(synthetic_pdf)
        assert len(pages) == len(SYNTHETIC_TEXT_PAGES), (
            f"Expected {len(SYNTHETIC_TEXT_PAGES)} pages, got {len(pages)}"
        )

    def test_pages_have_text(self, synthetic_pdf):
        from app.ingestion.pdf_extractor import extract_pages
        pages = extract_pages(synthetic_pdf)
        for pg in pages:
            assert pg.text.strip(), f"Page {pg.page_number} has no text"

    def test_page_numbers_are_1indexed(self, synthetic_pdf):
        from app.ingestion.pdf_extractor import extract_pages
        pages = extract_pages(synthetic_pdf)
        nums = [pg.page_number for pg in pages]
        assert nums[0] >= 1, "First page must be numbered ≥ 1"
        assert nums == sorted(set(nums)), "Page numbers must be unique and sorted"

    def test_attendance_rule_text_present(self, synthetic_pdf):
        from app.ingestion.pdf_extractor import extract_pages
        pages = extract_pages(synthetic_pdf)
        all_text = " ".join(pg.text for pg in pages).lower()
        assert "75 percent" in all_text or "75%" in all_text or "attendance" in all_text, (
            "Attendance rule text not found in extracted pages"
        )

    def test_page_returns_page_number_attribute(self, synthetic_pdf):
        from app.ingestion.pdf_extractor import extract_pages
        pages = extract_pages(synthetic_pdf)
        for pg in pages:
            assert hasattr(pg, "page_number"), "RawPage must have page_number"
            assert isinstance(pg.page_number, int)


# ── Test 4 — Chunking ─────────────────────────────────────────────────────────

class TestChunking:
    def test_produces_child_passages(self, synthetic_pdf):
        from app.ingestion.pdf_extractor import chunk_pages, extract_pages
        pages = extract_pages(synthetic_pdf)
        chunks = chunk_pages(pages)
        children = [c for c in chunks if not c.is_parent]
        assert len(children) >= 1, "Must produce at least one child passage"

    def test_produces_parent_passages(self, synthetic_pdf):
        from app.ingestion.pdf_extractor import chunk_pages, extract_pages
        pages = extract_pages(synthetic_pdf)
        chunks = chunk_pages(pages)
        parents = [c for c in chunks if c.is_parent]
        assert len(parents) >= 1, "Must produce at least one parent passage"

    def test_child_has_page_number(self, synthetic_pdf):
        from app.ingestion.pdf_extractor import chunk_pages, extract_pages
        pages = extract_pages(synthetic_pdf)
        chunks = chunk_pages(pages)
        children = [c for c in chunks if not c.is_parent]
        for ch in children:
            assert ch.page_number is not None and ch.page_number >= 1, (
                f"Child chunk missing valid page_number: {ch}"
            )

    def test_child_text_non_empty(self, synthetic_pdf):
        from app.ingestion.pdf_extractor import chunk_pages, extract_pages
        pages = extract_pages(synthetic_pdf)
        chunks = chunk_pages(pages)
        for ch in chunks:
            assert ch.text.strip(), f"Chunk index={ch.chunk_index} has empty text"

    def test_parent_chunk_index_monotone(self, synthetic_pdf):
        from app.ingestion.pdf_extractor import chunk_pages, extract_pages
        pages = extract_pages(synthetic_pdf)
        chunks = chunk_pages(pages)
        parent_idxs = [c.chunk_index for c in chunks if c.is_parent]
        assert parent_idxs == sorted(parent_idxs), "Parent chunk indices must be monotone"


# ── Test 5 — Full pipeline + DB ───────────────────────────────────────────────

class TestFullPipeline:
    def test_ingest_returns_completed_status(self, synthetic_pdf, isolated_db):
        from app.ingestion.pipeline import ingest_pdf
        from app.models.schemas import DocumentSource, DocumentVersionInfo, IngestionStatus
        doc = ingest_pdf(
            pdf_path=synthetic_pdf,
            source_type=DocumentSource.OFFICIAL,
            title="Synthetic B.Tech Regulations 2023-24",
            description="Test document generated by smoke test",
            version_info=DocumentVersionInfo(
                effective_date="2023-08-01",
                academic_year="2023-24",
                program_applicability=["B.Tech"],
                is_current=True,
                notes="Synthetic — not a real document",
            ),
        )
        assert doc.ingestion_status == IngestionStatus.COMPLETED, (
            f"Expected COMPLETED, got {doc.ingestion_status}. "
            f"Error: {doc.error_message}"
        )

    def test_document_record_saved_to_db(self, synthetic_pdf, isolated_db):
        from app.ingestion.pipeline import get_all_documents
        from app.models.schemas import DocumentSource
        docs = get_all_documents(source_type=DocumentSource.OFFICIAL)
        assert any(d["filename"] == synthetic_pdf.name for d in docs), (
            "Document not found in DB after ingestion"
        )

    def test_passages_saved_to_db(self, synthetic_pdf, isolated_db):
        from app.ingestion.pipeline import get_all_documents, get_passages_for_document
        from app.models.schemas import DocumentSource
        docs = get_all_documents(source_type=DocumentSource.OFFICIAL)
        target = next((d for d in docs if d["filename"] == synthetic_pdf.name), None)
        assert target is not None
        passages = get_passages_for_document(target["document_id"])
        assert len(passages) >= 2, (
            f"Expected ≥2 passages (parent+child), got {len(passages)}"
        )

    def test_version_metadata_in_db(self, synthetic_pdf, isolated_db):
        from app.ingestion.pipeline import get_all_documents
        from app.models.schemas import DocumentSource
        docs = get_all_documents(source_type=DocumentSource.OFFICIAL)
        target = next((d for d in docs if d["filename"] == synthetic_pdf.name), None)
        assert target["academic_year"] == "2023-24"
        assert target["effective_date"] == "2023-08-01"
        assert target["is_current"] == 1  # stored as int in SQLite

    def test_document_has_page_count(self, synthetic_pdf, isolated_db):
        from app.ingestion.pipeline import get_all_documents
        from app.models.schemas import DocumentSource
        docs = get_all_documents(source_type=DocumentSource.OFFICIAL)
        target = next((d for d in docs if d["filename"] == synthetic_pdf.name), None)
        assert target["page_count"] == len(SYNTHETIC_TEXT_PAGES), (
            f"Expected {len(SYNTHETIC_TEXT_PAGES)} pages in DB, got {target['page_count']}"
        )


# ── Test 6 — Deduplication ────────────────────────────────────────────────────

class TestDeduplication:
    def test_re_ingest_same_file_is_skipped(self, synthetic_pdf, isolated_db):
        from app.ingestion.pipeline import ingest_pdf
        from app.models.schemas import DocumentSource, IngestionStatus
        doc = ingest_pdf(
            pdf_path=synthetic_pdf,
            source_type=DocumentSource.OFFICIAL,
            title="Synthetic B.Tech Regulations 2023-24 (duplicate)",
        )
        assert doc.ingestion_status == IngestionStatus.SKIPPED, (
            f"Expected SKIPPED on re-ingest, got {doc.ingestion_status}"
        )

    def test_force_re_ingest_replaces(self, synthetic_pdf, isolated_db):
        from app.ingestion.pipeline import ingest_pdf
        from app.models.schemas import DocumentSource, IngestionStatus
        doc = ingest_pdf(
            pdf_path=synthetic_pdf,
            source_type=DocumentSource.OFFICIAL,
            title="Forced re-ingest",
            force=True,
        )
        assert doc.ingestion_status == IngestionStatus.COMPLETED, (
            f"Expected COMPLETED on forced re-ingest, got {doc.ingestion_status}"
        )


# ── Test 7 — Passage page numbers ─────────────────────────────────────────────

class TestPassagePageNumbers:
    def test_all_passages_have_valid_page_number(self, synthetic_pdf, isolated_db):
        from app.ingestion.pipeline import get_all_documents, get_passages_for_document
        from app.models.schemas import DocumentSource
        docs = get_all_documents(source_type=DocumentSource.OFFICIAL)
        target = next((d for d in docs if d["filename"] == synthetic_pdf.name), None)
        assert target is not None
        passages = get_passages_for_document(target["document_id"])
        for p in passages:
            assert p["page_number"] is not None, f"passage {p['passage_id']} missing page_number"
            assert p["page_number"] >= 1, f"page_number < 1: {p['page_number']}"


# ── Test 8 — Parent–child linkage ─────────────────────────────────────────────

class TestParentChildLinkage:
    def test_children_point_to_parents_in_same_doc(self, synthetic_pdf, isolated_db):
        from app.ingestion.pipeline import get_all_documents, get_passages_for_document
        from app.models.schemas import DocumentSource
        docs = get_all_documents(source_type=DocumentSource.OFFICIAL)
        target = next((d for d in docs if d["filename"] == synthetic_pdf.name), None)
        passages = get_passages_for_document(target["document_id"])
        parent_ids = {p["passage_id"] for p in passages if p["is_parent"]}
        children = [p for p in passages if not p["is_parent"]]
        for ch in children:
            if ch["parent_passage_id"] is not None:
                assert ch["parent_passage_id"] in parent_ids, (
                    f"Child {ch['passage_id']} points to unknown parent "
                    f"{ch['parent_passage_id']}"
                )

    def test_at_least_one_parent_exists(self, synthetic_pdf, isolated_db):
        from app.ingestion.pipeline import get_all_documents, get_passages_for_document
        from app.models.schemas import DocumentSource
        docs = get_all_documents(source_type=DocumentSource.OFFICIAL)
        target = next((d for d in docs if d["filename"] == synthetic_pdf.name), None)
        passages = get_passages_for_document(target["document_id"])
        parents = [p for p in passages if p["is_parent"]]
        assert len(parents) >= 1, "No parent passages found"


# ── Test 9 — Key-text retrievability ──────────────────────────────────────────

class TestKeyTextRetrievability:
    def test_attendance_rule_in_passages(self, synthetic_pdf, isolated_db):
        """The 75% attendance rule must appear in at least one stored passage."""
        from app.ingestion.pipeline import get_all_documents, get_passages_for_document
        from app.models.schemas import DocumentSource
        docs = get_all_documents(source_type=DocumentSource.OFFICIAL)
        target = next((d for d in docs if d["filename"] == synthetic_pdf.name), None)
        passages = get_passages_for_document(target["document_id"])
        all_text = " ".join(p["text"] for p in passages).lower()
        assert "75" in all_text or "attendance" in all_text, (
            "Key attendance-rule text not found in stored passages"
        )

    def test_grading_table_text_in_passages(self, synthetic_pdf, isolated_db):
        """Grading-table content must survive extraction and chunking."""
        from app.ingestion.pipeline import get_all_documents, get_passages_for_document
        from app.models.schemas import DocumentSource
        docs = get_all_documents(source_type=DocumentSource.OFFICIAL)
        target = next((d for d in docs if d["filename"] == synthetic_pdf.name), None)
        passages = get_passages_for_document(target["document_id"])
        all_text = " ".join(p["text"] for p in passages).lower()
        # At least one of the grade markers should appear
        found = any(g in all_text for g in ["grade", "sgpa", "cgpa", "10", "marks"])
        assert found, "Grading content not found in stored passages"


# ── Test 10 — Source registry validation ──────────────────────────────────────

class TestSourceRegistryStructure:
    def test_source_entry_dataclass_fields(self):
        from app.ingestion.source_registry import SourceEntry
        e = SourceEntry(
            filename="test.pdf",
            title="Test",
            description="desc",
            verified=False,
        )
        assert e.filename == "test.pdf"
        assert e.verified is False
        assert e.is_current is None  # unknown by default

    def test_verified_sources_have_required_fields(self):
        """Every verified source entry must have filename, title, source_url, and notes."""
        from app.ingestion.source_registry import get_verified_sources
        verified = get_verified_sources()
        assert isinstance(verified, list)
        for entry in verified:
            assert entry.filename, f"Verified entry missing filename: {entry}"
            assert entry.title, f"Verified entry missing title: {entry.filename}"
            assert entry.source_url, (
                f"Verified entry '{entry.filename}' must have source_url for provenance"
            )
            assert entry.notes, (
                f"Verified entry '{entry.filename}' must have notes"
            )
            assert entry.verified is True

    def test_get_all_sources_returns_list(self):
        from app.ingestion.source_registry import get_all_sources
        all_s = get_all_sources()
        assert isinstance(all_s, list)
        assert len(all_s) >= 1

    def test_placeholder_notes_warn_user(self):
        from app.ingestion.source_registry import get_all_sources
        for entry in get_all_sources():
            if not entry.verified:
                assert entry.notes, (
                    f"Unverified entry '{entry.filename}' must have notes explaining status"
                )
