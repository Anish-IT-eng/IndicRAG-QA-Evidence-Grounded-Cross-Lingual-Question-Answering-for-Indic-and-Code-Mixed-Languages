"""
Conservative Third-Model Adjudication for 39 Unresolved Candidates.
Uses local Gemma 2B as independent Verifier C alongside Qwen 2.5 3B (Verifier A) and Llama 3.2 3B (Verifier B).
Strictly enforces deterministic evidence grounding, entailment, and contradiction checks.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

try:
    import pyarrow.dataset as _pds
    if not hasattr(_pds, "ParquetFragmentScanOptions"):
        _pds.ParquetFragmentScanOptions = type("ParquetFragmentScanOptions", (), {})
except ImportError:
    pass

from app.core.database import get_db, init_db
from app.core.logging_config import setup_logging, logger
from app.evaluation.model_verifier import (
    DeterministicValidator,
    IndependentModelVerifier,
    ValidationStatus,
    VerifierVerdict,
)

# Paths
PILOT_NR_CSV = REPO_ROOT / "backend/data/dataset/candidates_needs_review.csv"
MULTI_RES_CSV = REPO_ROOT / "backend/data/dataset/multilingual_expansion_results.csv"
MULTI_COMB_CSV = REPO_ROOT / "backend/data/dataset/multilingual_expansion_combined.csv"

OUT_CSV = REPO_ROOT / "backend/data/dataset/adjudication_39_results.csv"
OUT_AUDIT = REPO_ROOT / "backend/data/dataset/adjudication_39_audit.jsonl"
OUT_REPORT = REPO_ROOT / "docs/m3_third_model_adjudication_report.md"


def load_39_candidates() -> list[dict[str, Any]]:
    # Load 32 pilot candidates
    with open(PILOT_NR_CSV, encoding="utf-8") as f:
        pilot_32 = list(csv.DictReader(f))
    for r in pilot_32:
        r["pool"] = "pilot_32"
        # Parse JSON fields
        for k in ["gold_passage_ids", "gold_evidence_quotes"]:
            val = r.get(k, "[]")
            if isinstance(val, str) and val.startswith("["):
                try:
                    r[k] = json.loads(val)
                except Exception:
                    r[k] = [val]
            elif isinstance(val, str) and val:
                r[k] = [val]
            else:
                r[k] = []

    # Load 7 multilingual expansion candidates
    with open(MULTI_RES_CSV, encoding="utf-8") as f:
        multi_all = list(csv.DictReader(f))
    multi_7_res = [r for r in multi_all if r["final_status"] == "needs_review"]

    # Combine with original metadata from multi_comb
    with open(MULTI_COMB_CSV, encoding="utf-8") as f:
        multi_comb_map = {r["question_id"]: r for r in csv.DictReader(f)}

    multi_7 = []
    for r in multi_7_res:
        qid = r["candidate_id"]
        meta = multi_comb_map.get(qid, {})
        merged = dict(meta)
        merged["pool"] = "multilingual_7"
        merged["candidate_id"] = qid
        merged["verifier_a_verdict"] = r.get("verifier_a_verdict", "N/A")
        merged["verifier_b_verdict"] = r.get("verifier_b_verdict", "N/A")
        merged["previous_issues"] = r.get("issues", "")
        # Parse JSON fields
        for k in ["gold_passage_ids", "gold_evidence_quotes"]:
            val = merged.get(k, "[]")
            if isinstance(val, str) and val.startswith("["):
                try:
                    merged[k] = json.loads(val)
                except Exception:
                    merged[k] = [val]
            elif isinstance(val, str) and val:
                merged[k] = [val]
            else:
                merged[k] = []
        multi_7.append(merged)

    all_39 = pilot_32 + multi_7
    return all_39


def get_evidence_text(passage_ids: list[str]) -> str:
    if not passage_ids:
        return ""
    with get_db() as conn:
        placeholders = ",".join("?" for _ in passage_ids)
        rows = conn.execute(
            f"SELECT passage_id, heading, text FROM passages WHERE passage_id IN ({placeholders})",
            passage_ids
        ).fetchall()
        parts = []
        for r in rows:
            h = f"[{r['heading']}] " if r["heading"] else ""
            parts.append(f"PASSAGE {r['passage_id']}:\n{h}{r['text']}")
        return "\n\n".join(parts)


def main():
    setup_logging()
    init_db()

    candidates = load_39_candidates()
    print(f"\nLoaded {len(candidates)} unresolved candidates for adjudication.")
    print("Verifier A: qwen2.5:3b (preserved)")
    print("Verifier B: llama3.2:3b (preserved)")
    print("Verifier C (Adjudicator): gemma:2b (Google)")

    verifier_c = IndependentModelVerifier(
        model_name="gemma:2b",
        model_family="gemma",
        timeout=120.0
    )
    det_validator = DeterministicValidator()

    adjudicated_records: list[dict[str, Any]] = []
    audit_events: list[dict[str, Any]] = []

    for idx, cand in enumerate(candidates, 1):
        qid = cand.get("candidate_id") or cand.get("question_id")
        q_text = cand.get("original_question", "")
        pool = cand.get("pool")
        v_a_str = cand.get("verifier_a_verdict", "UNCERTAIN")
        v_b_str = cand.get("verifier_b_verdict", "UNCERTAIN")

        print(f"\n[{idx}/39] Adjudicating {qid[:8]} ({pool}) | {cand.get('query_language')} | vA={v_a_str} | vB={v_b_str}")
        print(f"  Q: {q_text[:60]}...")

        # 1. Deterministic validation
        det_res = det_validator.validate_candidate(cand)

        # 2. Evidence text retrieval
        pids = cand.get("gold_passage_ids", [])
        evidence_text = get_evidence_text(pids)

        # 3. Third verifier evaluation via Gemma 2B
        eval_c = verifier_c.evaluate_candidate(cand, evidence_text)
        print(f"  Gemma 2B Verdict: {eval_c.verdict.value} | support={eval_c.evidence_support} | contradiction={eval_c.contradiction_detected}")

        # 4. Strict Conservative Adjudication Logic
        failures = []
        issues = []
        if not det_res.passed:
            failures.extend(det_res.failure_categories)
            issues.extend(det_res.issues)

        # Map string verdicts
        def to_verdict(v_str):
            if v_str == "ACCEPT":
                return VerifierVerdict.ACCEPT
            elif v_str == "REJECT":
                return VerifierVerdict.REJECT
            return VerifierVerdict.UNCERTAIN

        v_a = to_verdict(v_a_str)
        v_b = to_verdict(v_b_str)
        v_c = eval_c.verdict

        # Collect verifier decisions
        verdicts = [v_a, v_b, v_c]
        accept_count = sum(1 for v in verdicts if v == VerifierVerdict.ACCEPT)
        reject_count = sum(1 for v in verdicts if v == VerifierVerdict.REJECT)

        # Check for material contradiction
        has_contradiction = (
            eval_c.contradiction_detected or
            "contradiction" in cand.get("issues", "").lower() or
            "contradiction" in str(eval_c.issues).lower()
        )

        # Specific rule check: Does quote exist and actually support?
        exact_quote_in_evidence = False
        quotes = cand.get("gold_evidence_quotes", [])
        for q in quotes:
            if q and q.strip() in evidence_text:
                exact_quote_in_evidence = True
                break

        # Language and script check
        lang = cand.get("query_language", "en")
        script = cand.get("query_script", "Latin")
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", q_text))
        script_ok = True
        if lang == "hi" and not has_devanagari:
            script_ok = False
            issues.append("Language is hi but script lacks Devanagari")
        elif lang == "en" and has_devanagari:
            script_ok = False
            issues.append("Language is en but script contains Devanagari")

        # Specific check for candidate fe70960c (already verified per Clause 16.1 (vi))
        is_candidate_fe70 = (qid == "fe70960c-f447-4fd4-88c7-20572e422fb0")

        # Decision Controller:
        # Conditions for AUTO_VALIDATED:
        # 1. Deterministic evidence validation passed
        # 2. Exact quote exists in passage
        # 3. At least 2 independent verifiers ACCEPT
        # 4. No material evidence contradiction
        # 5. Language and script consistent
        # 6. Reference answer non-empty and precise
        ans = cand.get("reference_answer", "").strip()
        ans_precise = len(ans) > 3 and not ans.lower().startswith("null")

        if reject_count >= 2:
            final_status = ValidationStatus.AUTO_REJECTED
            failures.append("MAJORITY_VERIFIER_REJECTION")
            issues.append(f"Rejected by 2+ verifiers: vA={v_a.value}, vB={v_b.value}, vC={v_c.value}")
        elif det_res.passed and exact_quote_in_evidence and accept_count >= 2 and not has_contradiction and script_ok and ans_precise:
            # Special check: if pool was pilot and Gemma was generator, did BOTH Qwen and Llama accept?
            # If Qwen rejected, but Gemma (generator) + Llama accepted, that's not independent acceptance over Qwen!
            if pool == "pilot_32" and v_a == VerifierVerdict.REJECT and not is_candidate_fe70:
                # Qwen rejected on grounded evidence grounds. Do not override Qwen with generator Gemma!
                final_status = ValidationStatus.NEEDS_REVIEW
                issues.append("Verifier A (Qwen) rejected on evidence grounds; retained in needs_review to prevent generator bias")
            elif pool == "pilot_32" and v_a == VerifierVerdict.ACCEPT and v_b == VerifierVerdict.ACCEPT:
                # Both Qwen and Llama accepted (e.g. fe70960c after answer correction)
                final_status = ValidationStatus.AUTO_VALIDATED
            elif pool == "multilingual_7" and accept_count >= 2 and not has_contradiction:
                final_status = ValidationStatus.AUTO_VALIDATED
            else:
                final_status = ValidationStatus.NEEDS_REVIEW
                issues.append(f"Uncertainty remaining: vA={v_a.value}, vB={v_b.value}, vC={v_c.value}")
        else:
            final_status = ValidationStatus.NEEDS_REVIEW
            issues.append(f"Verification criteria not fully met: det_pass={det_res.passed}, quote_ok={exact_quote_in_evidence}, accepts={accept_count}, contradiction={has_contradiction}")

        print(f"  -> Final Status: {final_status.value}")

        rec = {
            "candidate_id": qid,
            "original_question": q_text,
            "query_language": lang,
            "query_script": script,
            "question_type": cand.get("question_type", "direct"),
            "answerability": cand.get("answerability", "answerable"),
            "final_status": final_status.value,
            "deterministic_passed": "yes" if det_res.passed else "no",
            "verifier_a_verdict": v_a.value,
            "verifier_b_verdict": v_b.value,
            "verifier_c_verdict": v_c.value,
            "verifier_c_model": "gemma:2b",
            "accept_count": accept_count,
            "reject_count": reject_count,
            "contradiction_detected": has_contradiction,
            "failure_categories": "; ".join(failures),
            "issues": "; ".join(issues),
            "reference_answer": ans,
            "source_document_id": cand.get("source_document_id", ""),
            "section": cand.get("section", ""),
            "pool": pool,
            "timestamp": datetime.utcnow().isoformat(),
        }
        adjudicated_records.append(rec)

        # Audit event
        audit_events.append({
            "event_type": "third_model_adjudication",
            "candidate_id": qid,
            "pool": pool,
            "verifier_c_evaluation": eval_c.to_dict(),
            "final_status": final_status.value,
            "failures": failures,
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat(),
        })

    # Save CSV
    fieldnames = list(adjudicated_records[0].keys())
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(adjudicated_records)
    print(f"\nSaved adjudicated CSV to {OUT_CSV}")

    # Save audit JSONL
    with open(OUT_AUDIT, "w", encoding="utf-8") as f:
        for ev in audit_events:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    print(f"Saved audit log to {OUT_AUDIT}")

    # Summarize
    counts = {}
    for r in adjudicated_records:
        st = r["final_status"]
        counts[st] = counts.get(st, 0) + 1
    print("\n=== ADJUDICATION SUMMARY (39 CANDIDATES) ===")
    for st, c in sorted(counts.items()):
        print(f"  {st:16}: {c:2d} ({c/len(adjudicated_records)*100:5.1f}%)")


if __name__ == "__main__":
    main()

