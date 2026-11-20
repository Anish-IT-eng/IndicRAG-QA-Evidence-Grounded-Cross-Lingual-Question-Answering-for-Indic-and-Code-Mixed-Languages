"""
Regression Test Suite for Sequential User-Document Retrieval with Automatic Official-Corpus Fallback.

Tests the 7 mandatory architectural scenarios:
  1. User-uploaded document has answer -> answers from user doc, cites "User-provided document", no fallback.
  2. User document missing answer -> automatically falls back to official corpus, cites "Official university document".
  3. Answer in both sources -> prioritizes user document evidence first.
  4. Partial answer in user PDF -> combines user + official evidence into cohesive grounded response.
  5. Conflicting documents -> detects direct regulatory contradiction and discloses conflict.
  6. Answer missing from both sources -> Stage 3 final institutional abstention stating evidence missing from both.
  7. Multi-user isolation -> User A cannot retrieve User B's uploaded documents.
"""
from __future__ import annotations

from unittest.mock import patch

from app.models.schemas import (
    Citation,
    DocumentSource,
    EvidenceDecision,
    EvidenceStatus,
    QueryAnalysis,
    QueryLanguage,
    QuestionType,
    RegulatoryRelationship,
    RetrievalResult,
    RetrievedPassage,
)
from app.retrieval.sequential_orchestrator import (
    SequentialRetrievalOrchestrator,
    get_sequential_orchestrator,
)


def _make_passage(
    passage_id: str,
    doc_id: str,
    text: str,
    source_type: DocumentSource,
    filename: str,
    page: int = 1,
    ceci_score: float = 0.85,
) -> RetrievedPassage:
    return RetrievedPassage(
        passage_id=passage_id,
        document_id=doc_id,
        text=text,
        score=0.90,
        retrieval_method="bm25",
        page_number=page,
        source_type=source_type,
        document_filename=filename,
        rerank_score=ceci_score,
    )


def _make_query_analysis(query: str = "Test question") -> QueryAnalysis:
    return QueryAnalysis(
        original_query=query,
        detected_language=QueryLanguage.ENGLISH,
        normalized_query=query.lower(),
        query_type=QuestionType.DIRECT,
        complexity_score=0.2,
    )


# ─── SCENARIO 1: User Document Has Answer ─────────────────────────────────────

def test_scenario_1_user_document_has_answer():
    """When user's uploaded doc has sufficient evidence, answer immediately without official fallback."""
    orchestrator = SequentialRetrievalOrchestrator()
    qa = _make_query_analysis("When will odd semester end examinations start?")

    user_passage = _make_passage(
        passage_id="p_user_cal_01",
        doc_id="doc_user_cal",
        text="Odd Semester End-Term Examinations will commence from December 15, 2026.",
        source_type=DocumentSource.UPLOAD,
        filename="Academic-Calendar-2026-27.pdf",
    )
    user_retrieval = RetrievalResult(
        query_analysis=qa,
        retrieved_passages=[user_passage],
        total_candidates=1,
    )
    user_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=[user_passage],
        explanation="Sufficient evidence found in user document.",
        retry_recommended=False,
        ceci_score=0.88,
    )

    with patch.object(orchestrator, "get_user_uploads", return_value=[{"document_id": "doc_user_cal"}]), \
         patch("app.retrieval.sequential_orchestrator.retrieve", return_value=user_retrieval) as mock_retrieve, \
         patch.object(orchestrator.evidence_controller, "evaluate", return_value=user_decision):

        decision, ret_res, summary = orchestrator.execute(query_analysis=qa, user_id="alice")

        assert summary["stage"] == "user_upload_sufficient"
        assert summary["fallback_triggered"] is False
        assert decision.status == EvidenceStatus.SUFFICIENT
        assert len(decision.valid_passages) == 1
        assert decision.valid_passages[0].source_type == DocumentSource.UPLOAD
        assert decision.valid_passages[0].document_filename == "Academic-Calendar-2026-27.pdf"
        # Only Stage 1 retrieve was called
        assert mock_retrieve.call_count == 1
        assert mock_retrieve.call_args[1]["collections"] == [DocumentSource.UPLOAD]


# ─── SCENARIO 2: User Document Missing Answer -> Fallback to Official ─────────

def test_scenario_2_user_document_missing_answer_fallback_to_official():
    """When user doc has insufficient evidence, automatically fallback to official university regulations."""
    orchestrator = SequentialRetrievalOrchestrator()
    qa = _make_query_analysis("What is the minimum attendance requirement for appearing in end-sem exams?")

    # Stage 1 returns insufficient/missing
    user_decision = EvidenceDecision(
        status=EvidenceStatus.INSUFFICIENT,
        valid_passages=[],
        explanation="No attendance rules found in user calendar.",
        retry_recommended=False,
        ceci_score=0.15,
    )
    user_retrieval = RetrievalResult(query_analysis=qa, retrieved_passages=[], total_candidates=0)

    # Stage 2 returns sufficient official evidence
    official_passage = _make_passage(
        passage_id="p_off_att_01",
        doc_id="doc_off_ord",
        text="A student must maintain a minimum attendance of 75% in each course to be eligible for end semester exams.",
        source_type=DocumentSource.OFFICIAL,
        filename="BTech_Ordinance_2023.pdf",
        page=12,
    )
    official_retrieval = RetrievalResult(
        query_analysis=qa,
        retrieved_passages=[official_passage],
        total_candidates=1,
    )
    official_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=[official_passage],
        explanation="Official attendance requirement verified.",
        retry_recommended=False,
        ceci_score=0.91,
    )

    def mock_retrieve_side_effect(**kwargs):
        if kwargs.get("collections") == [DocumentSource.UPLOAD]:
            return user_retrieval
        return official_retrieval

    def mock_eval_side_effect(ret, attempt=1):
        if ret == user_retrieval:
            return user_decision
        return official_decision

    with patch.object(orchestrator, "get_user_uploads", return_value=[{"document_id": "doc_user_cal"}]), \
         patch("app.retrieval.sequential_orchestrator.retrieve", side_effect=mock_retrieve_side_effect) as mock_ret, \
         patch.object(orchestrator.evidence_controller, "evaluate", side_effect=mock_eval_side_effect):

        decision, ret_res, summary = orchestrator.execute(query_analysis=qa, user_id="alice")

        assert summary["stage"] == "official_fallback"
        assert summary["fallback_triggered"] is True
        assert decision.status == EvidenceStatus.SUFFICIENT
        assert len(decision.valid_passages) == 1
        assert decision.valid_passages[0].source_type == DocumentSource.OFFICIAL
        assert decision.valid_passages[0].document_filename == "BTech_Ordinance_2023.pdf"
        assert mock_ret.call_count == 2


# ─── SCENARIO 3: Answer in Both Sources -> Prioritize User Document ───────────

def test_scenario_3_answer_in_both_sources_prioritizes_user_evidence():
    """When both user doc and official corpus contain answers, Stage 1 satisfies query with user provenance."""
    orchestrator = SequentialRetrievalOrchestrator()
    qa = _make_query_analysis("What is the grade for 80 marks?")

    user_passage = _make_passage(
        passage_id="p_user_grade_01",
        doc_id="doc_user_syllabus",
        text="Marks 80-89 corresponds to Grade A (Grade point 9).",
        source_type=DocumentSource.UPLOAD,
        filename="Course_Syllabus.pdf",
    )
    user_retrieval = RetrievalResult(query_analysis=qa, retrieved_passages=[user_passage], total_candidates=1)
    user_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=[user_passage],
        explanation="Satisfied by syllabus upload.",
        retry_recommended=False,
        ceci_score=0.86,
    )

    with patch.object(orchestrator, "get_user_uploads", return_value=[{"document_id": "doc_user_syllabus"}]), \
         patch("app.retrieval.sequential_orchestrator.retrieve", return_value=user_retrieval) as mock_ret, \
         patch.object(orchestrator.evidence_controller, "evaluate", return_value=user_decision):

        decision, ret_res, summary = orchestrator.execute(query_analysis=qa, user_id="alice")

        assert summary["stage"] == "user_upload_sufficient"
        assert summary["fallback_triggered"] is False
        assert mock_ret.call_count == 1
        assert decision.valid_passages[0].source_type == DocumentSource.UPLOAD


# ─── SCENARIO 4: Partial Answer in User Doc -> Combined Evidence ──────────────

def test_scenario_4_partial_user_evidence_combined_with_official():
    """When user doc satisfies partial conditions, combine compatible evidence from both sources."""
    orchestrator = SequentialRetrievalOrchestrator()
    qa = _make_query_analysis("What is the attendance requirement and the date for mid-semester exams?")

    user_passage = _make_passage(
        passage_id="p_user_midsem",
        doc_id="doc_user_cal",
        text="Mid-semester examinations commence on October 10, 2026.",
        source_type=DocumentSource.UPLOAD,
        filename="Academic-Calendar-2026-27.pdf",
    )
    user_decision = EvidenceDecision(
        status=EvidenceStatus.PARTIAL,
        valid_passages=[user_passage],
        explanation="Contains exam date, missing attendance requirements.",
        retry_recommended=True,
        ceci_score=0.45,
    )
    user_retrieval = RetrievalResult(query_analysis=qa, retrieved_passages=[user_passage], total_candidates=1)

    official_passage = _make_passage(
        passage_id="p_off_att",
        doc_id="doc_off_ord",
        text="Minimum attendance required is 75%.",
        source_type=DocumentSource.OFFICIAL,
        filename="BTech_Ordinance_2023.pdf",
    )
    official_decision = EvidenceDecision(
        status=EvidenceStatus.PARTIAL,
        valid_passages=[official_passage],
        explanation="Contains attendance rule, missing calendar dates.",
        retry_recommended=False,
        ceci_score=0.48,
    )
    official_retrieval = RetrievalResult(query_analysis=qa, retrieved_passages=[official_passage], total_candidates=1)

    combined_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=[user_passage, official_passage],
        explanation="Combined evidence satisfies both attendance and calendar questions.",
        retry_recommended=False,
        ceci_score=0.88,
    )

    def mock_retrieve_side_effect(**kwargs):
        if kwargs.get("collections") == [DocumentSource.UPLOAD]:
            return user_retrieval
        return official_retrieval

    def mock_eval_side_effect(ret, attempt=1):
        if ret == user_retrieval:
            return user_decision
        if ret == official_retrieval:
            return official_decision
        return combined_decision

    with patch.object(orchestrator, "get_user_uploads", return_value=[{"document_id": "doc_user_cal"}]), \
         patch("app.retrieval.sequential_orchestrator.retrieve", side_effect=mock_retrieve_side_effect), \
         patch.object(orchestrator.evidence_controller, "evaluate", side_effect=mock_eval_side_effect), \
         patch("app.retrieval.sequential_orchestrator.classify_regulatory_relationship", return_value=RegulatoryRelationship.DIFFERENT_REGULATORY_CONDITIONS):

        decision, ret_res, summary = orchestrator.execute(query_analysis=qa, user_id="alice")

        assert summary["stage"] == "combined_user_and_official"
        assert summary["fallback_triggered"] is True
        assert summary["combined_sources"] is True
        assert len(decision.valid_passages) == 2
        sources = {p.source_type for p in decision.valid_passages}
        assert DocumentSource.UPLOAD in sources
        assert DocumentSource.OFFICIAL in sources


# ─── SCENARIO 5: Conflicting Documents -> Conflict Disclosure ─────────────────

def test_scenario_5_conflicting_documents_detected():
    """When user document directly contradicts official regulation, flag CONFLICTING status."""
    orchestrator = SequentialRetrievalOrchestrator()
    qa = _make_query_analysis("What is the minimum attendance requirement?")

    user_passage = _make_passage(
        passage_id="p_user_att_conflict",
        doc_id="doc_user_note",
        text="Attendance requirement is relaxed to 60% for all departments this year.",
        source_type=DocumentSource.UPLOAD,
        filename="Unofficial_Circular.pdf",
    )
    user_decision = EvidenceDecision(
        status=EvidenceStatus.PARTIAL,
        valid_passages=[user_passage],
        explanation="Relaxed attendance statement.",
        retry_recommended=False,
        ceci_score=0.72,
    )
    user_retrieval = RetrievalResult(query_analysis=qa, retrieved_passages=[user_passage], total_candidates=1)

    official_passage = _make_passage(
        passage_id="p_off_att_ord",
        doc_id="doc_off_ord",
        text="A student must maintain a minimum attendance of 75% in each course.",
        source_type=DocumentSource.OFFICIAL,
        filename="BTech_Ordinance_2023.pdf",
    )
    official_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=[official_passage],
        explanation="Official 75% attendance rule.",
        retry_recommended=False,
        ceci_score=0.92,
    )
    official_retrieval = RetrievalResult(query_analysis=qa, retrieved_passages=[official_passage], total_candidates=1)

    def mock_retrieve_side_effect(**kwargs):
        if kwargs.get("collections") == [DocumentSource.UPLOAD]:
            return user_retrieval
        return official_retrieval

    def mock_eval_side_effect(ret, attempt=1):
        if ret == user_retrieval:
            return user_decision
        return official_decision

    with patch.object(orchestrator, "get_user_uploads", return_value=[{"document_id": "doc_user_note"}]), \
         patch("app.retrieval.sequential_orchestrator.retrieve", side_effect=mock_retrieve_side_effect), \
         patch.object(orchestrator.evidence_controller, "evaluate", side_effect=mock_eval_side_effect), \
         patch("app.retrieval.sequential_orchestrator.classify_regulatory_relationship", return_value=RegulatoryRelationship.GENUINE_CONFLICT):

        decision, ret_res, summary = orchestrator.execute(query_analysis=qa, user_id="alice")

        assert summary["stage"] == "conflicting_user_and_official"
        assert decision.status == EvidenceStatus.CONFLICTING
        assert "CONFLICTING REGULATIONS DETECTED" in decision.explanation


# ─── SCENARIO 6: Answer Missing in Both Sources -> Final Abstention ───────────

def test_scenario_6_missing_in_both_sources_abstains():
    """When question is unanswerable in both user docs and official corpus, abstain with institutional explanation."""
    orchestrator = SequentialRetrievalOrchestrator()
    qa = _make_query_analysis("What is the university policy on quantum teleporters?")

    user_decision = EvidenceDecision(
        status=EvidenceStatus.INSUFFICIENT,
        valid_passages=[],
        explanation="No relevant passages in user documents.",
        retry_recommended=False,
        ceci_score=0.0,
    )
    user_retrieval = RetrievalResult(query_analysis=qa, retrieved_passages=[], total_candidates=0)

    official_decision = EvidenceDecision(
        status=EvidenceStatus.MISSING,
        valid_passages=[],
        explanation="No relevant passages in official regulations.",
        retry_recommended=False,
        ceci_score=0.0,
    )
    official_retrieval = RetrievalResult(query_analysis=qa, retrieved_passages=[], total_candidates=0)

    def mock_retrieve_side_effect(**kwargs):
        if kwargs.get("collections") == [DocumentSource.UPLOAD]:
            return user_retrieval
        return official_retrieval

    def mock_eval_side_effect(ret, attempt=1):
        if ret == user_retrieval:
            return user_decision
        return official_decision

    with patch.object(orchestrator, "get_user_uploads", return_value=[{"document_id": "doc_user_cal"}]), \
         patch("app.retrieval.sequential_orchestrator.retrieve", side_effect=mock_retrieve_side_effect), \
         patch.object(orchestrator.evidence_controller, "evaluate", side_effect=mock_eval_side_effect):

        decision, ret_res, summary = orchestrator.execute(query_analysis=qa, user_id="alice")

        assert summary["stage"] == "final_abstention"
        assert summary["fallback_triggered"] is True
        assert decision.status == EvidenceStatus.INSUFFICIENT
        assert len(decision.valid_passages) == 0
        assert "UNANSWERABLE" in decision.explanation
        assert "user's uploaded documents" in decision.explanation
        assert "official university regulations" in decision.explanation


# ─── SCENARIO 7: Multi-User Isolation ─────────────────────────────────────────

def test_scenario_7_multi_user_isolation():
    """Verify that User B cannot retrieve User A's uploaded documents."""
    from app.retrieval.engine import RetrieverIndex
    from rank_bm25 import BM25Okapi

    idx = RetrieverIndex("upload")
    idx.passage_ids = ["p_alice_01", "p_bob_01", "p_filler_01", "p_filler_02", "p_filler_03"]
    idx.passage_texts = [
        "Alice personal research document on robotics navigation algorithms.",
        "Bob assignment notes on computer networks routing tables.",
        "Campus sports complex swimming pool timing schedule.",
        "Library book borrowing guidelines and overdue fine policy.",
        "Hostel mess food menu for academic semester.",
    ]
    idx.passage_meta = [
        {"user_id": "alice", "filename": "alice_notes.pdf"},
        {"user_id": "bob", "filename": "bob_notes.pdf"},
        {"user_id": "charlie", "filename": "sports.pdf"},
        {"user_id": "david", "filename": "library.pdf"},
        {"user_id": "eve", "filename": "hostel.pdf"},
    ]
    tokenized = [t.lower().split() for t in idx.passage_texts]
    idx.bm25 = BM25Okapi(tokenized)

    # Search as Bob for "networks routing"
    bob_results = idx.bm25_search("networks routing", top_k=5, user_id="bob")
    bob_pids = [r[0] for r in bob_results]
    assert "p_bob_01" in bob_pids
    assert "p_alice_01" not in bob_pids

    # Search as Alice for "robotics navigation"
    alice_results = idx.bm25_search("robotics navigation", top_k=5, user_id="alice")
    alice_pids = [r[0] for r in alice_results]
    assert "p_alice_01" in alice_pids
    assert "p_bob_01" not in alice_pids


# ─── Citation Provenance Invariants ───────────────────────────────────────────

def test_citation_provenance_labels():
    """Ensure Citation objects strictly carry correct source_type and source_label."""
    user_cit = Citation(
        document_id="doc_u1",
        passage_id="p_u1",
        page=3,
        filename="My_Notes.pdf",
        quote="Odd semester exams commence on Dec 15.",
        source_type=DocumentSource.UPLOAD,
        source_label="User-provided document",
    )
    assert user_cit.source_type == DocumentSource.UPLOAD
    assert user_cit.source_label == "User-provided document"
    assert user_cit.filename == "My_Notes.pdf"

    off_cit = Citation(
        document_id="doc_o1",
        passage_id="p_o1",
        page=15,
        filename="BTech_Ordinance_2023.pdf",
        quote="Minimum attendance of 75% required.",
        source_type=DocumentSource.OFFICIAL,
        source_label="Official university document",
    )
    assert off_cit.source_type == DocumentSource.OFFICIAL
    assert off_cit.source_label == "Official university document"


# ─── User Feedback / Disagreement Classification ─────────────────────────────

def test_feedback_correction_classification():
    """Verify that messages like 'your answer is wrong' or 'galat hai' are classified as FEEDBACK_CORRECTION."""
    from app.query.processor import process_query
    from app.models.schemas import QuestionType

    feedback_queries = [
        "your answer is wrong",
        "this is wrong",
        "that's wrong",
        "you are wrong",
        "wrong answer",
        "this is incorrect",
        "galat hai",
        "ye galat hai",
        "sahi nahi hai",
    ]
    for q in feedback_queries:
        qa = process_query(q)
        assert qa.query_type == QuestionType.FEEDBACK_CORRECTION, f"Failed for query: '{q}', got {qa.query_type}"

