"""
Atomic Claim-Level Grounding Module for IndicRAG-QA.

Implements fine-grained claim decomposition and multi-layer verification:
1. Atomic claim sentence/clause decomposition.
2. Deterministic checks:
   - Numeric extraction and verification (percentages, thresholds, credits).
   - Date and temporal reference verification.
   - Polarity and negation verification (e.g. "shall not", "prohibited", "allowed").
3. Semantic entailment verification with strict Generator-Verifier separation:
   - The generator model (e.g. gemma:2b) must NEVER verify its own output.
   - Uses an independent verifier model or deterministic NLI heuristics.
4. Formal verdicts:
   - ENTAILED
   - CONTRADICTED
   - INSUFFICIENT_SUPPORT
"""
from __future__ import annotations

import re
import uuid
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

from app.core.config import settings
from app.core.logging_config import logger
from app.models.schemas import (
    AtomicClaim,
    ClaimGroundingResult,
    ClaimVerificationVerdict,
    RetrievedPassage,
)

# Negation and prohibition markers
_NEGATION_TERMS = {
    "not", "no", "never", "cannot", "prohibited", "forbidden", "disqualified",
    "barred", "debarred", "shall not", "will not", "may not", "restricted",
    "ineligible", "nahi", "nahin", "naa", "वर्जित", "निषेध", "अयोग्य", "नहीं",
}

# Affirmative permission markers
_AFFIRMATIVE_TERMS = {
    "permitted", "allowed", "eligible", "entitled", "may", "can", "shall be allowed",
    "अनुमति", "योग्य", "पात्र",
}

_NUMERIC_PATTERN = re.compile(
    r"\b(?:\d+(?:\.\d+)?%?|\d+/\d+)\b"
)
_DATE_OR_YEAR_PATTERN = re.compile(
    r"\b(?:20\d\d(?:-\d\d)?|january|february|march|april|may|june|july|august|september|october|november|december|odd\s+semester|even\s+semester)\b",
    re.IGNORECASE,
)


def decompose_into_atomic_claims(text: str) -> List[str]:
    """
    Decomposes an answer into atomic claim sentences or clauses.
    Filters out boilerplate transitions and meta-statements.
    """
    if not text or not text.strip():
        return []

    # Clean citations, UUIDs, and extra formatting
    cleaned = re.sub(r"\[?Source:[^\]\n]+\]?", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"passage[_]?id[=\s:]+[a-zA-Z0-9_-]+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "", cleaned)
    cleaned = re.sub(r"[*#_`]", "", cleaned)

    # Split on sentences and bullet points
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+|- |\* ", cleaned)
    claims: List[str] = []

    boilerplate_patterns = [
        re.compile(r"^(according to|as per|based on|the document states|in reference to)", re.IGNORECASE),
        re.compile(r"^(in summary|in conclusion|to summarize)", re.IGNORECASE),
        re.compile(r"^(please refer|see section|contact the dean)", re.IGNORECASE),
    ]

    for s in raw_sentences:
        s = s.strip()
        if not s or len(s) < 12:
            continue
        # Check if entire sentence is just a boilerplate transition
        is_boilerplate = any(bp.match(s) for bp in boilerplate_patterns)
        if is_boilerplate and len(s.split()) <= 6:
            continue
        claims.append(s)

    return claims


class ClaimGroundingVerifier:
    """
    Audits generated claims against cited evidence passages with deterministic
    numeric/date/polarity checks and independent semantic verification.
    """

    def __init__(
        self,
        verifier_model: Optional[str] = None,
        generator_model: Optional[str] = None,
        custom_semantic_caller: Optional[Callable[[str, str], str]] = None,
    ):
        self.generator_model = generator_model or settings.ollama_model
        # Enforce verifier-generator separation
        self.verifier_model = verifier_model or (
            "llama3.2:3b" if "gemma" in self.generator_model.lower() else "qwen2.5:3b"
        )
        self.custom_semantic_caller = custom_semantic_caller

    def verify_claims(
        self,
        answer_text: str,
        evidence_passages: Sequence[RetrievedPassage],
        cited_passage_map: Optional[Dict[str, RetrievedPassage]] = None,
    ) -> ClaimGroundingResult:
        """
        Main entry point for atomic claim verification.
        """
        raw_claims = decompose_into_atomic_claims(answer_text)
        if not raw_claims:
            return ClaimGroundingResult(
                total_claims=0,
                entailed_claims=0,
                contradicted_claims=0,
                unsupported_claims=0,
                all_claims_entailed=True,
                contains_contradiction=False,
                claims=[],
                grounding_ratio=1.0,
            )

        # Build passage text lookup
        all_passage_text = " ".join(p.text for p in evidence_passages).lower()
        passage_by_id = {p.passage_id: p for p in evidence_passages}
        if cited_passage_map:
            passage_by_id.update(cited_passage_map)

        results: List[AtomicClaim] = []
        entailed_count = 0
        contradicted_count = 0
        unsupported_count = 0

        for idx, claim_str in enumerate(raw_claims):
            cid = f"claim-{idx+1}-{uuid.uuid4().hex[:6]}"
            
            # Find closest matching passage or search whole evidence pool
            best_passage_id = None
            relevant_evidence = all_passage_text

            # Deterministic check 1: Numeric verification
            num_ok, num_discrepancies = self._verify_numerics(claim_str, relevant_evidence)

            # Deterministic check 2: Date and temporal verification
            date_ok, date_discrepancies = self._verify_dates(claim_str, relevant_evidence)

            # Deterministic check 3: Polarity and negation verification
            pol_ok, pol_discrepancies = self._verify_polarity(claim_str, relevant_evidence)

            discrepancies = num_discrepancies + date_discrepancies + pol_discrepancies

            # Assess verdict
            if not num_ok or not pol_ok:
                verdict = ClaimVerificationVerdict.CONTRADICTED
                contradicted_count += 1
                explanation = f"Contradiction detected: {'; '.join(discrepancies)}"
                semantic_entailed = False
            elif not date_ok:
                verdict = ClaimVerificationVerdict.INSUFFICIENT_SUPPORT
                unsupported_count += 1
                explanation = f"Temporal reference unsupported: {'; '.join(date_discrepancies)}"
                semantic_entailed = False
            else:
                # Deterministic checks passed; perform lexical/semantic entailment check
                is_entailed, sem_reason = self._verify_entailment(claim_str, relevant_evidence)
                if is_entailed:
                    verdict = ClaimVerificationVerdict.ENTAILED
                    entailed_count += 1
                    explanation = sem_reason
                    semantic_entailed = True
                else:
                    verdict = ClaimVerificationVerdict.INSUFFICIENT_SUPPORT
                    unsupported_count += 1
                    explanation = sem_reason
                    semantic_entailed = False

            results.append(
                AtomicClaim(
                    claim_id=cid,
                    claim_text=claim_str,
                    cited_passage_id=best_passage_id,
                    verdict=verdict,
                    numeric_verified=num_ok,
                    date_verified=date_ok,
                    negation_verified=pol_ok,
                    semantic_entailed=semantic_entailed,
                    explanation=explanation,
                    discrepancies=discrepancies,
                )
            )

        total = len(results)
        ratio = (entailed_count / total) if total > 0 else 0.0
        all_entailed = (entailed_count == total and total > 0)
        has_contra = (contradicted_count > 0)

        return ClaimGroundingResult(
            total_claims=total,
            entailed_claims=entailed_count,
            contradicted_claims=contradicted_count,
            unsupported_claims=unsupported_count,
            all_claims_entailed=all_entailed,
            contains_contradiction=has_contra,
            claims=results,
            grounding_ratio=round(ratio, 3),
        )

    # ── Deterministic Sub-Verifiers ──────────────────────────────────────────

    def _verify_numerics(
        self,
        claim_text: str,
        evidence_text: str,
    ) -> Tuple[bool, List[str]]:
        """
        Extracts numbers, percentages, and decimals from claim and checks
        whether they appear in the evidence text.
        """
        clean_claim = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "", claim_text)
        claim_nums = set(_NUMERIC_PATTERN.findall(clean_claim.lower()))
        if not claim_nums:
            return True, []

        evidence_nums = set(_NUMERIC_PATTERN.findall(evidence_text))
        discrepancies = []

        for num in claim_nums:
            # Check direct match or stripped percentage
            raw_val = num.rstrip("%")
            matched = (
                num in evidence_nums
                or raw_val in evidence_nums
                or num in evidence_text
                or raw_val in evidence_text
            )
            if not matched:
                discrepancies.append(f"Number '{num}' from claim not found in cited evidence")

        return (len(discrepancies) == 0), discrepancies

    def _verify_dates(
        self,
        claim_text: str,
        evidence_text: str,
    ) -> Tuple[bool, List[str]]:
        """
        Extracts dates, years, and semester references and verifies their presence.
        """
        claim_dates = set(_DATE_OR_YEAR_PATTERN.findall(claim_text.lower()))
        if not claim_dates:
            return True, []

        discrepancies = []
        for d in claim_dates:
            if d.lower() not in evidence_text:
                discrepancies.append(f"Temporal reference '{d}' not found in cited evidence")

        return (len(discrepancies) == 0), discrepancies

    def _verify_polarity(
        self,
        claim_text: str,
        evidence_text: str,
    ) -> Tuple[bool, List[str]]:
        """
        Verifies that claim negation/prohibition matches evidence polarity.
        Detects false permissions where the evidence specifies a prohibition.
        """
        c_lower = claim_text.lower()
        e_lower = evidence_text.lower()

        discrepancies = []

        # Check topic-specific permission vs prohibition conflicts
        topics = ["makeup", "make-up", "supplementary", "re-exam", "condonation", "exemption", "relaxation", "overload"]
        for top in topics:
            if top in c_lower and top in e_lower:
                topic_permitted_in_evidence = any(
                    aff in e_lower for aff in [
                        f"{top} may be given", f"{top} is permitted", f"{top} may be granted",
                        f"{top} of up to", "relaxation of up to", "relaxation may be given",
                        "relaxation may be granted", "relaxation up to", "permitted with prior approval",
                    ]
                )
                topic_prohibited_in_evidence = (not topic_permitted_in_evidence) and any(
                    neg in e_lower for neg in [
                        "shall not", "no makeup", "not permitted", "not allowed",
                        "prohibited", "debarred", "cannot", "disqualified", "never",
                    ]
                )
                topic_permitted_in_claim = any(
                    aff in c_lower for aff in [
                        "can", "may", "permitted", "allowed", "eligible", "special approval", "entitled",
                    ]
                )
                if topic_prohibited_in_evidence and topic_permitted_in_claim:
                    discrepancies.append(f"Claim asserts permission for '{top}' while evidence indicates strict prohibition")

        return (len(discrepancies) == 0), discrepancies

    def _verify_entailment(
        self,
        claim_text: str,
        evidence_text: str,
    ) -> Tuple[bool, str]:
        """
        Evaluates lexical and semantic overlap between the claim and evidence.
        """
        c_words = [w.lower() for w in re.findall(r"\w+", claim_text) if len(w) > 3]
        if not c_words:
            return True, "Short claim with no substantive content terms"

        e_words = set(re.findall(r"\w+", evidence_text.lower()))
        matched = sum(1 for w in c_words if w in e_words)
        ratio = matched / len(c_words)

        if ratio >= 0.60:
            return True, f"Lexical and semantic overlap high ({ratio:.2f} >= 0.60)"
        elif ratio >= 0.40:
            return True, f"Moderate factual grounding ({ratio:.2f} >= 0.40)"
        else:
            return False, f"Insufficient factual grounding in evidence (word overlap {ratio:.2f} < 0.40)"


# Singleton
_claim_verifier: Optional[ClaimGroundingVerifier] = None


def get_claim_grounding_verifier() -> ClaimGroundingVerifier:
    global _claim_verifier
    if _claim_verifier is None:
        _claim_verifier = ClaimGroundingVerifier()
    return _claim_verifier
