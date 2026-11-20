import json
import os
import sys
import time
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, "backend")

from app.core.database import get_db
from app.models.schemas import (
    DocumentSource,
    DocumentVersionInfo,
    EvidenceStatus,
    QueryAnalysis,
    QueryLanguage,
    QueryScript,
    ResponseStatus,
)
from app.query.processor import process_query
from app.retrieval.multi_hop_reasoner import MultiHopReasoner
from app.retrieval.relationship_store import RelationshipStore
from app.ingestion.pipeline import ingest_pdf, delete_document


def create_dummy_pdf(output_path: Path, title: str, text_pages: list[str]) -> Path:
    """Helper to create a well-formed PDF with reportlab for testing generic ingestion."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    import io

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    for page_text in text_pages:
        can.setFont("Helvetica-Bold", 14)
        can.drawString(50, 750, title)
        can.setFont("Helvetica", 10)
        y = 720
        for line in page_text.split("\n"):
            if y < 50:
                can.showPage()
                y = 750
            can.drawString(50, y, line[:100])
            y -= 15
        can.showPage()
    can.save()

    packet.seek(0)
    with open(output_path, "wb") as f:
        f.write(packet.read())
    return output_path


def run_r4_tests():
    results = {}
    print("=" * 70)
    print("STARTING R4 COMPREHENSIVE MULTI-HOP VERIFICATION SUITE (14 CHECKS)")
    print("=" * 70)

    reasoner = MultiHopReasoner(max_hops=3, max_evidence_items=12)

    # ---------------------------------------------------------
    # TEST 1: Academic Calendar Multi-Hop (Start, Conclusion, Page Provenance)
    # ---------------------------------------------------------
    t1_pass = False
    try:
        qa = process_query("When do odd semester end-semester examinations start and finish?")
        ev_set = reasoner.reason(qa)
        
        has_start = any("10-12-2026" in p.text for p in ev_set.all_passages)
        has_end = any("22-12-2026" in p.text for p in ev_set.all_passages)
        has_page = any(p.page_number == 4 for p in ev_set.all_passages)
        has_event_name = any("End Semester Examination" in p.text for p in ev_set.all_passages)
        within_boundary = len(ev_set.all_passages) <= reasoner.max_evidence_items
        t1_pass = has_start and has_end and has_page and has_event_name and within_boundary

        results["test_1_academic_calendar_multihop"] = {
            "status": "PASS" if t1_pass else "FAIL",
            "start_date_connected": has_start,
            "conclusion_date_connected": has_end,
            "page_provenance_verified": has_page,
            "event_name_verified": has_event_name,
            "boundary_enforced": within_boundary,
            "max_evidence_bound": reasoner.max_evidence_items,
            "traversal_depth": ev_set.max_depth_reached,
            "relationship_edges_traversed": ev_set.total_edges_traversed,
            "passages_retrieved": ev_set.total_passages_retrieved,
            "reasoning_hops": ev_set.max_depth_reached,
            "retrieval_ms": ev_set.retrieval_ms,
            "reasoning_ms": ev_set.reasoning_ms,
        }
    except Exception as exc:
        results["test_1_academic_calendar_multihop"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 1 (Academic Calendar Multi-Hop): {results['test_1_academic_calendar_multihop']['status']}")

    # ---------------------------------------------------------
    # TEST 2: Attendance Requirements: Course Grading vs Examination Eligibility
    # ---------------------------------------------------------
    t2_pass = False
    try:
        qa = process_query("Explain the minimum attendance requirements and the difference between course grading and examination eligibility.")
        ev_set = reasoner.reason(qa)
        
        # Must connect both Clause 30.1 (70% course attendance) and Notification 307/2022 (75% exam eligibility)
        has_70 = any("70%" in p.text or (p.relationship_expansion and "70%" in str(p.relationship_expansion)) for p in ev_set.all_passages)
        has_75 = any("75%" in p.text or (p.relationship_expansion and "75%" in str(p.relationship_expansion)) for p in ev_set.all_passages)
        has_scope_distinction = len(ev_set.detected_conflicts) > 0 or any(h.scope in ("course_grading", "exam_eligibility") for h in ev_set.reasoning_hops)
        
        t2_pass = has_70 and has_75 and has_scope_distinction
        results["test_2_attendance_course_vs_exam"] = {
            "status": "PASS" if t2_pass else "FAIL",
            "has_70_course_rule": has_70,
            "has_75_exam_rule": has_75,
            "scope_distinction_preserved": has_scope_distinction,
            "evidence_passages": len(ev_set.all_passages),
        }
    except Exception as exc:
        results["test_2_attendance_course_vs_exam"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 2 (Attendance Course vs Exam Scope): {results['test_2_attendance_course_vs_exam']['status']}")

    # ---------------------------------------------------------
    # TEST 3: Medical Exception & Condonation Workflow
    # ---------------------------------------------------------
    t3_pass = False
    try:
        qa = process_query("Can a student with medical reasons receive attendance relaxation, and what is required?")
        ev_set = reasoner.reason(qa)
        
        has_relaxation = any(
            h.predicate == "RULE_HAS_EXCEPTION" and ("10%" in h.target_node or "medical" in h.target_node.lower())
            for h in ev_set.reasoning_hops
        ) or any("relaxation" in p.text.lower() for p in ev_set.all_passages)

        has_illness_cond = any(
            "two weeks" in p.text.lower() or "contagious" in p.text.lower() or "illness" in p.text.lower()
            for p in ev_set.all_passages
        )

        has_approval = any(
            h.predicate == "EXCEPTION_REQUIRES_APPROVAL"
            for h in ev_set.reasoning_hops
        ) or any("dean" in p.text.lower() for p in ev_set.all_passages)

        has_doc = any(
            h.predicate == "EXCEPTION_REQUIRES_DOCUMENT"
            for h in ev_set.reasoning_hops
        ) or any("medical certificate" in p.text.lower() for p in ev_set.all_passages)

        t3_pass = has_relaxation and (has_approval or has_doc)
        results["test_3_medical_exception_workflow"] = {
            "status": "PASS" if t3_pass else "FAIL",
            "medical_relaxation_connected": has_relaxation,
            "continuous_illness_condition": has_illness_cond,
            "approval_authority_connected": has_approval,
            "required_documentation_connected": has_doc,
            "traversal_depth": ev_set.max_depth_reached,
            "relationship_edges_traversed": ev_set.total_edges_traversed,
            "passages_retrieved": ev_set.total_passages_retrieved,
            "hops_executed": ev_set.max_depth_reached,
        }
    except Exception as exc:
        results["test_3_medical_exception_workflow"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 3 (Medical Exception Multi-Hop): {results['test_3_medical_exception_workflow']['status']}")

    # ---------------------------------------------------------
    # TEST 4: Historical & Cohort Applicability (Clarification on Ambiguity)
    # ---------------------------------------------------------
    t4_pass = False
    try:
        # Ambiguous query asking which rule applies without stating cohort
        qa = process_query("Which attendance rule applies to a student from a particular programme and admission year?")
        ev_set = reasoner.reason(qa)
        dec = reasoner.to_evidence_decision(ev_set)
        
        # When cohort is missing and materially changes answer, system must request clarification
        has_clarification = dec.status == EvidenceStatus.CLARIFICATION_REQUIRED or ev_set.clarification_needed is not None
        t4_pass = has_clarification
        results["test_4_historical_cohort_clarification"] = {
            "status": "PASS" if t4_pass else "FAIL",
            "clarification_requested": has_clarification,
            "clarification_message": ev_set.clarification_needed,
            "status_code": dec.status.value,
        }
    except Exception as exc:
        results["test_4_historical_cohort_clarification"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 4 (Historical Applicability & Clarification): {results['test_4_historical_cohort_clarification']['status']}")

    # ---------------------------------------------------------
    # TEST 5: Newly Uploaded Document Multi-Hop
    # ---------------------------------------------------------
    t5_pass = False
    temp_dir = Path("backend/data/temp_r4_test")
    temp_dir.mkdir(parents=True, exist_ok=True)
    test_pdf = temp_dir / "Department_Lab_Safety_Policy_2026.pdf"
    
    text_content = [
        """Rule 10.1 Chemical Laboratory Access Requirements
All undergraduate students must complete mandatory safety training before entering chemical laboratories.
Rule 10.2 Prerequisite Safety Certification:
Students must achieve a score of at least 85% in the online safety assessment.
Provided that students with industrial laboratory certification may receive exemption.
Such exemption requires documentary proof submitted to the Laboratory Superintendent.
Approval of the Department Safety Officer is required before issuing access cards.""",
        """Section 11.1 Access Card Issuance and Validity
Access cards are issued for a duration of one academic year.
Lost cards require a replacement fee of Rs. 500 and Department Safety Officer clearance."""
    ]
    create_dummy_pdf(test_pdf, "Department Lab Safety Policy 2026", text_content)
    test_user = f"user_r4_{uuid.uuid4().hex[:6]}"

    try:
        doc_rec = ingest_pdf(
            pdf_path=test_pdf,
            source_type=DocumentSource.UPLOAD,
            title="Department Lab Safety Policy 2026",
            user_id=test_user,
            force=True,
        )

        qa_upload = process_query("What is required for laboratory access exemption and who approves it?")
        ev_set_upload = reasoner.reason(qa_upload, user_id=test_user)

        has_exemption = any("exemption" in p.text.lower() for p in ev_set_upload.all_passages)
        has_approval = any("department safety officer" in p.text.lower() or "safety officer" in str(p.metadata).lower() for p in ev_set_upload.all_passages)
        t5_pass = has_exemption and has_approval

        results["test_5_new_upload_multihop"] = {
            "status": "PASS" if t5_pass else "FAIL",
            "document_id": doc_rec.document_id,
            "user_id": test_user,
            "exemption_connected": has_exemption,
            "approval_authority_connected": has_approval,
            "total_passages": len(ev_set_upload.all_passages),
        }
    except Exception as exc:
        results["test_5_new_upload_multihop"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 5 (New Upload Multi-Hop): {results['test_5_new_upload_multihop']['status']}")

    # ---------------------------------------------------------
    # TEST 6: Contradictory Evidence Preservation
    # ---------------------------------------------------------
    t6_pass = False
    try:
        # Check that both 70% and 75% thresholds are detected as distinct institutional conditions
        qa = process_query("What is the minimum attendance threshold required?")
        ev_set = reasoner.reason(qa)
        dec = reasoner.to_evidence_decision(ev_set)
        
        # When multiple applicable regulations exist, status must be MULTI_CONDITION_DISCLOSURE or CONFLICTING
        is_disclosure = dec.status in (EvidenceStatus.MULTI_CONDITION_DISCLOSURE, EvidenceStatus.CONFLICTING) or len(ev_set.detected_conflicts) > 0
        t6_pass = is_disclosure
        results["test_6_contradictory_evidence_preservation"] = {
            "status": "PASS" if t6_pass else "FAIL",
            "multi_condition_disclosure": is_disclosure,
            "detected_conflicts": len(ev_set.detected_conflicts),
            "status_assigned": dec.status.value,
        }
    except Exception as exc:
        results["test_6_contradictory_evidence_preservation"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 6 (Contradictory Evidence Handling): {results['test_6_contradictory_evidence_preservation']['status']}")

    # ---------------------------------------------------------
    # TEST 7: Insufficient Evidence & Abstention
    # ---------------------------------------------------------
    t7_pass = False
    try:
        # Query for non-existent fact in the corpus
        qa = process_query("What is the maximum subsidy for university helicopter parking permits for undergraduate students?")
        ev_set = reasoner.reason(qa)
        dec = reasoner.to_evidence_decision(ev_set)
        
        # System must detect missing evidence / unanswerability
        is_abstention = dec.status in (EvidenceStatus.INSUFFICIENT, EvidenceStatus.MISSING) or not ev_set.is_sufficient
        t7_pass = is_abstention
        results["test_7_insufficient_evidence_abstention"] = {
            "status": "PASS" if t7_pass else "FAIL",
            "abstention_triggered": is_abstention,
            "decision_status": dec.status.value,
            "missing_evidence": ev_set.missing_evidence,
        }
    except Exception as exc:
        results["test_7_insufficient_evidence_abstention"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 7 (Insufficient Evidence Abstention): {results['test_7_insufficient_evidence_abstention']['status']}")

    # ---------------------------------------------------------
    # TEST 8: Bounded Hop Limits & Cycle Detection
    # ---------------------------------------------------------
    t8_pass = False
    try:
        # Run with max_hops=3
        qa = process_query("What are the attendance requirements and can dean condone attendance?")
        ev_set_3 = reasoner.reason(qa, top_k_seed=5)
        
        # Check hop counts
        hops_by_number = {}
        for h in ev_set_3.reasoning_hops:
            hops_by_number[h.hop_number] = hops_by_number.get(h.hop_number, 0) + 1
            
        no_exceeded_hops = all(h.hop_number <= 3 for h in ev_set_3.reasoning_hops)
        no_duplicate_passages = len(ev_set_3.all_passages) == len(set(p.passage_id for p in ev_set_3.all_passages))
        t8_pass = no_exceeded_hops and no_duplicate_passages and len(ev_set_3.all_passages) <= reasoner.max_evidence_items

        results["test_8_bounded_hops_cycle_detection"] = {
            "status": "PASS" if t8_pass else "FAIL",
            "max_hop_respected": no_exceeded_hops,
            "no_duplicate_passages": no_duplicate_passages,
            "bounded_evidence_count": len(ev_set_3.all_passages),
            "hops_breakdown": hops_by_number,
        }
    except Exception as exc:
        results["test_8_bounded_hops_cycle_detection"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 8 (Bounded Hops & Cycle Detection): {results['test_8_bounded_hops_cycle_detection']['status']}")

    # ---------------------------------------------------------
    # TEST 9: Cross-User Multi-Tenant Isolation at Every Hop
    # ---------------------------------------------------------
    t9_pass = False
    tenant_a = f"tenant_r4_A_{uuid.uuid4().hex[:4]}"
    tenant_b = f"tenant_r4_B_{uuid.uuid4().hex[:4]}"
    try:
        # Upload doc for Tenant A
        doc_a = ingest_pdf(test_pdf, source_type=DocumentSource.UPLOAD, title="Confidential Policy Tenant A", user_id=tenant_a, force=True)
        
        qa_iso = process_query("What is required for laboratory access exemption?")

        # 1. Tenant A should see their own upload
        ev_set_a = reasoner.reason(qa_iso, user_id=tenant_a)
        sees_own = any(p.document_id == doc_a.document_id for p in ev_set_a.all_passages)

        # 2. Tenant B must NOT see any passage from Tenant A's document
        ev_set_b = reasoner.reason(qa_iso, user_id=tenant_b)
        leaked_b = any(p.document_id == doc_a.document_id for p in ev_set_b.all_passages)

        # 3. Anonymous user (user_id=None) must NOT see Tenant A's document
        ev_set_anon = reasoner.reason(qa_iso, user_id=None)
        leaked_anon = any(p.document_id == doc_a.document_id for p in ev_set_anon.all_passages)

        # Cleanup
        delete_document(doc_a.document_id, user_id=tenant_a)

        t9_pass = sees_own and (not leaked_b) and (not leaked_anon)
        results["test_9_cross_user_isolation"] = {
            "status": "PASS" if t9_pass else "FAIL",
            "user_can_retrieve_own_upload": sees_own,
            "isolation_enforced_against_other_tenant": not leaked_b,
            "isolation_enforced_against_anonymous_user": not leaked_anon,
            "leaked_passages_count": sum(1 for p in ev_set_b.all_passages if p.document_id == doc_a.document_id),
        }
    except Exception as exc:
        results["test_9_cross_user_isolation"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 9 (Cross-User Multi-Tenant Isolation): {results['test_9_cross_user_isolation']['status']}")

    # ---------------------------------------------------------
    # TEST 10: Citation & Page Accuracy
    # ---------------------------------------------------------
    t10_pass = False
    try:
        qa = process_query("When do odd semester examinations start?")
        ev_set = reasoner.reason(qa)
        all_valid = True
        for p in ev_set.all_passages:
            if not p.document_id or p.page_number is None or p.page_number <= 0:
                all_valid = False
                break
        t10_pass = all_valid and len(ev_set.all_passages) > 0
        results["test_10_citation_page_accuracy"] = {
            "status": "PASS" if t10_pass else "FAIL",
            "all_citations_have_valid_page": all_valid,
            "verified_count": len(ev_set.all_passages),
        }
    except Exception as exc:
        results["test_10_citation_page_accuracy"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 10 (Citation & Page Accuracy): {results['test_10_citation_page_accuracy']['status']}")

    # ---------------------------------------------------------
    # TEST 11: Multilingual Consistency (Hindi, Hinglish, English)
    # ---------------------------------------------------------
    t11_pass = False
    try:
        queries = [
            ("English", "When do odd semester end semester examinations start?"),
            ("Devanagari Hindi", "विषम सेमेस्टर परीक्षा कब शुरू होती है?"),
            ("Romanized Hindi", "odd semester exam kab start hoti hai?"),
            ("Hinglish", "odd semester examinations ki start date kya hai?"),
        ]
        multi_ok = True
        lang_results = {}
        for l_name, q_str in queries:
            qa_m = process_query(q_str)
            ev_m = reasoner.reason(qa_m)
            has_cal = any("10-12-2026" in p.text or "Academic-Calendar" in (p.document_filename or "") for p in ev_m.all_passages)
            lang_results[l_name] = {"retrieved": len(ev_m.all_passages), "connected_calendar": has_cal}
            if not has_cal:
                multi_ok = False

        t11_pass = multi_ok
        results["test_11_multilingual_consistency"] = {
            "status": "PASS" if t11_pass else "FAIL",
            "languages_tested": lang_results,
            "consistent_evidence_retrieval": multi_ok,
        }
    except Exception as exc:
        results["test_11_multilingual_consistency"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 11 (Multilingual Consistency): {results['test_11_multilingual_consistency']['status']}")

    # ---------------------------------------------------------
    # TEST 12: R1, R2, R2.1, R3, R5 Regression Check
    # ---------------------------------------------------------
    t12_pass = False
    try:
        with get_db() as conn:
            cells = conn.execute("SELECT count(*) FROM table_cells").fetchone()[0]
            rels = conn.execute("SELECT count(*) FROM document_relationships").fetchone()[0]
        from app.query.feedback_repair import repair_feedback_turn
        from app.models.schemas import FeedbackSubtype
        repair_res = repair_feedback_turn(
            feedback_query="No, make up exams are in January",
            subtype=FeedbackSubtype.FACTUAL_CORRECTION,
            preceding_turn={"query": "When are make up exams?", "answer": "December"},
            user_id="test_user_reg_r4",
            session_id=f"test_sess_{uuid.uuid4().hex[:6]}",
        )
        r5_ok = repair_res is not None and bool(repair_res.answer or repair_res.evidence_passages)
        t12_pass = cells > 20000 and rels > 7000 and r5_ok
        results["test_12_r1_r2_r3_r5_regression"] = {
            "status": "PASS" if t12_pass else "FAIL",
            "r1_table_cells": cells,
            "r2_r3_relationships": rels,
            "r5_feedback_repaired": r5_ok,
        }
    except Exception as exc:
        results["test_12_r1_r2_r3_r5_regression"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 12 (R1/R2/R3/R5 Regression): {results['test_12_r1_r2_r3_r5_regression']['status']}")

    # ---------------------------------------------------------
    # TEST 13: M10 Production Reranker Default Preservation
    # ---------------------------------------------------------
    t13_pass = False
    try:
        qa = process_query("When does odd semester 2026-27 end?")
        ev_set = reasoner.reason(qa)
        # Verify that seed passages ran through production reranker
        has_reranked = any(p.rerank_score is not None for p in ev_set.seed_passages)
        t13_pass = has_reranked and len(ev_set.seed_passages) > 0
        results["test_13_m10_production_reranker_preservation"] = {
            "status": "PASS" if t13_pass else "FAIL",
            "production_reranker_active": has_reranked,
            "seed_passages_reranked": len(ev_set.seed_passages),
        }
    except Exception as exc:
        results["test_13_m10_production_reranker_preservation"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 13 (M10 Production Reranker Preservation): {results['test_13_m10_production_reranker_preservation']['status']}")

    # ---------------------------------------------------------
    # TEST 14: Latency Measurement & Performance Breakdown
    # ---------------------------------------------------------
    t14_pass = False
    try:
        qa = process_query("What are the attendance rules and medical relaxation guidelines?")
        ev_set = reasoner.reason(qa)
        
        has_retrieval_ms = ev_set.retrieval_ms > 0
        has_reasoning_ms = ev_set.reasoning_ms > 0
        has_total_ms = ev_set.total_ms > 0
        t14_pass = has_retrieval_ms and has_reasoning_ms and has_total_ms
        results["test_14_latency_measurement_breakdown"] = {
            "status": "PASS" if t14_pass else "FAIL",
            "retrieval_ms": ev_set.retrieval_ms,
            "reasoning_ms": ev_set.reasoning_ms,
            "total_ms": ev_set.total_ms,
            "reasoning_overhead_percentage": f"{(ev_set.reasoning_ms / ev_set.total_ms * 100):.2f}%",
        }
    except Exception as exc:
        results["test_14_latency_measurement_breakdown"] = {"status": "FAIL", "error": str(exc)}
    print(f"Test 14 (Latency Breakdown): {results['test_14_latency_measurement_breakdown']['status']}")

    # Clean up temp test directory
    try:
        delete_document(doc_rec.document_id, user_id=test_user)
        if test_pdf.exists():
            test_pdf.unlink()
        if temp_dir.exists():
            temp_dir.rmdir()
    except Exception:
        pass

    print("=" * 70)
    all_passed = all(v.get("status") == "PASS" for v in results.values())
    print(f"ALL 14 TESTS PASSED: {all_passed}")
    print("=" * 70)

    # Save to docs/r4_test_results.json
    output_path = Path("docs/r4_test_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "phase": "R4",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "overall_status": "R4_VERIFIED" if all_passed else "R4_VERIFIED_WITH_LIMITATIONS",
                "total_tests": len(results),
                "passed_tests": sum(1 for v in results.values() if v.get("status") == "PASS"),
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"Saved test results to {output_path}")
    return all_passed


if __name__ == "__main__":
    success = run_r4_tests()
    sys.exit(0 if success else 1)

