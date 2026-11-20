"""
IndicRAG-QA — M6 Phase 2B: Theory-Anchored Evidence Scoring & Heuristic Controller Pilot Evaluation.

Executes:
1. Environment & Corpus integrity verification.
2. Full retrieval, CECI scoring, and Evidence Controller evaluation across all 60 benchmark candidates:
   - Primary Pilot Set: 29 ELIGIBLE_PROVISIONAL candidates (27 answerable, 2 unanswerable).
   - Diagnostic Set: 31 EXCLUDED candidates (24 needs_review, 7 auto_rejected).
3. Atomic claim grounding audit on all generated / reference answers.
4. Auditable output artifacts generation:
   - m6_phase2b_query_eval.csv
   - m6_phase2b_claim_grounding.csv
   - m6_phase2b_controller_trace.jsonl
   - m6_phase2b_config.json
   - m6_phase2b_manifest.json
5. Descriptive pilot evaluation summary without claims of empirical calibration.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.logging_config import logger
from app.generation.claim_grounding import get_claim_grounding_verifier
from app.models.schemas import (
    DocumentSource,
    EvidenceStatus,
    QueryAnalysis,
    QuestionType,
    RetrievedPassage,
    RetrievalResult,
)
from app.query.processor import process_query
from app.retrieval.engine import retrieve
from app.retrieval.evidence_controller import get_evidence_controller

CORPUS_DB_PATH = backend_dir / "data" / "db" / "indicrag.db"
QUALIFICATION_PATH = backend_dir / "data" / "dataset" / "m6_benchmark_qualification.csv"
BENCHMARK_PATH = backend_dir / "data" / "dataset" / "m6_expanded_benchmark_n60.csv"
OUTPUT_DIR = backend_dir / "data" / "experiments" / "m6"

EXPECTED_CORPUS_HASH = "8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d"
EXPECTED_M3_HASH = "093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520"
EXPECTED_N60_HASH = "a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae"


def compute_corpus_hash(db_path: Path) -> str:
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT passage_id, text FROM passages WHERE parent_passage_id IS NOT NULL ORDER BY passage_id")
    rows = cursor.fetchall()
    conn.close()
    hasher = hashlib.sha256()
    for pid, text in rows:
        hasher.update(pid.encode("utf-8"))
        hasher.update(text.encode("utf-8"))
    return hasher.hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_pilot():
    print("=" * 80)
    print("IndicRAG-QA — M6 Phase 2B: Heuristic Evidence Scoring Pilot Evaluation")
    print("=" * 80)

    # 1. Integrity Verification
    corpus_hash = compute_corpus_hash(CORPUS_DB_PATH)
    n60_hash = sha256_file(BENCHMARK_PATH)

    print(f"Corpus DB Hash:    {corpus_hash} (Matches: {corpus_hash == EXPECTED_CORPUS_HASH})")
    print(f"Benchmark N=60:    {n60_hash} (Matches: {n60_hash == EXPECTED_N60_HASH})")

    if corpus_hash != EXPECTED_CORPUS_HASH:
        raise RuntimeError("Corpus DB hash mismatch!")
    if n60_hash != EXPECTED_N60_HASH:
        raise RuntimeError("Expanded benchmark hash mismatch!")

    # 2. Load Qualified Records
    records = []
    with open(QUALIFICATION_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    print(f"Loaded {len(records)} qualification records from {QUALIFICATION_PATH.name}")

    eligible_records = [r for r in records if r["eligibility_status"] == "ELIGIBLE_PROVISIONAL"]
    excluded_records = [r for r in records if r["eligibility_status"] != "ELIGIBLE_PROVISIONAL"]

    print(f"  - Primary Pilot Set (Eligible): {len(eligible_records)} (27 answerable, 2 unanswerable)")
    print(f"  - Diagnostic Set (Excluded):   {len(excluded_records)} (13 answerable, 18 unanswerable)")

    controller = get_evidence_controller()
    claim_verifier = get_claim_grounding_verifier()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    query_eval_rows = []
    claim_grounding_rows = []
    controller_traces = []

    print("\nExecuting evaluation pipeline across all 60 benchmark records...")

    for idx, r in enumerate(records, 1):
        cid = r["candidate_id"]
        q_text = r["original_question"]
        gold_ans = r["answerability"]
        ref_answer = r.get("reference_answer", "")
        cohort_group = r["eligibility_status"]
        lang = r.get("query_language", "en")

        # Step A: Query Processing
        t0 = time.perf_counter()
        qa = process_query(q_text)

        # Step B: Retrieval
        rr = retrieve(qa, collections=[DocumentSource.OFFICIAL], top_k=5, use_reranker=True)

        # Step C: Controller Evaluation
        dec = controller.evaluate(rr, attempt=1)
        lat_ms = (time.perf_counter() - t0) * 1000

        # Step D: Map Decision to Answerability
        if dec.status in (EvidenceStatus.SUFFICIENT, EvidenceStatus.PARTIAL):
            pred_ans = "answerable"
        else:
            pred_ans = "unanswerable"

        is_correct = (pred_ans == gold_ans)

        # Step E: Claim Grounding on Reference / Generated Answer
        claim_res = claim_verifier.verify_claims(
            answer_text=ref_answer,
            evidence_passages=dec.valid_passages,
        )

        for c in claim_res.claims:
            claim_grounding_rows.append({
                "candidate_id": cid,
                "cohort_group": cohort_group,
                "claim_id": c.claim_id,
                "claim_text": c.claim_text,
                "verdict": c.verdict.value,
                "numeric_verified": c.numeric_verified,
                "date_verified": c.date_verified,
                "negation_verified": c.negation_verified,
                "semantic_entailed": c.semantic_entailed,
                "discrepancies": "; ".join(c.discrepancies),
                "explanation": c.explanation,
            })

        # Step F: Extract CECI details
        ceci_score = dec.ceci_score if dec.ceci_score is not None else 0.0
        f_dict = dec.ceci_features or {}

        top1_p = dec.valid_passages[0] if dec.valid_passages else None
        top1_raw = top1_p.score if top1_p else 0.0
        top1_mod = top1_p.retrieval_method if top1_p else "none"

        query_eval_rows.append({
            "candidate_id": cid,
            "cohort_group": cohort_group,
            "original_question": q_text,
            "query_language": lang,
            "gold_answerability": gold_ans,
            "controller_status": dec.status.value,
            "predicted_answerability": pred_ans,
            "is_correct_answerability": is_correct,
            "ceci_heuristic_score": round(ceci_score, 4),
            "f1_top1_relevance": f_dict.get("f1_top1_relevance", 0.0),
            "f2_score_margin": f_dict.get("f2_score_margin", 0.0),
            "f3_modality_consensus": f_dict.get("f3_modality_consensus", 0.0),
            "f4_keyword_coverage": f_dict.get("f4_keyword_coverage", 0.0),
            "f5_regulatory_fit": f_dict.get("f5_regulatory_fit", 0.0),
            "coverage_score": round(dec.coverage_score, 4),
            "clarification_needed": dec.clarification_needed,
            "total_claims": claim_res.total_claims,
            "entailed_claims": claim_res.entailed_claims,
            "contradicted_claims": claim_res.contradicted_claims,
            "grounding_ratio": claim_res.grounding_ratio,
            "latency_ms": round(lat_ms, 2),
            "explanation": dec.explanation,
        })

        # Step G: Auditable Trace
        controller_traces.append({
            "candidate_id": cid,
            "cohort_group": cohort_group,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "query": q_text,
            "gold_answerability": gold_ans,
            "controller_status": dec.status.value,
            "predicted_answerability": pred_ans,
            "is_correct": is_correct,
            "ceci_heuristic_score": round(ceci_score, 4),
            "ceci_features": f_dict,
            "retrieved_passage_count": len(rr.retrieved_passages),
            "valid_passage_count": len(dec.valid_passages),
            "conflicting_passage_count": len(dec.conflicting_passages),
            "claim_grounding": {
                "total_claims": claim_res.total_claims,
                "entailed": claim_res.entailed_claims,
                "contradicted": claim_res.contradicted_claims,
                "grounding_ratio": claim_res.grounding_ratio,
            },
            "explanation": dec.explanation,
        })

        if idx % 10 == 0 or idx == len(records):
            print(f"  Processed {idx}/{len(records)} records...")

    # 3. Write Deliverables
    query_eval_csv = OUTPUT_DIR / "m6_phase2b_query_eval.csv"
    with open(query_eval_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(query_eval_rows[0].keys()))
        w.writeheader()
        w.writerows(query_eval_rows)

    claim_csv = OUTPUT_DIR / "m6_phase2b_claim_grounding.csv"
    with open(claim_csv, "w", newline="", encoding="utf-8") as f:
        if claim_grounding_rows:
            w = csv.DictWriter(f, fieldnames=list(claim_grounding_rows[0].keys()))
            w.writeheader()
            w.writerows(claim_grounding_rows)

    trace_jsonl = OUTPUT_DIR / "m6_phase2b_controller_trace.jsonl"
    with open(trace_jsonl, "w", encoding="utf-8") as f:
        for t in controller_traces:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    # Configuration artifact
    config_dict = {
        "milestone": "M6",
        "phase": "Phase 2B",
        "execution_date": datetime.now(timezone.utc).isoformat(),
        "framework": "theory_anchored_heuristic_pilot",
        "empirical_calibration": False,
        "empirical_calibration_deferred_reason": "Sample size (N=29, N_neg=2) mathematically prohibits valid empirical Platt scaling, isotonic regression, or nested cross-fitting.",
        "ceci_weights": {
            "w1_relevance": 0.35,
            "w2_margin": 0.15,
            "w3_consensus": 0.15,
            "w4_keyword_cov": 0.15,
            "w5_regulatory": 0.20,
        },
        "thresholds": {
            "tau_sufficient": 0.65,
            "tau_insufficient": 0.35,
            "multi_part_coverage_threshold": 0.60,
        },
        "override_precedence": [
            "1. Missing mandatory cohort parameter -> CLARIFICATION_REQUIRED",
            "2. Genuine document version contradiction -> CONFLICTING",
            "3. Out-of-domain scope or 0 retrieved evidence -> MISSING",
            "4. Contradictory user premise -> INSUFFICIENT",
            "5. Zero valid citations / passages -> INSUFFICIENT",
            "6. CECI confidence thresholding (tau_suff=0.65, tau_insuff=0.35) -> SUFFICIENT / PARTIAL / INSUFFICIENT",
        ],
        "corpus_hash": corpus_hash,
        "n60_benchmark_hash": n60_hash,
    }

    config_file = OUTPUT_DIR / "m6_phase2b_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)

    # 4. Compute Metrics for Primary Pilot Set (N=29)
    eligible_eval = [row for row in query_eval_rows if row["cohort_group"] == "ELIGIBLE_PROVISIONAL"]
    excluded_eval = [row for row in query_eval_rows if row["cohort_group"] != "ELIGIBLE_PROVISIONAL"]

    tp = sum(1 for r in eligible_eval if r["gold_answerability"] == "answerable" and r["predicted_answerability"] == "answerable")
    tn = sum(1 for r in eligible_eval if r["gold_answerability"] == "unanswerable" and r["predicted_answerability"] == "unanswerable")
    fp = sum(1 for r in eligible_eval if r["gold_answerability"] == "unanswerable" and r["predicted_answerability"] == "answerable")
    fn = sum(1 for r in eligible_eval if r["gold_answerability"] == "answerable" and r["predicted_answerability"] == "unanswerable")

    acc = (tp + tn) / len(eligible_eval) if eligible_eval else 0.0
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_ans = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

    prec_un = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    rec_un = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1_un = (2 * prec_un * rec_un) / (prec_un + rec_un) if (prec_un + rec_un) > 0 else 0.0
    macro_f1 = (f1_ans + f1_un) / 2.0

    # Status distribution
    status_counts_elig = {}
    for r in eligible_eval:
        st = r["controller_status"]
        status_counts_elig[st] = status_counts_elig.get(st, 0) + 1

    status_counts_excl = {}
    for r in excluded_eval:
        st = r["controller_status"]
        status_counts_excl[st] = status_counts_excl.get(st, 0) + 1

    # Mean CECI by answerability in pilot set
    ceci_ans = [r["ceci_heuristic_score"] for r in eligible_eval if r["gold_answerability"] == "answerable"]
    ceci_un = [r["ceci_heuristic_score"] for r in eligible_eval if r["gold_answerability"] == "unanswerable"]

    mean_ceci_ans = sum(ceci_ans) / len(ceci_ans) if ceci_ans else 0.0
    mean_ceci_un = sum(ceci_un) / len(ceci_un) if ceci_un else 0.0

    # Manifest artifact
    manifest_dict = {
        "milestone": "M6",
        "phase": "Phase 2B",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "corpus_sha256": corpus_hash,
        "n60_benchmark_sha256": n60_hash,
        "total_benchmark_records": len(records),
        "primary_pilot_set": {
            "n_records": len(eligible_eval),
            "n_answerable": sum(1 for r in eligible_eval if r["gold_answerability"] == "answerable"),
            "n_unanswerable": sum(1 for r in eligible_eval if r["gold_answerability"] == "unanswerable"),
            "accuracy": round(acc, 4),
            "precision_answerable": round(prec, 4),
            "recall_answerable": round(rec, 4),
            "f1_answerable": round(f1_ans, 4),
            "precision_unanswerable": round(prec_un, 4),
            "recall_unanswerable": round(rec_un, 4),
            "f1_unanswerable": round(f1_un, 4),
            "macro_f1": round(macro_f1, 4),
            "confusion_matrix": {"TP": tp, "TN": tn, "FP": fp, "FN": fn},
            "status_distribution": status_counts_elig,
            "mean_ceci_answerable": round(mean_ceci_ans, 4),
            "mean_ceci_unanswerable": round(mean_ceci_un, 4),
        },
        "diagnostic_excluded_set": {
            "n_records": len(excluded_eval),
            "n_answerable": sum(1 for r in excluded_eval if r["gold_answerability"] == "answerable"),
            "n_unanswerable": sum(1 for r in excluded_eval if r["gold_answerability"] == "unanswerable"),
            "status_distribution": status_counts_excl,
        },
        "files_generated": [
            "backend/data/experiments/m6/m6_phase2b_query_eval.csv",
            "backend/data/experiments/m6/m6_phase2b_claim_grounding.csv",
            "backend/data/experiments/m6/m6_phase2b_controller_trace.jsonl",
            "backend/data/experiments/m6/m6_phase2b_config.json",
            "backend/data/experiments/m6/m6_phase2b_manifest.json",
        ],
    }

    manifest_file = OUTPUT_DIR / "m6_phase2b_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2)

    # 5. Print Results Summary
    print("\n" + "=" * 80)
    print("M6 PHASE 2B PILOT EVALUATION RESULTS")
    print("=" * 80)
    print(f"Primary Pilot Set (N={len(eligible_eval)}):")
    print(f"  - Answerability Accuracy:        {acc:.1%}")
    print(f"  - Macro F1:                      {macro_f1:.4f}")
    print(f"  - Answerable F1 (N=27):          {f1_ans:.4f} (Prec: {prec:.4f}, Rec: {rec:.4f})")
    print(f"  - Unanswerable F1 (N=2):         {f1_un:.4f} (Prec: {prec_un:.4f}, Rec: {rec_un:.4f})")
    print(f"  - Confusion Matrix:              TP={tp}, TN={tn}, FP={fp}, FN={fn}")
    print(f"  - Mean CECI Score (Answerable):  {mean_ceci_ans:.4f}")
    print(f"  - Mean CECI Score (Unanswerable):{mean_ceci_un:.4f}")
    print(f"  - Controller State Breakdown:    {status_counts_elig}")
    print("\nDiagnostic Excluded Set (N=31):")
    print(f"  - Controller State Breakdown:    {status_counts_excl}")
    print("\nDeliverables successfully written to:")
    print(f"  1. {query_eval_csv}")
    print(f"  2. {claim_csv}")
    print(f"  3. {trace_jsonl}")
    print(f"  4. {config_file}")
    print(f"  5. {manifest_file}")
    print("=" * 80)


if __name__ == "__main__":
    run_pilot()
