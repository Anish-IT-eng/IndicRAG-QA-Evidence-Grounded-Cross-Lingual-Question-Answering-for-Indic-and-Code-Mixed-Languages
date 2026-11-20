"""
Independent Model Verification and Deterministic Validation Framework for IndicRAG-QA.

Implements M3 dataset validation:
1. Deterministic validation checks (grounding, passage verification, quote verification,
   duplicate detection, placeholder detection, language consistency, applicability).
2. Two independent model verifiers from distinct model families (run sequentially).
3. Decision controller with four formal states:
   - auto_validated
   - auto_rejected
   - needs_review
   - human_verified
4. Output reporting and auditable JSONL execution logging.

CRITICAL RESEARCH RULES:
- Never label automated validation as human verification.
- Do not import automated approvals into the human-approved dataset.
- Candidate generation model (e.g. gemma:2b) must not count as either verifier.
"""
from __future__ import annotations

import csv
import json
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import httpx

from app.core.config import settings
from app.core.database import get_db
from app.core.logging_config import logger
from app.models.schemas import (
    AnswerabilityLabel,
    QueryLanguage,
    QueryScript,
    QuestionType,
    ValidationStatus,
)


# ─────────────────────────────────────────────────────────────────────────────
# Enums and Schemas
# ─────────────────────────────────────────────────────────────────────────────

class VerifierVerdict(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class VerifierEvaluation:
    candidate_id: str
    model_name: str
    model_family: str
    verdict: VerifierVerdict
    answer_correctness: bool
    evidence_support: bool
    answerability: str                     # "answerable" | "unanswerable"
    language_correctness: bool
    contradiction_detected: bool
    explanation: str
    supporting_quote: Optional[str] = None
    issues: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    raw_response: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d


@dataclass
class DeterministicCheckResult:
    passed: bool
    checks: dict[str, bool]
    issues: list[str]
    failure_categories: list[str]
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FinalValidationResult:
    candidate_id: str
    original_question: str
    query_language: str
    query_script: str
    question_type: str
    answerability: str
    reference_answer: Optional[str]
    source_document_id: Optional[str]
    gold_passage_ids: list[str]
    gold_evidence_quotes: list[str]
    deterministic_result: DeterministicCheckResult
    verifier_a_result: Optional[VerifierEvaluation]
    verifier_b_result: Optional[VerifierEvaluation]
    final_status: ValidationStatus
    failure_categories: list[str]
    issues: list[str]
    timestamp: str
    prompt_version: str = "v1.0-independent-verification"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["final_status"] = self.final_status.value
        return d


# ─────────────────────────────────────────────────────────────────────────────
# 1. Deterministic Validation Engine
# ─────────────────────────────────────────────────────────────────────────────

_PLACEHOLDER_PATTERNS = [
    re.compile(r"question\s+text\s+in\s+specified\s+language", re.IGNORECASE),
    re.compile(r"concise\s+reference\s+answer", re.IGNORECASE),
    re.compile(r"exact\s+supporting\s+quote", re.IGNORECASE),
    re.compile(r"null\s+if\s+unanswerable", re.IGNORECASE),
    re.compile(r"<\s*insert\b", re.IGNORECASE),
    re.compile(r"\[\s*insert\b", re.IGNORECASE),
    re.compile(r"^\s*null\s*$", re.IGNORECASE),
    re.compile(r"^\s*none\s*$", re.IGNORECASE),
]

_DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097F]")
_LATIN_REGEX = re.compile(r"[A-Za-z]")


class DeterministicValidator:
    """
    Strict, deterministic quality verification of candidate QA instances.
    Evaluates evidence ground truth, quote matching against DB, placeholders,
    metadata integrity, language scripts, and duplicates.
    """

    def __init__(self, db_conn_factory=None):
        self.get_db = db_conn_factory or get_db
        self._seen_questions: list[str] = []

    def reset_duplicate_tracker(self):
        self._seen_questions.clear()

    def _normalize_text(self, s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r"[^\w\s]", "", s)
        return re.sub(r"\s+", " ", s)

    def _jaccard_similarity(self, s1: str, s2: str) -> float:
        set1 = set(self._normalize_text(s1).split())
        set2 = set(self._normalize_text(s2).split())
        if not set1 or not set2:
            return 0.0
        return len(set1 & set2) / len(set1 | set2)

    def validate_candidate(self, candidate: dict[str, Any]) -> DeterministicCheckResult:
        checks: dict[str, bool] = {
            "required_metadata_present": True,
            "not_placeholder": True,
            "not_duplicate": True,
            "valid_text_structure": True,
            "source_doc_exists": True,
            "passage_exists": True,
            "quote_matches_passage": True,
            "answer_supported": True,
            "language_script_consistent": True,
            "academic_applicability_valid": True,
            "no_superseded_conflict": True,
        }
        issues: list[str] = []
        failure_categories: list[str] = []
        details: dict[str, Any] = {}

        qid = str(candidate.get("question_id") or "").strip()
        question = str(candidate.get("original_question") or "").strip()
        answer = str(candidate.get("reference_answer") or "").strip()
        lang = str(candidate.get("query_language") or "").strip().lower()
        script = str(candidate.get("query_script") or "").strip()
        qtype = str(candidate.get("question_type") or "").strip()
        answerability = str(candidate.get("answerability") or "").strip().lower()
        doc_id = str(candidate.get("source_document_id") or "").strip()

        # Parse gold passages
        raw_pids = candidate.get("gold_passage_ids")
        if isinstance(raw_pids, str):
            try:
                pids = json.loads(raw_pids)
            except Exception:
                pids = [raw_pids] if raw_pids else []
        elif isinstance(raw_pids, list):
            pids = raw_pids
        else:
            pids = []

        # Parse gold quotes
        raw_quotes = candidate.get("gold_evidence_quotes")
        if isinstance(raw_quotes, str):
            try:
                quotes = json.loads(raw_quotes)
            except Exception:
                quotes = [raw_quotes] if raw_quotes else []
        elif isinstance(raw_quotes, list):
            quotes = raw_quotes
        else:
            quotes = []

        # 1. Required metadata
        if not qid or not question or not lang or not qtype or not answerability or not doc_id:
            checks["required_metadata_present"] = False
            issues.append("Missing mandatory metadata fields")
            failure_categories.append("METADATA_INCOMPLETE")

        # 2. Placeholder detection
        is_placeholder = False
        for pat in _PLACEHOLDER_PATTERNS:
            if pat.search(question) or pat.search(answer):
                is_placeholder = True
                break
        if is_placeholder:
            checks["not_placeholder"] = False
            issues.append(f"Placeholder or template text detected in candidate {qid}")
            failure_categories.append("PLACEHOLDER_DETECTED")

        # 2b. Garbled / repetitive nonsense text detection
        words = question.split()
        if len(words) >= 3:
            avg_word_len = sum(len(w) for w in words) / len(words)
            short_ratio = sum(1 for w in words if len(w) <= 2) / len(words)
            if avg_word_len <= 1.8 or short_ratio > 0.65:
                checks["valid_text_structure"] = False
                issues.append(f"Garbled, repetitive, or fragmented text structure detected in candidate {qid}")
                failure_categories.append("GARBLED_OR_NONSENSE_TEXT")

        # 3. Duplicate detection
        for prev_q in self._seen_questions:
            sim = self._jaccard_similarity(question, prev_q)
            if sim >= 0.80:
                checks["not_duplicate"] = False
                issues.append(f"Near-duplicate question detected (similarity {sim:.2f} with previous candidate)")
                failure_categories.append("DUPLICATE_QUESTION")
                break
        self._seen_questions.append(question)

        # 4. Source document check from SQLite
        doc_row = None
        try:
            with self.get_db() as conn:
                doc_row = conn.execute(
                    "SELECT document_id, filename, is_current, academic_year, superseded_by "
                    "FROM documents WHERE document_id = ?",
                    (doc_id,)
                ).fetchone()
        except Exception as e:
            issues.append(f"DB access error for document {doc_id}: {e}")

        if not doc_row:
            checks["source_doc_exists"] = False
            issues.append(f"Source document {doc_id} not found in database")
            failure_categories.append("DOCUMENT_NOT_FOUND")
        else:
            details["document_filename"] = doc_row["filename"]
            details["document_is_current"] = doc_row["is_current"]
            details["document_superseded_by"] = doc_row["superseded_by"]

            # 9. Applicability & 10. Superseded check
            if doc_row["is_current"] == 0 and "historical" not in doc_row["filename"].lower() and "2017" in doc_row["filename"]:
                # Historical document used without qualification
                if "historical" not in question.lower() and "2017" not in question:
                    checks["academic_applicability_valid"] = False
                    issues.append(f"Question relies on historical document {doc_row['filename']} without year qualification")
                    failure_categories.append("HISTORICAL_APPLICABILITY_CONFLICT")

            if doc_row["superseded_by"]:
                checks["no_superseded_conflict"] = False
                issues.append(f"Document {doc_row['filename']} has been superseded by {doc_row['superseded_by']}")
                failure_categories.append("SUPERSEDED_DOCUMENT_CONFLICT")

        # 5. Passage existence & 6. Quote matching from SQLite
        retrieved_passages: list[dict[str, Any]] = []
        if pids:
            try:
                with self.get_db() as conn:
                    for pid in pids:
                        p_row = conn.execute(
                            "SELECT passage_id, document_id, text, page_number, section "
                            "FROM passages WHERE passage_id = ?",
                            (str(pid),)
                        ).fetchone()
                        if not p_row:
                            checks["passage_exists"] = False
                            issues.append(f"Passage ID {pid} not found in passages table")
                            failure_categories.append("PASSAGE_NOT_FOUND")
                        else:
                            retrieved_passages.append(dict(p_row))
            except Exception as e:
                issues.append(f"DB error fetching passages: {e}")
        elif answerability == "answerable":
            checks["passage_exists"] = False
            issues.append("Answerable question provided 0 gold passage IDs")
            failure_categories.append("MISSING_EVIDENCE_PASSAGE")

        details["retrieved_passages_count"] = len(retrieved_passages)

        # 6. Quote matching
        if quotes and retrieved_passages:
            all_passage_text = " ".join(p["text"] for p in retrieved_passages)
            norm_all = self._normalize_text(all_passage_text)
            for q_quote in quotes:
                if not q_quote or q_quote.strip() in ("", "[]", "null"):
                    continue
                norm_quote = self._normalize_text(q_quote)
                if norm_quote not in norm_all:
                    checks["quote_matches_passage"] = False
                    issues.append(f"Supporting quote does not match original passage text: '{q_quote[:60]}...'")
                    failure_categories.append("FABRICATED_OR_UNMATCHED_QUOTE")
        elif quotes and not retrieved_passages and answerability == "answerable":
            checks["quote_matches_passage"] = False
            failure_categories.append("FABRICATED_OR_UNMATCHED_QUOTE")

        # 7. Answer supported & Answerability check
        if answerability == "answerable":
            if not answer or answer.lower() in ("null", "none", ""):
                checks["answer_supported"] = False
                issues.append("Answerable question has empty or null reference answer")
                failure_categories.append("EMPTY_ANSWERABLE_REFERENCE")
        elif answerability == "unanswerable":
            # For unanswerable, if answer claims specific factual claims not supported by any passage
            if len(quotes) > 0 and quotes != [""]:
                # Often generator hallucinated an evidence quote for an unanswerable question
                if checks["quote_matches_passage"] is False:
                    checks["answer_supported"] = False
                    issues.append("Unanswerable question contains fabricated quote")
                    failure_categories.append("UNANSWERABLE_FABRICATED_EVIDENCE")

        # 8. Language and script consistency
        has_devanagari = bool(_DEVANAGARI_REGEX.search(question))
        has_latin = bool(_LATIN_REGEX.search(question))

        if lang == "hi" and not has_devanagari:
            checks["language_script_consistent"] = False
            issues.append(f"Question tagged as 'hi' (Devanagari Hindi) contains 0 Devanagari characters: '{question[:40]}'")
            failure_categories.append("LANGUAGE_SCRIPT_MISMATCH")
        elif lang == "en" and has_devanagari:
            checks["language_script_consistent"] = False
            issues.append(f"Question tagged as 'en' contains Devanagari characters: '{question[:40]}'")
            failure_categories.append("LANGUAGE_SCRIPT_MISMATCH")

        passed = all(checks.values())
        return DeterministicCheckResult(
            passed=passed,
            checks=checks,
            issues=issues,
            failure_categories=failure_categories,
            details=details,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Independent Model Verifier Engine
# ─────────────────────────────────────────────────────────────────────────────

_VERIFIER_SYSTEM_PROMPT = """You are an independent academic regulation QA auditor for Bennett University.
Your job is to independently evaluate whether a candidate QA record is strictly accurate, factual, well-formed, and completely grounded in the provided official source evidence.

Evaluate the following dimensions:
1. Question clarity, grammaticality, and relevance to university rules.
2. Reference answer correctness: Is it factually supported by the evidence? Does it contain hallucinations?
3. Evidence support and entailment: Does the cited evidence passage actually prove the reference answer?
4. Answerability: Is the question genuinely answerable or unanswerable from the provided text?
5. Language and script correctness: Is the text linguistically natural and consistent with the tagged language?
6. Contradictions: Does the claim contradict university rules or rely on outdated/superseded terms?

CRITICAL:
- You must output ONLY a valid, parseable JSON object.
- Do not output preamble, greetings, or explanations outside the JSON object.
- Verdict must be exactly one of: "ACCEPT", "REJECT", or "UNCERTAIN".
- If any hallucination, unsupported claim, or template placeholder exists, verdict MUST be "REJECT".
- If the question is ambiguous or evidence is incomplete, verdict MUST be "UNCERTAIN".

Required JSON format:
{
  "candidate_id": "<candidate_id>",
  "verdict": "ACCEPT | REJECT | UNCERTAIN",
  "answer_correctness": true | false,
  "evidence_support": true | false,
  "answerability": "answerable | unanswerable",
  "language_correctness": true | false,
  "contradiction_detected": true | false,
  "explanation": "concise rationale",
  "supporting_quote": "exact quote if supported, or null",
  "issues": ["list of detected issues, or empty"]
}
"""

_VERIFIER_USER_PROMPT_TEMPLATE = """Please audit the following candidate QA record:

Candidate ID: {candidate_id}
Tagged Language: {language} ({script})
Question Type: {question_type}
Claimed Answerability: {answerability}

QUESTION:
{question}

REFERENCE ANSWER:
{reference_answer}

CLAIMED SUPPORTING QUOTE:
{supporting_quote}

OFFICIAL EVIDENCE PASSAGES:
{evidence_passages}

Output your audit strictly as JSON conforming to the requested schema:"""

_UNANSWERABLE_VERIFIER_USER_PROMPT_TEMPLATE = """Please audit the following UNANSWERABLE candidate QA record:

Candidate ID: {candidate_id}
Tagged Language: {language} ({script})
Question Type: {question_type}
Target Evaluation: UNANSWERABILITY AUDIT (Candidate is claimed to be UNANSWERABLE)

QUESTION:
{question}

REFERENCE ANSWER / REFUSAL EXPLANATION:
{reference_answer}

CLAIMED REASON / CONTEXT:
{supporting_quote}

OFFICIAL CORPUS RETRIEVAL / RELEVANT EXCERPTS (if any):
{evidence_passages}

CRITICAL UNANSWERABLE AUDIT CRITERIA:
- The question must be genuinely unanswerable from Bennett University official regulations (e.g. out-of-scope, missing cohort parameters, contradictory user premise, or unspecified policy).
- The absence of an evidence citation or lack of supporting quote is EXPECTED for unanswerable records; DO NOT reject simply because evidence_passages is "(No evidence passages cited)" or quote is empty.
- If the question is genuinely unanswerable and the reference answer appropriately declines or explains why the rule is absent/prohibited, set answer_correctness: true, evidence_support: true, answerability: "unanswerable", and verdict: "ACCEPT".
- If the question IS actually answerable from official regulations, or if the reference answer hallucinates non-existent facts, set verdict: "REJECT".

Output your audit strictly as JSON conforming to the requested schema:"""


class IndependentModelVerifier:
    """
    Manages an independent LLM verifier instance via Ollama REST API.
    Calls are isolated and sequential to keep memory footprint within 16 GB laptop constraints.
    """

    def __init__(
        self,
        model_name: str,
        model_family: str,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        custom_caller: Optional[Callable[[str, str], str]] = None,
    ):
        self.model_name = model_name
        self.model_family = model_family
        self.base_url = base_url or settings.ollama_base_url
        self.timeout = timeout
        self.custom_caller = custom_caller  # For test mocks / deterministic fixtures

    def _extract_json_response(self, raw: str) -> dict[str, Any]:
        """Resilient multi-strategy JSON extractor."""
        raw = raw.strip()
        # Direct parse
        try:
            return json.loads(raw)
        except Exception:
            pass

        # Markdown fenced code block
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1))
            except Exception:
                pass

        # Outer bracket search
        bracket_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if bracket_match:
            try:
                return json.loads(bracket_match.group(0))
            except Exception:
                pass

        raise ValueError(f"Could not parse valid JSON from model response: {raw[:150]}...")

    def evaluate_candidate(
        self,
        candidate: dict[str, Any],
        evidence_text: str,
    ) -> VerifierEvaluation:
        qid = str(candidate.get("question_id") or "")
        question = str(candidate.get("original_question") or "")
        answer = str(candidate.get("reference_answer") or "")
        lang = str(candidate.get("query_language") or "en")
        script = str(candidate.get("query_script") or "Latin")
        qtype = str(candidate.get("question_type") or "direct")
        answerability = str(candidate.get("answerability") or "answerable")

        raw_quotes = candidate.get("gold_evidence_quotes") or []
        quote_str = json.dumps(raw_quotes) if isinstance(raw_quotes, list) else str(raw_quotes)

        # Select specialized template for unanswerable candidates to prevent false rejections
        if answerability.lower() == "unanswerable":
            template = _UNANSWERABLE_VERIFIER_USER_PROMPT_TEMPLATE
        else:
            template = _VERIFIER_USER_PROMPT_TEMPLATE

        user_prompt = template.format(
            candidate_id=qid,
            language=lang,
            script=script,
            question_type=qtype,
            answerability=answerability,
            question=question,
            reference_answer=answer,
            supporting_quote=quote_str,
            evidence_passages=evidence_text if evidence_text.strip() else "(No evidence passages cited)",
        )

        t0 = time.time()
        raw_output = ""
        try:
            if self.custom_caller:
                raw_output = self.custom_caller(user_prompt, _VERIFIER_SYSTEM_PROMPT)
            else:
                payload = {
                    "model": self.model_name,
                    "prompt": user_prompt,
                    "system": _VERIFIER_SYSTEM_PROMPT,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for strict evaluation
                        "num_predict": 512,
                    },
                }
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(f"{self.base_url}/api/generate", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    raw_output = data.get("response", "").strip()

            latency_ms = (time.time() - t0) * 1000.0
            parsed = self._extract_json_response(raw_output)

            # Map verdict string to enum
            v_str = str(parsed.get("verdict") or "UNCERTAIN").strip().upper()
            if v_str == "ACCEPT":
                verdict = VerifierVerdict.ACCEPT
            elif v_str == "REJECT":
                verdict = VerifierVerdict.REJECT
            else:
                verdict = VerifierVerdict.UNCERTAIN

            return VerifierEvaluation(
                candidate_id=qid,
                model_name=self.model_name,
                model_family=self.model_family,
                verdict=verdict,
                answer_correctness=bool(parsed.get("answer_correctness", False)),
                evidence_support=bool(parsed.get("evidence_support", False)),
                answerability=str(parsed.get("answerability", "answerable")),
                language_correctness=bool(parsed.get("language_correctness", True)),
                contradiction_detected=bool(parsed.get("contradiction_detected", False)),
                explanation=str(parsed.get("explanation") or ""),
                supporting_quote=parsed.get("supporting_quote"),
                issues=list(parsed.get("issues") or []),
                latency_ms=latency_ms,
                raw_response=raw_output,
            )

        except Exception as e:
            latency_ms = (time.time() - t0) * 1000.0
            logger.warning("Verifier %s failed on candidate %s: %s", self.model_name, qid, e)
            return VerifierEvaluation(
                candidate_id=qid,
                model_name=self.model_name,
                model_family=self.model_family,
                verdict=VerifierVerdict.UNCERTAIN,
                answer_correctness=False,
                evidence_support=False,
                answerability=answerability,
                language_correctness=True,
                contradiction_detected=False,
                explanation=f"Verifier failed or timed out: {type(e).__name__}: {e}",
                issues=[f"ExecutionError: {e}"],
                latency_ms=latency_ms,
                raw_response=raw_output,
            )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Decision Controller
# ─────────────────────────────────────────────────────────────────────────────

class VerificationDecisionController:
    """
    Combines deterministic checks and two independent model verifiers to make
    a final decision for each candidate QA record.

    Allowed statuses:
    - auto_validated
    - auto_rejected
    - needs_review
    - human_verified (never set by automated verification)
    """

    def decide(
        self,
        candidate: dict[str, Any],
        deterministic: DeterministicCheckResult,
        verifier_a: Optional[VerifierEvaluation] = None,
        verifier_b: Optional[VerifierEvaluation] = None,
    ) -> Tuple[ValidationStatus, list[str], list[str]]:
        """
        Returns (status, combined_failure_categories, combined_issues).
        """
        issues = list(deterministic.issues)
        failures = list(deterministic.failure_categories)

        # 1. Deterministic Hard Rejections
        # Any template placeholder, duplicate question, missing document, or fabricated quote
        # is immediately and unequivocally rejected.
        hard_reject_checks = [
            "not_placeholder",
            "not_duplicate",
            "valid_text_structure",
            "source_doc_exists",
            "passage_exists",
        ]
        if any(not deterministic.checks.get(c, True) for c in hard_reject_checks):
            return ValidationStatus.AUTO_REJECTED, failures, issues

        if deterministic.checks.get("quote_matches_passage") is False:
            return ValidationStatus.AUTO_REJECTED, failures, issues

        # 2. Both Verifiers Failed or Unavailable
        if not verifier_a or not verifier_b:
            issues.append("One or both independent verifiers were unavailable")
            failures.append("VERIFIER_UNAVAILABLE")
            return ValidationStatus.NEEDS_REVIEW, failures, issues

        if verifier_a.issues:
            issues.extend([f"VerifierA: {i}" for i in verifier_a.issues])
        if verifier_b.issues:
            issues.extend([f"VerifierB: {i}" for i in verifier_b.issues])

        # 3. Verifier Rejection
        # If both verifiers reject -> auto_rejected
        if verifier_a.verdict == VerifierVerdict.REJECT and verifier_b.verdict == VerifierVerdict.REJECT:
            failures.append("DUAL_VERIFIER_REJECTION")
            return ValidationStatus.AUTO_REJECTED, failures, issues

        # 4. Mandatory Acceptance Criteria for auto_validated:
        # - All deterministic checks passed
        # - Both verifiers return ACCEPT
        # - Both confirm answer_correctness == True
        # - Both confirm evidence_support == True
        # - Neither detects contradiction (contradiction_detected == False)
        # - Language correctness affirmed by both
        is_both_accept = (
            verifier_a.verdict == VerifierVerdict.ACCEPT and
            verifier_b.verdict == VerifierVerdict.ACCEPT
        )
        is_both_supported = (
            verifier_a.answer_correctness is True and
            verifier_b.answer_correctness is True and
            verifier_a.evidence_support is True and
            verifier_b.evidence_support is True
        )
        no_contradiction = (
            verifier_a.contradiction_detected is False and
            verifier_b.contradiction_detected is False
        )
        lang_ok = (
            verifier_a.language_correctness is True and
            verifier_b.language_correctness is True
        )

        if deterministic.passed and is_both_accept and is_both_supported and no_contradiction and lang_ok:
            return ValidationStatus.AUTO_VALIDATED, failures, issues

        # 5. Any Disagreement, Ambiguity, or Warning -> needs_review
        if verifier_a.verdict != verifier_b.verdict:
            failures.append("VERIFIER_DISAGREEMENT")
            issues.append(f"Disagreement: Verifier A ({verifier_a.model_name})={verifier_a.verdict.value}, Verifier B ({verifier_b.model_name})={verifier_b.verdict.value}")

        if verifier_a.verdict == VerifierVerdict.UNCERTAIN or verifier_b.verdict == VerifierVerdict.UNCERTAIN:
            failures.append("VERIFIER_UNCERTAINTY")

        if not deterministic.passed:
            failures.append("DETERMINISTIC_WARNING")

        if verifier_a.contradiction_detected or verifier_b.contradiction_detected:
            failures.append("CONTRADICTION_FLAGGED")

        return ValidationStatus.NEEDS_REVIEW, failures, issues


# ─────────────────────────────────────────────────────────────────────────────
# 4. Pipeline Coordinator, Reporting, and Audit Logging
# ─────────────────────────────────────────────────────────────────────────────

class IndependentVerificationPipeline:
    """
    Coordinates end-to-end verification across an entire dataset candidate list:
    1. Deterministic validation
    2. Sequential Verifier A execution
    3. Sequential Verifier B execution
    4. Decision controller adjudication
    5. Output writing (CSV, JSONL audit log, Markdown summary)
    """

    def __init__(
        self,
        verifier_a: IndependentModelVerifier,
        verifier_b: IndependentModelVerifier,
        db_conn_factory=None,
    ):
        self.verifier_a = verifier_a
        self.verifier_b = verifier_b
        self.db_conn_factory = db_conn_factory or get_db
        self.validator = DeterministicValidator(self.db_conn_factory)
        self.controller = VerificationDecisionController()

    def _get_evidence_text(self, candidate: dict[str, Any]) -> str:
        """Fetch passage texts from DB for the prompt."""
        raw_pids = candidate.get("gold_passage_ids")
        if isinstance(raw_pids, str):
            try:
                pids = json.loads(raw_pids)
            except Exception:
                pids = [raw_pids] if raw_pids else []
        elif isinstance(raw_pids, list):
            pids = raw_pids
        else:
            pids = []

        if not pids:
            return ""

        chunks = []
        try:
            with self.db_conn_factory() as conn:
                for pid in pids:
                    row = conn.execute(
                        "SELECT text, page_number, heading FROM passages WHERE passage_id = ?",
                        (str(pid),)
                    ).fetchone()
                    if row:
                        page_str = f" (page {row['page_number']})" if row["page_number"] else ""
                        heading_str = f" [{row['heading']}]" if row["heading"] else ""
                        chunks.append(f"Passage ID: {pid}{page_str}{heading_str}\n{row['text']}")
        except Exception as e:
            logger.warning("Error fetching evidence text: %s", e)

        return "\n\n".join(chunks)

    def run_pipeline(
        self,
        candidates: list[dict[str, Any]],
        skip_llm_if_deterministic_reject: bool = True,
    ) -> list[FinalValidationResult]:
        self.validator.reset_duplicate_tracker()
        results: list[FinalValidationResult] = []

        total = len(candidates)
        logger.info("Starting independent verification pipeline for %d candidates...", total)

        for idx, candidate in enumerate(candidates, 1):
            qid = str(candidate.get("question_id") or f"idx-{idx}")
            logger.info("[%d/%d] Processing candidate %s...", idx, total, qid[:8])

            # 1. Deterministic validation
            det_res = self.validator.validate_candidate(candidate)

            v_a_res: Optional[VerifierEvaluation] = None
            v_b_res: Optional[VerifierEvaluation] = None

            # Optimization: If deterministic check produces hard rejection (placeholder,
            # broken citation, missing doc), skip LLM calls to save memory & time.
            is_hard_reject = not det_res.checks.get("not_placeholder", True) or \
                             not det_res.checks.get("not_duplicate", True) or \
                             not det_res.checks.get("source_doc_exists", True) or \
                             not det_res.checks.get("passage_exists", True) or \
                             not det_res.checks.get("quote_matches_passage", True)

            if not (skip_llm_if_deterministic_reject and is_hard_reject):
                evidence_text = self._get_evidence_text(candidate)

                # 2. Sequential Verifier A execution
                v_a_res = self.verifier_a.evaluate_candidate(candidate, evidence_text)

                # 3. Sequential Verifier B execution
                v_b_res = self.verifier_b.evaluate_candidate(candidate, evidence_text)

            # 4. Decision Controller
            status, failures, issues = self.controller.decide(
                candidate=candidate,
                deterministic=det_res,
                verifier_a=v_a_res,
                verifier_b=v_b_res,
            )

            # Clean parsing for quotes / passage ids
            raw_pids = candidate.get("gold_passage_ids") or []
            if isinstance(raw_pids, str):
                try:
                    parsed_pids = json.loads(raw_pids)
                except Exception:
                    parsed_pids = [raw_pids]
            else:
                parsed_pids = raw_pids

            raw_quotes = candidate.get("gold_evidence_quotes") or []
            if isinstance(raw_quotes, str):
                try:
                    parsed_quotes = json.loads(raw_quotes)
                except Exception:
                    parsed_quotes = [raw_quotes]
            else:
                parsed_quotes = raw_quotes

            res = FinalValidationResult(
                candidate_id=qid,
                original_question=str(candidate.get("original_question") or ""),
                query_language=str(candidate.get("query_language") or ""),
                query_script=str(candidate.get("query_script") or ""),
                question_type=str(candidate.get("question_type") or ""),
                answerability=str(candidate.get("answerability") or ""),
                reference_answer=candidate.get("reference_answer"),
                source_document_id=candidate.get("source_document_id"),
                gold_passage_ids=parsed_pids,
                gold_evidence_quotes=parsed_quotes,
                deterministic_result=det_res,
                verifier_a_result=v_a_res,
                verifier_b_result=v_b_res,
                final_status=status,
                failure_categories=failures,
                issues=issues,
                timestamp=datetime.now().isoformat(),
            )
            results.append(res)

        return results

    @staticmethod
    def export_results_csv(results: list[FinalValidationResult], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        headers = [
            "candidate_id",
            "original_question",
            "query_language",
            "query_script",
            "question_type",
            "answerability",
            "final_status",
            "deterministic_passed",
            "verifier_a_model",
            "verifier_a_verdict",
            "verifier_b_model",
            "verifier_b_verdict",
            "failure_categories",
            "issues",
            "reference_answer",
            "source_document_id",
            "timestamp",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "candidate_id": r.candidate_id,
                    "original_question": r.original_question,
                    "query_language": r.query_language,
                    "query_script": r.query_script,
                    "question_type": r.question_type,
                    "answerability": r.answerability,
                    "final_status": r.final_status.value,
                    "deterministic_passed": "yes" if r.deterministic_result.passed else "no",
                    "verifier_a_model": r.verifier_a_result.model_name if r.verifier_a_result else "N/A",
                    "verifier_a_verdict": r.verifier_a_result.verdict.value if r.verifier_a_result else "N/A",
                    "verifier_b_model": r.verifier_b_result.model_name if r.verifier_b_result else "N/A",
                    "verifier_b_verdict": r.verifier_b_result.verdict.value if r.verifier_b_result else "N/A",
                    "failure_categories": "; ".join(r.failure_categories),
                    "issues": "; ".join(r.issues),
                    "reference_answer": r.reference_answer or "",
                    "source_document_id": r.source_document_id or "",
                    "timestamp": r.timestamp,
                })
        logger.info("Saved validation CSV to %s", output_path)

    @staticmethod
    def export_audit_jsonl(results: list[FinalValidationResult], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
        logger.info("Saved audit JSONL to %s", output_path)

    @staticmethod
    def generate_summary_report(
        results: list[FinalValidationResult],
        model_a_name: str,
        model_b_name: str,
        output_path: Optional[Path] = None,
    ) -> str:
        total = len(results)
        status_counts: dict[str, int] = {}
        lang_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}
        failure_counts: dict[str, int] = {}

        agree_accept = agree_reject = agree_uncertain = disagree = skipped_llm = 0

        for r in results:
            st = r.final_status.value
            status_counts[st] = status_counts.get(st, 0) + 1

            lang = r.query_language or "unknown"
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

            qtype = r.question_type or "unknown"
            type_counts[qtype] = type_counts.get(qtype, 0) + 1

            for fc in r.failure_categories:
                failure_counts[fc] = failure_counts.get(fc, 0) + 1

            if r.verifier_a_result and r.verifier_b_result:
                va = r.verifier_a_result.verdict
                vb = r.verifier_b_result.verdict
                if va == vb:
                    if va == VerifierVerdict.ACCEPT:
                        agree_accept += 1
                    elif va == VerifierVerdict.REJECT:
                        agree_reject += 1
                    else:
                        agree_uncertain += 1
                else:
                    disagree += 1
            else:
                skipped_llm += 1

        md = []
        md.append("# M3 Independent Model Verification Report\n")
        md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append(f"**Total Candidates Evaluated:** {total}\n")
        md.append(f"**Verifier A:** `{model_a_name}`")
        md.append(f"**Verifier B:** `{model_b_name}`\n")

        md.append("## 1. Validation Status Breakdown\n")
        md.append("| Status | Count | Percentage | Definition |")
        md.append("|---|---|---|---|")
        definitions = {
            "auto_validated": "Passed all deterministic checks + dual independent model agreement",
            "auto_rejected": "Clear fabricated/unmatched quotes, placeholders, or dual rejection",
            "needs_review": "Model disagreement, ambiguity, warnings, or missing passages",
            "human_verified": "Human review confirmed (never assigned by automated system)",
        }
        for st in ["auto_validated", "auto_rejected", "needs_review", "human_verified"]:
            cnt = status_counts.get(st, 0)
            pct = (cnt / total * 100) if total else 0
            md.append(f"| `{st}` | **{cnt}** | {pct:.1f}% | {definitions.get(st, '')} |")

        md.append("\n## 2. Independent Verifier Agreement Matrix\n")
        md.append("| Category | Count |")
        md.append("|---|---|")
        md.append(f"| Both Agree: ACCEPT | {agree_accept} |")
        md.append(f"| Both Agree: REJECT | {agree_reject} |")
        md.append(f"| Both Agree: UNCERTAIN | {agree_uncertain} |")
        md.append(f"| Verifier Disagreement | {disagree} |")
        md.append(f"| Skipped LLM (deterministic reject) | {skipped_llm} |")

        md.append("\n## 3. Distribution by Tagged Query Language\n")
        md.append("| Language | Count | Percentage |")
        md.append("|---|---|---|")
        for lang, cnt in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (cnt / total * 100) if total else 0
            md.append(f"| `{lang}` | {cnt} | {pct:.1f}% |")

        md.append("\n## 4. Failure Categories Summary\n")
        if failure_counts:
            md.append("| Failure Category | Count | Description |")
            md.append("|---|---|---|")
            for fc, cnt in sorted(failure_counts.items(), key=lambda x: x[1], reverse=True):
                md.append(f"| `{fc}` | {cnt} | Flagged during verification |")
        else:
            md.append("*(No failure categories triggered)*")

        report_str = "\n".join(md) + "\n"

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_str)
            logger.info("Saved validation summary report to %s", output_path)

        return report_str
