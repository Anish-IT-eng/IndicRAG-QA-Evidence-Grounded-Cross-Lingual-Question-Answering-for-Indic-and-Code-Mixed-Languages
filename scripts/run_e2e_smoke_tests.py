"""
Comprehensive 10-Scenario End-to-End Smoke Test Suite.
Verifies the complete IndicRAG-QA stack running live on Windows:
- Backend: http://127.0.0.1:8000
- Frontend: http://127.0.0.1:5500
"""
import sys
import json
import time
import httpx

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5500"

client = httpx.Client(timeout=180.0)

test_results = []

def record(test_num, name, status, details):
    test_results.append({
        "test_num": test_num,
        "name": name,
        "status": status,
        "details": details
    })
    print(f"\n[{'PASS' if status == 'PASS' else 'FAIL'}] Scenario {test_num}: {name}")
    for k, v in details.items():
        print(f"  {k}: {v}")

def run_all():
    print("=================================================================")
    print("INDICRAG-QA LOCAL RUNTIME VERIFICATION — 10 SMOKE TEST SCENARIOS")
    print("=================================================================")

    # 1. English Question
    t0 = time.time()
    q1 = "What happens if a student misses a makeup exam?"
    r1 = client.post(f"{BACKEND_URL}/query", json={"query": q1, "collection": ["official"]})
    d1 = r1.json()
    record(1, "English Question", "PASS" if r1.status_code == 200 else "FAIL", {
        "query": q1,
        "http_code": r1.status_code,
        "response_status": d1.get("status"),
        "evidence_status": d1.get("evidence_status"),
        "answer_preview": d1.get("answer", "")[:100] + "...",
        "latency_sec": round(time.time() - t0, 2)
    })

    # 2. Devanagari Hindi Question
    t0 = time.time()
    q2 = "सेमेस्टर शुरू होने के बाद छात्र कितने समय के भीतर पंजीकृत कोर्स में नया विषय जोड़ या हटा सकते हैं?"
    r2 = client.post(f"{BACKEND_URL}/query", json={"query": q2, "collection": ["official"]})
    d2 = r2.json()
    record(2, "Devanagari Hindi Question", "PASS" if r2.status_code == 200 else "FAIL", {
        "query": q2,
        "http_code": r2.status_code,
        "response_status": d2.get("status"),
        "evidence_status": d2.get("evidence_status"),
        "answer_preview": d2.get("answer", "")[:100] + "...",
        "latency_sec": round(time.time() - t0, 2)
    })

    # 3. Code-Mixed Hinglish Question
    t0 = time.time()
    q3 = "Semester khatam hone se kitne hafte pehle tak course withdraw karne ki permission milti hai?"
    r3 = client.post(f"{BACKEND_URL}/query", json={"query": q3, "collection": ["official"]})
    d3 = r3.json()
    record(3, "Code-Mixed Hinglish Question", "PASS" if r3.status_code == 200 else "FAIL", {
        "query": q3,
        "http_code": r3.status_code,
        "response_status": d3.get("status"),
        "evidence_status": d3.get("evidence_status"),
        "answer_preview": d3.get("answer", "")[:100] + "...",
        "latency_sec": round(time.time() - t0, 2)
    })

    # 4. Romanized Hindi Question
    t0 = time.time()
    q4 = "Supplementary examination mein student ko maximum kaun sa grade mil sakta hai?"
    r4 = client.post(f"{BACKEND_URL}/query", json={"query": q4, "collection": ["official"]})
    d4 = r4.json()
    record(4, "Romanized Hindi Question", "PASS" if r4.status_code == 200 else "FAIL", {
        "query": q4,
        "http_code": r4.status_code,
        "response_status": d4.get("status"),
        "evidence_status": d4.get("evidence_status"),
        "answer_preview": d4.get("answer", "")[:100] + "...",
        "latency_sec": round(time.time() - t0, 2)
    })

    # 5. Unanswerable Question
    t0 = time.time()
    q5 = "What is the prescribed fee for submitting a PhD dissertation thesis according to the SCSET UG academic regulations?"
    r5 = client.post(f"{BACKEND_URL}/query", json={"query": q5, "collection": ["official"]})
    d5 = r5.json()
    is_safe = d5.get("status") == "unanswerable" and len(d5.get("citations", [])) == 0
    record(5, "Unanswerable Question", "PASS" if is_safe else "FAIL", {
        "query": q5,
        "http_code": r5.status_code,
        "response_status": d5.get("status"),
        "evidence_status": d5.get("evidence_status"),
        "citations_count": len(d5.get("citations", [])),
        "safe_abstention_enforced": is_safe,
        "answer": d5.get("answer"),
        "latency_sec": round(time.time() - t0, 2)
    })

    # 6. Regulatory Conflict Question
    t0 = time.time()
    q6 = "What is the minimum attendance requirement?"
    r6 = client.post(f"{BACKEND_URL}/query", json={"query": q6, "collection": ["official"]})
    d6 = r6.json()
    is_conflict = d6.get("evidence_status") == "conflicting" or d6.get("status") == "conflicting_versions"
    record(6, "Regulatory Conflict Question", "PASS" if is_conflict else "FAIL", {
        "query": q6,
        "http_code": r6.status_code,
        "response_status": d6.get("status"),
        "evidence_status": d6.get("evidence_status"),
        "conflict_detected": is_conflict,
        "answer_preview": d6.get("answer", "")[:100] + "...",
        "latency_sec": round(time.time() - t0, 2)
    })

    # 7. Clarification-Required Question
    t0 = time.time()
    q7 = "What is the grade requirement for students?"
    r7 = client.post(f"{BACKEND_URL}/query", json={"query": q7, "collection": ["official"]})
    d7 = r7.json()
    record(7, "Clarification / Ambiguous Handling", "PASS" if r7.status_code == 200 else "FAIL", {
        "query": q7,
        "http_code": r7.status_code,
        "response_status": d7.get("status"),
        "evidence_status": d7.get("evidence_status"),
        "answer_preview": d7.get("answer", "")[:100] + "...",
        "latency_sec": round(time.time() - t0, 2)
    })

    # 8. Citation Click & Passage Inspector
    t0 = time.time()
    # Check passages endpoint for document
    r_docs = client.get(f"{BACKEND_URL}/documents")
    docs = r_docs.json()
    first_doc = docs[0]
    doc_id = first_doc["document_id"]
    r_passages = client.get(f"{BACKEND_URL}/documents/{doc_id}/passages")
    passages = r_passages.json()
    has_passages = len(passages) > 0 and "text" in passages[0]
    record(8, "Citation Click & Passage Inspector", "PASS" if has_passages else "FAIL", {
        "target_doc_id": doc_id,
        "target_doc_title": first_doc.get("title"),
        "passages_retrieved": len(passages),
        "first_passage_id": passages[0].get("passage_id") if passages else None,
        "first_passage_snippet": (passages[0].get("text")[:80] + "...") if passages else None,
        "latency_sec": round(time.time() - t0, 2)
    })

    # 9. Official Document Listing
    t0 = time.time()
    r_off = client.get(f"{BACKEND_URL}/documents?source_type=official")
    off_docs = r_off.json()
    is_4_docs = len(off_docs) == 4 and all(d["source_type"] == "official" for d in off_docs)
    record(9, "Official Document Listing", "PASS" if is_4_docs else "FAIL", {
        "official_doc_count": len(off_docs),
        "titles": [d["filename"] for d in off_docs],
        "all_source_type_official": is_4_docs,
        "latency_sec": round(time.time() - t0, 2)
    })

    # 10. User-Upload Isolation
    t0 = time.time()
    r_up = client.get(f"{BACKEND_URL}/documents?source_type=upload")
    up_docs = r_up.json()
    r_off = client.get(f"{BACKEND_URL}/documents?source_type=official")
    off_docs = r_off.json()
    is_isolated = len(up_docs) == 0 and len(off_docs) == 4
    record(10, "User-Upload Isolation", "PASS" if is_isolated else "FAIL", {
        "upload_doc_count": len(up_docs),
        "official_doc_count": len(off_docs),
        "corpus_isolated": is_isolated,
        "latency_sec": round(time.time() - t0, 2)
    })

    # Check frontend HTTP server
    r_front = client.get(f"{FRONTEND_URL}/")
    front_ok = r_front.status_code == 200 and "IndicRAG-QA" in r_front.text
    print("\n-----------------------------------------------------------------")
    print(f"Frontend Server Check (http://127.0.0.1:5500): {'ONLINE (200 OK)' if front_ok else 'OFFLINE'}")
    print("-----------------------------------------------------------------")

    # Summary table
    passed_count = sum(1 for t in test_results if t["status"] == "PASS")
    print(f"\nFINAL SMOKE TEST SUMMARY: {passed_count}/10 SCENARIOS PASSED")
    print("=================================================================")

if __name__ == "__main__":
    run_all()
