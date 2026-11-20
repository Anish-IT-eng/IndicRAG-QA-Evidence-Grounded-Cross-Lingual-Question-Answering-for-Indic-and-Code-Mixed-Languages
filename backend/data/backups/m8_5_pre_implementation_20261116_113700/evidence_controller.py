"""
Evidence and Answerability Controller for IndicRAG-QA.

Evaluates retrieved passages and query context using the Composite Evidence
Confidence Index (CECI) and strict six-state override precedence:
  1. CLARIFICATION_REQUIRED : Query lacks mandatory cohort/batch or program parameter.
  2. CONFLICTING           : Version conflicts or genuine regulatory contradictions.
  3. MISSING                : Out-of-domain query or zero retrieved passages in corpus.
  4. INSUFFICIENT           : Contradictory user premise, zero citations, or low CECI (< 0.35).
  5. PARTIAL                : Incomplete sub-question coverage or moderate CECI [0.35, 0.65).
  6. SUFFICIENT             : Full evidence grounded in official corpus (CECI >= 0.65).

CRITICAL RESEARCH RULES:
- High CECI score CAN NEVER override missing citations, contradictory premises,
  missing cohort parameters, or genuine document conflicts.
- Precedence is strictly deterministic and hierarchical.
- CECI thresholds (tau_suff = 0.65, tau_insuff = 0.35) are heuristic pilot parameters.
"""
from __future__ import annotations

import re
from typing import Optional, Sequence, Tuple

from app.core.config import settings
from app.core.logging_config import logger
from app.models.schemas import (
    EvidenceDecision,
    EvidenceStatus,
    QueryAnalysis,
    RetrievedPassage,
    RetrievalResult,
)
from app.retrieval.ceci import CECIEstimator, CECIResult


# Cohort keywords indicating explicit temporal or regulation context
_COHORT_KEYWORDS = {
    "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027",
    "notification 307", "ordinance 2017", "clause 30", "batch", "cohort",
    "academic year", "शैक्षणिक कैलेंडर", "सत्र", "अधिसूचना 307",
}

# Premise contradiction patterns (action prohibited by fundamental university ordinance)
_CONTRADICTORY_PREMISE_PATTERNS = [
    # Makeup or supplementary after debarment with 'X' grade
    (
        re.compile(r"('x'|x\s+grade|grade\s+'?x'?|attendance\s+shortage|उपस्थिति\s+की\s+कमी).*?(makeup|make-up|supplementary|re-exam|special\s+approval|छूट|विशेष\s+अनुमति)", re.IGNORECASE),
        "Debarment due to attendance shortage ('X' grade) strictly disqualifies student from makeup or supplementary examinations; full course repetition is mandatory."
    ),
    # Makeup exam after passing course or receiving passing grade
    (
        re.compile(r"(passed|cleared|grade\s+[abc]|उत्तीर्ण).*?(makeup|make-up|re-exam|reappear|supplementary)", re.IGNORECASE),
        "Makeup examinations are strictly restricted to approved medical/extenuating absences or failed courses; they cannot be taken for courses already passed."
    ),
    # Course registration while under suspension / expulsion
    (
        re.compile(r"(suspended|expelled|rusticated|निलंबित|निष्कासित).*?(register|enroll|summer|semester|पंजीकरण)", re.IGNORECASE),
        "Students under disciplinary suspension or expulsion are strictly barred from academic registration."
    ),
]


class EvidenceController:
    """
    Interprets retrieval results and produces an EvidenceDecision with CECI
    confidence metrics and six-state override hierarchy.
    """

    def __init__(
        self,
        min_score: float = settings.evidence_min_score,
        sufficient_count: int = settings.evidence_sufficient_count,
        max_retries: int = settings.max_retrieval_retries,
        tau_suff: float = 0.65,
        tau_insuff: float = 0.35,
        ceci_estimator: Optional[CECIEstimator] = None,
    ):
        self.min_score = min_score
        self.sufficient_count = sufficient_count
        self.max_retries = max_retries
        self.tau_suff = tau_suff
        self.tau_insuff = tau_insuff
        self.ceci_estimator = ceci_estimator or CECIEstimator()

    # ── Public interface ──────────────────────────────────────────────────────

    def evaluate(
        self,
        retrieval_result: RetrievalResult,
        attempt: int = 1,
    ) -> EvidenceDecision:
        passages = retrieval_result.retrieved_passages
        query_analysis = retrieval_result.query_analysis
        query_text = (query_analysis.original_query or "").strip()

        # ── Step 1: Precedence Override — Missing Mandatory Cohort Parameter ──
        # If policy varies across cohorts and no cohort/year is specified in query
        needs_clarification, clarif_reason = self._check_missing_cohort_parameter(
            query_text, query_analysis, passages
        )
        if needs_clarification:
            logger.info("Override Step 1: CLARIFICATION_REQUIRED triggered for query '%s'", query_text[:60])
            return EvidenceDecision(
                status=EvidenceStatus.CLARIFICATION_REQUIRED,
                valid_passages=passages,
                clarification_needed=True,
                explanation=clarif_reason,
                retry_recommended=False,
            )

        # ── Step 2: Precedence Override — Genuine Version Conflicts ──────────
        valid, conflicting = self._split_passages(passages)
        
        # A genuine version conflict occurs when competing regulations clash in the top evidence:
        # e.g. top passage is conflicting, or a conflicting passage closely rivals the valid passage,
        # or an explicit superseded_by relationship connects the top documents.
        is_genuine_conflict = False
        if conflicting and valid:
            top_valid_score = max((p.score for p in valid), default=0.0)
            top_conf_score = max((p.score for p in conflicting), default=0.0)
            # Check if top passage itself is flagged as conflicting
            if passages[0] in conflicting:
                is_genuine_conflict = True
            # Or if conflicting passage is a close rival to the top valid passage
            elif top_conf_score >= top_valid_score * 0.80:
                valid_doc_ids = {p.document_id for p in valid}
                conf_doc_ids = {p.document_id for p in conflicting}
                if valid_doc_ids != conf_doc_ids:
                    is_genuine_conflict = True

        if is_genuine_conflict:
            logger.info("Override Step 2: CONFLICTING triggered (%d conflicting vs %d valid)", len(conflicting), len(valid))
            cov = self._coverage_score(valid, query_analysis)
            return EvidenceDecision(
                status=EvidenceStatus.CONFLICTING,
                valid_passages=valid,
                conflicting_passages=conflicting,
                coverage_score=cov,
                explanation=(
                    "Multiple conflicting document versions found with competing relevance. "
                    "The applicable rule differs by academic year or program."
                ),
                retry_recommended=False,
            )

        # ── Step 3: Precedence Override — Zero Retrieved Evidence (MISSING) ───
        if not passages:
            logger.info("Override Step 3: MISSING triggered (0 passages retrieved)")
            return EvidenceDecision(
                status=EvidenceStatus.MISSING,
                explanation=(
                    "No passages were retrieved. "
                    "The information does not exist in the official university corpus."
                ),
                retry_recommended=attempt < self.max_retries,
                ceci_score=0.0,
            )

        # Out-of-domain check
        if self._is_out_of_domain(query_text, valid):
            logger.info("Override Step 3: MISSING triggered (out-of-domain query)")
            return EvidenceDecision(
                status=EvidenceStatus.MISSING,
                valid_passages=valid,
                explanation=(
                    "The query appears out-of-domain with respect to Bennett University academic regulations."
                ),
                retry_recommended=False,
                ceci_score=0.0,
            )

        # ── Step 4: Precedence Override — Contradictory User Premise ─────────
        # High CECI can NEVER override a contradictory premise
        has_contradiction, contra_reason = self._check_contradictory_premise(
            query_text, query_analysis, valid
        )
        if has_contradiction:
            logger.info("Override Step 4: INSUFFICIENT triggered by contradictory premise")
            return EvidenceDecision(
                status=EvidenceStatus.INSUFFICIENT,
                valid_passages=valid,
                coverage_score=0.0,
                explanation=f"Contradictory premise detected: {contra_reason}",
                retry_recommended=False,
            )

        # ── Step 5: Precedence Override — Zero Valid Passages / Citations ─────
        if not valid:
            logger.info("Override Step 5: INSUFFICIENT triggered (0 valid passages)")
            return EvidenceDecision(
                status=EvidenceStatus.INSUFFICIENT,
                valid_passages=[],
                coverage_score=0.0,
                explanation="No valid non-superseded evidence passages available to answer the query.",
                retry_recommended=attempt < self.max_retries,
                ceci_score=0.0,
            )

        # ── Step 6: CECI Evaluation & Heuristic Decision Rules ────────────────
        ceci_result = self.ceci_estimator.estimate(
            passages=valid,
            query_analysis=query_analysis,
        )
        psi = ceci_result.ceci_heuristic_score
        coverage = self._coverage_score(valid, query_analysis)
        sub_coverage = self._sub_question_coverage(valid, query_analysis)

        # Coverage check: if query has intent keywords but evidence has zero keyword coverage,
        # the retrieved evidence cannot answer the query
        if query_analysis.intent_keywords and coverage == 0.0:
            return EvidenceDecision(
                status=EvidenceStatus.INSUFFICIENT,
                valid_passages=valid,
                coverage_score=0.0,
                sub_question_coverage=sub_coverage,
                retry_recommended=attempt < self.max_retries,
                explanation="None of the query intent keywords were found in the retrieved evidence.",
                ceci_score=psi,
                ceci_features=ceci_result.features,
            )

        # Decision thresholding
        if psi >= self.tau_suff:
            if query_analysis.is_multi_part and coverage < 0.6:
                status = EvidenceStatus.PARTIAL
                explanation = (
                    f"Evidence confidence is high (CECI: {psi:.3f} >= {self.tau_suff:.2f}), "
                    f"but multi-part query has incomplete sub-question coverage ({coverage:.2f})."
                )
            else:
                status = EvidenceStatus.SUFFICIENT
                explanation = (
                    f"Sufficient evidence identified (CECI: {psi:.3f} >= {self.tau_suff:.2f})."
                )
        elif psi >= self.tau_insuff:
            status = EvidenceStatus.PARTIAL
            explanation = (
                f"Partial evidence confidence (CECI: {psi:.3f} in [{self.tau_insuff:.2f}, {self.tau_suff:.2f}))."
            )
        else:
            status = EvidenceStatus.INSUFFICIENT
            explanation = (
                f"Insufficient evidence confidence (CECI: {psi:.3f} < {self.tau_insuff:.2f})."
            )

        retry = (status == EvidenceStatus.INSUFFICIENT and attempt < self.max_retries)

        return EvidenceDecision(
            status=status,
            valid_passages=valid,
            coverage_score=coverage,
            sub_question_coverage=sub_coverage,
            retry_recommended=retry,
            explanation=explanation,
            ceci_score=psi,
            ceci_features=ceci_result.features,
        )

    # ── Deterministic Helper Verifiers ───────────────────────────────────────

    def _check_missing_cohort_parameter(
        self,
        query_text: str,
        query_analysis: QueryAnalysis,
        passages: list[RetrievedPassage],
    ) -> Tuple[bool, str]:
        """
        Detects queries regarding rules that changed across cohorts (e.g. attendance)
        where the user omits the cohort/batch/year parameter.
        """
        q_lower = query_text.lower()

        # Check if query touches cohort-varying topics (e.g. minimum attendance threshold)
        is_attendance_threshold_query = (
            ("attendance" in q_lower or "उपस्थिति" in q_lower)
            and ("minimum" in q_lower or "न्यूनतम" in q_lower or "percentage" in q_lower or "कितने प्रतिशत" in q_lower or "required" in q_lower)
        )

        if not is_attendance_threshold_query:
            return False, ""

        # Check if any cohort/year keyword is present
        has_cohort_spec = any(kw in q_lower for kw in _COHORT_KEYWORDS)
        if has_cohort_spec:
            return False, ""

        # Also inspect whether retrieved evidence shows multi-ordinance variance (2017 vs Notification 307 / 2022)
        has_2017 = any("2017" in (p.text + (p.heading or "") + (p.section or "")) for p in passages)
        has_307 = any("307" in (p.text + (p.heading or "") + (p.section or "")) or "2022" in (p.text + (p.heading or "")) for p in passages)

        if has_2017 and has_307:
            return (
                True,
                "Query lacks student cohort or admission year parameter. Minimum attendance requirements "
                "differ between Ordinance 2017 (80% with 10% condonation) and Notification 307 / 2022 regulations "
                "(75% with 5% condonation). Please specify student batch or admission year."
            )

        return False, ""

    def _check_contradictory_premise(
        self,
        query_text: str,
        query_analysis: QueryAnalysis,
        passages: list[RetrievedPassage],
    ) -> Tuple[bool, str]:
        """
        Detects queries whose premise directly contradicts fundamental university ordinances.
        """
        for pattern, explanation in _CONTRADICTORY_PREMISE_PATTERNS:
            if pattern.search(query_text):
                return True, explanation
        return False, ""

    def _is_out_of_domain(
        self,
        query_text: str,
        passages: list[RetrievedPassage],
    ) -> bool:
        """
        Heuristic out-of-domain detector for queries completely unrelated to academic regulations.
        """
        if not passages:
            return True
        out_of_domain_tokens = {
            "recipe", "cooking", "pizza", "burger", "astronomy", "spacecraft",
            "cricket world cup", "hollywood", "weather in tokyo", "fifa",
        }
        q_tokens = set(re.findall(r"\w+", query_text.lower()))
        if q_tokens.intersection(out_of_domain_tokens):
            return True
        return False

    def _split_passages(
        self,
        passages: list[RetrievedPassage],
    ) -> tuple[list[RetrievedPassage], list[RetrievedPassage]]:
        """Separate valid passages from those flagged as superseded or conflicting."""
        valid, conflicting = [], []
        for p in passages:
            if p.version_info.superseded_by:
                conflicting.append(p)
            elif p.is_valid_for_query is False:
                conflicting.append(p)
            else:
                valid.append(p)
        return valid, conflicting

    def _coverage_score(
        self,
        passages: list[RetrievedPassage],
        query_analysis: QueryAnalysis,
    ) -> float:
        """
        Heuristic coverage: check how many intent keywords appear in evidence text.
        """
        if not query_analysis.intent_keywords or not passages:
            return 1.0 if passages else 0.0

        all_text = " ".join(p.text.lower() for p in passages)
        matched = sum(
            1 for kw in query_analysis.intent_keywords if kw in all_text
        )
        return matched / len(query_analysis.intent_keywords)

    def _sub_question_coverage(
        self,
        passages: list[RetrievedPassage],
        query_analysis: QueryAnalysis,
    ) -> dict[str, bool]:
        """
        For each sub-question, check whether any retrieved passage seems relevant.
        Uses keyword overlap heuristic.
        """
        coverage: dict[str, bool] = {}
        all_text = " ".join(p.text.lower() for p in passages)
        for sq in query_analysis.sub_questions:
            kws = [w.lower() for w in sq.split() if len(w) > 3]
            if not kws:
                coverage[sq] = True
                continue
            matched = sum(1 for kw in kws if kw in all_text)
            coverage[sq] = matched >= max(1, len(kws) // 2)
        return coverage


# Singleton
_evidence_controller: Optional[EvidenceController] = None


def get_evidence_controller() -> EvidenceController:
    global _evidence_controller
    if _evidence_controller is None:
        _evidence_controller = EvidenceController()
    return _evidence_controller
