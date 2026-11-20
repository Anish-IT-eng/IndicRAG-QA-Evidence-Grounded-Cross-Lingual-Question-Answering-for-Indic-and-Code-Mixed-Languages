"""
Tests for Independent Model Verification and Deterministic Validation Framework.

Covers all required behaviors:
1. Both verifiers agreeing correctly (auto_validated)
2. Verifier disagreement (needs_review)
3. Incorrect evidence quotes (auto_rejected)
4. Unsupported answers (unsupported flag / rejection)
5. Duplicate and near-duplicate questions (auto_rejected)
6. Placeholder questions (auto_rejected)
7. False unanswerable classifications
8. Historical/current regulation conflicts (needs_review)
9. Malformed verifier JSON (graceful fallback to needs_review)
10. Model timeout and unavailable model (graceful fallback to needs_review)
11. Reproducible decision outcomes
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Generator
import pytest

from app.evaluation.model_verifier import (
    DeterministicCheckResult,
    DeterministicValidator,
    IndependentModelVerifier,
    IndependentVerificationPipeline,
    VerificationDecisionController,
    VerifierEvaluation,
    VerifierVerdict,
)
from app.models.schemas import ValidationStatus


# ─────────────────────────────────────────────────────────────────────────────
# Test Fixtures: In-memory mock database
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE documents (
            document_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            source_url TEXT,
            source_type TEXT NOT NULL DEFAULT 'official',
            file_hash TEXT NOT NULL DEFAULT 'dummyhash',
            ingestion_timestamp TEXT NOT NULL DEFAULT '2026-11-10',
            ingestion_status TEXT NOT NULL DEFAULT 'completed',
            is_current INTEGER,
            academic_year TEXT,
            superseded_by TEXT
        );

        CREATE TABLE passages (
            passage_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL REFERENCES documents(document_id),
            text TEXT NOT NULL,
            page_number INTEGER,
            section TEXT,
            heading TEXT
        );
    """)

    # Current document
    conn.execute("""
        INSERT INTO documents (document_id, filename, is_current, academic_year, superseded_by)
        VALUES ('doc-current-01', 'Academic-Rules-for-SCSET_UG.pdf', 1, '2026-27', NULL)
    """)
    # Historical document
    conn.execute("""
        INSERT INTO documents (document_id, filename, is_current, academic_year, superseded_by)
        VALUES ('doc-hist-01', 'SEAS-Ordinance-Rules-Regulations-2017.pdf', 0, '2017-18', NULL)
    """)

    # Passages
    conn.execute("""
        INSERT INTO passages (passage_id, document_id, text, page_number, section, heading)
        VALUES (
            'pass-01',
            'doc-current-01',
            'A student must have a minimum of 75% attendance in each course to be eligible to appear in the end term examination. Students with attendance between 60% and 75% may be condoned by the Dean on medical grounds.',
            19,
            '30',
            'Attendance Requirements'
        )
    """)
    conn.execute("""
        INSERT INTO passages (passage_id, document_id, text, page_number, section, heading)
        VALUES (
            'pass-02',
            'doc-hist-01',
            'Old 2017 ordinance rule: Minimum attendance was 70% in all registered courses.',
            15,
            '12',
            'Old Attendance Regulation'
        )
    """)
    conn.commit()

    @contextmanager
    def _get_test_db() -> Generator[sqlite3.Connection, None, None]:
        yield conn

    return _get_test_db


@pytest.fixture
def base_valid_candidate():
    return {
        "question_id": "q-valid-101",
        "original_question": "What is the minimum attendance required to appear in the end term examination?",
        "query_language": "en",
        "query_script": "Latin",
        "question_type": "direct",
        "answerability": "answerable",
        "reference_answer": "Students must have a minimum of 75% attendance in each course.",
        "gold_passage_ids": ["pass-01"],
        "source_document_id": "doc-current-01",
        "page_number": 19,
        "section": "30",
        "gold_evidence_quotes": ["A student must have a minimum of 75% attendance in each course"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 & 2: Both Verifiers Agree (Accept & Reject)
# ─────────────────────────────────────────────────────────────────────────────

def test_both_verifiers_agree_accept(mock_db, base_valid_candidate):
    verifier_a = IndependentModelVerifier(
        model_name="qwen2.5:3b",
        model_family="qwen",
        custom_caller=lambda p, s: json.dumps({
            "candidate_id": base_valid_candidate["question_id"],
            "verdict": "ACCEPT",
            "answer_correctness": True,
            "evidence_support": True,
            "answerability": "answerable",
            "language_correctness": True,
            "contradiction_detected": False,
            "explanation": "Answer is fully supported by clause 30.",
            "issues": []
        })
    )
    verifier_b = IndependentModelVerifier(
        model_name="llama3.2:3b",
        model_family="llama",
        custom_caller=lambda p, s: json.dumps({
            "candidate_id": base_valid_candidate["question_id"],
            "verdict": "ACCEPT",
            "answer_correctness": True,
            "evidence_support": True,
            "answerability": "answerable",
            "language_correctness": True,
            "contradiction_detected": False,
            "explanation": "Verified against passage text.",
            "issues": []
        })
    )

    pipeline = IndependentVerificationPipeline(verifier_a, verifier_b, db_conn_factory=mock_db)
    results = pipeline.run_pipeline([base_valid_candidate])

    assert len(results) == 1
    res = results[0]
    assert res.final_status == ValidationStatus.AUTO_VALIDATED
    assert res.deterministic_result.passed is True
    assert res.verifier_a_result.verdict == VerifierVerdict.ACCEPT
    assert res.verifier_b_result.verdict == VerifierVerdict.ACCEPT


def test_both_verifiers_agree_reject(mock_db, base_valid_candidate):
    verifier_a = IndependentModelVerifier(
        model_name="qwen2.5:3b",
        model_family="qwen",
        custom_caller=lambda p, s: json.dumps({
            "candidate_id": base_valid_candidate["question_id"],
            "verdict": "REJECT",
            "answer_correctness": False,
            "evidence_support": False,
            "answerability": "answerable",
            "language_correctness": True,
            "contradiction_detected": False,
            "explanation": "Reference answer is inaccurate.",
            "issues": ["Inaccurate factual threshold"]
        })
    )
    verifier_b = IndependentModelVerifier(
        model_name="llama3.2:3b",
        model_family="llama",
        custom_caller=lambda p, s: json.dumps({
            "candidate_id": base_valid_candidate["question_id"],
            "verdict": "REJECT",
            "answer_correctness": False,
            "evidence_support": False,
            "answerability": "answerable",
            "language_correctness": True,
            "contradiction_detected": False,
            "explanation": "Not supported by university regulations.",
            "issues": ["Factually incorrect"]
        })
    )

    pipeline = IndependentVerificationPipeline(verifier_a, verifier_b, db_conn_factory=mock_db)
    results = pipeline.run_pipeline([base_valid_candidate])

    assert len(results) == 1
    res = results[0]
    assert res.final_status == ValidationStatus.AUTO_REJECTED
    assert "DUAL_VERIFIER_REJECTION" in res.failure_categories


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Verifier Disagreement -> needs_review
# ─────────────────────────────────────────────────────────────────────────────

def test_verifier_disagreement(mock_db, base_valid_candidate):
    verifier_a = IndependentModelVerifier(
        model_name="qwen2.5:3b",
        model_family="qwen",
        custom_caller=lambda p, s: json.dumps({
            "candidate_id": base_valid_candidate["question_id"],
            "verdict": "ACCEPT",
            "answer_correctness": True,
            "evidence_support": True,
            "answerability": "answerable",
            "language_correctness": True,
            "contradiction_detected": False,
            "explanation": "Looks fine to Verifier A.",
            "issues": []
        })
    )
    verifier_b = IndependentModelVerifier(
        model_name="llama3.2:3b",
        model_family="llama",
        custom_caller=lambda p, s: json.dumps({
            "candidate_id": base_valid_candidate["question_id"],
            "verdict": "REJECT",
            "answer_correctness": False,
            "evidence_support": False,
            "answerability": "answerable",
            "language_correctness": True,
            "contradiction_detected": False,
            "explanation": "Verifier B disagrees with phrasing.",
            "issues": ["Question is slightly ambiguous"]
        })
    )

    pipeline = IndependentVerificationPipeline(verifier_a, verifier_b, db_conn_factory=mock_db)
    results = pipeline.run_pipeline([base_valid_candidate])

    assert len(results) == 1
    res = results[0]
    assert res.final_status == ValidationStatus.NEEDS_REVIEW
    assert "VERIFIER_DISAGREEMENT" in res.failure_categories


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Incorrect Evidence Quotes -> auto_rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_incorrect_evidence_quotes(mock_db, base_valid_candidate):
    bad_candidate = dict(base_valid_candidate)
    bad_candidate["gold_evidence_quotes"] = [
        "A student must maintain 99.9% attendance or be expelled from campus immediately"
    ]

    validator = DeterministicValidator(db_conn_factory=mock_db)
    det_res = validator.validate_candidate(bad_candidate)

    assert det_res.passed is False
    assert det_res.checks["quote_matches_passage"] is False
    assert "FABRICATED_OR_UNMATCHED_QUOTE" in det_res.failure_categories

    controller = VerificationDecisionController()
    status, failures, _ = controller.decide(bad_candidate, det_res)
    assert status == ValidationStatus.AUTO_REJECTED


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Unsupported Answers -> rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_unsupported_answers(mock_db, base_valid_candidate):
    empty_answer_candidate = dict(base_valid_candidate)
    empty_answer_candidate["reference_answer"] = ""

    validator = DeterministicValidator(db_conn_factory=mock_db)
    det_res = validator.validate_candidate(empty_answer_candidate)

    assert det_res.checks["answer_supported"] is False
    assert "EMPTY_ANSWERABLE_REFERENCE" in det_res.failure_categories


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Duplicate Questions -> auto_rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_duplicate_questions(mock_db, base_valid_candidate):
    candidate1 = dict(base_valid_candidate, question_id="q-orig")
    candidate2 = dict(
        base_valid_candidate,
        question_id="q-dup",
        original_question="What is the minimum attendance required to appear in the end semester examination?"
    )

    validator = DeterministicValidator(db_conn_factory=mock_db)
    res1 = validator.validate_candidate(candidate1)
    res2 = validator.validate_candidate(candidate2)

    assert res1.checks["not_duplicate"] is True
    assert res2.checks["not_duplicate"] is False
    assert "DUPLICATE_QUESTION" in res2.failure_categories

    controller = VerificationDecisionController()
    status, _, _ = controller.decide(candidate2, res2)
    assert status == ValidationStatus.AUTO_REJECTED


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: Placeholder Questions -> auto_rejected
# ─────────────────────────────────────────────────────────────────────────────

def test_placeholder_questions(mock_db, base_valid_candidate):
    placeholder_candidate = dict(
        base_valid_candidate,
        original_question="Question text in specified language",
        reference_answer="Concise reference answer (or null if unanswerable)"
    )

    validator = DeterministicValidator(db_conn_factory=mock_db)
    det_res = validator.validate_candidate(placeholder_candidate)

    assert det_res.checks["not_placeholder"] is False
    assert "PLACEHOLDER_DETECTED" in det_res.failure_categories

    controller = VerificationDecisionController()
    status, _, _ = controller.decide(placeholder_candidate, det_res)
    assert status == ValidationStatus.AUTO_REJECTED


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: False Unanswerable Classifications
# ─────────────────────────────────────────────────────────────────────────────

def test_false_unanswerable_with_fabricated_evidence(mock_db, base_valid_candidate):
    unans_candidate = dict(
        base_valid_candidate,
        answerability="unanswerable",
        reference_answer="Unanswerable",
        gold_evidence_quotes=["This quote was completely fabricated by LLM"]
    )

    validator = DeterministicValidator(db_conn_factory=mock_db)
    det_res = validator.validate_candidate(unans_candidate)

    assert det_res.checks["quote_matches_passage"] is False
    assert "UNANSWERABLE_FABRICATED_EVIDENCE" in det_res.failure_categories


# ─────────────────────────────────────────────────────────────────────────────
# Test 9: Historical Regulation Conflicts -> needs_review
# ─────────────────────────────────────────────────────────────────────────────

def test_historical_regulation_conflicts(mock_db, base_valid_candidate):
    hist_candidate = dict(
        base_valid_candidate,
        source_document_id="doc-hist-01",
        gold_passage_ids=["pass-02"],
        gold_evidence_quotes=["Old 2017 ordinance rule: Minimum attendance was 70% in all registered courses."],
        original_question="What is the current required attendance for all undergraduate students?"
    )

    validator = DeterministicValidator(db_conn_factory=mock_db)
    det_res = validator.validate_candidate(hist_candidate)

    assert det_res.checks["academic_applicability_valid"] is False
    assert "HISTORICAL_APPLICABILITY_CONFLICT" in det_res.failure_categories

    controller = VerificationDecisionController()
    status, failures, _ = controller.decide(hist_candidate, det_res)
    assert status == ValidationStatus.NEEDS_REVIEW


# ─────────────────────────────────────────────────────────────────────────────
# Test 10: Malformed Verifier JSON -> needs_review
# ─────────────────────────────────────────────────────────────────────────────

def test_malformed_verifier_json(mock_db, base_valid_candidate):
    malformed_verifier = IndependentModelVerifier(
        model_name="test-model",
        model_family="test",
        custom_caller=lambda p, s: "This is not JSON at all: [broken output {"
    )

    eval_res = malformed_verifier.evaluate_candidate(base_valid_candidate, "sample evidence")
    assert eval_res.verdict == VerifierVerdict.UNCERTAIN
    assert any("ExecutionError" in i for i in eval_res.issues)

    controller = VerificationDecisionController()
    validator = DeterministicValidator(db_conn_factory=mock_db)
    det_res = validator.validate_candidate(base_valid_candidate)

    status, _, _ = controller.decide(
        base_valid_candidate,
        det_res,
        verifier_a=eval_res,
        verifier_b=eval_res
    )
    assert status == ValidationStatus.NEEDS_REVIEW


# ─────────────────────────────────────────────────────────────────────────────
# Test 11: Model Timeout and Unavailable Model -> needs_review
# ─────────────────────────────────────────────────────────────────────────────

def test_model_timeout_and_unavailable(mock_db, base_valid_candidate):
    def _timeout_caller(p, s):
        raise TimeoutError("Ollama HTTP connection timed out after 60s")

    timeout_verifier = IndependentModelVerifier(
        model_name="timeout-model",
        model_family="test",
        custom_caller=_timeout_caller
    )

    eval_res = timeout_verifier.evaluate_candidate(base_valid_candidate, "evidence")
    assert eval_res.verdict == VerifierVerdict.UNCERTAIN
    assert "TimeoutError" in eval_res.explanation

    controller = VerificationDecisionController()
    validator = DeterministicValidator(db_conn_factory=mock_db)
    det_res = validator.validate_candidate(base_valid_candidate)

    status, _, _ = controller.decide(
        base_valid_candidate,
        det_res,
        verifier_a=eval_res,
        verifier_b=eval_res
    )
    assert status == ValidationStatus.NEEDS_REVIEW


# ─────────────────────────────────────────────────────────────────────────────
# Test 12: Reproducible Decision Outcomes
# ─────────────────────────────────────────────────────────────────────────────

def test_reproducible_decision_outcomes(mock_db, base_valid_candidate):
    v_a = IndependentModelVerifier(
        model_name="qwen2.5:3b",
        model_family="qwen",
        custom_caller=lambda p, s: json.dumps({
            "candidate_id": base_valid_candidate["question_id"],
            "verdict": "ACCEPT",
            "answer_correctness": True,
            "evidence_support": True,
            "answerability": "answerable",
            "language_correctness": True,
            "contradiction_detected": False,
            "explanation": "Deterministic verification pass",
            "issues": []
        })
    )
    v_b = IndependentModelVerifier(
        model_name="llama3.2:3b",
        model_family="llama",
        custom_caller=lambda p, s: json.dumps({
            "candidate_id": base_valid_candidate["question_id"],
            "verdict": "ACCEPT",
            "answer_correctness": True,
            "evidence_support": True,
            "answerability": "answerable",
            "language_correctness": True,
            "contradiction_detected": False,
            "explanation": "Deterministic verification pass",
            "issues": []
        })
    )

    p1 = IndependentVerificationPipeline(v_a, v_b, db_conn_factory=mock_db)
    r1 = p1.run_pipeline([base_valid_candidate])

    p2 = IndependentVerificationPipeline(v_a, v_b, db_conn_factory=mock_db)
    r2 = p2.run_pipeline([base_valid_candidate])

    assert r1[0].final_status == r2[0].final_status == ValidationStatus.AUTO_VALIDATED
    assert r1[0].failure_categories == r2[0].failure_categories
    assert r1[0].deterministic_result.checks == r2[0].deterministic_result.checks

