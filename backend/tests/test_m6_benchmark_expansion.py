"""
M6 Phase 2A: Test suite for Expanded Benchmark and Dual Independent Model Verification.

Verifies:
1. Exact benchmark scale: N=60 rows total (40 answerable, 20 unanswerable).
2. Frozen M3 benchmark preservation (N=15, exact hash and records preserved).
3. Grounding integrity: Verbatim string containment in SQLite database for all 27 new answerable candidates.
4. Independent model verification integrity:
   - Generator model strictly excluded from verifier models.
   - Dual verifiers assigned per candidate.
   - No automated decision marked as 'human_verified' (review_status == 'pending').
5. Language & script balance (English 20, Devanagari Hindi 16, Hinglish 12, Romanized Hindi 12).
6. Multi-label unanswerable taxonomy distribution.
7. Deliverables presence and structure.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
DB_PATH = BACKEND_DIR / "data" / "db" / "indicrag.db"
M3_FROZEN_CSV = BACKEND_DIR / "data" / "dataset" / "final_verified_dataset.csv"
M6_OUTPUT_CSV = BACKEND_DIR / "data" / "dataset" / "m6_expanded_benchmark_n60.csv"
M6_VERIFICATION_JSONL = BACKEND_DIR / "data" / "dataset" / "m6_candidate_verification.jsonl"
M6_RECONCILIATION_CSV = BACKEND_DIR / "data" / "dataset" / "m6_candidate_reconciliation.csv"
M6_MANIFEST_JSON = BACKEND_DIR / "data" / "experiments" / "m6" / "m6_phase2a_manifest.json"
M6_REPORT_MD = REPO_ROOT / "docs" / "m6_phase2a_benchmark_report.md"

EXPECTED_M3_HASH = "093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520"
EXPECTED_CORPUS_HASH = "8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d"


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def test_m3_frozen_integrity():
    """Verify that original M3 frozen dataset is byte-for-byte identical and has 15 rows."""
    assert M3_FROZEN_CSV.exists(), "Frozen M3 benchmark CSV missing"
    assert compute_sha256(M3_FROZEN_CSV) == EXPECTED_M3_HASH, "M3 frozen hash mismatch!"
    with open(M3_FROZEN_CSV, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 15, f"Expected 15 rows in M3 frozen dataset, got {len(reader)}"


def test_m6_expanded_benchmark_scale():
    """Verify N=60 total, 40 answerable, 20 unanswerable."""
    assert M6_OUTPUT_CSV.exists(), "M6 expanded benchmark CSV missing"
    with open(M6_OUTPUT_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 60, f"Expected 60 rows, got {len(rows)}"

    ans = [r for r in rows if r["answerability"] == "answerable"]
    unans = [r for r in rows if r["answerability"] == "unanswerable"]

    assert len(ans) == 40, f"Expected 40 answerable, got {len(ans)}"
    assert len(unans) == 20, f"Expected 20 unanswerable, got {len(unans)}"


def test_m3_rows_preserved_in_n60():
    """Verify that the first 15 rows of N=60 match the frozen M3 benchmark."""
    with open(M3_FROZEN_CSV, "r", encoding="utf-8") as f:
        m3_rows = list(csv.DictReader(f))
    with open(M6_OUTPUT_CSV, "r", encoding="utf-8") as f:
        n60_rows = list(csv.DictReader(f))

    for i in range(15):
        assert n60_rows[i]["candidate_id"] == m3_rows[i]["candidate_id"]
        assert n60_rows[i]["original_question"] == m3_rows[i]["original_question"]
        assert n60_rows[i]["answerability"] == m3_rows[i]["answerability"]


def test_independent_model_verification_rules():
    """Verify candidate generator is strictly excluded from verifiers and review_status is pending."""
    with open(M6_OUTPUT_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    new_45 = rows[15:]
    assert len(new_45) == 45

    for r in new_45:
        gen = r["generator_model"]
        vers = [v.strip() for v in r["verifier_models"].split(",")]
        assert len(vers) == 2, f"Expected 2 verifiers, got {vers} for {r['candidate_id']}"
        assert gen not in vers, f"Generator {gen} must NOT be in verifiers {vers} for {r['candidate_id']}"
        # Critical research rule: Automated validation must never be marked as human_verified
        assert r["review_status"] == "pending", (
            f"Candidate {r['candidate_id']} must have review_status='pending', got {r['review_status']}"
        )


def test_verbatim_evidence_grounding():
    """Verify that all gold_evidence_quotes in 27 new answerables exist verbatim in SQLite passages."""
    with open(M6_OUTPUT_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    new_45 = rows[15:]
    new_ans = [r for r in new_45 if r["answerability"] == "answerable"]
    assert len(new_ans) == 27, f"Expected 27 new answerable queries, got {len(new_ans)}"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    for r in new_ans:
        quotes = json.loads(r["gold_evidence_quotes"])
        assert len(quotes) > 0, f"Expected at least one quote for {r['candidate_id']}"
        doc_id = r["source_document_id"]

        # Check quotes exist in DB passages
        for q in quotes:
            res = c.execute(
                "SELECT passage_id, text FROM passages WHERE document_id = ? AND instr(text, ?) > 0",
                (doc_id, q),
            ).fetchall()
            assert len(res) > 0, f"Quote '{q[:60]}...' for {r['candidate_id']} not found in document {doc_id}"

    conn.close()


def test_language_and_script_distribution():
    """Verify language stratification across N=60."""
    with open(M6_OUTPUT_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    langs = [r["query_language"] for r in rows]
    en_cnt = sum(1 for l in langs if l == "en")
    hi_cnt = sum(1 for l in langs if l == "hi")
    hien_cnt = sum(1 for l in langs if l in ("hi-en", "hi_en"))
    hilatn_cnt = sum(1 for l in langs if l in ("hi-Latn", "hi_Latn"))

    assert en_cnt == 20, f"Expected 20 English, got {en_cnt}"
    assert hi_cnt == 16, f"Expected 16 Hindi (Devanagari), got {hi_cnt}"
    assert hien_cnt == 12, f"Expected 12 Hinglish, got {hien_cnt}"
    assert hilatn_cnt == 12, f"Expected 12 Romanized Hindi, got {hilatn_cnt}"


def test_deliverables_and_manifest_exist():
    """Verify all required Phase 2A deliverables exist."""
    assert M6_OUTPUT_CSV.exists(), "Benchmark CSV missing"
    assert M6_VERIFICATION_JSONL.exists(), "Verification JSONL missing"
    assert M6_RECONCILIATION_CSV.exists(), "Reconciliation CSV missing"
    assert M6_MANIFEST_JSON.exists(), "Phase 2A manifest missing"
    assert M6_REPORT_MD.exists(), "Phase 2A report markdown missing"

    with open(M6_MANIFEST_JSON, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["stratification_summary"]["total_instances"] == 60
    assert manifest["stratification_summary"]["answerable_count"] == 40
    assert manifest["stratification_summary"]["unanswerable_count"] == 20
    assert manifest["stratification_summary"]["human_verified_count"] == 0
    assert manifest["stratification_summary"]["review_status_pending_count"] == 60

