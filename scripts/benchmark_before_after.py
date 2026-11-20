"""
Benchmark before and after optimization latencies across the 10 verification scenarios.
Saves results to backend/data/experiments/m7/m7_latency_comparison.csv.
"""
import sys
import time
import json
import httpx
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"
client = httpx.Client(base_url=BASE_URL, timeout=180.0)

test_scenarios = [
    {
        "id": "SCEN-01",
        "category": "English Query",
        "query": "What happens if a student misses a makeup exam?",
        "expected_status": ["conflicting_versions", "answered"],
        "baseline_latency_sec": 18.5,
    },
    {
        "id": "SCEN-02",
        "category": "Devanagari Hindi",
        "query": "सेमेस्टर शुरू होने के बाद छात्र कितने समय के भीतर पंजीकृत कोर्स में नया विषय जोड़ या हटा सकते हैं?",
        "expected_status": ["unanswerable", "answered"],
        "baseline_latency_sec": 8.5,
    },
    {
        "id": "SCEN-03",
        "category": "Code-Mixed Hinglish",
        "query": "Semester khatam hone se kitne hafte pehle tak course withdraw karne ki permission milti hai?",
        "expected_status": ["unanswerable", "answered"],
        "baseline_latency_sec": 87.2,
    },
    {
        "id": "SCEN-04",
        "category": "Romanized Hindi",
        "query": "Supplementary examination mein student ko maximum kaun sa grade mil sakta hai?",
        "expected_status": ["unanswerable", "answered"],
        "baseline_latency_sec": 167.7,
    },
    {
        "id": "SCEN-05",
        "category": "Unanswerable Policy",
        "query": "What is the prescribed fee for submitting a PhD dissertation thesis according to the SCSET UG academic regulations?",
        "expected_status": ["unanswerable"],
        "baseline_latency_sec": 8.0,
    },
    {
        "id": "SCEN-06",
        "category": "Regulatory Conflict",
        "query": "What is the minimum attendance requirement?",
        "expected_status": ["conflicting_versions"],
        "baseline_latency_sec": 14.5,
    },
    {
        "id": "SCEN-07",
        "category": "Ambiguous / Clarification",
        "query": "What is the grade requirement for students?",
        "expected_status": ["unanswerable", "clarification_needed"],
        "baseline_latency_sec": 8.2,
    },
    {
        "id": "SCEN-08",
        "category": "Passage Inspector",
        "query": "GET /documents/{id}/passages",
        "expected_status": ["passages_retrieved"],
        "baseline_latency_sec": 0.05,
    },
    {
        "id": "SCEN-09",
        "category": "Official Listing",
        "query": "GET /documents?source_type=official",
        "expected_status": ["4_documents"],
        "baseline_latency_sec": 0.04,
    },
    {
        "id": "SCEN-10",
        "category": "Upload Isolation",
        "query": "GET /documents?source_type=upload",
        "expected_status": ["0_documents_isolated"],
        "baseline_latency_sec": 0.03,
    },
]

def run_benchmark():
    records = []
    print("=" * 70)
    print("RUNNING BEFORE/AFTER LATENCY BENCHMARK & COMPARISON")
    print("=" * 70)

    for item in test_scenarios:
        scen_id = item["id"]
        cat = item["category"]
        q = item["query"]
        base_s = item["baseline_latency_sec"]

        t0 = time.perf_counter()
        if scen_id == "SCEN-08":
            docs = client.get("/documents").json()
            doc_id = docs[0]["document_id"]
            resp = client.get(f"/documents/{doc_id}/passages")
            status_val = "passages_retrieved" if resp.status_code == 200 and len(resp.json()) > 0 else "error"
            opt_s = time.perf_counter() - t0
            evidence_val = "N/A"
        elif scen_id == "SCEN-09":
            resp = client.get("/documents?source_type=official")
            status_val = "4_documents" if resp.status_code == 200 and len(resp.json()) == 4 else "error"
            opt_s = time.perf_counter() - t0
            evidence_val = "N/A"
        elif scen_id == "SCEN-10":
            resp = client.get("/documents?source_type=upload")
            status_val = "0_documents_isolated" if resp.status_code == 200 and len(resp.json()) == 0 else "error"
            opt_s = time.perf_counter() - t0
            evidence_val = "N/A"
        else:
            resp = client.post("/query", json={"query": q, "collection": ["official"]})
            opt_s = time.perf_counter() - t0
            d = resp.json()
            status_val = d.get("status", "error")
            evidence_val = d.get("evidence_status", "error")

        speedup_pct = max(0.0, ((base_s - opt_s) / base_s) * 100) if base_s > opt_s else 0.0
        passed = status_val in item["expected_status"]

        print(f"[{'PASS' if passed else 'FAIL'}] {scen_id} ({cat}): Baseline={base_s:.2f}s | Optimized={opt_s:.2f}s | Speedup={speedup_pct:.1f}%")
        
        records.append({
            "scenario_id": scen_id,
            "category": cat,
            "query_text": q,
            "baseline_latency_sec": round(base_s, 2),
            "optimized_latency_sec": round(opt_s, 2),
            "latency_reduction_pct": round(speedup_pct, 1),
            "observed_status": status_val,
            "observed_evidence_status": evidence_val,
            "verification_status": "PASS" if passed else "FAIL"
        })

    df = pd.DataFrame(records)
    out_csv = "backend/data/experiments/m7/m7_latency_comparison.csv"
    df.to_csv(out_csv, index=False)
    print("\nBenchmark comparison written to:", out_csv)
    print("=" * 70)

if __name__ == "__main__":
    run_benchmark()

