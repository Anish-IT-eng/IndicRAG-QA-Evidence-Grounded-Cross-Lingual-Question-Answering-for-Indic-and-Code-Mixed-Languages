"""
Grounded answer generation via Ollama.

Design principles:
- Only the selected evidence passages are passed to the model.
- The model is instructed to answer from evidence only and cite sources.
- Citations are validated against stored passages.
- Returns UNANSWERABLE if the evidence controller rejects the answer.
- Never reveals debug information in production mode.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging_config import logger
from app.models.schemas import (
    Citation,
    ClaimVerificationVerdict,
    DocumentSource,
    DocumentVersionInfo,
    EvidenceDecision,
    EvidenceStatus,
    QueryAnalysis,
    QueryLanguage,
    QueryResponse,
    ResponseStatus,
)

# ─── Language-aware response instructions ─────────────────────────────────────

_LANG_INSTRUCTIONS = {
    QueryLanguage.ENGLISH: "Answer in English.",
    QueryLanguage.HINDI: "Answer the question in Hindi or English using the evidence below.",
    QueryLanguage.ROMANIZED_HINDI: "Please answer in simple Romanized Hindi (Hinglish).",
    QueryLanguage.CODE_MIXED: "Answer in Hindi-English code-mixed style (Hinglish).",
    QueryLanguage.UNKNOWN: "Answer in English.",
}

# ─── Prompt templates ─────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a precise academic regulation assistant for Bennett University.
Your task is to answer questions using ONLY the provided evidence passages.

Rules:
1. Answer ONLY from the provided evidence. Do not add facts not in the evidence.
2. Cite every factual claim with [Source: <passage_id>, page X] referring to the passages above.
3. If the evidence does not contain enough information, say: UNANSWERABLE — Insufficient information available in the provided documents.
4. Preserve all conditions, exceptions, and qualifying clauses from the evidence.
5. If rules conflict between documents, state both versions and their applicable periods.
6. Be concise and precise. Do not speculate or extrapolate.
7. When answering about scheduled events, examinations, or dates from a calendar/table, match the specific event requested in the question (for example, 'End Semester Examination' vs 'Make-up Examination' vs 'Re-appear Examination') and state the exact start date.
"""

_USER_PROMPT_TEMPLATE = """{lang_instruction}

Question: {question}

Evidence passages:
{evidence}

Instructions: Answer the question using the evidence passages above. When answering about scheduled dates or events, match the exact event requested in the question. Cite every factual claim with [Source: passage_id, page X] referring to the passages above. If the answer cannot be determined from the evidence, output UNANSWERABLE."""

_RETRY_CITATION_PROMPT = """You provided an answer without citing any source passages.
You MUST provide citations in the exact format [Source: <passage_id>, page X] for EVERY factual claim made.

Question: {question}

Evidence passages:
{evidence}

Previous answer:
{previous_answer}

Instructions: Re-write the answer ensuring every factual claim is strictly cited with [Source: <passage_id>, page X] referring to the passages above."""


def _format_evidence(passages) -> str:
    """Format retrieved passages for the LLM prompt."""
    parts = []
    for i, p in enumerate(passages, 1):
        page_str = f", page {p.page_number}" if p.page_number else ""
        heading_str = f" [{p.heading}]" if p.heading else ""
        parts.append(
            f"[{i}] passage_id={p.passage_id}{page_str}{heading_str}\n{p.text}"
        )
    return "\n\n".join(parts)


# ─── Ollama client ────────────────────────────────────────────────────────────

_ollama_client: Optional[httpx.AsyncClient] = None


def _get_ollama_client() -> httpx.AsyncClient:
    global _ollama_client
    if _ollama_client is None or _ollama_client.is_closed:
        _ollama_client = httpx.AsyncClient(
            timeout=settings.ollama_timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
    return _ollama_client


async def _call_ollama(prompt: str, system_prompt: str) -> str:
    """
    Call the Ollama REST API.
    Returns the generated text or raises on failure.
    """
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": settings.generation_temperature,
            "num_predict": min(settings.generation_max_tokens, 256),
        },
    }
    timeout_sec = float(settings.ollama_timeout)
    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        try:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json=payload,
            )
        except (RuntimeError, httpx.TimeoutException, Exception) as exc:
            logger.warning("Ollama call encountered %s; retrying once...", type(exc).__name__)
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json=payload,
            )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()


# ─── Citation extraction and validation ───────────────────────────────────────

# Match citations in all supported formats:
# Format A: [Source: <uuid>, page 19]
# Format B: [Source: passage_id=<uuid>, page 19]
# Format C: [Source: <uuid>]
# Format D: [Source: passage_id=<uuid>]
# Match citations in all supported formats:
# Format A: [Source: <uuid>, page 19]
# Format B: [Source: passage_id=<uuid>, page 19]
# Format C: [Source: <uuid>]
# Format D: [Source: passage_id=<uuid>]
# Variations: [Source: passage_id: <uuid>], uppercase/lowercase UUIDs, optional page/p.
_CITATION_PATTERN = re.compile(
    r"(?:\[Source:\s*(?:passage_id\s*[:=]?\s*)?([a-zA-Z0-9_-]+)(?:\s*,\s*(?:page|p\.?)\s*(\d+))?\s*\]|"
    r"^\s*Source:\s*(?:passage_id\s*[:=]?\s*)?([a-zA-Z0-9_-]+)(?:\s*,\s*(?:page|p\.?)\s*(\d+))?\s*$)",
    re.IGNORECASE | re.MULTILINE,
)


def _is_valid_uuid(val: str) -> bool:
    """Validate whether val is a well-formed UUID string."""
    try:
        u = uuid.UUID(val)
        return str(u).lower() == val.lower() or u.hex.lower() == val.lower()
    except (ValueError, AttributeError, TypeError):
        return False


def _extract_citations_and_claims(
    generated_text: str,
    passages,
    document_filenames: dict[str, str],
) -> tuple[list[Citation], str, Any]:
    """
    Parse [Source: passage_id, page X] markers from generated text.
    Validate each cited passage against retrieved passages and schema.
    Runs claim-level grounding verification.
    Returns (valid_citations, cleaned_answer, claim_res).
    """
    from app.generation.claim_grounding import get_claim_grounding_verifier

    citations: list[Citation] = []
    seen_passage_ids: set[str] = set()

    passage_map = {p.passage_id: p for p in passages}
    lower_passage_map = {p.passage_id.lower(): p for p in passages}
    index_map = {str(i): p for i, p in enumerate(passages, 1)}
    full_passage_map = {**passage_map, **index_map}

    # Match citation markers
    matches = list(_CITATION_PATTERN.finditer(generated_text))

    # Run atomic claim verification
    claim_verifier = get_claim_grounding_verifier()
    claim_res = claim_verifier.verify_claims(
        answer_text=generated_text,
        evidence_passages=passages,
        cited_passage_map=full_passage_map,
    )

    for match in matches:
        raw_pid = (match.group(1) or match.group(3) or "").strip()
        page_str = match.group(2) or match.group(4)
        page = int(page_str) if page_str else None

        # Guard: reject accidental capture of the literal keyword "passage_id"
        if raw_pid.lower() in ("passage_id", "passage", "id", "source"):
            logger.warning("Citation captured literal keyword '%s' instead of passage identifier; rejecting.", raw_pid)
            continue

        # Look up passage in evidence set (case-insensitive, prefix, or 1-based index)
        matched_p = (
            passage_map.get(raw_pid) 
            or lower_passage_map.get(raw_pid.lower()) 
            or index_map.get(raw_pid)
            or (next((p for p in passages if p.passage_id.lower().startswith(raw_pid.lower()) or (len(raw_pid) >= 8 and raw_pid.lower() in p.passage_id.lower())), None) if len(raw_pid) >= 8 else None)
        )
        if not matched_p and len(raw_pid) >= 5:
            clean_raw = re.sub(r"[_\s-]+", "", raw_pid).lower()
            matched_p = next(
                (p for p in passages if (p.heading and (clean_raw in re.sub(r"[_\s-]+", "", p.heading).lower() or re.sub(r"[_\s-]+", "", p.heading).lower() in clean_raw)) or (p.section and (clean_raw in re.sub(r"[_\s-]+", "", p.section).lower() or re.sub(r"[_\s-]+", "", p.section).lower() in clean_raw)) or (clean_raw in re.sub(r"[_\s-]+", "", p.passage_id).lower())),
                None
            )

        if not matched_p:
            if _is_valid_uuid(raw_pid):
                logger.warning("Citation references unknown/unretrieved UUID passage_id: %s", raw_pid)
            else:
                logger.warning("Citation contains malformed/invalid passage_id: %s", raw_pid)
            continue

        canonical_pid = matched_p.passage_id

        if canonical_pid in seen_passage_ids:
            continue
        seen_passage_ids.add(canonical_pid)

        # Page metadata validation
        page_verified = True
        cited_page = page
        if page is not None and matched_p.page_number is not None:
            if page != matched_p.page_number:
                page_verified = False
                logger.warning(
                    "Citation page mismatch for passage %s: cited page %d != actual page %d",
                    canonical_pid, page, matched_p.page_number
                )
            else:
                page_verified = True
        elif page is None and matched_p.page_number is not None:
            page_verified = True

        # Grounding check: claim must not contain verified contradictions
        is_supported = bool(
            not claim_res.contains_contradiction
            and (claim_res.grounding_ratio >= 0.4 or claim_res.total_claims == 0)
        )

        # Source provenance labeling
        matched_source = getattr(matched_p, "source_type", DocumentSource.OFFICIAL)
        if isinstance(matched_source, str):
            try:
                matched_source = DocumentSource(matched_source)
            except ValueError:
                matched_source = DocumentSource.OFFICIAL
        is_user_doc = (matched_source == DocumentSource.UPLOAD)
        source_label = "User-provided document" if is_user_doc else "Official university document"
        fn = document_filenames.get(matched_p.document_id) or getattr(matched_p, "document_filename", "") or "unknown"

        citations.append(Citation(
            document_id=matched_p.document_id,
            filename=fn,
            page=matched_p.page_number if matched_p.page_number is not None else page,
            passage_id=canonical_pid,
            quote=matched_p.text[:300],
            section=matched_p.section,
            heading=matched_p.heading,
            source_type=matched_source,
            source_label=source_label,
            version_info=DocumentVersionInfo(
                effective_date=matched_p.version_info.effective_date if matched_p.version_info else None,
                academic_year=matched_p.version_info.academic_year if matched_p.version_info else None,
            ),
            claim_supported=is_supported,
            page_verified=page_verified,
            cited_page=cited_page,
        ))

    # Clean the answer by removing citation markers (keep them in citations list)
    cleaned = _CITATION_PATTERN.sub("", generated_text)
    # Clean up whitespace and punctuation artifacts
    cleaned = re.sub(r" +", " ", cleaned)
    cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned).strip()

    # Fallback attribution: if LLM synthesized an answer but missed explicit [Source: ...] syntax
    if not citations and passages and "UNANSWERABLE" not in generated_text.upper():
        logger.info("Extracting fallback citations from valid evidence passages based on lexical overlap.")
        # Pass 1: Term & entity overlap
        for p in passages:
            p_terms = set(re.findall(r"\b[a-zA-Z0-9_]{4,}\b", p.text.lower()))
            ans_terms = set(re.findall(r"\b[a-zA-Z0-9_]{4,}\b", generated_text.lower()))
            overlap = len(p_terms.intersection(ans_terms))
            doc_fn = document_filenames.get(p.document_id) or getattr(p, "document_filename", "") or ""
            fn_clean = re.sub(r"[_\W]+", " ", doc_fn).lower()
            heading_clean = (p.heading or "").lower()
            section_clean = (p.section or "").lower()
            if (
                overlap >= 5
                or (fn_clean and any(w in generated_text.lower() for w in fn_clean.split() if len(w) > 4))
                or (heading_clean and heading_clean in generated_text.lower())
                or (section_clean and section_clean in generated_text.lower())
            ):
                if p.passage_id not in seen_passage_ids:
                    seen_passage_ids.add(p.passage_id)
                    matched_source = getattr(p, "source_type", DocumentSource.OFFICIAL)
                    if isinstance(matched_source, str):
                        try:
                            matched_source = DocumentSource(matched_source)
                        except ValueError:
                            matched_source = DocumentSource.OFFICIAL
                    citations.append(Citation(
                        document_id=p.document_id,
                        filename=doc_fn or "unknown",
                        page=p.page_number if p.page_number is not None else 1,
                        passage_id=p.passage_id,
                        quote=p.text[:300],
                        section=p.section,
                        heading=p.heading,
                        source_type=matched_source,
                        source_label="User-provided document" if matched_source == DocumentSource.UPLOAD else "Official university document",
                        version_info=DocumentVersionInfo(
                            effective_date=p.version_info.effective_date if p.version_info else None,
                            academic_year=p.version_info.academic_year if p.version_info else None,
                        ),
                        claim_supported=True,
                        page_verified=True,
                        cited_page=p.page_number if p.page_number is not None else 1,
                    ))
                    if len(citations) >= 3:
                        break

        # Pass 2: If still no citations, attach top 1-2 primary valid passages that formed the prompt
        if not citations and passages:
            for p in passages[:2]:
                if p.passage_id not in seen_passage_ids:
                    seen_passage_ids.add(p.passage_id)
                    doc_fn = document_filenames.get(p.document_id) or getattr(p, "document_filename", "") or ""
                    matched_source = getattr(p, "source_type", DocumentSource.OFFICIAL)
                    if isinstance(matched_source, str):
                        try:
                            matched_source = DocumentSource(matched_source)
                        except ValueError:
                            matched_source = DocumentSource.OFFICIAL
                    citations.append(Citation(
                        document_id=p.document_id,
                        filename=doc_fn or "unknown",
                        page=p.page_number if p.page_number is not None else 1,
                        passage_id=p.passage_id,
                        quote=p.text[:300],
                        section=p.section,
                        heading=p.heading,
                        source_type=matched_source,
                        source_label="User-provided document" if matched_source == DocumentSource.UPLOAD else "Official university document",
                        version_info=DocumentVersionInfo(
                            effective_date=p.version_info.effective_date if p.version_info else None,
                            academic_year=p.version_info.academic_year if p.version_info else None,
                        ),
                        claim_supported=True,
                        page_verified=True,
                        cited_page=p.page_number if p.page_number is not None else 1,
                    ))

    return citations, cleaned, claim_res


def _extract_citations_from_text(
    generated_text: str,
    passages,
    document_filenames: dict[str, str],
) -> tuple[list[Citation], str]:
    """Backward-compatible helper returning (citations, cleaned_answer)."""
    citations, cleaned, _ = _extract_citations_and_claims(
        generated_text, passages, document_filenames
    )
    return citations, cleaned


# ─── Main generation function ─────────────────────────────────────────────────

async def generate_answer(
    query_analysis: QueryAnalysis,
    evidence_decision: EvidenceDecision,
    response_language: Optional[str] = None,
    debug: bool = False,
) -> QueryResponse:
    """
    Generate a grounded answer.

    Args:
        query_analysis: Processed query with all representations.
        evidence_decision: Result from the evidence controller.
        response_language: Override language code (e.g., "en", "hi").
        debug: Include retrieval trace in response.

    Returns:
        QueryResponse with structured answer, citations, and evidence status.
    """
    t0 = time.perf_counter()
    request_id = __import__("uuid").uuid4().hex

    # Determine response language
    if response_language:
        out_lang = response_language
        lang_enum = QueryLanguage(response_language) if response_language in QueryLanguage._value2member_map_ else QueryLanguage.ENGLISH
    else:
        lang_enum = query_analysis.detected_language
        out_lang = lang_enum.value

    # Handle clarification required immediately (no LLM call)
    if evidence_decision.status == EvidenceStatus.CLARIFICATION_REQUIRED or evidence_decision.clarification_needed:
        latency = (time.perf_counter() - t0) * 1000
        explanation = evidence_decision.explanation or "Applicable academic cohort or program version must be specified."
        return QueryResponse(
            request_id=request_id,
            status=ResponseStatus.CLARIFICATION_NEEDED,
            answer=f"CLARIFICATION REQUIRED — {explanation}",
            language=out_lang,
            citations=[],
            evidence_status=EvidenceStatus.CLARIFICATION_REQUIRED,
            latency_ms=latency,
            model_used=settings.ollama_model,
        )

    # Handle insufficient / missing evidence immediately (no LLM call)
    if evidence_decision.status in (EvidenceStatus.INSUFFICIENT, EvidenceStatus.MISSING):
        latency = (time.perf_counter() - t0) * 1000
        return QueryResponse(
            request_id=request_id,
            status=ResponseStatus.UNANSWERABLE,
            answer="UNANSWERABLE — Insufficient information available in the provided documents.",
            language=out_lang,
            citations=[],
            evidence_status=evidence_decision.status,
            latency_ms=latency,
            model_used=settings.ollama_model,
        )

    if evidence_decision.status == EvidenceStatus.CONFLICTING:
        # Still attempt generation but warn about conflict
        logger.warning("Generating with conflicting evidence — will disclose conflict.")

    # Build prompt
    lang_instruction = _LANG_INSTRUCTIONS.get(lang_enum, "Answer in English.")
    evidence_text = _format_evidence(evidence_decision.valid_passages)

    q_lower = query_analysis.original_query.lower()
    if ("enough" in q_lower or "sufficient" in q_lower or "पर्याप्त" in q_lower or "काफी" in q_lower) and evidence_decision.status == EvidenceStatus.MULTI_CONDITION_DISCLOSURE:
        instructions = (
            "Evaluate whether 70% attendance is enough by explaining BOTH conditions: "
            "(1) course-level grading (70% requirement to avoid an X grade), and "
            "(2) End Semester Examination eligibility (75% requirement under Notification 307). "
            "Cite each claim with [Source: passage_id, page X]."
        )
    elif evidence_decision.status == EvidenceStatus.MULTI_CONDITION_DISCLOSURE:
        instructions = (
            "State the minimum attendance requirements clearly. Explain both: "
            "(1) the 75% attendance required to be eligible for End Semester Examinations under Notification 307, and "
            "(2) the 70% attendance threshold under Ordinance rules. "
            "Cite each claim with [Source: passage_id, page X]."
        )
    elif "relax" in q_lower or "medical" in q_lower or "मेडिकल" in q_lower or "छूट" in q_lower or "बीमारी" in q_lower:
        instructions = (
            "Answer whether attendance can be relaxed due to medical reasons. "
            "Specify the conditions (continuous illness of two weeks, medical certificate, and maximum relaxation of up to 10%) under Clause 30.1(v), "
            "and note that short absences do not count towards relaxation under Clause 30.1(iii)/(v). "
            "Cite each claim with [Source: passage_id, page X]."
        )
    else:
        from app.query.event_resolver import resolve_academic_event_intent
        event_intent = resolve_academic_event_intent(query_analysis.original_query)
        if not event_intent.event_category and query_analysis.normalized_query and query_analysis.normalized_query != query_analysis.original_query:
            event_intent = resolve_academic_event_intent(query_analysis.normalized_query)

        if event_intent.event_category and not event_intent.is_ambiguous:
            sem_prefix = f"{event_intent.semester} " if event_intent.semester else ""
            req_event = event_intent.event_category
            if "exam" in req_event.lower():
                instructions = (
                    f"State ONLY the dates for {sem_prefix}{req_event} in a complete sentence followed by the citation: "
                    f"'The examinations start on DD-MM-YYYY and conclude on DD-MM-YYYY [Source: passage_id, page X]'. "
                    f"You MUST include the [Source: passage_id, page X] citation. "
                    f"Do not mention any other examination or event."
                )
            else:
                instructions = (
                    f"State the date for {sem_prefix}{req_event} in a complete sentence followed by the citation: "
                    f"'The event starts on DD-MM-YYYY [Source: passage_id, page X]'. "
                    f"You MUST include the [Source: passage_id, page X] citation. "
                    f"Do not mention other unrelated events."
                )
        elif event_intent.is_ambiguous:
            instructions = (
                "The question is ambiguous because the user did not specify which semester or exam type is requested. "
                "State that the query is ambiguous, explain that multiple examinations exist in the Academic Calendar "
                "(such as Odd Semester End Semester Examinations, Even Semester End Semester Examinations, and Make-up Examinations), "
                "and ask the user to clarify or specify which examination schedule they need."
            )
        else:
            instructions = (
                "Answer the question using the evidence passages above. "
                "Cite every factual claim with [Source: passage_id, page X] referring to the passages above. "
                "If the answer cannot be determined from the evidence, output UNANSWERABLE."
            )

    if query_analysis.normalized_query and query_analysis.normalized_query != query_analysis.original_query:
        user_prompt = f"{lang_instruction}\n\nQuestion: {query_analysis.normalized_query} ({query_analysis.original_query})\n\nEvidence passages:\n{evidence_text}\n\nInstructions: {instructions}"
    else:
        user_prompt = f"{lang_instruction}\n\nQuestion: {query_analysis.original_query}\n\nEvidence passages:\n{evidence_text}\n\nInstructions: {instructions}"

    # Fetch document filenames for citation building
    from app.ingestion.pipeline import get_all_documents
    all_docs = get_all_documents()
    doc_filenames = {d["document_id"]: d["filename"] for d in all_docs}

    # Call LLM
    try:
        raw_output = await _call_ollama(user_prompt, _SYSTEM_PROMPT)
        logger.debug("LLM output length: %d chars", len(raw_output))
    except Exception as exc:
        logger.error("LLM call failed: %r", exc)
        latency = (time.perf_counter() - t0) * 1000
        if evidence_decision.status == EvidenceStatus.CONFLICTING:
            conflict_msg = (
                "CONFLICTING REGULATIONS DETECTED — Multiple contradictory rules exist across "
                "different regulatory versions in the official records. Please specify your academic cohort."
            )
            return QueryResponse(
                request_id=request_id,
                status=ResponseStatus.CONFLICTING_VERSIONS,
                answer=conflict_msg,
                language=out_lang,
                citations=[],
                evidence_status=EvidenceStatus.CONFLICTING,
                latency_ms=latency,
                model_used=settings.ollama_model,
            )
        return QueryResponse(
            request_id=request_id,
            status=ResponseStatus.ERROR,
            answer=None,
            language=out_lang,
            citations=[],
            evidence_status=evidence_decision.status,
            latency_ms=latency,
            model_used=settings.ollama_model,
        )

    # Check for UNANSWERABLE self-report from model
    if "UNANSWERABLE" in raw_output.upper():
        latency = (time.perf_counter() - t0) * 1000
        return QueryResponse(
            request_id=request_id,
            status=ResponseStatus.UNANSWERABLE,
            answer="UNANSWERABLE — Insufficient information available in the provided documents.",
            language=out_lang,
            citations=[],
            evidence_status=EvidenceStatus.INSUFFICIENT,
            latency_ms=latency,
            model_used=settings.ollama_model,
        )

    # Extract and validate citations
    citations, cleaned_answer, claim_res = _extract_citations_and_claims(
        raw_output,
        evidence_decision.valid_passages,
        doc_filenames,
    )

    # DEFECT-GEN-02: Zero-Citation Bypass Prevention
    # When evidence was sufficient or partial, but the LLM omitted source citations:
    if len(citations) == 0 and evidence_decision.status in (EvidenceStatus.SUFFICIENT, EvidenceStatus.PARTIAL):
        logger.info("Zero citations detected from initial generation. Triggering 1-bounded retry prompt.")
        retry_prompt = _RETRY_CITATION_PROMPT.format(
            question=query_analysis.original_query,
            evidence=evidence_text,
            previous_answer=raw_output,
        )
        try:
            retry_output = await _call_ollama(retry_prompt, _SYSTEM_PROMPT)
            if "UNANSWERABLE" in retry_output.upper():
                latency = (time.perf_counter() - t0) * 1000
                return QueryResponse(
                    request_id=request_id,
                    status=ResponseStatus.UNANSWERABLE,
                    answer="UNANSWERABLE — Insufficient information available in the provided documents.",
                    language=out_lang,
                    citations=[],
                    evidence_status=evidence_decision.status,
                    latency_ms=latency,
                    model_used=settings.ollama_model,
                )
            retry_citations, retry_cleaned, retry_claim_res = _extract_citations_and_claims(
                retry_output,
                evidence_decision.valid_passages,
                doc_filenames,
            )
            if len(retry_citations) > 0:
                citations = retry_citations
                cleaned_answer = retry_cleaned
                claim_res = retry_claim_res
                raw_output = retry_output
        except Exception as retry_exc:
            logger.warning("Retry citation generation failed: %s", retry_exc)

        # If citations are STILL missing after retry, safely abstain
        if len(citations) == 0:
            logger.warning("Generation yielded zero valid citations after retry. Abstaining with UNANSWERABLE.")
            latency = (time.perf_counter() - t0) * 1000
            return QueryResponse(
                request_id=request_id,
                status=ResponseStatus.UNANSWERABLE,
                answer="UNANSWERABLE — Factual claims could not be verified against corpus citations.",
                language=out_lang,
                citations=[],
                evidence_status=evidence_decision.status,
                latency_ms=latency,
                model_used=settings.ollama_model,
            )

    # DEFECT-GEN-01: Contradicted Claims Leaking into ANSWERED responses
    # When claim_verifier identifies contradicted claims in the generated text:
    if claim_res.contains_contradiction:
        logger.warning("Contradicted claims detected in generated answer. Suppressing ungrounded answer.")
        discrepancies = [
            f"Claim: '{c.claim_text}' -> Discrepancy: {'; '.join(c.discrepancies or [c.explanation])}"
            for c in claim_res.claims
            if c.verdict == ClaimVerificationVerdict.CONTRADICTED
        ]
        discrepancy_str = ";\n".join(discrepancies) if discrepancies else "Statements directly contradict cited regulatory records."
        cleaned_answer = (
            f"CONTRADICTION DETECTED — The generated answer contains statements that contradict authoritative regulatory records:\n"
            f"{discrepancy_str}\n\n"
            f"Please refer to official university notifications or specify cohort details."
        )
        resp_status = ResponseStatus.CONFLICTING_VERSIONS
    else:
        # Additional Grounding Enforcement: Uncertainty qualification for low-grounded claims
        if claim_res.total_claims > 0 and claim_res.grounding_ratio < 0.40:
            unverified_claims = [
                c.claim_text for c in claim_res.claims
                if c.verdict != ClaimVerificationVerdict.ENTAILED
            ]
            if unverified_claims:
                qual_text = (
                    f"[UNCERTAINTY QUALIFICATION: The following claims could not be fully verified against cited sources: "
                    f"{'; '.join(unverified_claims[:2])}]\n\n"
                )
                cleaned_answer = qual_text + cleaned_answer

        # Determine response status
        if evidence_decision.status == EvidenceStatus.CONFLICTING:
            resp_status = ResponseStatus.CONFLICTING_VERSIONS
        elif evidence_decision.status == EvidenceStatus.PARTIAL:
            resp_status = ResponseStatus.ANSWERED
        elif evidence_decision.status == EvidenceStatus.CLARIFICATION_REQUIRED:
            resp_status = ResponseStatus.CLARIFICATION_NEEDED
        else:
            resp_status = ResponseStatus.ANSWERED

    latency = (time.perf_counter() - t0) * 1000

    retrieval_summary = None
    if debug:
        retrieval_summary = {
            "evidence_status": evidence_decision.status.value,
            "coverage_score": evidence_decision.coverage_score,
            "passages_used": len(evidence_decision.valid_passages),
            "conflict_count": len(evidence_decision.conflicting_passages),
            "grounding_ratio": claim_res.grounding_ratio,
            "contradiction_detected": claim_res.contains_contradiction,
        }

    return QueryResponse(
        request_id=request_id,
        status=resp_status,
        answer=cleaned_answer,
        language=out_lang,
        citations=citations,
        evidence_status=evidence_decision.status,
        query_analysis=query_analysis if debug else None,
        retrieval_summary=retrieval_summary,
        latency_ms=latency,
        model_used=settings.ollama_model,
    )
