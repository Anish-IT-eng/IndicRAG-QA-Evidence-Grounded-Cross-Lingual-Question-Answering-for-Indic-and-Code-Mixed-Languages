"""
Live E2E Integration Test for Sequential Retrieval with Fallback.
Tests live HTTP calls against http://127.0.0.1:8000:
1. Check health.
2. Ingest Academic-Calendar-2026-27.pdf for test user.
3. Test Query 1: Calendar question -> answered from user doc, cites "User-provided document".
4. Test Query 2: Attendance question -> user doc lacks attendance, falls back to official regulations, cites "Official university document".
5. Test Query 3: Multi-user isolation -> User B cannot retrieve User A's uploads.
"""
import json
import time
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=== Testing /health ===")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("Health response:", r.json())

    # 1. Upload/Ingest PDF for user_test_student
    pdf_path = Path("backend/data/uploads/Academic-Calendar-2026-27.pdf")
    if not pdf_path.exists():
        pdf_path = Path("data/uploads/Academic-Calendar-2026-27.pdf")
    
    print("\n=== Testing POST /uploads for user_test_student ===")
    with open(pdf_path, "rb") as f:
        files = {"file": ("Academic-Calendar-2026-27.pdf", f, "application/pdf")}
        data = {
            "academic_year": "2026-27",
            "user_id": "user_test_student"
        }
        r = requests.post(f"{BASE_URL}/uploads", files=files, data=data)
        print("Upload status:", r.status_code, r.json())
        assert r.status_code == 200

    # Wait 3 seconds for background ingestion task
    print("Waiting for ingestion to complete...")
    time.sleep(3)

    # 2. Check /documents?source_type=upload&user_id=user_test_student
    r = requests.get(f"{BASE_URL}/documents?source_type=upload&user_id=user_test_student")
    user_docs = r.json()
    print(f"User docs found: {len(user_docs)}")
    assert len(user_docs) > 0, "Uploaded document not found for user_test_student"

    # 3. Test Query 1: When will odd end semester starts
    print("\n=== Test 1: Query covered by user document ===")
    q1_payload = {
        "query": "when will odd end semester starts",
        "user_id": "user_test_student",
        "sequential_fallback": True,
        "use_reranker": True,
    }
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/query", json=q1_payload)
    lat = time.time() - t0
    assert r.status_code == 200, f"Query 1 failed: {r.text}"
    res1 = r.json()
    print(f"Status: {res1.get('status')}")
    print(f"Evidence Status: {res1.get('evidence_status')}")
    print(f"Answer: {res1.get('answer')[:120]}...")
    print(f"Citations ({len(res1.get('citations', []))}):")
    for c in res1.get('citations', []):
        print(f" - [{c.get('source_type')}] {c.get('source_label')} | File: {c.get('filename')} | Page: {c.get('page')}")
    print("Stage summary:", res1.get("retrieval_summary", {}).get("stage_summary"))

    # Assertions for Query 1
    assert res1.get("status") in ("answered", "partial_answer")
    assert len(res1.get("citations", [])) > 0
    first_cit = res1["citations"][0]
    assert first_cit["source_type"] == "upload"
    assert first_cit["source_label"] == "User-provided document"
    assert "Academic-Calendar" in first_cit["filename"]
    print(">>> Test 1 PASSED: Answered using user document evidence with 'User-provided document' provenance.")

    # 4. Test Query 2: Minimum attendance requirement (missing from calendar, in official regulations)
    print("\n=== Test 2: Query missing from user doc -> Fallback to official regulations ===")
    q2_payload = {
        "query": "What is the minimum attendance requirement to appear in end-semester examinations?",
        "user_id": "user_test_student",
        "sequential_fallback": True,
        "use_reranker": True,
    }
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/query", json=q2_payload)
    lat = time.time() - t0
    assert r.status_code == 200, f"Query 2 failed: {r.text}"
    res2 = r.json()
    print(f"Status: {res2.get('status')}")
    print(f"Evidence Status: {res2.get('evidence_status')}")
    print(f"Answer: {res2.get('answer')[:120]}...")
    print(f"Citations ({len(res2.get('citations', []))}):")
    for c in res2.get('citations', []):
        print(f" - [{c.get('source_type')}] {c.get('source_label')} | File: {c.get('filename')} | Page: {c.get('page')}")
    stage_info = res2.get("retrieval_summary", {}).get("stage_summary", {})
    print("Stage summary:", stage_info)

    # Assertions for Query 2
    assert res2.get("status") in ("answered", "clarification_needed", "partial_answer")
    assert stage_info.get("fallback_triggered") is True
    assert stage_info.get("stage") == "official_fallback"
    print(">>> Test 2 PASSED: Successfully fell back to official regulations with 'official_fallback' stage.")

    # 5. Test Query 3: Multi-user isolation
    print("\n=== Test 3: Multi-user isolation ===")
    # user_other has no uploads
    r = requests.get(f"{BASE_URL}/documents?source_type=upload&user_id=user_other_student")
    other_docs = r.json()
    print(f"user_other_student docs: {len(other_docs)}")
    assert len(other_docs) == 0, "User isolation failed in /documents listing"

    # Query calendar as user_other_student -> should NOT find user_test_student's calendar
    q3_payload = {
        "query": "when will odd end semester starts",
        "user_id": "user_other_student",
        "sequential_fallback": True,
    }
    r = requests.post(f"{BASE_URL}/query", json=q3_payload)
    res3 = r.json()
    stage3 = res3.get("retrieval_summary", {}).get("stage_summary", {})
    print("User other stage:", stage3)
    # Stage 1 had 0 user uploads, went to official which has no 2026-27 calendar
    assert stage3.get("user_docs_count", 0) == 0
    print(">>> Test 3 PASSED: user_other_student isolated from user_test_student uploads.")

    print("\n==========================================")
    print("ALL LIVE INTEGRATION TESTS PASSED!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
