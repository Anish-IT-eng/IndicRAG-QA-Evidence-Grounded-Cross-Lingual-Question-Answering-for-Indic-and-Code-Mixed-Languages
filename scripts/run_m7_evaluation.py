"""
M7 End-to-End Benchmark Evaluation Script.
Evaluates the integrated system on the frozen M3 benchmark (N=15)
and records performance, latency, evidence status, and citation traceability.
"""
from __future__ import annotations

import csv
import json
import time
import sys
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path("backend").resolve()
sys.path.insert(0, str(backend_dir))

from app.api.main import app

client = TestClient(app)

M3_PATH = Path("backend/data/dataset/final_verified_dataset.csv")
OUT_CSV = Path("backend/data/experiments/m7/m7_integration_results.csv")
OUT_MANIFEST = Path("backend/data/experiments/m7/m7_manifest.json")


def run_m7_eval():
    with open(M3_PATH, encoding="utf-8") as f:
        m3_queries = list(csv.DictReader(f))

    print(f"Evaluating {len(m3_queries)} frozen M3 benchmark queries against integrated API...")

    results = []
    latencies = []

    for idx, q in enumerate(m3_queries, 1):
        qid = q.get("question_id", f"q_{idx}")
        qtext = q["original_question"]
        lang = q.get("query_language", "en")
        gold_ans = q.get("answerability", "answerable")

        t0 = time.perf_counter()
        resp = client.post("/query", json={"query": qtext, "collection": ["official"], "debug": True})
        lat = (time.perf_counter() - t0) * 1000
        latencies.append(lat)

        data = resp.json() if resp.status_code == 200 else {}
        ans = data.get("answer") or ""

        results.append({
            "question_id": qid,
            "query_text": qtext,
            "language": lang,
            "gold_answerability": gold_ans,
            "http_status": resp.status_code,
            "response_status": data.get("status"),
            "evidence_status": data.get("evidence_status"),
            "citations_count": len(data.get("citations", [])),
            "client_latency_ms": round(lat, 2),
            "backend_latency_ms": round(data.get("latency_ms", 0.0), 2),
            "answer_preview": ans[:120].replace("\n", " "),
        })
        print(f"[{idx}/{len(m3_queries)}] {qid[:8]} | {lang} | status={data.get('status')} | cit={len(data.get('citations', []))} | lat={lat:.1f}ms")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    manifest = {
        "milestone": "M7",
        "phase": "M7_Phase_1",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_queries_evaluated": len(results),
        "mean_latency_ms": round(float(sum(latencies) / len(latencies)), 2),
        "min_latency_ms": round(float(min(latencies)), 2),
        "max_latency_ms": round(float(max(latencies)), 2),
        "status_counts": {
            "answered": sum(1 for r in results if r["response_status"] == "answered"),
            "unanswerable": sum(1 for r in results if r["response_status"] == "unanswerable"),
            "conflicting_versions": sum(1 for r in results if r["response_status"] == "conflicting_versions"),
            "clarification_needed": sum(1 for r in results if r["response_status"] == "clarification_needed"),
            "error": sum(1 for r in results if r["response_status"] == "error"),
        },
        "all_http_ok": all(r["http_status"] == 200 for r in results),
        "deliverables": [
            "docs/m7_frontend_integration_design.md",
            "docs/m7_frontend_integration_report.md",
            "backend/tests/test_m7_frontend_api_integration.py",
            "docs/m7_accessibility_and_language_report.md",
            "docs/m7_performance_report.md",
            "backend/data/experiments/m7/m7_integration_results.csv",
            "backend/data/experiments/m7/m7_manifest.json",
            "docs/indicrag_qa_final_research_report.md"
        ]
    }
    with open(OUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("M7 evaluation successfully completed.")


if __name__ == "__main__":
    run_m7_eval()

