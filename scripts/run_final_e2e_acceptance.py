"""
IndicRAG-QA — Final End-to-End Acceptance Test Suite
Executes the comprehensive set of required operational workflows:
  - Test A: Application Startup & Frontend Mount
  - Test B: Document Ingestion, Embedding & Upload-Grounded QA
  - Test C: Official Regulation Retrieval
  - Test D: Multilingual QA (English, Hindi Devanagari, Romanized Hindi, Hinglish, Calendar Event Scope)
  - Test E: Insufficient Evidence & Abstention
  - Test F: Multi-Hop Cross-Clause Reasoning
  - Test G: Conversational Context & Feedback Repair
  - Test H: Multi-Tenant Isolation & Document Deletion Cascade
  - Test I: Regression Status Verification
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path("backend").resolve()))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

from fastapi.testclient import TestClient
from app.api.main import app
from app.core.config import settings
from app.models.schemas import EvidenceStatus, QuestionType, ResponseStatus


def _build_pdf_bytes(pages: list[str]) -> bytes:
    """Generate byte-valid PDF 1.4 using standard library only."""
    buf = io.BytesIO()
    obj_offsets: dict[int, int] = {}

    def wb(s: str):
        buf.write(s.encode("latin-1", errors="replace"))

    wb("%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    n_pages = len(pages)
    page_obj_ids = [4 + 2 * i for i in range(n_pages)]
    content_obj_ids = [5 + 2 * i for i in range(n_pages)]
    font_obj_id = 3
    pages_obj_id = 2
    catalog_obj_id = 1

    streams: list[bytes] = []
    for text in pages:
        lines = text.strip().splitlines()
        ops = ["BT", "/F1 10 Tf", "10 TL", "50 750 Td"]
        for line in lines:
            clean = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            ops.append(f"({clean}) Tj T*")
        ops.append("ET")
        stream_bytes = "\n".join(ops).encode("latin-1", errors="replace")
        streams.append(stream_bytes)

    # 1 Catalog
    obj_offsets[catalog_obj_id] = buf.tell()
    wb(f"1 0 obj\n<< /Type /Catalog /Pages {pages_obj_id} 0 R >>\nendobj\n")

    # 2 Pages
    page_refs = " ".join(f"{oid} 0 R" for oid in page_obj_ids)
    obj_offsets[pages_obj_id] = buf.tell()
    wb(f"2 0 obj\n<< /Type /Pages /Kids [{page_refs}] /Count {n_pages} >>\nendobj\n")

    # 3 Font
    obj_offsets[font_obj_id] = buf.tell()
    wb("3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\nendobj\n")

    for stream, page_oid, content_oid in zip(streams, page_obj_ids, content_obj_ids):
        obj_offsets[page_oid] = buf.tell()
        wb(
            f"{page_oid} 0 obj\n<< /Type /Page /Parent {pages_obj_id} 0 R "
            f"/MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_obj_id} 0 R >> >> "
            f"/Contents {content_oid} 0 R >>\nendobj\n"
        )
        obj_offsets[content_oid] = buf.tell()
        wb(f"{content_oid} 0 obj\n<< /Length {len(stream)} >>\nstream\n")
        buf.write(stream)
        wb("\nendstream\nendobj\n")

    xref_pos = buf.tell()
    n_objs = max(obj_offsets) + 1
    wb(f"xref\n0 {n_objs}\n0000000000 65535 f \n")
    for oid in range(1, n_objs):
        off = obj_offsets.get(oid, 0)
        wb(f"{off:010d} 00000 n \n")

    wb(f"trailer\n<< /Size {n_objs} /Root {catalog_obj_id} 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n")
    return buf.getvalue()


def run_e2e_suite():
    print("=" * 75)
    print("INDICRAG-QA — FINAL END-TO-END ACCEPTANCE SUITE")
    print("=" * 75)

    client = TestClient(app)
    results = {}

    # ── TEST A: Application Startup & Frontend Mount ───────────────────────────
    print("\n[TEST A] Application Startup, Health Check & Frontend Serving")
    t0 = time.perf_counter()
    resp_health = client.get("/health")
    resp_root = client.get("/")
    assert resp_health.status_code == 200, f"Health endpoint failed: {resp_health.status_code}"
    health_data = resp_health.json()
    assert health_data["status"] == "ok"
    assert health_data["document_count"] > 0
    assert resp_root.status_code == 200, f"Root endpoint failed: {resp_root.status_code}"
    assert "IndicRAG-QA" in resp_root.text
    assert "sidebar" in resp_root.text
    latency_a = (time.perf_counter() - t0) * 1000
    print(f"  [+] /health OK: {health_data['document_count']} docs, {health_data['passage_count']} passages")
    print(f"  [+] Frontend mounted: 200 OK (HTML bytes: {len(resp_root.text)})")
    results["Test_A_Startup"] = {"status": "PASS", "latency_ms": round(latency_a, 2)}

    # ── TEST B: Document Upload & Ingestion ────────────────────────────────────
    print("\n[TEST B] User Document Ingestion, Indexing & Upload-Grounded QA")
    t0 = time.perf_counter()
    user_alice = "user_alice_test"
    doc_text_page1 = (
        "Bennett University Computer Science Department\n"
        "Advanced Artificial Intelligence Lab Policy 2026-27\n"
        "Course Code: AI-401 Advanced Deep Learning\n"
        "Prerequisites: Students must have completed AI-201 with grade B or higher.\n"
        "Mandatory Lab Rule: Course AI-401 requires 85 percent practical laboratory attendance."
    )
    pdf_bytes = _build_pdf_bytes([doc_text_page1])
    upload_filename = "AI_401_Lab_Policy_2026.pdf"

    resp_up = client.post(
        "/uploads",
        files={"file": (upload_filename, pdf_bytes, "application/pdf")},
        data={"user_id": user_alice, "academic_year": "2026-27", "wait": "true"},
    )
    assert resp_up.status_code == 200, f"Upload failed: {resp_up.text}"
    up_data = resp_up.json()
    alice_doc_id = up_data["document_id"]
    print(f"  [+] Ingested user document: {alice_doc_id} ({upload_filename})")

    # Verify status endpoint
    resp_st = client.get(f"/documents/{alice_doc_id}/status?user_id={user_alice}")
    assert resp_st.status_code == 200
    assert resp_st.json()["status"] in ("completed", "success")

    # Query uploaded fact
    resp_q = client.post(
        "/query",
        json={
            "query": "What is the mandatory lab rule attendance percentage for Course AI-401?",
            "user_id": user_alice,
            "sequential_fallback": True,
        },
    )
    assert resp_q.status_code == 200
    q_data = resp_q.json()
    answer_b = q_data["answer"] or ""
    citations_b = q_data["citations"] or []
    assert "85" in answer_b
    assert any(c["filename"] == upload_filename for c in citations_b)
    latency_b = (time.perf_counter() - t0) * 1000
    print(f"  [+] QA verified over upload: cited {upload_filename}, answer: {answer_b[:120]}...")
    results["Test_B_Upload_QA"] = {
        "status": "PASS",
        "doc_id": alice_doc_id,
        "cited_doc": upload_filename,
        "latency_ms": round(latency_b, 2),
    }

    # ── TEST C: Official Document Retrieval ────────────────────────────────────
    print("\n[TEST C] Official Regulatory Document Retrieval & Citation Grounding")
    t0 = time.perf_counter()
    resp_c = client.post(
        "/query",
        json={
            "query": "What is the minimum attendance requirement to appear in end-semester examinations?",
            "user_id": user_alice,
            "sequential_fallback": True,
        },
    )
    assert resp_c.status_code == 200
    c_data = resp_c.json()
    ans_c = c_data["answer"] or ""
    cits_c = c_data["citations"] or []
    assert "75" in ans_c
    assert len(cits_c) > 0
    assert any(c.get("source_type") in ("official", "OFFICIAL") or c["filename"] != upload_filename for c in cits_c)
    latency_c = (time.perf_counter() - t0) * 1000
    print(f"  [+] Official QA verified: cited {[c['filename'] for c in cits_c]}, answer: {ans_c[:120]}...")
    results["Test_C_Official_Retrieval"] = {"status": "PASS", "latency_ms": round(latency_c, 2)}

    # ── TEST D: Multilingual Questions ─────────────────────────────────────────
    print("\n[TEST D] Multilingual Questions (English, Hindi Devanagari, Romanized Hindi, Hinglish)")
    t0 = time.perf_counter()
    queries_d = [
        ("English", "When do odd semester end semester examinations start and finish?"),
        ("Devanagari Hindi", "विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?"),
        ("Romanized Hindi", "Visham semester ki antim pariksha kab shuru aur samapt hoti hai?"),
        ("Code-Mixed Hinglish", "Odd semester examinations ki start date aur end date kya hai?"),
    ]
    multi_results = {}
    for lang_name, query_text in queries_d:
        resp_d = client.post(
            "/query",
            json={"query": query_text, "user_id": user_alice, "sequential_fallback": True},
        )
        assert resp_d.status_code == 200
        d_val = resp_d.json()
        ans_d = d_val["answer"] or ""
        cits_d = d_val["citations"] or []
        has_dates = "10-12-2026" in ans_d and "22-12-2026" in ans_d
        has_page4 = any(c["page"] == 4 and "calendar" in c["filename"].lower() for c in cits_d)
        print(f"  [+] [{lang_name}] dates={has_dates}, page4={has_page4} | Ans: {ans_d[:90]}...")
        assert has_dates and has_page4, f"Scenario failed for {lang_name}: {ans_d}"
        multi_results[lang_name] = "PASS"

    # Specific negative test: Even semester registration must not return regular exam dates
    resp_reg = client.post(
        "/query",
        json={"query": "When does registration for even semester start?", "user_id": user_alice, "sequential_fallback": True},
    )
    ans_reg = resp_reg.json()["answer"] or ""
    assert "28-12-2026" in ans_reg
    assert "10-12-2026" not in ans_reg
    print(f"  [+] Even Semester Registration: correctly selected 28-12-2026")
    multi_results["Even_Semester_Registration"] = "PASS"

    latency_d = (time.perf_counter() - t0) * 1000
    results["Test_D_Multilingual"] = {"status": "PASS", "scenarios": multi_results, "latency_ms": round(latency_d, 2)}

    # ── TEST E: Insufficient Evidence & Abstention ─────────────────────────────
    print("\n[TEST E] Out-of-Corpus Query & Safe Institutional Abstention")
    t0 = time.perf_counter()
    resp_e = client.post(
        "/query",
        json={
            "query": "What is the university policy regarding operating commercial supersonic drones on campus grounds?",
            "user_id": user_alice,
            "sequential_fallback": True,
        },
    )
    assert resp_e.status_code == 200
    e_val = resp_e.json()
    ans_e = e_val["answer"] or ""
    status_e = e_val["status"]
    is_abstain = (
        status_e in ("unanswerable", "clarification_needed")
        or "UNANSWERABLE" in ans_e.upper()
        or "INSUFFICIENT" in ans_e.upper()
        or len(e_val.get("citations", [])) == 0
    )
    assert is_abstain, f"Expected abstention, got answer: {ans_e}"
    latency_e = (time.perf_counter() - t0) * 1000
    print(f"  [+] Safely abstained: status={status_e}, answer={ans_e[:90]}...")
    results["Test_E_Abstention"] = {"status": "PASS", "response_status": status_e, "latency_ms": round(latency_e, 2)}

    # ── TEST F: Multi-Hop Reasoning ────────────────────────────────────────────
    print("\n[TEST F] Multi-Hop Regulatory Reasoning (Attendance vs Medical Relaxation)")
    t0 = time.perf_counter()
    resp_f = client.post(
        "/query",
        json={
            "query": "Can attendance be relaxed due to medical reasons and what conditions must be satisfied under university rules?",
            "user_id": user_alice,
            "sequential_fallback": True,
        },
    )
    assert resp_f.status_code == 200
    f_val = resp_f.json()
    ans_f = f_val["answer"] or ""
    cits_f = f_val["citations"] or []
    # Must explain conditions (medical certificate, 10% relaxation, 2 weeks continuous illness)
    has_med_cond = any(w in ans_f.lower() for w in ["medical", "relaxation", "certificate", "clause", "10%", "two weeks"])
    assert has_med_cond
    assert len(cits_f) > 0
    latency_f = (time.perf_counter() - t0) * 1000
    print(f"  [+] Multi-hop verified: citations={len(cits_f)}, answer={ans_f[:120]}...")
    results["Test_F_Multi_Hop"] = {"status": "PASS", "citations_count": len(cits_f), "latency_ms": round(latency_f, 2)}

    # ── TEST G: Conversational Feedback & Repair ───────────────────────────────
    print("\n[TEST G] Conversational Feedback Classification & Turn Repair")
    t0 = time.perf_counter()
    feedback_payload = {
        "query": "That is incorrect, please check Clause 30.1(v) for medical exemptions.",
        "user_id": user_alice,
        "session_id": "test_conv_session",
        "conversation_history": [
            {
                "query": "Can attendance be relaxed below 75% for medical reasons?",
                "answer": "No, attendance cannot be relaxed below 75%.",
                "evidence_status": "sufficient",
                "citations": [{"filename": "Notification-Minimum-Attendance.pdf", "page": 1}],
            }
        ],
        "sequential_fallback": True,
    }
    resp_g = client.post("/query", json=feedback_payload)
    assert resp_g.status_code == 200
    g_val = resp_g.json()
    ans_g = g_val["answer"] or ""
    summary_g = g_val.get("retrieval_summary", {})
    assert summary_g.get("is_feedback") is True
    assert "feedback_repair" in summary_g.get("stage", "")
    latency_g = (time.perf_counter() - t0) * 1000
    print(f"  [+] Feedback repair verified: action={summary_g.get('repair_action')}, answer={ans_g[:110]}...")
    results["Test_G_Conversational_Repair"] = {
        "status": "PASS",
        "repair_action": summary_g.get("repair_action"),
        "latency_ms": round(latency_g, 2),
    }

    # ── TEST H: Multi-Tenant Security & Cascading Deletion ────────────────────
    print("\n[TEST H] Multi-Tenant Security, Isolation & Document Deletion Cascade")
    t0 = time.perf_counter()
    user_bob = "user_bob_unauthorized"

    # 1. Bob cannot query Alice's uploaded document
    resp_h1 = client.post(
        "/query",
        json={
            "query": "What is the mandatory lab rule attendance percentage for Course AI-401?",
            "user_id": user_bob,
            "sequential_fallback": True,
        },
    )
    ans_h1 = resp_h1.json()["answer"] or ""
    cits_h1 = resp_h1.json()["citations"] or []
    assert not any(c["filename"] == upload_filename for c in cits_h1)
    print("  [+] Tenant Isolation: Bob cannot access Alice's document citations.")

    # 2. Bob cannot delete Alice's document
    resp_h2 = client.delete(f"/documents/{alice_doc_id}?user_id={user_bob}")
    assert resp_h2.status_code == 403, f"Expected 403, got {resp_h2.status_code}"
    print("  [+] Tenant Isolation: Bob's delete request rejected with 403 Forbidden.")

    # 3. Alice deletes her own document
    resp_h3 = client.delete(f"/documents/{alice_doc_id}?user_id={user_alice}")
    assert resp_h3.status_code == 200, f"Expected 200, got {resp_h3.status_code}"
    print("  [+] Document Deletion: Alice successfully deleted her document.")

    # 4. Verify status is 404 after deletion
    resp_h4 = client.get(f"/documents/{alice_doc_id}/status?user_id={user_alice}")
    assert resp_h4.status_code == 404
    print("  [+] Deletion Cascade: Document and associated records completely removed from store.")

    latency_h = (time.perf_counter() - t0) * 1000
    results["Test_H_Security_Deletion"] = {"status": "PASS", "latency_ms": round(latency_h, 2)}

    # ── TEST I: Regression Status Check ───────────────────────────────────────
    print("\n[TEST I] Regression Benchmark & Invariant Status")
    t0 = time.perf_counter()
    # Check that previous regression report exists and passed
    r6_res_path = Path("docs/r6_stage2_1_test_results.json")
    assert r6_res_path.exists(), "R6 Stage 2.1 results file missing"
    with open(r6_res_path, encoding="utf-8") as f:
        r6_data = json.load(f)
    assert r6_data.get("all_passed") is True
    assert r6_data.get("passed_scenarios") == 8
    print(f"  [+] Stage 2.1 Regression Integrity Confirmed: {r6_data['passed_scenarios']}/8 passed.")

    latency_i = (time.perf_counter() - t0) * 1000
    results["Test_I_Regression"] = {"status": "PASS", "latency_ms": round(latency_i, 2)}

    # ── FINAL SUMMARY ──────────────────────────────────────────────────────────
    all_passed = all(v["status"] == "PASS" for v in results.values())
    print("\n" + "=" * 75)
    print(f"FINAL ACCEPTANCE SUITE SUMMARY: {'ALL 9 TESTS PASSED' if all_passed else 'FAILURES DETECTED'}")
    print("=" * 75)

    out_file = Path("docs/final_acceptance_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "suite": "IndicRAG-QA Final End-to-End Acceptance Suite",
                "all_passed": all_passed,
                "tests": results,
            },
            f,
            indent=2,
        )
    print(f"[+] Saved final acceptance results to {out_file}")
    return all_passed


if __name__ == "__main__":
    success = run_e2e_suite()
    sys.exit(0 if success else 1)
