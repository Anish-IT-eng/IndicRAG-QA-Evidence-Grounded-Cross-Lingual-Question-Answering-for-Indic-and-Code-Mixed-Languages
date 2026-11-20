"""
IndicRAG-QA — R6 Stage 2.1 Regression Evaluation Suite
Executes 8 comprehensive scenarios verifying multilingual event alignment, calendar reconciliation,
negative constraint enforcement, ambiguity handling, and citation integrity.

Scenarios:
1. English: When do odd semester end semester examinations start and finish?
2. Devanagari Hindi: विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?
3. Romanized Hindi: Visham semester ki antim pariksha kab shuru aur samapt hoti hai?
4. Code-Mixed Hinglish: Odd semester examinations ki start date aur end date kya hai?
5. Make-up Exam Query: Must NOT select regular odd semester exam (10-12-2026).
6. Even Semester Registration Query: Must NOT select odd semester regular exam.
7. Ambiguous Query: Must abstain / request clarification, NOT guess.
8. Citation Validation Check: Citations must strictly reference Academic-Calendar-2026-27.pdf, Page 4 or 5.

Saves granular results and telemetry to:
docs/r6_stage2_1_test_results.json
"""
import sys
import time
import json
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

sys.path.insert(0, str(Path("backend").resolve()))

from app.core.config import settings
from app.query.processor import process_query
from app.retrieval.multi_hop_reasoner import MultiHopReasoner
from app.generation.generator import generate_answer
from app.models.schemas import EvidenceStatus, ResponseStatus

SCENARIOS = [
    {
        "id": "scenario_1_english",
        "name": "English Odd Semester End Exam",
        "query": "When do odd semester end semester examinations start and finish?",
        "expected_event": "Odd Semester End Semester Examination",
        "must_contain": ["10-12-2026", "22-12-2026"],
        "must_not_contain": ["25-01-2027", "01-07-2026"],
        "expected_page": [4, 5],
        "allow_abstention": False,
    },
    {
        "id": "scenario_2_devanagari_hindi",
        "name": "Devanagari Hindi Odd Semester End Exam",
        "query": "विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?",
        "expected_event": "Odd Semester End Semester Examination",
        "must_contain": ["10-12-2026", "22-12-2026"],
        "must_not_contain": ["25-01-2027", "01-07-2026"],
        "expected_page": [4, 5],
        "allow_abstention": False,
    },
    {
        "id": "scenario_3_romanized_hindi",
        "name": "Romanized Hindi Odd Semester End Exam",
        "query": "Visham semester ki antim pariksha kab shuru aur samapt hoti hai?",
        "expected_event": "Odd Semester End Semester Examination",
        "must_contain": ["10-12-2026", "22-12-2026"],
        "must_not_contain": ["25-01-2027", "01-07-2026"],
        "expected_page": [4, 5],
        "allow_abstention": False,
    },
    {
        "id": "scenario_4_hinglish",
        "name": "Code-Mixed Hinglish Odd Semester End Exam",
        "query": "Odd semester examinations ki start date aur end date kya hai?",
        "expected_event": "Odd Semester End Semester Examination",
        "must_contain": ["10-12-2026", "22-12-2026"],
        "must_not_contain": ["25-01-2027", "01-07-2026"],
        "expected_page": [4, 5],
        "allow_abstention": False,
    },
    {
        "id": "scenario_5_makeup_exam",
        "name": "Odd Semester Make-up Examination",
        "query": "When are the odd semester make-up examinations held?",
        "expected_event": "Make-up Examination",
        "must_contain": ["2027"],
        "must_not_contain": ["10-12-2026 to 22-12-2026", "start on 10-12-2026"],
        "expected_page": [4, 5],
        "allow_abstention": False,
    },
    {
        "id": "scenario_6_registration",
        "name": "Even Semester Registration",
        "query": "When does registration for even semester start?",
        "expected_event": "Registration",
        "must_contain": ["28-12-2026"],
        "must_not_contain": ["10-12-2026", "22-12-2026"],
        "expected_page": [4, 5],
        "allow_abstention": False,
    },
    {
        "id": "scenario_7_ambiguous_exam",
        "name": "Ambiguous Examination Query",
        "query": "When are the examinations?",
        "expected_event": "Ambiguous",
        "must_contain": [],
        "must_not_contain": [],
        "expected_page": [],
        "allow_abstention": True,
    },
    {
        "id": "scenario_8_citation_validation",
        "name": "Strict Citation Provenance Check",
        "query": "What are the start and finish dates for Odd Semester End Semester Examinations 2026-27?",
        "expected_event": "Odd Semester End Semester Examination",
        "must_contain": ["10-12-2026", "22-12-2026"],
        "must_not_contain": [],
        "expected_page": [4, 5],
        "allow_abstention": False,
    },
]

async def run_regression():
    print("=" * 70)
    print("INDICRAG-QA — R6 STAGE 2.1 REGRESSION EVALUATION SUITE (8 SCENARIOS)")
    print("=" * 70)

    reasoner = MultiHopReasoner(max_hops=3, max_evidence_items=12)
    results = []

    for idx, sc in enumerate(SCENARIOS, 1):
        sc_id = sc["id"]
        name = sc["name"]
        q = sc["query"]
        print(f"\n[{idx}/8] Scenario: {name} ({sc_id})")
        print(f"Query: {q}")
        await asyncio.sleep(0.5)

        t0_total = time.perf_counter()

        # Step 1: Query processing
        t0_proc = time.perf_counter()
        qa = process_query(q)
        proc_ms = (time.perf_counter() - t0_proc) * 1000

        # Step 2: Multi-Hop Reasoning
        t0_reason = time.perf_counter()
        ev_set = reasoner.reason(query_analysis=qa)
        reason_ms = (time.perf_counter() - t0_reason) * 1000
        decision = reasoner.to_evidence_decision(ev_set)

        # Step 3: Generation
        t0_gen = time.perf_counter()
        retry_triggered = False
        resp = None
        try:
            resp = await generate_answer(query_analysis=qa, evidence_decision=decision)
            if resp is None or resp.status == ResponseStatus.ERROR or not resp.answer:
                retry_triggered = True
                print("First generation attempt failed/empty; retrying once...")
                await asyncio.sleep(1.0)
                resp = await generate_answer(query_analysis=qa, evidence_decision=decision)
        except Exception as exc:
            retry_triggered = True
            print(f"Generation error ({exc}); retrying once...")
            await asyncio.sleep(1.0)
            resp = await generate_answer(query_analysis=qa, evidence_decision=decision)

        gen_ms = (time.perf_counter() - t0_gen) * 1000
        total_ms = (time.perf_counter() - t0_total) * 1000

        answer = (resp.answer or "") if resp else ""
        citations = resp.citations if resp else []
        abstained = (
            resp is None
            or resp.status in (ResponseStatus.UNANSWERABLE, ResponseStatus.CLARIFICATION_NEEDED)
            or "UNANSWERABLE" in answer.upper()
            or "CLARIFICATION" in answer.upper()
            or "AMBIGUOUS" in answer.upper()
        )

        # Verify negative constraints
        violated_negative = [bad for bad in sc["must_not_contain"] if bad.lower() in answer.lower()]
        
        # Verify positive constraints
        matched_positive = [good for good in sc["must_contain"] if good.lower() in answer.lower()]
        passed_positive = (len(matched_positive) == len(sc["must_contain"]))

        # Verify citations
        valid_citations = [
            c for c in citations
            if "calendar" in (c.filename or "").lower()
            and (not sc["expected_page"] or c.page in sc["expected_page"])
        ]
        citation_valid = (
            (len(citations) > 0 and len(valid_citations) == len(citations))
            if not sc["allow_abstention"] and not abstained
            else True
        )

        # Verdict
        if sc_id == "scenario_7_ambiguous_exam":
            # For ambiguous query, passing means abstaining or asking for clarification or disclosing ambiguity
            passed = (abstained or "specify" in answer.lower() or "clarification" in answer.lower() or "ambiguous" in answer.lower() or "which" in answer.lower() or "clarify" in answer.lower())
        else:
            passed = (
                not violated_negative
                and passed_positive
                and (sc["allow_abstention"] or not abstained)
                and citation_valid
                and len(ev_set.all_passages) <= 12
            )

        print(f"Status: {'PASS' if passed else 'FAIL'}")
        print(f"Answer: {answer[:180]}...")
        print(f"Citations: {[{'fn': c.filename, 'page': c.page, 'pid': c.passage_id[:16]} for c in citations]}")
        print(f"Telemetry: Reasoning={reason_ms:.1f}ms | Gen={gen_ms:.1f}ms | Total={total_ms:.1f}ms | Retry={retry_triggered}")

        results.append({
            "scenario_id": sc_id,
            "scenario_name": name,
            "query": q,
            "detected_language": str(qa.detected_language),
            "detected_script": str(qa.detected_script),
            "normalized_query": qa.normalized_query,
            "status": "PASS" if passed else "FAIL",
            "evidence_passages_count": len(ev_set.all_passages),
            "boundary_enforced": len(ev_set.all_passages) <= 12,
            "traversal_hops": ev_set.max_depth_reached,
            "edges_traversed": ev_set.total_edges_traversed,
            "answer": answer,
            "citations_count": len(citations),
            "valid_citations_count": len(valid_citations),
            "citations": [{"filename": c.filename, "page": c.page, "passage_id": c.passage_id} for c in citations],
            "abstained": abstained,
            "positive_matches": matched_positive,
            "negative_violations": violated_negative,
            "telemetry": {
                "retrieval_reasoning_ms": round(reason_ms, 2),
                "generation_ms": round(gen_ms, 2),
                "total_elapsed_ms": round(total_ms, 2),
                "retry_triggered": retry_triggered,
            }
        })

    all_passed = all(r["status"] == "PASS" for r in results)
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    print("\n" + "=" * 70)
    print(f"STAGE 2.1 REGRESSION SUMMARY: {pass_count} / 8 SCENARIOS PASSED ({'ALL PASSED' if all_passed else 'FAILURES DETECTED'})")
    print("=" * 70)

    out_file = Path("docs/r6_stage2_1_test_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "stage": "R6 Stage 2.1 — Multilingual Event Alignment Repair Regression",
            "total_scenarios": len(results),
            "passed_scenarios": pass_count,
            "all_passed": all_passed,
            "scenarios": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved results to {out_file}")

asyncio.run(run_regression())
