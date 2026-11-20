"""
Live Evaluation Script for M8.5: Regulatory-Aware Evidence Controller.
Runs the 7 M8.3 attendance queries against the live SQLite DB and FAISS index,
captures complete decision traces, and outputs CSV and JSON artifacts.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

# Add backend root to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.models.schemas import DocumentSource, EvidenceStatus
from app.query.processor import process_query
from app.retrieval.engine import retrieve, get_official_index
from app.retrieval.evidence_controller import get_evidence_controller
from app.retrieval.regulatory_classifier import classify_regulatory_relationship

# 7 M8.3 Attendance Queries
M83_QUERIES = [
    {
        "query_id": "AQ-01",
        "query_text": "What is the minimum attendance required?",
        "target_condition": "COURSE_GRADING & EXAM_ELIGIBILITY",
        "temporal_anchor": "UNANCHORED",
        "expected_state": "CLARIFICATION_REQUIRED",
    },
    {
        "query_id": "AQ-02",
        "query_text": "What attendance is required to sit for end semester exams?",
        "target_condition": "EXAM_ELIGIBILITY",
        "temporal_anchor": "CURRENT_DEFAULT",
        "expected_state": "SUFFICIENT",
    },
    {
        "query_id": "AQ-03",
        "query_text": "How much attendance is required to avoid an X grade?",
        "target_condition": "COURSE_GRADING",
        "temporal_anchor": "CURRENT_DEFAULT",
        "expected_state": "SUFFICIENT",
    },
    {
        "query_id": "AQ-04",
        "query_text": "Is 70% attendance enough?",
        "target_condition": "COURSE_GRADING & EXAM_ELIGIBILITY",
        "temporal_anchor": "CURRENT_DEFAULT",
        "expected_state": "SUFFICIENT",
    },
    {
        "query_id": "AQ-05",
        "query_text": "Is 75% compulsory for SCSET students?",
        "target_condition": "EXAM_ELIGIBILITY",
        "temporal_anchor": "CURRENT_DEFAULT",
        "expected_state": "SUFFICIENT",
    },
    {
        "query_id": "AQ-06",
        "query_text": "What was the attendance rule in 2017?",
        "target_condition": "HISTORICAL_RULE",
        "temporal_anchor": "2017",
        "expected_state": "SUFFICIENT",
    },
    {
        "query_id": "AQ-07",
        "query_text": "Can attendance be relaxed due to medical reasons?",
        "target_condition": "MEDICAL_CONDONATION",
        "temporal_anchor": "CURRENT_DEFAULT",
        "expected_state": "SUFFICIENT",
    },
]

def run_evaluation():
    print("Loading retrieval indexes...")
    idx = get_official_index()
    print(f"Loaded official index: {len(idx.passage_ids)} passages ready={idx.is_ready()}")
    controller = get_evidence_controller()

    csv_rows = []
    traces = []

    print(f"\nEvaluating {len(M83_QUERIES)} queries...")
    for item in M83_QUERIES:
        qid = item["query_id"]
        qtext = item["query_text"]
        print(f"--- Running {qid}: '{qtext}' ---")

        # 1. Process query
        qa = process_query(qtext)

        # 2. Retrieve official documents
        rr = retrieve(
            query_analysis=qa,
            collections=[DocumentSource.OFFICIAL],
            top_k=8,
            use_reranker=True,
            use_mqr=False,
            use_pdr=True,
        )

        # 3. Evaluate evidence
        dec = controller.evaluate(rr)

        # Classify pairwise relationships between top passages
        pair_relationships = []
        passages = dec.valid_passages or rr.retrieved_passages
        for i in range(min(3, len(passages))):
            for j in range(i + 1, min(3, len(passages))):
                rel = classify_regulatory_relationship(passages[i], passages[j], qa)
                pair_relationships.append({
                    "passage_a": passages[i].passage_id,
                    "doc_a": passages[i].document_id,
                    "passage_b": passages[j].passage_id,
                    "doc_b": passages[j].document_id,
                    "relationship": rel.value,
                })

        # Check pass/fail against acceptance criteria
        expected_state = item["expected_state"]
        actual_state = dec.status.value
        passed = False
        if expected_state == "CLARIFICATION_REQUIRED":
            passed = actual_state in ("clarification_required", "multi_condition_disclosure")
        elif expected_state == "SUFFICIENT":
            passed = actual_state == "sufficient"

        citations = []
        for p in (dec.valid_passages or passages)[:3]:
            sec = p.section or p.heading or "General"
            citations.append(f"{p.document_id} ({sec})")
        citations_str = "; ".join(citations)

        csv_rows.append({
            "query_id": qid,
            "query_text": qtext,
            "target_condition": item["target_condition"],
            "temporal_anchor": item["temporal_anchor"],
            "expected_state": expected_state,
            "controller_state": actual_state,
            "ceci_score": round(dec.ceci_score, 4) if dec.ceci_score is not None else 0.0,
            "clarification_needed": dec.clarification_needed,
            "citations": citations_str,
            "pass_fail": "PASS" if passed else "FAIL",
            "explanation": dec.explanation,
        })

        traces.append({
            "query_id": qid,
            "query_text": qtext,
            "query_analysis": {
                "detected_language": qa.detected_language.value if qa.detected_language else None,
                "temporal_intent_mode": qa.temporal_intent_mode.value if qa.temporal_intent_mode else None,
                "target_cohort": qa.target_cohort,
                "target_academic_year": qa.target_academic_year,
                "target_programme": qa.target_programme,
                "target_conditions": [c.value for c in qa.target_conditions] if qa.target_conditions else [],
            },
            "retrieved_passages_summary": [
                {
                    "passage_id": p.passage_id,
                    "document_id": p.document_id,
                    "score": round(p.score, 4),
                    "rerank_score": round(p.rerank_score, 4) if p.rerank_score is not None else None,
                    "section": p.section or p.heading,
                    "condition": p.regulatory_condition.value if p.regulatory_condition else None,
                    "version_flag": getattr(p, "_version_flag", None),
                }
                for p in rr.retrieved_passages[:5]
            ],
            "regulatory_relationships": pair_relationships,
            "decision": {
                "status": dec.status.value,
                "ceci_score": round(dec.ceci_score, 4) if dec.ceci_score is not None else 0.0,
                "coverage_score": round(dec.coverage_score, 4) if dec.coverage_score is not None else 0.0,
                "clarification_needed": dec.clarification_needed,
                "explanation": dec.explanation,
                "detected_conditions": [c.value for c in dec.detected_conditions] if dec.detected_conditions else [],
            },
            "evaluation_outcome": "PASS" if passed else "FAIL",
        })

    # Save CSV
    out_dir = backend_dir / "data" / "experiments" / "m8"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "m8_5_controller_test_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "query_id", "query_text", "target_condition", "temporal_anchor",
            "expected_state", "controller_state", "ceci_score", "clarification_needed",
            "citations", "pass_fail", "explanation",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Saved CSV results to {csv_path}")

    # Save JSON traces
    json_path = out_dir / "m8_5_regulatory_decision_traces.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(traces, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON traces to {json_path}")

    print("\n--- Summary of Results ---")
    for r in csv_rows:
        print(f"[{r['pass_fail']}] {r['query_id']} ({r['expected_state']} -> {r['controller_state']}) CECI={r['ceci_score']}")

if __name__ == "__main__":
    run_evaluation()

