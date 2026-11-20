"""
Unit and Integration Test Suite for M6 Phase 2B:
Theory-Anchored Evidence Scoring, CECI, and Six-State Evidence Controller.

Verifies:
1. Score normalizers (BM25, Dense, Cross-Encoder, RRF rank fusion) and boundary behaviors.
2. CECI convex combination properties, same-scale margin, and conservative fallbacks.
3. Six-state evidence controller and deterministic override precedence.
4. Atomic claim grounding (numeric, date, negation, and semantic entailment).
5. Model verifier unanswerable candidate audit template.
6. Regression test for E10 retrieval score defect.
"""
from __future__ import annotations

import math
import pytest

from app.models.schemas import (
    ClaimVerificationVerdict,
    DocumentSource,
    DocumentVersionInfo,
    EvidenceDecision,
    EvidenceStatus,
    QueryAnalysis,
    QuestionType,
    RetrievedPassage,
    RetrievalResult,
)
from app.retrieval.score_normalizer import (
    NormalizedScore,
    RetrievalModality,
    normalize_bm25_score,
    normalize_cross_encoder_score,
    normalize_dense_score,
    normalize_retrieval_score,
    normalize_rrf_ranks,
)
from app.retrieval.ceci import (
    CECIEstimator,
    CECIResult,
    CECIWeights,
)
from app.retrieval.evidence_controller import (
    EvidenceController,
    get_evidence_controller,
)
from app.generation.claim_grounding import (
    ClaimGroundingVerifier,
    decompose_into_atomic_claims,
)
from app.evaluation.model_verifier import (
    DeterministicValidator,
    IndependentModelVerifier,
    VerifierVerdict,
    _UNANSWERABLE_VERIFIER_USER_PROMPT_TEMPLATE,
    _VERIFIER_USER_PROMPT_TEMPLATE,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Tests for Transparent Score Normalization
# ─────────────────────────────────────────────────────────────────────────────

class TestScoreNormalizers:
    """Verifies heuristic normalizers map disparate score scales into [0, 1]."""

    def test_bm25_sigmoid_normalization(self):
        # Baseline center = 15.0, scale = 3.0
        norm_center = normalize_bm25_score(15.0)
        assert math.isclose(norm_center.normalized_score, 0.5, abs_tol=1e-4)
        assert norm_center.raw_score == 15.0
        assert norm_center.modality == RetrievalModality.BM25
        assert norm_center.is_empirically_calibrated is False

        # Monotonicity
        norm_low = normalize_bm25_score(9.0)
        norm_high = normalize_bm25_score(24.0)
        assert 0.0 <= norm_low.normalized_score < norm_center.normalized_score < norm_high.normalized_score <= 1.0

        # Boundary / extreme handling
        norm_neg = normalize_bm25_score(-10.0)
        assert norm_neg.normalized_score == 0.0
        norm_huge = normalize_bm25_score(1000.0)
        assert norm_huge.normalized_score == 1.0
        norm_nan = normalize_bm25_score(float("nan"))
        assert norm_nan.normalized_score == 0.0

    def test_dense_logistic_normalization(self):
        norm_zero = normalize_dense_score(0.0)
        assert math.isclose(norm_zero.normalized_score, 0.5, abs_tol=1e-4)
        assert norm_zero.modality == RetrievalModality.DENSE
        assert norm_zero.is_empirically_calibrated is False

        # Typical cosine similarity ranges in [0.3, 0.85]
        norm_typical = normalize_dense_score(0.72)
        assert 0.5 < norm_typical.normalized_score < 1.0
        assert norm_typical.raw_score == 0.72

        # Boundary handling
        norm_nan = normalize_dense_score(float("nan"))
        assert norm_nan.normalized_score == 0.0
        norm_inf = normalize_dense_score(float("inf"))
        assert norm_inf.normalized_score == 1.0

    def test_cross_encoder_normalization(self):
        norm_logit = normalize_cross_encoder_score(3.5)
        assert norm_logit.raw_score == 3.5
        assert 0.5 < norm_logit.normalized_score <= 1.0
        assert norm_logit.modality == RetrievalModality.CROSS_ENCODER
        assert norm_logit.is_empirically_calibrated is False

        norm_neg_logit = normalize_cross_encoder_score(-4.0)
        assert 0.0 <= norm_neg_logit.normalized_score < 0.5

    def test_rrf_rank_normalization_and_ties(self):
        # Empty pool
        assert normalize_rrf_ranks([]) == []

        # Single candidate pool: must return 1.0
        single = [{"passage_id": "p1", "score": 0.033}]
        norm_single = normalize_rrf_ranks(single, get_score_fn=lambda x: x["score"])
        assert len(norm_single) == 1
        assert norm_single[0].normalized_score == 1.0

        # Multi-candidate pool with strict rank order (K=4)
        candidates = [
            {"passage_id": "p1", "score": 0.05},
            {"passage_id": "p2", "score": 0.04},
            {"passage_id": "p3", "score": 0.03},
            {"passage_id": "p4", "score": 0.02},
        ]
        norm_list = normalize_rrf_ranks(candidates, get_score_fn=lambda x: x["score"])
        assert len(norm_list) == 4
        # Ranks 1, 2, 3, 4 -> (4 - 1 + 1)/4 = 1.0, 0.75, 0.50, 0.25
        assert math.isclose(norm_list[0].normalized_score, 1.0)
        assert math.isclose(norm_list[1].normalized_score, 0.75)
        assert math.isclose(norm_list[2].normalized_score, 0.50)
        assert math.isclose(norm_list[3].normalized_score, 0.25)

        # Tie handling: 2 tied candidates at rank 2 and 3
        tied_candidates = [
            {"passage_id": "p1", "score": 0.05},
            {"passage_id": "p2", "score": 0.03},
            {"passage_id": "p3", "score": 0.03},
            {"passage_id": "p4", "score": 0.01},
        ]
        norm_tied = normalize_rrf_ranks(tied_candidates, get_score_fn=lambda x: x["score"])
        assert norm_tied[1].normalized_score == norm_tied[2].normalized_score
        # Avg rank for tied items is 2.5 -> (4 - 2.5 + 1)/4 = 2.5 / 4 = 0.625
        assert math.isclose(norm_tied[1].normalized_score, 0.625)

    def test_unified_dispatcher(self):
        s_bm25 = normalize_retrieval_score(15.0, "bm25")
        assert s_bm25.modality == RetrievalModality.BM25
        s_dense = normalize_retrieval_score(0.8, "dense")
        assert s_dense.modality == RetrievalModality.DENSE
        s_ce = normalize_retrieval_score(2.0, "cross_encoder")
        assert s_ce.modality == RetrievalModality.CROSS_ENCODER


# ─────────────────────────────────────────────────────────────────────────────
# 2. Tests for CECI Estimator
# ─────────────────────────────────────────────────────────────────────────────

class TestCECIEstimator:
    """Verifies CECI convex combination formulation, margins, and fallbacks."""

    def test_convex_weights_validation(self):
        # Valid default weights sum to 1.0
        w = CECIWeights()
        total = w.w_relevance + w.w_margin + w.w_consensus + w.w_keyword_cov + w.w_regulatory
        assert math.isclose(total, 1.0)

        # Negative weights rejected
        with pytest.raises(ValueError):
            CECIWeights(w_relevance=-0.1, w_margin=0.4, w_consensus=0.3, w_keyword_cov=0.2, w_regulatory=0.2)

        # Sum != 1.0 rejected
        with pytest.raises(ValueError):
            CECIWeights(w_relevance=0.5, w_margin=0.5, w_consensus=0.5, w_keyword_cov=0.0, w_regulatory=0.0)

    def test_zero_passages_fallback(self):
        estimator = CECIEstimator()
        res = estimator.estimate([])
        assert res.ceci_heuristic_score == 0.0
        for f_name, f_val in res.features.items():
            assert f_val == 0.0

    def test_relevance_source_precedence_and_margin(self):
        estimator = CECIEstimator()

        # Case A: Cross-encoder scores present
        p1 = RetrievedPassage(
            passage_id="p1", document_id="d1", text="Course attendance rule",
            score=0.8, retrieval_method="hybrid", rerank_score=3.0, source_type=DocumentSource.OFFICIAL,
        )
        p2 = RetrievedPassage(
            passage_id="p2", document_id="d1", text="Exam eligibility rule",
            score=0.7, retrieval_method="hybrid", rerank_score=1.0, source_type=DocumentSource.OFFICIAL,
        )
        res = estimator.estimate([p1, p2])
        assert res.primary_modality == "cross_encoder"
        # Margin calculated on cross-encoder normalized scores:
        # p1 norm cross-encoder > p2 norm cross-encoder
        assert res.features["f1_top1_relevance"] > 0.5
        assert res.features["f2_score_margin"] > 0.0

    def test_conservative_missing_keyword_fallback(self):
        estimator = CECIEstimator()
        p1 = RetrievedPassage(
            passage_id="p1", document_id="d1", text="General ordinance",
            score=0.8, retrieval_method="dense", source_type=DocumentSource.OFFICIAL,
        )
        # QueryAnalysis with empty intent keywords -> conservative neutral 0.5
        qa = QueryAnalysis(original_query="What is the rule?", intent_keywords=[])
        res = estimator.estimate([p1], query_analysis=qa)
        assert res.features["f4_keyword_coverage"] == 0.5


# ─────────────────────────────────────────────────────────────────────────────
# 3. Tests for Six-State Evidence Controller & Override Precedence
# ─────────────────────────────────────────────────────────────────────────────

class TestEvidenceController:
    """Verifies the six evidence states and strict deterministic override hierarchy."""

    @pytest.fixture
    def controller(self):
        return EvidenceController(tau_suff=0.65, tau_insuff=0.35)

    def test_override_step1_clarification_required(self, controller):
        # Query asking for attendance threshold without stating cohort/batch
        # with retrieved passages showing both 2017 and Notification 307
        p_2017 = RetrievedPassage(
            passage_id="p-2017", document_id="doc-2017",
            text="Under Ordinance 2017 Clause 30, minimum attendance is 80%.",
            score=18.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
        )
        p_307 = RetrievedPassage(
            passage_id="p-307", document_id="doc-307",
            text="Notification 307 for 2022 batch states minimum attendance is 75%.",
            score=17.5, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
        )
        qa = QueryAnalysis(
            original_query="What is the minimum attendance percentage required for B.Tech?",
            intent_keywords=["attendance", "minimum", "percentage"],
        )
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_2017, p_307])
        dec = controller.evaluate(rr)

        assert dec.status == EvidenceStatus.CLARIFICATION_REQUIRED
        assert dec.clarification_needed is True
        assert "cohort" in dec.explanation.lower()

    def test_override_step2_conflicting_versions(self, controller):
        # Passage marked superseded
        p_valid = RetrievedPassage(
            passage_id="pv", document_id="dv", text="Current policy text",
            score=18.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
        )
        p_conf = RetrievedPassage(
            passage_id="pc", document_id="dc", text="Old policy text",
            score=17.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
            version_info=DocumentVersionInfo(superseded_by="dv"),
        )
        qa = QueryAnalysis(original_query="What is the grading policy?")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_valid, p_conf])
        dec = controller.evaluate(rr)

        assert dec.status == EvidenceStatus.CONFLICTING
        assert len(dec.conflicting_passages) == 1

    def test_override_step3_zero_retrieved_missing(self, controller):
        qa = QueryAnalysis(original_query="Irrelevant topic")
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[])
        dec = controller.evaluate(rr)

        assert dec.status == EvidenceStatus.MISSING
        assert dec.ceci_score == 0.0

    def test_override_step4_contradictory_premise_blocks_high_ceci(self, controller):
        # Even with high retrieval scores, asking for makeup exam after 'X' grade must yield INSUFFICIENT
        p_rule = RetrievedPassage(
            passage_id="p1", document_id="d1",
            text="A student receiving 'X' grade due to attendance shortage shall repeat the entire course. No makeup examination.",
            score=25.0, retrieval_method="bm25", rerank_score=4.0, source_type=DocumentSource.OFFICIAL,
        )
        qa = QueryAnalysis(
            original_query="If a student gets an 'X' grade due to attendance shortage, can they get special approval for a makeup exam?",
            intent_keywords=["attendance", "makeup"],
        )
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p_rule])
        dec = controller.evaluate(rr)

        # Must NOT be SUFFICIENT despite high scores
        assert dec.status == EvidenceStatus.INSUFFICIENT
        assert "contradictory premise" in dec.explanation.lower()

    def test_state_sufficient_on_high_ceci(self, controller):
        p1 = RetrievedPassage(
            passage_id="p1", document_id="d1",
            text="Clause 14: A student must earn a minimum of 160 credits for B.Tech degree completion.",
            score=22.0, retrieval_method="bm25", rerank_score=3.5, source_type=DocumentSource.OFFICIAL,
        )
        qa = QueryAnalysis(
            original_query="How many total credits are required for B.Tech degree completion?",
            intent_keywords=["credits", "completion", "degree"],
        )
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p1])
        dec = controller.evaluate(rr)

        assert dec.status == EvidenceStatus.SUFFICIENT
        assert dec.ceci_score is not None
        assert dec.ceci_score >= 0.65

    def test_state_partial_on_multi_part_incomplete_coverage(self, controller):
        p1 = RetrievedPassage(
            passage_id="p1", document_id="d1",
            text="Credits requirement is 160.",
            score=20.0, retrieval_method="bm25", rerank_score=2.5, source_type=DocumentSource.OFFICIAL,
        )
        # Multi-part query asking about both credits AND hostel fees
        qa = QueryAnalysis(
            original_query="What are the B.Tech credits requirement and what is the hostel curfew time?",
            is_multi_part=True,
            sub_questions=["What is the credits requirement?", "What is the hostel curfew time?"],
            intent_keywords=["credits", "curfew", "hostel", "time"],
        )
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[p1])
        dec = controller.evaluate(rr)

        # Incomplete coverage (< 0.6) yields PARTIAL
        assert dec.status == EvidenceStatus.PARTIAL


# ─────────────────────────────────────────────────────────────────────────────
# 4. Tests for Atomic Claim Grounding
# ─────────────────────────────────────────────────────────────────────────────

class TestClaimGrounding:
    """Verifies atomic claim decomposition and numeric/date/negation checks."""

    def test_atomic_claim_decomposition(self):
        text = (
            "According to official university regulations, the minimum attendance required is 75%. "
            "Students with less than 75% attendance receive an 'X' grade. "
            "In conclusion, students must repeat the entire course."
        )
        claims = decompose_into_atomic_claims(text)
        assert len(claims) >= 2
        # Boilerplate transitions should be filtered or minimized
        assert any("75%" in c for c in claims)
        assert any("'X' grade" in c for c in claims)

    def test_numeric_verification_catches_hallucination(self):
        verifier = ClaimGroundingVerifier()
        # Answer claims 60% attendance, but passage specifies 75%
        answer = "The minimum attendance percentage required is 60% for all students."
        p = RetrievedPassage(
            passage_id="p1", document_id="d1",
            text="Notification 307: The minimum attendance requirement is 75% in each course.",
            score=1.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
        )
        res = verifier.verify_claims(answer, [p])
        assert res.contains_contradiction is True
        assert res.contradicted_claims >= 1
        claim = res.claims[0]
        assert claim.numeric_verified is False
        assert claim.verdict == ClaimVerificationVerdict.CONTRADICTED

    def test_polarity_verification_catches_false_permission(self):
        verifier = ClaimGroundingVerifier()
        # Answer claims student is permitted to take makeup exam, but passage strictly prohibits
        answer = "A student debarred with 'X' grade can take a makeup exam with Dean approval."
        p = RetrievedPassage(
            passage_id="p1", document_id="d1",
            text="Students awarded 'X' grade due to attendance shortage shall not be permitted to take makeup or supplementary examinations.",
            score=1.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
        )
        res = verifier.verify_claims(answer, [p])
        assert res.contains_contradiction is True
        assert res.claims[0].negation_verified is False
        assert res.claims[0].verdict == ClaimVerificationVerdict.CONTRADICTED

    def test_fully_grounded_claim_is_entailed(self):
        verifier = ClaimGroundingVerifier()
        answer = "A student must earn a minimum of 160 credits for the B.Tech degree."
        p = RetrievedPassage(
            passage_id="p1", document_id="d1",
            text="To qualify for the award of B.Tech degree, a student must successfully earn 160 credits.",
            score=1.0, retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
        )
        res = verifier.verify_claims(answer, [p])
        assert res.all_claims_entailed is True
        assert res.claims[0].verdict == ClaimVerificationVerdict.ENTAILED


# ─────────────────────────────────────────────────────────────────────────────
# 5. Tests for Model Verifier Unanswerable Path
# ─────────────────────────────────────────────────────────────────────────────

class TestModelVerifierUnanswerablePath:
    """Verifies that unanswerable candidates use the specialized negative audit path."""

    def test_unanswerable_template_selected_and_does_not_reject_empty_citations(self):
        candidate = {
            "question_id": "q-unans-01",
            "original_question": "What is the fee refund policy for students who withdraw after the final date?",
            "reference_answer": "UNANSWERABLE — The official academic ordinances do not specify the fee refund policy for late withdrawals.",
            "query_language": "en",
            "query_script": "Latin",
            "question_type": "direct",
            "answerability": "unanswerable",
            "gold_evidence_quotes": [],
            "source_document_id": "doc-ordinance",
        }

        # Mock caller to inspect user prompt
        prompt_captured = {}
        def mock_caller(prompt, system):
            prompt_captured["user"] = prompt
            return '{"candidate_id": "q-unans-01", "verdict": "ACCEPT", "answer_correctness": true, "evidence_support": true, "answerability": "unanswerable", "language_correctness": true, "contradiction_detected": false, "explanation": "Valid unanswerable question"}'

        verifier = IndependentModelVerifier(
            model_name="test-verifier",
            model_family="llama",
            custom_caller=mock_caller,
        )
        eval_res = verifier.evaluate_candidate(candidate, evidence_text="")

        assert eval_res.verdict == VerifierVerdict.ACCEPT
        assert "UNANSWERABILITY AUDIT" in prompt_captured["user"]
        assert "DO NOT reject simply because evidence_passages is \"(No evidence passages cited)\"" in prompt_captured["user"]


# ─────────────────────────────────────────────────────────────────────────────
# 6. Regression Test for E10 Retrieval Score Defect
# ─────────────────────────────────────────────────────────────────────────────

class TestE10DefectRegression:
    """
    Verifies that the E10 defect (claiming certainty on weak/insufficient evidence)
    is permanently prevented by the heuristic controller.
    """

    def test_weak_retrieval_triggers_insufficient_or_retry(self):
        ctrl = get_evidence_controller()
        weak_passage = RetrievedPassage(
            passage_id="p-weak", document_id="d1",
            text="The university was established by the state legislature in 2016.",
            score=3.0,  # Far below provisional BM25 center
            retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
        )
        qa = QueryAnalysis(
            original_query="What is the exact penalty for late course drop in odd semester?",
            intent_keywords=["penalty", "late", "drop"],
        )
        rr = RetrievalResult(query_analysis=qa, retrieved_passages=[weak_passage])
        dec = ctrl.evaluate(rr, attempt=1)

        assert dec.status == EvidenceStatus.INSUFFICIENT
        assert dec.retry_recommended is True
        assert dec.ceci_score is not None
        assert dec.ceci_score < 0.35

