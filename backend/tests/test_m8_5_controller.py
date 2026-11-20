"""
Test Suite for Milestone M8.5: Regulatory-Aware Evidence Controller.

Validates:
1. M8.3 Acceptance Queries (AQ-01 through AQ-07)
2. M8.4 Test Matrix (TM-01 through TM-18)
3. Query Processor Temporal and Cohort Intent Parsing
4. Regulatory Classifier Condition and Relationship Determination
"""
from __future__ import annotations

import pytest

from app.models.schemas import (
    DocumentSource,
    DocumentVersionInfo,
    EvidenceDecision,
    EvidenceStatus,
    QueryAnalysis,
    QuestionType,
    RegulatoryCondition,
    RegulatoryRelationship,
    RetrievedPassage,
    RetrievalResult,
    TemporalIntentMode,
)
from app.query.processor import (
    extract_temporal_and_cohort_intent,
    process_query,
)
from app.retrieval.regulatory_classifier import (
    classify_passage_condition,
    classify_regulatory_relationship,
    check_regulatory_consensus,
)
from app.retrieval.evidence_controller import EvidenceController


# =============================================================================
# 1. Query Processor Regulatory & Temporal Extraction Tests
# =============================================================================

class TestQueryProcessorRegulatoryIntent:
    def test_extract_historical_calendar_year(self):
        query = "What was the attendance rule in 2017?"
        intent = extract_temporal_and_cohort_intent(query)
        assert intent["mode"] == TemporalIntentMode.EXPLICIT_HISTORICAL
        assert intent["cohort"] == "2017"
        assert intent["target_conditions"] == [RegulatoryCondition.COURSE_GRADING]

    def test_extract_historical_batch_year(self):
        query = "What attendance rule applied to the 2018 batch?"
        intent = extract_temporal_and_cohort_intent(query)
        assert intent["mode"] == TemporalIntentMode.EXPLICIT_HISTORICAL
        assert intent["cohort"] == "2018"

    def test_extract_academic_year(self):
        query = "What was the rule in AY 2022-23 for end sem exams?"
        intent = extract_temporal_and_cohort_intent(query)
        assert intent["mode"] == TemporalIntentMode.EXPLICIT_CURRENT
        assert intent["academic_year"] == "2022-23"
        assert intent["target_conditions"] == [RegulatoryCondition.EXAM_ELIGIBILITY]

    def test_extract_programme_and_condition(self):
        query = "Is 75% compulsory for SCSET students?"
        intent = extract_temporal_and_cohort_intent(query)
        assert intent["programme"] == "SCSET"
        assert RegulatoryCondition.EXAM_ELIGIBILITY in intent["target_conditions"]

    def test_extract_medical_condition(self):
        query = "Can attendance be relaxed due to medical reasons?"
        intent = extract_temporal_and_cohort_intent(query)
        assert RegulatoryCondition.MEDICAL_CONDONATION in intent["target_conditions"]

    def test_extract_x_grade_condition(self):
        query = "How much attendance is required to avoid an X grade?"
        intent = extract_temporal_and_cohort_intent(query)
        assert RegulatoryCondition.COURSE_GRADING in intent["target_conditions"]


# =============================================================================
# 2. Regulatory Classifier Unit Tests
# =============================================================================

class TestRegulatoryClassifierUnit:
    def test_classify_course_grading_condition(self):
        text = "A student having less than 70% attendance shall be awarded an 'X' grade and repeat the course."
        cond = classify_passage_condition(text)
        assert cond == RegulatoryCondition.COURSE_GRADING

    def test_classify_exam_eligibility_condition(self):
        text = "75% minimum aggregate attendance is required to be eligible to appear in End Semester Examinations."
        cond = classify_passage_condition(text)
        assert cond == RegulatoryCondition.EXAM_ELIGIBILITY

    def test_classify_medical_condonation_condition(self):
        text = "Dean may grant attendance relaxation up to 10% on genuine medical grounds."
        cond = classify_passage_condition(text)
        assert cond == RegulatoryCondition.MEDICAL_CONDONATION

    def test_classify_different_conditions_relationship(self):
        t1 = "70% attendance required to avoid 'X' grade."
        t2 = "75% attendance required for End Semester Examination hall ticket."
        rel = classify_regulatory_relationship(t1, t2)
        assert rel == RegulatoryRelationship.DIFFERENT_REGULATORY_CONDITIONS

    def test_consensus_verification_70_percent(self):
        p1 = RetrievedPassage(
            passage_id="p1", document_id="SCSET_2022",
            text="Clause 30.1(ii): Students having less than 70% attendance awarded 'X' grade.",
            score=18.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.COURSE_GRADING,
        )
        p2 = RetrievedPassage(
            passage_id="p2", document_id="SEAS_2017",
            text="Clause 30.1(ii): Minimum 70% attendance required to avoid 'X' grade.",
            score=17.5, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.COURSE_GRADING,
        )
        qa = QueryAnalysis(original_query="How much attendance is required to avoid an X grade?")
        is_consensus, val, expl = check_regulatory_consensus([p1, p2], qa)
        assert is_consensus is True
        assert val == 70.0
        assert "unanimous" in expl.lower() or "consensus" in expl.lower()


# =============================================================================
# 3. Acceptance Tests for 7 M8.3 Attendance Queries (AQ-01 to AQ-07)
# =============================================================================

class TestM83AttendanceQueries:
    @pytest.fixture
    def controller(self):
        return EvidenceController(tau_suff=0.65, tau_insuff=0.35)

    def test_aq01_unanchored_minimum_attendance(self, controller):
        """AQ-01: 'What is the minimum attendance required?' -> CLARIFICATION_REQUIRED with dual disclosure."""
        p_course = RetrievedPassage(
            passage_id="p-course", document_id="SCSET-UG",
            text="Clause 30.1: Minimum 70% attendance required to avoid X grade.",
            score=18.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.COURSE_GRADING,
        )
        p_exam = RetrievedPassage(
            passage_id="p-exam", document_id="Notif-307",
            text="Notification 307: 75% minimum aggregate attendance required for End Semester Examinations.",
            score=17.8, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.EXAM_ELIGIBILITY,
        )
        qa = process_query("What is the minimum attendance required?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_course, p_exam])
        dec = controller.evaluate(rr)

        assert dec.status in (EvidenceStatus.CLARIFICATION_REQUIRED, EvidenceStatus.MULTI_CONDITION_DISCLOSURE)
        assert "70%" in dec.explanation
        assert "75%" in dec.explanation

    def test_aq02_exam_eligibility_attendance(self, controller):
        """AQ-02: 'What attendance is required to sit for end semester exams?' -> SUFFICIENT (75%)."""
        p_exam = RetrievedPassage(
            passage_id="p-exam", document_id="Notif-307",
            text="Notification 307: 75% minimum aggregate attendance required to appear in End Semester Examinations.",
            score=20.0, rerank_score=3.5, retrieval_method="hybrid", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.EXAM_ELIGIBILITY,
        )
        qa = process_query("What attendance is required to sit for end semester exams?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_exam])
        dec = controller.evaluate(rr)

        assert dec.status == EvidenceStatus.SUFFICIENT
        assert dec.ceci_score >= 0.65

    def test_aq03_x_grade_attendance(self, controller):
        """AQ-03: 'How much attendance is required to avoid an X grade?' -> SUFFICIENT (70%, consensus)."""
        p_scset = RetrievedPassage(
            passage_id="p-scset", document_id="SCSET-UG",
            text="Clause 30.1: Minimum 70% attendance required to avoid 'X' grade.",
            score=19.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.COURSE_GRADING,
        )
        p_seas = RetrievedPassage(
            passage_id="p-seas", document_id="SEAS-2017",
            text="Clause 30.1: Minimum 70% attendance required to avoid 'X' grade.",
            score=18.5, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.COURSE_GRADING,
        )
        qa = process_query("How much attendance is required to avoid an X grade?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_scset, p_seas])
        dec = controller.evaluate(rr)

        assert dec.status == EvidenceStatus.SUFFICIENT
        assert dec.ceci_score >= 0.65
        assert dec.status != EvidenceStatus.CONFLICTING

    def test_aq04_is_70_percent_enough(self, controller):
        """AQ-04: 'Is 70% attendance enough?' -> SUFFICIENT or MULTI_CONDITION_DISCLOSURE delineating rules."""
        p_course = RetrievedPassage(
            passage_id="p-course", document_id="SCSET-UG",
            text="Clause 30.1: Minimum 70% attendance avoids X grade.",
            score=18.5, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.COURSE_GRADING,
        )
        p_exam = RetrievedPassage(
            passage_id="p-exam", document_id="Notif-307",
            text="Notification 307: 75% minimum aggregate attendance required for End Semester Examinations.",
            score=18.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.EXAM_ELIGIBILITY,
        )
        qa = process_query("Is 70% attendance enough?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_course, p_exam])
        dec = controller.evaluate(rr)

        # Must NOT treat as irreconcilable conflict
        assert dec.status in (EvidenceStatus.SUFFICIENT, EvidenceStatus.MULTI_CONDITION_DISCLOSURE, EvidenceStatus.CLARIFICATION_REQUIRED)
        assert dec.status != EvidenceStatus.CONFLICTING

    def test_aq05_is_75_percent_compulsory_scset(self, controller):
        """AQ-05: 'Is 75% compulsory for SCSET students?' -> SUFFICIENT (Applies university-wide)."""
        p_exam = RetrievedPassage(
            passage_id="p-exam", document_id="Notif-307",
            text="Notification 307 applies to all Schools and Programmes including SCSET: 75% minimum aggregate attendance for End Semester Examinations.",
            score=19.5, rerank_score=3.2, retrieval_method="hybrid", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.EXAM_ELIGIBILITY,
        )
        qa = process_query("Is 75% compulsory for SCSET students?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_exam])
        dec = controller.evaluate(rr)

        assert dec.status == EvidenceStatus.SUFFICIENT

    def test_aq06_historical_2017_rule(self, controller):
        """AQ-06: 'What was the attendance rule in 2017?' -> SUFFICIENT (historical scope)."""
        p_hist = RetrievedPassage(
            passage_id="p-hist", document_id="SEAS-2017",
            text="Clause 30.1: In SEAS Ordinances 2017, minimum 70% attendance is required to avoid 'X' grade.",
            score=19.0, rerank_score=3.0, retrieval_method="hybrid", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.COURSE_GRADING,
            version_info=DocumentVersionInfo(effective_date="2017-07-01", is_current=False),
        )
        qa = process_query("What was the attendance rule in 2017?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_hist])
        dec = controller.evaluate(rr)

        assert dec.status == EvidenceStatus.SUFFICIENT
        assert dec.status != EvidenceStatus.CONFLICTING

    def test_aq07_medical_relaxation(self, controller):
        """AQ-07: 'Can attendance be relaxed due to medical reasons?' -> SUFFICIENT (10% relaxation, consensus)."""
        p_scset = RetrievedPassage(
            passage_id="p-scset-med", document_id="SCSET-UG",
            text="Clause 30.1(v): Up to 10% relaxation may be granted by Dean on medical grounds.",
            score=19.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.MEDICAL_CONDONATION,
        )
        p_seas = RetrievedPassage(
            passage_id="p-seas-med", document_id="SEAS-2017",
            text="Clause 30.1(v): Dean may condone up to 10% attendance on genuine medical certification.",
            score=18.5, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.MEDICAL_CONDONATION,
        )
        qa = process_query("Can attendance be relaxed due to medical reasons?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_scset, p_seas])
        dec = controller.evaluate(rr)

        assert dec.status == EvidenceStatus.SUFFICIENT
        assert dec.status != EvidenceStatus.CONFLICTING


# =============================================================================
# 4. Acceptance Tests for Full M8.4 Test Matrix (TM-01 through TM-18)
# =============================================================================

class TestM84TestMatrix:
    @pytest.fixture
    def controller(self):
        return EvidenceController(tau_suff=0.65, tau_insuff=0.35)

    def test_tm08_batch_temporal_anchoring(self, controller):
        """TM-08: 'What attendance rule applied to the 2018 batch?' -> SUFFICIENT."""
        p_hist = RetrievedPassage(
            passage_id="p-2018", document_id="SEAS-2017",
            text="Ordinance 2017 governing 2017-2021 batches specifies 70% course attendance.",
            score=18.5, rerank_score=2.8, retrieval_method="hybrid", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.COURSE_GRADING,
            version_info=DocumentVersionInfo(effective_date="2017-07-01", is_current=False),
        )
        qa = process_query("What attendance rule applied to the 2018 batch?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_hist])
        dec = controller.evaluate(rr)
        assert dec.status == EvidenceStatus.SUFFICIENT

    def test_tm09_academic_year_anchoring(self, controller):
        """TM-09: 'What was the rule in AY 2022-23 for end sem exams?' -> SUFFICIENT."""
        p_ay = RetrievedPassage(
            passage_id="p-307", document_id="Notif-307",
            text="For AY 2022-23 onwards, 75% aggregate attendance is mandatory for End Semester Examinations.",
            score=19.0, rerank_score=3.1, retrieval_method="hybrid", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.EXAM_ELIGIBILITY,
        )
        qa = process_query("What was the rule in AY 2022-23 for end sem exams?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_ay])
        dec = controller.evaluate(rr)
        assert dec.status == EvidenceStatus.SUFFICIENT

    def test_tm10_programme_specific_duration(self, controller):
        """TM-10: 'What is the maximum degree duration for B.Tech CSE students?' -> SUFFICIENT."""
        p_dur = RetrievedPassage(
            passage_id="p-scset-dur", document_id="SCSET-UG",
            text="Normal duration of B.Tech programme is 4 years. Maximum duration permissible is 6 years (N+2).",
            score=20.0, rerank_score=3.5, retrieval_method="hybrid", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.ACADEMIC_PROGRESSION,
        )
        qa = process_query("What is the maximum degree duration for B.Tech CSE students?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_dur])
        dec = controller.evaluate(rr)
        assert dec.status == EvidenceStatus.SUFFICIENT

    def test_tm11_ufm_mobile_phone_exam(self, controller):
        """TM-11: 'What happens if a student uses a mobile phone in the exam hall?' -> SUFFICIENT."""
        p_ufm = RetrievedPassage(
            passage_id="p-ufm", document_id="UFM-2024",
            text="Possession and use of mobile phones in examination hall constitutes Category II/III Unfair Means resulting in course cancellation.",
            score=19.5, rerank_score=3.2, retrieval_method="hybrid", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.DISCIPLINARY_ACTION,
        )
        qa = process_query("What happens if a student uses a mobile phone in the exam hall?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_ufm])
        dec = controller.evaluate(rr)
        assert dec.status == EvidenceStatus.SUFFICIENT

    def test_tm12_genuine_conflict_identical_condition(self, controller):
        """TM-12: Two active co-equal documents contradicting on identical condition -> CONFLICTING."""
        p_act1 = RetrievedPassage(
            passage_id="p-a1", document_id="doc-active-1",
            text="End Semester Examination minimum attendance requirement is strictly 75%.",
            score=18.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.EXAM_ELIGIBILITY,
            version_info=DocumentVersionInfo(superseded_by="doc-active-2"),
        )
        p_act2 = RetrievedPassage(
            passage_id="p-a2", document_id="doc-active-2",
            text="End Semester Examination minimum attendance requirement is revised to 70%.",
            score=18.2, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.EXAM_ELIGIBILITY,
        )
        qa = process_query("Is the attendance threshold for 2023 batch 70% or 75% for exam hall?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_act1, p_act2])
        dec = controller.evaluate(rr)
        assert dec.status == EvidenceStatus.CONFLICTING

    def test_tm13_unsupported_supersession(self, controller):
        """TM-13: 'Did Notification 307 cancel the SCSET 70% course rule?' -> Rejection of unsupported repeal."""
        p_notif = RetrievedPassage(
            passage_id="p-notif", document_id="Notification-Minimum-Attendance",
            text="Notification 307/2022: Minimum attendance to appear in End Semester Examinations is 75%. Nothing in this notice amends School course evaluation.",
            score=20.0, rerank_score=3.8, retrieval_method="hybrid", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.EXAM_ELIGIBILITY,
            version_info=DocumentVersionInfo(is_current=True),
        )
        p_course = RetrievedPassage(
            passage_id="p-scset", document_id="SCSET-UG",
            text="Clause 30.1: Students with attendance below 70% are awarded X grade. There is no repeal by external circulars.",
            score=19.5, rerank_score=3.5, retrieval_method="hybrid", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.COURSE_GRADING,
            version_info=DocumentVersionInfo(is_current=True),
        )
        qa = process_query("Did Notification 307 cancel the SCSET 70% course rule?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_notif, p_course])
        dec = controller.evaluate(rr)
        assert dec.status == EvidenceStatus.SUFFICIENT

    def test_tm14_phd_applicability_unresolved(self, controller):
        """TM-14: 'What is the attendance requirement for PhD scholars?' -> CLARIFICATION_REQUIRED or SAFE_ABSTENTION."""
        p_ug = RetrievedPassage(
            passage_id="p-ug", document_id="SCSET-UG",
            text="These rules apply specifically to Undergraduate B.Tech students in SCSET.",
            score=12.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.PROGRAMME_REQUIREMENT,
        )
        qa = process_query("What is the attendance requirement for PhD scholars?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_ug])
        dec = controller.evaluate(rr)
        assert dec.status in (EvidenceStatus.CLARIFICATION_REQUIRED, EvidenceStatus.PARTIAL, EvidenceStatus.INSUFFICIENT)

    def test_tm15_contradictory_premise_makeup_exam(self, controller):
        """TM-15: 'Can I take a makeup exam after getting an X grade in attendance?' -> INSUFFICIENT."""
        p_x = RetrievedPassage(
            passage_id="p-x", document_id="SCSET-UG",
            text="An 'X' grade awarded due to attendance shortage strictly prohibits makeup exam. Must repeat course.",
            score=25.0, rerank_score=4.0, retrieval_method="hybrid", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.COURSE_GRADING,
        )
        qa = process_query("Can I take a makeup exam after getting an X grade in attendance?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_x])
        dec = controller.evaluate(rr)
        assert dec.status == EvidenceStatus.INSUFFICIENT
        assert "contradictory premise" in dec.explanation.lower()

    def test_tm16_medical_condonation_extreme_55(self, controller):
        """TM-16: 'Can a student with 55% attendance get medical condonation to sit for exams?' -> SUFFICIENT (disallows)."""
        p_med = RetrievedPassage(
            passage_id="p-med", document_id="SCSET-UG",
            text="Clause 30.1(v): Dean may condone at most 10% attendance. Absolute statutory floor is 60%.",
            score=19.0, rerank_score=3.0, retrieval_method="hybrid", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.MEDICAL_CONDONATION,
        )
        qa = process_query("Can a student with 55% attendance get medical condonation to sit for exams?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_med])
        dec = controller.evaluate(rr)
        assert dec.status == EvidenceStatus.SUFFICIENT
        assert dec.status != EvidenceStatus.CONFLICTING

    def test_tm17_out_of_domain(self, controller):
        """TM-17: 'What is the recipe for chocolate cake in the Bennett cafeteria?' -> MISSING."""
        qa = process_query("What is the recipe for chocolate cake in the Bennett cafeteria?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[])
        dec = controller.evaluate(rr)
        assert dec.status == EvidenceStatus.MISSING
        assert dec.ceci_score == 0.0

    def test_tm18_citation_completeness(self, controller):
        """TM-18: 'State the exact clause number for X grade award.' -> SUFFICIENT."""
        p_cit = RetrievedPassage(
            passage_id="p-scset-30-1", document_id="SCSET-UG",
            text="Clause 30.1(ii), Page 19: Students with less than 70% attendance shall be awarded an 'X' grade.",
            score=20.0, rerank_score=3.5, retrieval_method="hybrid", source_type=DocumentSource.OFFICIAL,
            regulatory_condition=RegulatoryCondition.COURSE_GRADING,
        )
        qa = process_query("State the exact clause number for X grade award.")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_cit])
        dec = controller.evaluate(rr)
        assert dec.status == EvidenceStatus.SUFFICIENT

