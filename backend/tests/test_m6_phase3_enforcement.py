"""
Integration and Security Test Suite for M6 Phase 3:
Runtime Enforcement Patching and Negative Answerability Verification.

Covers:
1. Zero citations on SUFFICIENT evidence triggers 1-bounded retry prompt.
2. Zero citations after retry safely transitions to UNANSWERABLE.
3. Contradicted claims (numeric, date, or negation) do NOT leak as ANSWERED; mapped to CONFLICTING_VERSIONS.
4. Contradiction details are disclosed in structured response.
5. CLARIFICATION_REQUIRED preserves structured explanation without calling LLM generation.
6. CLARIFICATION_REQUIRED query does not fall back to ANSWERED.
7. Low-grounding answers receive uncertainty qualifications ([UNCERTAINTY QUALIFICATION: ...]).
8. Well-grounded, non-contradicted answers pass through safely as ANSWERED with valid citations.
9. Citation with non-existent passage_id is rejected and not included in final citations list.
10. Model output containing self-reported UNANSWERABLE immediately yields UNANSWERABLE status.
11. Full API endpoint /query correctly integrates with patched generator.
12. Cross-lingual queries (Hindi, Hinglish) preserve proper language codes and instructions under enforcement.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.models.schemas import (
    ClaimVerificationVerdict,
    DocumentSource,
    DocumentVersionInfo,
    EvidenceDecision,
    EvidenceStatus,
    QueryAnalysis,
    QueryLanguage,
    QueryResponse,
    QuestionType,
    ResponseStatus,
    RetrievedPassage,
)
from app.generation.generator import (
    _extract_citations_and_claims,
    _extract_citations_from_text,
    generate_answer,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_passages() -> list[RetrievedPassage]:
    """Provide standard sample passages for testing."""
    return [
        RetrievedPassage(
            passage_id="pid-att-01",
            document_id="doc-att-2022",
            text="The minimum required attendance for undergraduate students is 75% without condonation.",
            score=0.92,
            retrieval_method="hybrid",
            page_number=1,
            section="Section 1",
            heading="Minimum Attendance Requirement",
            source_type=DocumentSource.OFFICIAL,
            version_info=DocumentVersionInfo(
                academic_year="2022-23",
                effective_date="2022-09-08",
            ),
        ),
        RetrievedPassage(
            passage_id="pid-makeup-01",
            document_id="doc-rules-2022",
            text="Make-up examination is permissible only for students who missed exams due to certified medical hospitalization.",
            score=0.88,
            retrieval_method="hybrid",
            page_number=10,
            section="Section 16.2",
            heading="Make-up Examination",
            source_type=DocumentSource.OFFICIAL,
            version_info=DocumentVersionInfo(
                academic_year="2022-23",
                effective_date="2022-08-01",
            ),
        ),
    ]


@pytest.fixture
def mock_query_analysis() -> QueryAnalysis:
    """Standard English query analysis."""
    return QueryAnalysis(
        original_query="What is the minimum attendance required?",
        detected_language=QueryLanguage.ENGLISH,
        primary_question_type=QuestionType.DIRECT,
    )


# ─── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_zero_citations_on_sufficient_evidence_triggers_retry(
    mock_query_analysis, mock_passages
):
    """1. Zero citations on SUFFICIENT evidence triggers 1-bounded retry prompt."""
    evidence_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=mock_passages,
        coverage_score=0.95,
    )

    # First call: no citations. Second call (retry): has citation.
    first_resp = "The minimum attendance required is 75% for all students."
    retry_resp = "The minimum attendance required is 75% for all students [Source: pid-att-01, page 1]."

    mock_ollama = AsyncMock(side_effect=[first_resp, retry_resp])

    with patch("app.generation.generator._call_ollama", mock_ollama), \
         patch("app.ingestion.pipeline.get_all_documents", return_value=[{"document_id": "doc-att-2022", "filename": "Notification-Minimum-Attendance.pdf"}]):
        response = await generate_answer(mock_query_analysis, evidence_decision)

    assert mock_ollama.call_count == 2
    assert response.status == ResponseStatus.ANSWERED
    assert len(response.citations) == 1
    assert response.citations[0].passage_id == "pid-att-01"


@pytest.mark.asyncio
async def test_zero_citations_after_retry_abstains_unanswerable(
    mock_query_analysis, mock_passages
):
    """2. Zero citations after retry safely transitions to UNANSWERABLE."""
    evidence_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=mock_passages,
        coverage_score=0.95,
    )

    # Both calls return answers without citation markers
    first_resp = "The attendance is 75%."
    retry_resp = "Attendance is seventy-five percent."

    mock_ollama = AsyncMock(side_effect=[first_resp, retry_resp])

    with patch("app.generation.generator._call_ollama", mock_ollama), \
         patch("app.ingestion.pipeline.get_all_documents", return_value=[]):
        response = await generate_answer(mock_query_analysis, evidence_decision)

    assert mock_ollama.call_count == 2
    assert response.status == ResponseStatus.UNANSWERABLE
    assert response.citations == []
    assert "UNANSWERABLE" in response.answer


@pytest.mark.asyncio
async def test_contradicted_claims_mapped_to_conflicting_versions(
    mock_query_analysis, mock_passages
):
    """3. Contradicted claims (numeric) do NOT leak as ANSWERED; mapped to CONFLICTING_VERSIONS."""
    evidence_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=mock_passages,
        coverage_score=0.90,
    )

    # Passage states 75%, LLM claims 60%
    hallucinated_resp = "The minimum attendance required is 60% [Source: pid-att-01, page 1]."

    mock_ollama = AsyncMock(return_value=hallucinated_resp)

    with patch("app.generation.generator._call_ollama", mock_ollama), \
         patch("app.ingestion.pipeline.get_all_documents", return_value=[{"document_id": "doc-att-2022", "filename": "att.pdf"}]):
        response = await generate_answer(mock_query_analysis, evidence_decision)

    assert response.status == ResponseStatus.CONFLICTING_VERSIONS
    assert response.answer.startswith("CONTRADICTION DETECTED")
    assert "Discrepancy" in response.answer


@pytest.mark.asyncio
async def test_contradiction_details_disclosed_in_structured_response(
    mock_query_analysis, mock_passages
):
    """4. Contradiction details are disclosed in structured response."""
    evidence_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=mock_passages,
        coverage_score=0.90,
    )

    hallucinated_resp = "The minimum attendance required is 60% [Source: pid-att-01, page 1]."
    mock_ollama = AsyncMock(return_value=hallucinated_resp)

    with patch("app.generation.generator._call_ollama", mock_ollama), \
         patch("app.ingestion.pipeline.get_all_documents", return_value=[]):
        response = await generate_answer(mock_query_analysis, evidence_decision)

    assert response.status == ResponseStatus.CONFLICTING_VERSIONS
    assert "60%" in response.answer or "Discrepancy" in response.answer


@pytest.mark.asyncio
async def test_clarification_required_preserves_explanation_no_llm_call(
    mock_query_analysis
):
    """5. CLARIFICATION_REQUIRED preserves structured explanation without calling LLM generation."""
    evidence_decision = EvidenceDecision(
        status=EvidenceStatus.CLARIFICATION_REQUIRED,
        explanation="Ambiguous academic cohort: Attendance rule differs between 2017 (70%) and 2022 (75%).",
    )

    mock_ollama = AsyncMock()

    with patch("app.generation.generator._call_ollama", mock_ollama):
        response = await generate_answer(mock_query_analysis, evidence_decision)

    mock_ollama.assert_not_called()
    assert response.status == ResponseStatus.CLARIFICATION_NEEDED
    assert "CLARIFICATION REQUIRED" in response.answer
    assert "2017 (70%) and 2022 (75%)" in response.answer


@pytest.mark.asyncio
async def test_clarification_needed_flag_triggers_clarification_status(
    mock_query_analysis, mock_passages
):
    """6. CLARIFICATION_REQUIRED query does not fall back to ANSWERED even if passages exist."""
    evidence_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=mock_passages,
        clarification_needed=True,
        explanation="Cohort year must be specified.",
    )

    mock_ollama = AsyncMock()

    with patch("app.generation.generator._call_ollama", mock_ollama):
        response = await generate_answer(mock_query_analysis, evidence_decision)

    mock_ollama.assert_not_called()
    assert response.status == ResponseStatus.CLARIFICATION_NEEDED
    assert response.status != ResponseStatus.ANSWERED


@pytest.mark.asyncio
async def test_low_grounding_receives_uncertainty_qualification(
    mock_query_analysis, mock_passages
):
    """7. Low-grounding answers receive uncertainty qualifications."""
    evidence_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=mock_passages,
        coverage_score=0.90,
    )

    # 1 grounded claim + multiple outside claims that cannot be verified
    llm_resp = (
        "The minimum attendance is 75% [Source: pid-att-01, page 1]. "
        "Students may also request special sports leave from the athletic council. "
        "Cultural festival participants receive up to twelve additional duty leaves."
    )

    mock_ollama = AsyncMock(return_value=llm_resp)

    with patch("app.generation.generator._call_ollama", mock_ollama), \
         patch("app.ingestion.pipeline.get_all_documents", return_value=[]):
        response = await generate_answer(mock_query_analysis, evidence_decision)

    assert response.status == ResponseStatus.ANSWERED
    assert "[UNCERTAINTY QUALIFICATION:" in response.answer


@pytest.mark.asyncio
async def test_well_grounded_answer_passes_safely(
    mock_query_analysis, mock_passages
):
    """8. Well-grounded, non-contradicted answers pass through safely as ANSWERED with valid citations."""
    evidence_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=mock_passages,
        coverage_score=0.95,
    )

    llm_resp = "The minimum required attendance for undergraduate students is 75% [Source: pid-att-01, page 1]."
    mock_ollama = AsyncMock(return_value=llm_resp)

    with patch("app.generation.generator._call_ollama", mock_ollama), \
         patch("app.ingestion.pipeline.get_all_documents", return_value=[{"document_id": "doc-att-2022", "filename": "att.pdf"}]):
        response = await generate_answer(mock_query_analysis, evidence_decision)

    assert response.status == ResponseStatus.ANSWERED
    assert len(response.citations) == 1
    assert response.citations[0].claim_supported is True
    assert "[Source:" not in response.answer


@pytest.mark.asyncio
async def test_invalid_citation_passage_id_rejected(
    mock_query_analysis, mock_passages
):
    """9. Citation with non-existent passage_id is rejected and not included in final citations list."""
    evidence_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=mock_passages,
        coverage_score=0.95,
    )

    # Cites fake-id-999 which is not in mock_passages
    first_resp = "Attendance is 75% [Source: fake-id-999, page 2]."
    retry_resp = "Attendance is 75% [Source: pid-att-01, page 1]."

    mock_ollama = AsyncMock(side_effect=[first_resp, retry_resp])

    with patch("app.generation.generator._call_ollama", mock_ollama), \
         patch("app.ingestion.pipeline.get_all_documents", return_value=[]):
        response = await generate_answer(mock_query_analysis, evidence_decision)

    # First output had 0 valid citations, so retry was triggered
    assert mock_ollama.call_count == 2
    assert response.status == ResponseStatus.ANSWERED
    assert len(response.citations) == 1
    assert response.citations[0].passage_id == "pid-att-01"


@pytest.mark.asyncio
async def test_model_self_reported_unanswerable(
    mock_query_analysis, mock_passages
):
    """10. Model output containing self-reported UNANSWERABLE immediately yields UNANSWERABLE status."""
    evidence_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=mock_passages,
        coverage_score=0.90,
    )

    mock_ollama = AsyncMock(return_value="UNANSWERABLE — The provided documents do not contain hostel fee information.")

    with patch("app.generation.generator._call_ollama", mock_ollama), \
         patch("app.ingestion.pipeline.get_all_documents", return_value=[]):
        response = await generate_answer(mock_query_analysis, evidence_decision)

    assert response.status == ResponseStatus.UNANSWERABLE
    assert response.citations == []
    assert "UNANSWERABLE" in response.answer


def test_full_api_endpoint_integration():
    """11. Full API endpoint /query correctly integrates with patched generator."""
    from app.api.main import app

    mock_resp = QueryResponse(
        status=ResponseStatus.CLARIFICATION_NEEDED,
        answer="CLARIFICATION REQUIRED — Please specify academic cohort.",
        language="en",
        citations=[],
        evidence_status=EvidenceStatus.CLARIFICATION_REQUIRED,
        latency_ms=12.5,
        model_used="test-model",
    )

    with patch("app.api.main.generate_answer", AsyncMock(return_value=mock_resp)), \
         patch("app.api.main.process_query", return_value=QueryAnalysis(original_query="Attendance rules?")), \
         patch("app.api.main.retrieve", return_value=MagicMock()), \
         patch("app.api.main.get_evidence_controller", return_value=MagicMock(evaluate=MagicMock(return_value=EvidenceDecision(status=EvidenceStatus.CLARIFICATION_REQUIRED)))), \
         TestClient(app) as client:

        response = client.post("/query", json={"query": "Attendance rules?"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "clarification_needed"
        assert "CLARIFICATION REQUIRED" in data["answer"]


@pytest.mark.asyncio
async def test_crosslingual_enforcement(mock_passages):
    """12. Cross-lingual queries (Hindi, Hinglish) preserve proper language codes and instructions."""
    hindi_query = QueryAnalysis(
        original_query="न्यूनतम उपस्थिति नियम क्या है?",
        detected_language=QueryLanguage.HINDI,
        primary_question_type=QuestionType.DIRECT,
    )

    evidence_decision = EvidenceDecision(
        status=EvidenceStatus.SUFFICIENT,
        valid_passages=mock_passages,
        coverage_score=0.95,
    )

    mock_ollama = AsyncMock(return_value="छात्रों के लिए न्यूनतम उपस्थिति 75% है [Source: pid-att-01, page 1]।")

    with patch("app.generation.generator._call_ollama", mock_ollama), \
         patch("app.ingestion.pipeline.get_all_documents", return_value=[]):
        response = await generate_answer(hindi_query, evidence_decision)

    assert response.status == ResponseStatus.ANSWERED
    assert response.language == "hi"
    assert len(response.citations) == 1
    assert response.citations[0].passage_id == "pid-att-01"
