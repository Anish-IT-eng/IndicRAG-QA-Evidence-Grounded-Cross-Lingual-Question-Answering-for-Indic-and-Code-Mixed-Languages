import asyncio
import os
import sys
import uuid
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import get_db, init_db
from app.ingestion.pdf_extractor import extract_pages, chunk_pages
from app.ingestion.pipeline import ingest_pdf
from app.models.schemas import DocumentSource, DocumentVersionInfo, ResponseStatus, EvidenceStatus
from app.query.processor import process_query
from app.retrieval.engine import retrieve, get_upload_index, get_official_index
from app.retrieval.evidence_controller import get_evidence_controller
from app.generation.generator import generate_answer


def run_tests():
    print("=" * 80)
    print("R1 TEST: RELIABLE PDF EXTRACTION & TABLE RECONSTRUCTION")
    print("=" * 80)

    pdf_path = Path("backend/data/uploads/Academic-Calendar-2026-27.pdf")
    if not pdf_path.exists():
        pdf_path = Path("backend/data/official/Academic-Calendar-2026-27.pdf")
    assert pdf_path.exists(), f"Cannot find PDF at {pdf_path}"

    # 1. Extraction Test
    print(f"\n1. Testing extract_pages on: {pdf_path}")
    pages = extract_pages(pdf_path)
    print(f"Total pages extracted: {len(pages)}")
    assert len(pages) == 9, f"Expected 9 pages, got {len(pages)}"

    tables_found = sum(len(p.tables) for p in pages)
    print(f"Total tables detected across pages: {tables_found}")
    assert tables_found >= 9, f"Expected >= 9 tables, got {tables_found}"

    p4 = pages[3]  # Page 4 (1-based page 4 is index 3)
    assert len(p4.tables) >= 1, "Page 4 must have a table"
    p4_tbl = p4.tables[0]
    print(f"Page 4 Table ID: {p4_tbl.get('table_id')}, Headers: {p4_tbl.get('headers')}, Rows: {len(p4_tbl.get('rows', []))}, Confidence: {p4_tbl.get('confidence')}")
    assert "Date" in p4_tbl.get("headers", []), "Table headers must include 'Date'"
    assert "Event" in p4_tbl.get("headers", []), "Table headers must include 'Event'"

    has_p4_exam = any("End Semester Examination" in r.get("Event", "") for r in p4_tbl.get("rows", []))
    assert has_p4_exam, "Page 4 table must contain 'End Semester Examination' event"
    print(">>> Page 4 Table Structure & Exam Event Verified Successfully!")

    # 2. Chunking Protection Test
    print("\n2. Testing chunk_pages protection for table relationships...")
    chunks = chunk_pages(pages)
    table_chunks = [c for c in chunks if c.table_ref is not None]
    print(f"Total chunks: {len(chunks)} (Table chunks: {len(table_chunks)})")
    assert len(table_chunks) >= 20, f"Expected table chunks, got {len(table_chunks)}"

    p4_exam_chunks = [c for c in chunks if c.page_number == 4 and "10-12-2026" in c.text]
    assert len(p4_exam_chunks) >= 1, "Must have chunk with 10-12-2026 on Page 4"
    exam_chunk = p4_exam_chunks[0]
    print(f"P4 Exam Chunk Index: {exam_chunk.chunk_index}, Table Ref: {exam_chunk.table_ref}")
    print(f"P4 Exam Chunk Text Sample:\n{exam_chunk.text[:250]}...")
    assert "End Semester Examination" in exam_chunk.text
    assert "10-12-2026" in exam_chunk.text
    print(">>> Chunking successfully preserved table rows and headers!")

    # 3. Ingestion Pipeline Test
    print("\n3. Testing Ingestion Pipeline into Upload Collection...")
    user_id = f"test-user-{uuid.uuid4().hex[:8]}"
    doc_rec = ingest_pdf(
        pdf_path=pdf_path,
        source_type=DocumentSource.UPLOAD,
        title="Academic Calendar 2026-27",
        description="University academic calendar for 2026-27 session",
        version_info=DocumentVersionInfo(academic_year="2026-27", is_current=True),
        force=True,
        user_id=user_id,
    )
    print(f"Ingested Document ID: {doc_rec.document_id}, Status: {doc_rec.ingestion_status}")

    # Check SQLite document_tables and table_cells
    with get_db() as conn:
        t_count = conn.execute("SELECT COUNT(*) FROM document_tables WHERE document_id = ?", (doc_rec.document_id,)).fetchone()[0]
        c_count = conn.execute("SELECT COUNT(*) FROM table_cells WHERE document_id = ?", (doc_rec.document_id,)).fetchone()[0]
        print(f"SQLite document_tables count for doc: {t_count}")
        print(f"SQLite table_cells count for doc: {c_count}")
        assert t_count >= 8, f"Expected at least 8 tables in DB, got {t_count}"
        assert c_count >= 100, f"Expected >= 100 cells, got {c_count}"
        
        exam_cell = conn.execute(
            "SELECT * FROM table_cells WHERE document_id = ? AND page_number = 4 AND cell_value LIKE '%End Semester Examination%'",
            (doc_rec.document_id,)
        ).fetchone()
        if exam_cell:
            print(f"DB Table Cell Verified: Row {exam_cell['row_index']}, Col {exam_cell['col_index']} ({exam_cell['header']}): {exam_cell['cell_value']}")

    # 4. Regression Query Retrieval Test
    print("\n4. Testing Retrieval for Regression Query:")
    q_text = "When will odd semester end semester examinations start?"
    print(f"Query: '{q_text}'")
    qa = process_query(q_text)
    ret_res = retrieve(qa, collections=[DocumentSource.UPLOAD], top_k=5, user_id=user_id)
    print(f"Retrieved {len(ret_res.retrieved_passages)} passages.")
    for idx, p in enumerate(ret_res.retrieved_passages[:3]):
        tref = p.table_ref or (p.metadata.get("table_ref", "") if hasattr(p, "metadata") and p.metadata else "")
        print(f"  Rank {idx+1} [p.{p.page_number}] (Score: {p.score:.3f}, Table: {tref}): {p.text[:120].replace(chr(10), ' ')}...")

    p4_matches = [p for p in ret_res.retrieved_passages[:3] if p.page_number == 4]
    assert len(p4_matches) >= 1, "Page 4 must be among the top 3 retrieved passages"
    assert any("10-12-2026" in p.text for p in p4_matches), "Top Page 4 passages must contain examination start date 10-12-2026"
    print(">>> Retrieval successfully placed Page 4 table at top ranks!")

    # 5. End-to-End Generation Test with Local Ollama
    print("\n5. Running End-to-End Generation with Local Ollama...")
    ec = get_evidence_controller()
    evidence_decision = ec.evaluate(ret_res, attempt=1)
    print(f"Evidence Decision Status: {evidence_decision.status}, CECI: {evidence_decision.ceci_score:.3f}")
    ans = asyncio.run(generate_answer(qa, evidence_decision))
    print("\n" + "=" * 40 + " GENERATED ANSWER " + "=" * 40)
    print(ans.answer)
    print("=" * 98)
    print(f"Status: {ans.status}")
    print(f"Evidence Status: {ans.evidence_status}")
    print(f"Citations: {len(ans.citations)}")
    for c in ans.citations:
        pid = getattr(c, 'passage_id', getattr(c, 'source_passage_id', 'unknown'))
        pg = getattr(c, 'page', getattr(c, 'page_number', 'unknown'))
        print(f"  * [Source: {pid}, page: {pg}] '{c.quote[:80]}...'")

    # Verify grounding
    assert ans.status.value in ["answered", "clarification_needed"] or "10" in ans.answer, f"Expected answered, got {ans.status}"
    assert "10" in ans.answer or "december" in ans.answer.lower() or "12-2026" in ans.answer, "Answer must reference the examination date"
    assert len(ans.citations) >= 1, "Must have valid citation"
    print("\n>>> REGRESSION TEST PASSED: Accurate, Grounded Answer Generated!")

    # 6. Negative / Unsupported Question Abstention Test
    print("\n6. Testing Unrelated / Unsupported Question Abstention Behavior...")
    unsupported_q = "What is the scholarship percentage for students with CGPA 9.8 in Harvard University?"
    print(f"Query: '{unsupported_q}'")
    qa_un = process_query(unsupported_q)
    ret_un = retrieve(qa_un, collections=[DocumentSource.UPLOAD], top_k=5, user_id=user_id)
    ev_un = ec.evaluate(ret_un, attempt=1)
    ans_un = asyncio.run(generate_answer(qa_un, ev_un))
    print(f"Unsupported Query Status: {ans_un.status}")
    print(f"Answer: {ans_un.answer[:120]}...")
    assert ans_un.status.value in ["unanswerable", "insufficient_evidence"] or "UNANSWERABLE" in ans_un.answer, f"Expected unanswerable, got {ans_un.status}"
    print(">>> ABSTENTION INTEGRITY PRESERVED: Unsupported question properly rejected!")

    print("\n" + "=" * 80)
    print("ALL R1 TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
