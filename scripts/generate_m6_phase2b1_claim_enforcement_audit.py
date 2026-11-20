import csv
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
out_dir = backend_dir / "data/experiments/m6"

claim_csv = out_dir / "m6_phase2b_claim_grounding.csv"
eval_csv = out_dir / "m6_phase2b_query_eval.csv"
qual_csv = backend_dir / "data/dataset/m6_benchmark_qualification.csv"
out_audit_csv = out_dir / "m6_phase2b1_claim_enforcement_audit.csv"

with open(claim_csv, "r", encoding="utf-8") as f:
    claims = list(csv.DictReader(f))

with open(eval_csv, "r", encoding="utf-8") as f:
    eval_map = {r["candidate_id"]: r for r in csv.DictReader(f)}

with open(qual_csv, "r", encoding="utf-8") as f:
    qual_map = {r["candidate_id"]: r for r in csv.DictReader(f)}

audit_rows = []

for c in claims:
    cid = c["candidate_id"]
    eval_row = eval_map.get(cid, {})
    qual_row = qual_map.get(cid, {})
    
    q_text = eval_row.get("original_question", qual_row.get("original_question", ""))
    gold_ans = eval_row.get("gold_answerability", qual_row.get("answerability", ""))
    ctrl_status = eval_row.get("controller_status", "unknown")
    verdict = c["verdict"]
    
    # In the architecture:
    # If controller_status == "insufficient" or "missing" or "clarification_required":
    #   The controller abstains; generator outputs UNANSWERABLE -> claim was suppressed from final user answer!
    # If controller_status == "conflicting":
    #   generator outputs ResponseStatus.CONFLICTING_VERSIONS -> answer is returned with disclosure!
    # If controller_status == "partial":
    #   generator outputs ResponseStatus.ANSWERED (partial) -> answer is returned!
    # If controller_status == "sufficient":
    #   generator outputs ResponseStatus.ANSWERED -> answer is returned!
    
    ctrl_abstained = ctrl_status in ("insufficient", "missing", "clarification_required")
    appeared_in_answer = not ctrl_abstained
    was_suppressed = ctrl_abstained
    downgraded = (ctrl_status == "partial")
    
    # Citation marked supported: in generator.py, citation.claim_supported is set to:
    # not claim_res.contains_contradiction and (claim_res.grounding_ratio >= 0.4 or claim_res.total_claims == 0)
    # If this specific claim was CONTRADICTED, the citation must NOT be marked supported!
    has_contradiction = (eval_row.get("contradicted_claims", "0") != "0")
    citation_marked_supported = (not has_contradiction) and (float(eval_row.get("grounding_ratio", 0.0)) >= 0.4)
    
    if appeared_in_answer:
        if verdict == "CONTRADICTED":
            enforcement = "LEAKAGE_HAZARD: Contradicted claim appeared in final response (governed by CONFLICTING disclosure or PARTIAL answer)."
        elif verdict == "INSUFFICIENT_SUPPORT":
            enforcement = "POTENTIAL_UNGROUNDED: Claim lacking direct verbatim support appeared in final response."
        else:
            enforcement = "VERIFIED_SAFE: Entailed claim properly grounded in official evidence."
    else:
        if verdict in ("CONTRADICTED", "INSUFFICIENT_SUPPORT"):
            enforcement = "SUCCESSFULLY_SUPPRESSED: Flawed/unsupported claim blocked by controller abstention."
        else:
            enforcement = "CONSERVATIVE_ABSTENTION: Valid claim suppressed due to conservative controller gating."

    audit_rows.append({
        "candidate_id": cid,
        "cohort_group": c["cohort_group"],
        "claim_id": c["claim_id"],
        "claim_text": c["claim_text"],
        "verdict": verdict,
        "numeric_verified": c["numeric_verified"],
        "date_verified": c["date_verified"],
        "negation_verified": c["negation_verified"],
        "semantic_entailed": c["semantic_entailed"],
        "discrepancies": c.get("discrepancies", ""),
        "explanation": c.get("explanation", ""),
        "query_text": q_text,
        "gold_answerability": gold_ans,
        "controller_status": ctrl_status,
        "appeared_in_final_answer": appeared_in_answer,
        "was_suppressed": was_suppressed,
        "answer_downgraded_to_partial": downgraded,
        "controller_abstained": ctrl_abstained,
        "citation_marked_supported": citation_marked_supported,
        "enforcement_audit_summary": enforcement,
    })

with open(out_audit_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(audit_rows[0].keys()))
    w.writeheader()
    w.writerows(audit_rows)

print(f"Wrote {len(audit_rows)} claim enforcement audit rows to {out_audit_csv}")

