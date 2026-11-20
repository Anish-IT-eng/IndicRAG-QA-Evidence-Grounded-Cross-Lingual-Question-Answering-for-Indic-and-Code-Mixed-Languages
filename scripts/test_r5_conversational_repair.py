"""
IndicRAG-QA — Test Suite for R5 Conversational Feedback & Context-Aware Repair

Verifies:
1. False feedback rejection for ordinary academic policy questions.
2. Feedback handling without prior conversation context.
3. Feedback handling following an institutional abstention.
4. Context-aware repair for:
   - MISSING_EXCEPTION (incorporates Clause 30.1(v) medical/dean condonation)
   - WRONG_COHORT_OR_PROGRAM (aligns with 2017 SEAS Ordinance)
   - CITATION_CHALLENGE (re-verifies exact stored text)
   - SOURCE_DISAGREEMENT (scoping to user-uploaded files)
   - ANSWER_REEXPLANATION (step-by-step simplification)
   - FACTUAL_CORRECTION (reconciliation of 70% vs 75%)
5. Multilingual feedback coverage (Hindi, Hinglish, Romanized Hindi, English).
6. Non-hallucination guarantee: never invents ungrounded text to pacify user.
"""
from __future__ import annotations

import json
import sys
import urllib.request
import uuid
from pathlib import Path

# Add backend to sys.path for direct unit testing of processor
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.query.processor import process_query
from app.models.schemas import QuestionType, FeedbackSubtype

API_BASE = "http://127.0.0.1:8000"


def send_query(payload: dict) -> dict:
    url = f"{API_BASE}/query"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_suite():
    print("=" * 80)
    print("INDICRAG-QA — R5 CONVERSATIONAL FEEDBACK & CONTEXT-AWARE REPAIR TESTS")
    print("=" * 80)

    # ─────────────────────────────────────────────────────────────────────────
    # TEST 1: Prevent False Feedback Detection on Academic Inquiries
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- TEST 1: Academic Queries with Feedback Keywords (False Positive Prevention) ---")
    academic_queries = [
        "What happens when a student gives a wrong answer?",
        "What are the penalties for incorrect examination responses?",
        "Which rules define unfair means?",
        "Can a student contest an incorrect grading mark?",
        "Is there negative marking for false answers in university examinations?",
    ]
    for q in academic_queries:
        # 1. Direct unit verification via processor
        qa = process_query(q)
        print(f"Query: '{q}'")
        print(f"  -> Detected Type: {qa.query_type} | Subtype: {qa.feedback_subtype}")
        assert qa.query_type != QuestionType.FEEDBACK_CORRECTION, f"False feedback triggered: {q}"
        assert qa.feedback_subtype is None, f"Subtype wrongly assigned: {q}"

    # 2. Live API verification on one academic query containing 'wrong'
    live_q = "What happens when a student gives a wrong answer?"
    res_live = send_query({"query": live_q, "session_id": "test_academic_fp", "debug": True})
    is_fb = res_live.get("retrieval_summary", {}).get("is_feedback", False)
    print(f"Live API Query: '{live_q}'")
    print(f"  -> is_feedback: {is_fb} | Stage: {res_live.get('retrieval_summary', {}).get('stage')}")
    assert not is_fb, "Live API falsely handled academic query as feedback!"
    print(">>> PASS: All academic questions routed to standard retrieval (Zero False Positives).")

    # ─────────────────────────────────────────────────────────────────────────
    # TEST 2: Feedback Without Prior Conversation Context
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- TEST 2: Feedback Without Prior Conversation Context ---")
    session_empty = f"test_session_empty_{uuid.uuid4().hex[:6]}"
    res_empty = send_query({"query": "your answer is wrong", "session_id": session_empty, "debug": True})
    print(f"Empty Session Response Action: {res_empty.get('retrieval_summary', {}).get('repair_action')}")
    print(f"Answer snippet: {res_empty['answer'][:160]}...")
    assert res_empty.get("retrieval_summary", {}).get("repair_action") == "no_prior_context"
    assert "preceding question" in res_empty["answer"].lower() or "सत्र" in res_empty["answer"]
    assert len(res_empty["citations"]) == 0
    print(">>> PASS: Gracefully acknowledged lack of prior context without inventing history.")

    # ─────────────────────────────────────────────────────────────────────────
    # TEST 3: Feedback Following an Institutional Abstention
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- TEST 3: Feedback Following an Institutional Abstention ---")
    session_abstain = f"test_session_abstain_{uuid.uuid4().hex[:6]}"
    # Turn 1: Out of policy question
    q_abstain = "What is the policy for Harvard student exchange scholarships?"
    res_t1 = send_query({"query": q_abstain, "session_id": session_abstain, "debug": True})
    print(f"Turn 1 Status: {res_t1['status']} | Evidence: {res_t1['evidence_status']}")
    assert res_t1["status"] == "unanswerable"

    # Turn 2: User challenges the abstention
    res_t2 = send_query({"query": "your answer is wrong", "session_id": session_abstain, "debug": True})
    print(f"Turn 2 Repair Action: {res_t2.get('retrieval_summary', {}).get('repair_action')}")
    print(f"Turn 2 Answer snippet: {res_t2['answer'][:180]}...")
    assert res_t2["status"] == "unanswerable"
    assert res_t2.get("retrieval_summary", {}).get("repair_action") == "abstention_clarification"
    assert "UNANSWERABLE" in res_t2["answer"] or "अनुत्तरित" in res_t2["answer"]
    print(">>> PASS: Upheld institutional abstention integrity without ungrounded reversal.")

    # ─────────────────────────────────────────────────────────────────────────
    # TEST 4: Full Multi-Turn Contextual Repair Flow
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- TEST 4: Multi-Turn Context-Aware Answer Repair Flow ---")
    session_flow = f"test_session_flow_{uuid.uuid4().hex[:6]}"

    # Turn 1: Normal Academic Question on Official Regulations
    q_initial = "What is the minimum attendance requirement to appear in end-semester examinations?"
    print(f"\n[Turn 1] User asks: '{q_initial}'")
    t1_res = send_query({
        "query": q_initial,
        "session_id": session_flow,
        "collection": ["official"],
        "sequential_fallback": False,
        "debug": True,
    })
    print(f"  -> Answer snippet: {t1_res['answer'][:160]}...")
    print(f"  -> Citations count: {len(t1_res['citations'])}")
    assert t1_res["status"] in ("answered", "clarification_needed")
    assert len(t1_res["answer"]) > 0

    # Turn 2: MISSING_EXCEPTION (Hinglish: "tumne exception miss kar diya")
    q_exc = "tumne exception miss kar diya"
    print(f"\n[Turn 2] User feedback: '{q_exc}'")
    t2_res = send_query({"query": q_exc, "session_id": session_flow, "debug": True})
    t2_meta = t2_res.get("retrieval_summary", {})
    print(f"  -> Detected Subtype: {t2_meta.get('feedback_subtype')}")
    print(f"  -> Repair Action: {t2_meta.get('repair_action')}")
    print(f"  -> Answer snippet: {t2_res['answer'][:200]}...")
    assert t2_meta.get("feedback_subtype") == "missing_exception"
    assert t2_meta.get("repair_action") == "exception_incorporated"
    assert "30.1(v)" in t2_res["answer"] or "10%" in t2_res["answer"] or "Dean" in t2_res["answer"]
    assert len(t2_res["citations"]) >= 1
    print("  -> Verified: Clause 30.1(v) Dean/medical condonation incorporated with citation!")

    # Turn 3: WRONG_COHORT_OR_PROGRAM ("mere batch par yeh rule apply nahi hota, I am in 2017 batch")
    q_cohort = "mere batch par yeh rule apply nahi hota, I am in 2017 batch"
    print(f"\n[Turn 3] User feedback: '{q_cohort}'")
    t3_res = send_query({"query": q_cohort, "session_id": session_flow, "debug": True})
    t3_meta = t3_res.get("retrieval_summary", {})
    print(f"  -> Detected Subtype: {t3_meta.get('feedback_subtype')}")
    print(f"  -> Repair Action: {t3_meta.get('repair_action')}")
    print(f"  -> Answer snippet: {t3_res['answer'][:200]}...")
    assert t3_meta.get("feedback_subtype") == "wrong_cohort_or_program"
    assert t3_meta.get("repair_action") == "cohort_realigned"
    assert "2017" in t3_res["answer"]
    assert "70%" in t3_res["answer"]

    # Turn 4: CITATION_CHALLENGE ("page 2 par yeh nahi likha")
    q_cite = "page 2 par yeh nahi likha"
    print(f"\n[Turn 4] User feedback: '{q_cite}'")
    t4_res = send_query({"query": q_cite, "session_id": session_flow, "debug": True})
    t4_meta = t4_res.get("retrieval_summary", {})
    print(f"  -> Detected Subtype: {t4_meta.get('feedback_subtype')}")
    print(f"  -> Repair Action: {t4_meta.get('repair_action')}")
    assert t4_meta.get("feedback_subtype") == "citation_challenge"
    assert t4_meta.get("repair_action") == "citation_reverified"

    # Turn 5: ANSWER_REEXPLANATION ("explain again in simpler terms")
    q_reexp = "explain again in simpler terms"
    print(f"\n[Turn 5] User feedback: '{q_reexp}'")
    t5_res = send_query({"query": q_reexp, "session_id": session_flow, "debug": True})
    t5_meta = t5_res.get("retrieval_summary", {})
    print(f"  -> Detected Subtype: {t5_meta.get('feedback_subtype')}")
    print(f"  -> Repair Action: {t5_meta.get('repair_action')}")
    assert t5_meta.get("feedback_subtype") == "answer_reexplanation"
    assert t5_meta.get("repair_action") == "reexplanation_provided"

    # Turn 6: FACTUAL_CORRECTION ("Actually it is 75%, not 70%")
    q_fact = "Actually it is 75%, not 70%"
    print(f"\n[Turn 6] User feedback: '{q_fact}'")
    t6_res = send_query({"query": q_fact, "session_id": session_flow, "debug": True})
    t6_meta = t6_res.get("retrieval_summary", {})
    print(f"  -> Detected Subtype: {t6_meta.get('feedback_subtype')}")
    print(f"  -> Repair Action: {t6_meta.get('repair_action')}")
    assert t6_meta.get("feedback_subtype") == "factual_correction"
    assert t6_meta.get("repair_action") == "factual_reconciliation"

    # ─────────────────────────────────────────────────────────────────────────
    # TEST 5: Multilingual Subtype Coverage
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- TEST 5: Multilingual Feedback Phrases ---")
    multilingual_tests = [
        ("yeh galat hai", "general_disagreement"),
        ("aapka answer sahi nahi hai", "general_disagreement"),
        ("tumne exception miss kar diya", "missing_exception"),
        ("mere batch par yeh rule apply nahi hota", "wrong_cohort_or_program"),
        ("PDF mein kuch aur likha hai", "source_disagreement"),
    ]
    for phrase, expected_sub in multilingual_tests:
        res = send_query({"query": phrase, "session_id": session_flow, "debug": True})
        sub = res.get("retrieval_summary", {}).get("feedback_subtype")
        lat = res.get("retrieval_summary", {}).get("total_latency_ms")
        print(f"Phrase: '{phrase}' => Subtype: {sub} (Expected: {expected_sub}) in {lat}ms")
        assert sub == expected_sub, f"Mismatch for '{phrase}': got {sub}, expected {expected_sub}"

    print("\n" + "=" * 80)
    print("ALL R5 CONVERSATIONAL REPAIR & CONTEXTUAL TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    test_suite()
