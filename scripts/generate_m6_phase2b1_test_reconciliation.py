import csv
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
out_dir = backend_dir / "data/experiments/m6"
out_dir.mkdir(parents=True, exist_ok=True)

# Documented vs Actual test counts
# STATUS.md originally listed:
# - test_api.py                      10/10
# - test_database.py                  4/4
# - test_ingestion_smoke.py          32/32
# - test_metrics.py                  18/18  <-- TYPO: Actual is 24/24!
# - test_model_verifier.py           12/12
# - test_query_processor.py          22/22
# - test_retrieval_baselines.py      12/12
# - test_m5_advanced_rag.py          19/19
# - test_m6_benchmark_expansion.py    7/7
# - test_m6_phase2b_scoring_and_controller.py 21/21

test_data = [
    {
        "test_file": "backend/tests/test_api.py",
        "documented_count_in_status_md": 10,
        "actual_collected_count": 10,
        "passed_count": 10,
        "failed_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "discrepancy_delta": 0,
        "reconciliation_notes": "Exact match. Covers FastAPI endpoints, health, ingest, and upload validation.",
    },
    {
        "test_file": "backend/tests/test_database.py",
        "documented_count_in_status_md": 4,
        "actual_collected_count": 4,
        "passed_count": 4,
        "failed_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "discrepancy_delta": 0,
        "reconciliation_notes": "Exact match. Covers SQLite table initialization, idempotency, document/passage CRUD.",
    },
    {
        "test_file": "backend/tests/test_ingestion_smoke.py",
        "documented_count_in_status_md": 32,
        "actual_collected_count": 32,
        "passed_count": 32,
        "failed_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "discrepancy_delta": 0,
        "reconciliation_notes": "Exact match. Covers PDF extraction, SHA-256 deduplication, parent-child chunking, and source registry.",
    },
    {
        "test_file": "backend/tests/test_metrics.py",
        "documented_count_in_status_md": 18,
        "actual_collected_count": 24,
        "passed_count": 24,
        "failed_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "discrepancy_delta": +6,
        "reconciliation_notes": "Discrepancy identified. STATUS.md contained a stale documentation string (18) from M4; actual module contains 24 tests (12 retrieval, 9 answer, 3 answerability).",
    },
    {
        "test_file": "backend/tests/test_model_verifier.py",
        "documented_count_in_status_md": 12,
        "actual_collected_count": 12,
        "passed_count": 12,
        "failed_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "discrepancy_delta": 0,
        "reconciliation_notes": "Exact match. Covers deterministic validation rules and independent LLM verification controller.",
    },
    {
        "test_file": "backend/tests/test_query_processor.py",
        "documented_count_in_status_md": 22,
        "actual_collected_count": 22,
        "passed_count": 22,
        "failed_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "discrepancy_delta": 0,
        "reconciliation_notes": "Exact match. Covers multilingual language/script detection, normalization, and decomposition.",
    },
    {
        "test_file": "backend/tests/test_retrieval_baselines.py",
        "documented_count_in_status_md": 12,
        "actual_collected_count": 12,
        "passed_count": 12,
        "failed_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "discrepancy_delta": 0,
        "reconciliation_notes": "Exact match. Covers BM25, Dense FAISS, RRF fusion, deduplication, and version awareness.",
    },
    {
        "test_file": "backend/tests/test_m5_advanced_rag.py",
        "documented_count_in_status_md": 19,
        "actual_collected_count": 19,
        "passed_count": 19,
        "failed_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "discrepancy_delta": 0,
        "reconciliation_notes": "Exact match. Covers adaptive router, translation-assisted retrieval, and adaptive token budget.",
    },
    {
        "test_file": "backend/tests/test_m6_benchmark_expansion.py",
        "documented_count_in_status_md": 7,
        "actual_collected_count": 7,
        "passed_count": 7,
        "failed_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "discrepancy_delta": 0,
        "reconciliation_notes": "Exact match. Covers expanded benchmark schemas, unanswerable categorization, and verifier exclusion.",
    },
    {
        "test_file": "backend/tests/test_m6_phase2b_scoring_and_controller.py",
        "documented_count_in_status_md": 21,
        "actual_collected_count": 21,
        "passed_count": 21,
        "failed_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "discrepancy_delta": 0,
        "reconciliation_notes": "Exact match. Covers score normalizers, convex CECI, six-state controller precedence, and claim grounding.",
    },
]

out_csv = out_dir / "m6_phase2b1_test_reconciliation.csv"
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(test_data[0].keys()))
    writer.writeheader()
    writer.writerows(test_data)

print(f"Wrote {len(test_data)} test reconciliation rows to {out_csv}")

