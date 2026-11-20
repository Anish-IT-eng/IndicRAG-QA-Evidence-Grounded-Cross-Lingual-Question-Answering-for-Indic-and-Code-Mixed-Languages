"""
Regulatory Condition and Relationship Classifier for IndicRAG-QA.

Implements the formal M8.4 condition and relationship taxonomy:
- Conditions: COURSE_GRADING, EXAM_ELIGIBILITY, MEDICAL_CONDONATION, DISCIPLINARY_ACTION,
              ACADEMIC_PROGRESSION, PROGRAMME_REQUIREMENT, OTHER.
- Relationships: SAME_CONDITION_AGREEMENT, SAME_CONDITION_DIFFERENT_VERSION,
                 DIFFERENT_REGULATORY_CONDITIONS, EXPLICITLY_SUPERSEDES,
                 PROGRAMME_SPECIFIC_RULE, HISTORICAL_RULE, APPLICABILITY_UNRESOLVED,
                 GENUINE_CONFLICT.
"""
from __future__ import annotations

import re
from typing import Optional, Sequence

from app.models.schemas import (
    DocumentSource,
    QueryAnalysis,
    RegulatoryCondition,
    RegulatoryRelationship,
    RetrievedPassage,
    TemporalIntentMode,
)


def classify_passage_condition(
    passage: RetrievedPassage | str,
) -> RegulatoryCondition:
    """
    Classifies a retrieved passage (or raw text string) into one of the 7 RegulatoryConditions
    using document identity, section/clause metadata, and authoritative text patterns.
    Does NOT rely merely on numerical percentage matching.
    """
    if isinstance(passage, str):
        doc_id = ""
        text = passage.lower()
        heading = ""
        section = ""
    else:
        doc_id = (passage.document_id or "").lower()
        text = (passage.text or "").lower()
        heading = (passage.heading or "").lower()
        section = (passage.section or "").lower()
    combined = f"{heading} {section} {text}"

    # 1. Disciplinary Action / UFM
    if "ufm" in doc_id or "discipline" in doc_id or "conduct" in doc_id:
        return RegulatoryCondition.DISCIPLINARY_ACTION
    if "unfair means" in combined or "malpractice" in combined or "proctorial" in combined:
        return RegulatoryCondition.DISCIPLINARY_ACTION

    # 2. Medical Condonation / Attendance Relaxation
    if "relaxation in attendance" in combined or "medical ground" in combined or "hospitalization" in combined:
        return RegulatoryCondition.MEDICAL_CONDONATION
    if "30.1 (v)" in combined or "30.1(v)" in combined:
        return RegulatoryCondition.MEDICAL_CONDONATION

    # 3. End Semester Examination Eligibility
    if "notification" in doc_id or "307" in doc_id:
        return RegulatoryCondition.EXAM_ELIGIBILITY
    if "end semester examination" in combined and ("admit card" in combined or "withhold" in combined or "appear" in combined):
        return RegulatoryCondition.EXAM_ELIGIBILITY

    # 4. Course-Level Grading & 'X' Grade Debarment
    if "'x' grade" in combined or "x grade" in combined or "grade 'x'" in combined or "repeat the course" in combined:
        return RegulatoryCondition.COURSE_GRADING
    if "30.1 (ii)" in combined or "30.1(ii)" in combined or "in a course, failing which" in combined:
        return RegulatoryCondition.COURSE_GRADING

    # 5. Academic Progression (Duration, Credits, CGPA, Promotion)
    if "duration of the programme" in combined or "maximum duration" in combined or "minimum cgpa" in combined:
        return RegulatoryCondition.ACADEMIC_PROGRESSION
    if "semester promotion" in combined or "credit requirement" in combined:
        return RegulatoryCondition.ACADEMIC_PROGRESSION

    # 6. Programme Requirement (Branch change, core/electives)
    if "change of branch" in combined or "branch transfer" in combined or "curriculum" in combined:
        return RegulatoryCondition.PROGRAMME_REQUIREMENT

    # 7. Calendar / Administrative Operational Dates
    if "calendar" in doc_id or "registration date" in combined or "commencement of classes" in combined:
        return RegulatoryCondition.OTHER

    # Fallback to general condition based on keywords
    if "attendance" in combined:
        if "exam" in combined or "examination" in combined:
            return RegulatoryCondition.EXAM_ELIGIBILITY
        return RegulatoryCondition.COURSE_GRADING

    return RegulatoryCondition.OTHER


def classify_regulatory_relationship(
    pass_a: RetrievedPassage | str,
    pass_b: RetrievedPassage | str,
    query_analysis: Optional[QueryAnalysis] = None,
) -> RegulatoryRelationship:
    """
    Classifies the legal and regulatory relationship between two passages (or raw strings).
    """
    if isinstance(pass_a, str):
        pass_a = RetrievedPassage(
            passage_id="tmp_a", document_id="", text=pass_a, score=1.0,
            retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
        )
    if isinstance(pass_b, str):
        pass_b = RetrievedPassage(
            passage_id="tmp_b", document_id="", text=pass_b, score=1.0,
            retrieval_method="bm25", source_type=DocumentSource.OFFICIAL,
        )

    cond_a = pass_a.regulatory_condition or classify_passage_condition(pass_a)
    cond_b = pass_b.regulatory_condition or classify_passage_condition(pass_b)

    # Check distinct regulatory conditions
    if cond_a != cond_b:
        return RegulatoryRelationship.DIFFERENT_REGULATORY_CONDITIONS

    # Passages govern the SAME condition
    # Check if an explicit supersession clause connects them
    v_a = pass_a.version_info
    v_b = pass_b.version_info
    if (v_a and v_a.superseded_by == pass_b.document_id) or (v_b and v_b.superseded_by == pass_a.document_id):
        return RegulatoryRelationship.EXPLICITLY_SUPERSEDES

    # Check consensus between historical and current documents
    is_a_current = v_a.is_current if v_a else True
    is_b_current = v_b.is_current if v_b else True

    # Extract numerical thresholds if present
    thresh_a = _extract_numerical_threshold(pass_a.text)
    thresh_b = _extract_numerical_threshold(pass_b.text)

    if thresh_a is not None and thresh_b is not None:
        if thresh_a == thresh_b:
            # Both agree on the exact same threshold for the same condition
            return RegulatoryRelationship.SAME_CONDITION_AGREEMENT
        else:
            # Thresholds differ
            if is_a_current != is_b_current:
                # One is historical and one is current -> chronologically different version
                return RegulatoryRelationship.SAME_CONDITION_DIFFERENT_VERSION
            elif is_a_current is True and is_b_current is True:
                # Both currently active in same jurisdiction clashing -> genuine conflict
                return RegulatoryRelationship.GENUINE_CONFLICT

    if is_a_current is False or is_b_current is False:
        return RegulatoryRelationship.HISTORICAL_RULE

    return RegulatoryRelationship.SAME_CONDITION_AGREEMENT


def check_regulatory_consensus(
    passages: Sequence[RetrievedPassage],
    condition_or_qa: RegulatoryCondition | QueryAnalysis | None = None,
) -> tuple[bool, Optional[float], str]:
    """
    Checks if all retrieved passages for a given condition agree on the threshold.
    Returns (has_consensus, common_threshold, explanation).
    """
    target_condition: Optional[RegulatoryCondition] = None
    if isinstance(condition_or_qa, RegulatoryCondition):
        target_condition = condition_or_qa
    elif isinstance(condition_or_qa, QueryAnalysis):
        if condition_or_qa.target_conditions:
            target_condition = condition_or_qa.target_conditions[0]
        else:
            # Infer from passages
            for p in passages:
                c = p.regulatory_condition or classify_passage_condition(p)
                if c != RegulatoryCondition.OTHER:
                    target_condition = c
                    break

    if target_condition is not None:
        cond_passages = [
            p for p in passages
            if (p.regulatory_condition or classify_passage_condition(p)) == target_condition
        ]
    else:
        cond_passages = list(passages)

    if not cond_passages:
        return False, None, "No passages found for condition"

    thresholds = set()
    for p in cond_passages:
        th = _extract_numerical_threshold(p.text)
        if th is not None:
            thresholds.add(th)

    cond_name = target_condition.value if target_condition else "condition"
    if len(thresholds) == 1:
        val = next(iter(thresholds))
        return True, val, f"Unanimous agreement across versions on {val}% for {cond_name}."

    if len(thresholds) == 0:
        return False, None, "No explicit numerical threshold found in passages."

    return False, None, f"Differing thresholds {sorted(list(thresholds))} found across documents."


def _extract_numerical_threshold(text: str) -> Optional[float]:
    """
    Extracts percentage threshold (e.g. 70%, 75%, 10%) from clause text.
    """
    match = re.search(r"\b(\d{1,2}(?:\.\d+)?)\s*%", text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None

