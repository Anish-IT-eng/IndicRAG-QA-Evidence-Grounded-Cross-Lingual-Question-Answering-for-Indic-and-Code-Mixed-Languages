# IndicRAG-QA — M6 Phase 3: Runtime Enforcement Patching and Verification Report

**Document Title:** Runtime Enforcement Patching, Security Verification, and Evidence Answerability Enforcement  
**Milestone:** M6 — Evidence Reliability and Answerability  
**Phase:** Phase 3 (Controlled Implementation, Regression Testing, and Independent Verification)  
**Date:** 2026-11-11  
**Author:** Senior RAG Reliability Engineer & Research Evaluation Lead  
**Status:** COMPLETED & VERIFIED  

---

## Executive Summary

Phase 3 implements production runtime enforcement patches across the answer generation layer [`backend/app/generation/generator.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/generation/generator.py) to resolve the three critical vulnerabilities identified during the Phase 2C diagnostic audit. Without altering frozen benchmark datasets, modifying the underlying SQLite corpus, or compromising historical milestones, Phase 3 establishes deterministic guarantees that:
1. Contradicted claims are suppressed from user-facing answers and mapped strictly to `ResponseStatus.CONFLICTING_VERSIONS` (or abstentions).
2. Zero-citation responses on sufficient evidence undergo a 1-bounded regeneration prompt; if citations remain missing, the system safely abstains with `ResponseStatus.UNANSWERABLE`.
3. `CLARIFICATION_REQUIRED` evidence states deterministically map to `ResponseStatus.CLARIFICATION_NEEDED` without invoking unnecessary LLM generation or leaking unverified content.
4. Low-grounded claims ($\text{grounding ratio} < 0.40$) are prefixed with structured uncertainty qualifications.

A complete 12-scenario automated security and enforcement test suite was added in [`backend/tests/test_m6_phase3_enforcement.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/tests/test_m6_phase3_enforcement.py). The entire backend test suite now passes with **175 passing tests** (142 baseline + 21 Phase 2B + 12 Phase 3).

---

## 1. Provenance and Integrity Verification

All foundational cryptographic digests were verified prior to and post-implementation:

| Artifact Target | Expected SHA-256 Digest | Verified Runtime SHA-256 | Integrity Status |
|---|---|---|---|
| **Corpus Passages (142 child passages)** | `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d` | `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d` | **MATCH (100%)** |
| **M3 Frozen Benchmark ($N=15$)** | `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` | `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` | **MATCH (100%)** |
| **M6 Benchmark ($N=60$)** | `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` | `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` | **MATCH (100%)** |
| **M6 Qualification Ledger ($N=60$)** | `db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13` | `db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13` | **MATCH (100%)** |
| **M6 Phase 3 Negative Benchmark ($N=33$)** | `492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa` | `492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa` | **NEW BENCHMARK (100%)** |

---

## 2. Source Discrepancies Reconciled

During the Phase 3 preflight audit, historical documentation anomalies were resolved against the actual SQLite corpus records:

1. **Attendance Publication Date (`2020` vs `2022`):**
   - The authoritative official attendance notification is `Notification-Minimum-Attendance.pdf` (Passage `0280358a-ff3c-4964-88ab-419a9147b1f0`).
   - Reference No. is `BU/RO/Notification/307/2022`, dated **08th September, 2022**, issued by the Registrar.
   - It became effective **AY 2022-23 (Odd Semester onwards)** and establishes a mandatory **75% minimum attendance** threshold without condonation.
   - The prior "2020" reference in early exploratory notes was an OCR/typographical slip.
2. **Clause References (§12.4 / §9.2 vs §16.1 / §15.7):**
   - Clause search across all 142 passages confirmed that neither "§12.4" nor "§9.2" exists in the corpus DB.
   - The authentic make-up examination clauses are:
     - 2017 Ordinance: **Section 16, Clause 16.1** ("Theory Courses", Page 19, Passage `54dd6b69`) and **Clause 16.2** ("Makeup of End Semester Examination", Page 19, Passage `54dd6b69`).
     - 2022 SCSET Rules: **Section 15.7** ("Grading for failing to meet Attendance Requirement", Page 9, Passage `1163039d`) and **Section 16, Clause 16.2** ("Makeup of End Semester Examination", Page 10, Passage `625fba4f`).
3. **Attendance Rate Divergence (70% vs 75%):**
   - 2017 Ordinance (§30.1(ii), Passage `f88ec726`): minimum **70%** attendance; falling below 70% results in course deregistration with grade 'X'.
   - 2022 Notification 307/2022 (Passage `0280358a`): minimum **75%** attendance with effect from AY 2022-23.
   - 2022 SCSET Rules (§15.7, Passage `5fd38f8d`): allows Dean condonation up to 15% (minimum 60%) for certified medical emergencies.

---

## 3. Runtime Enforcement Patches in `generator.py`

File modified: [`backend/app/generation/generator.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/generation/generator.py).  
Backup preserved: `backend/app/generation/generator.py.bak_20261111_p3`.

### Patch Details

#### 1. DEFECT-GEN-01: Contradicted Claims Suppression
- **Problem:** In Phase 2C, when atomic claim verification detected a factual contradiction (e.g., numeric, date, or negation contradiction), `citation.claim_supported` was marked `False`, but the answer text containing the hallucinated or contradicted claim was returned as `ResponseStatus.ANSWERED`.
- **Patch:**
  ```python
  if claim_res.contains_contradiction:
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
  ```

#### 2. DEFECT-GEN-02: Zero-Citation Bypass Prevention
- **Problem:** When the LLM generated an answer without `[Source: ...]` markers on `SUFFICIENT` or `PARTIAL` evidence, `citations` remained empty, bypassing claim verification, and emitting unverified text as `ResponseStatus.ANSWERED`.
- **Patch:**
  - Implemented 1-bounded retry prompt (`_RETRY_CITATION_PROMPT`) explicitly instructing the model to provide citations for each factual claim.
  - If valid citations remain absent after retry, the generator safely abstains:
    ```python
    if len(citations) == 0:
        return QueryResponse(
            status=ResponseStatus.UNANSWERABLE,
            answer="UNANSWERABLE — Factual claims could not be verified against corpus citations.",
            citations=[],
            ...
        )
    ```

#### 3. DEFECT-GEN-03: Deterministic Clarification Handling
- **Problem:** Downstream generator logic could default to `ANSWERED` when the evidence controller returned `CLARIFICATION_REQUIRED`.
- **Patch:**
  - Fast-path short-circuiting:
    ```python
    if evidence_decision.status == EvidenceStatus.CLARIFICATION_REQUIRED or evidence_decision.clarification_needed:
        explanation = evidence_decision.explanation or "Applicable academic cohort or program version must be specified."
        return QueryResponse(
            status=ResponseStatus.CLARIFICATION_NEEDED,
            answer=f"CLARIFICATION REQUIRED — {explanation}",
            citations=[],
            evidence_status=EvidenceStatus.CLARIFICATION_REQUIRED,
            ...
        )
    ```

#### 4. Additional Grounding Enforcement
- When `claim_res.grounding_ratio < 0.40` without direct contradiction, the generator prepends a structured uncertainty qualification:
  `[UNCERTAINTY QUALIFICATION: The following claims could not be fully verified against cited sources: ...]`

---

## 4. Automated Security & Enforcement Test Suite

Test suite location: [`backend/tests/test_m6_phase3_enforcement.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/tests/test_m6_phase3_enforcement.py).

All 12 test scenarios pass with zero failures:

| Scenario ID | Test Name | Defect Vector | Verified Behavior | Status |
|---|---|---|---|---|
| `SEC-01` | `test_zero_citations_on_sufficient_evidence_triggers_retry` | `DEFECT-GEN-02` | Triggers 1-bounded retry prompt when citations are missing | **PASS** |
| `SEC-02` | `test_zero_citations_after_retry_abstains_unanswerable` | `DEFECT-GEN-02` | Safely abstains with `UNANSWERABLE` if retry omits citations | **PASS** |
| `SEC-03` | `test_contradicted_claims_mapped_to_conflicting_versions` | `DEFECT-GEN-01` | Suppresses direct answer on numeric contradiction; sets `CONFLICTING_VERSIONS` | **PASS** |
| `SEC-04` | `test_contradiction_details_disclosed_in_structured_response` | `DEFECT-GEN-01` | Formats explicit contradiction warning with discrepancy details | **PASS** |
| `SEC-05` | `test_clarification_required_preserves_explanation_no_llm_call` | `DEFECT-GEN-03` | Emits `CLARIFICATION_NEEDED` without calling Ollama LLM | **PASS** |
| `SEC-06` | `test_clarification_needed_flag_triggers_clarification_status` | `DEFECT-GEN-03` | Prevents fallback to `ANSWERED` when `clarification_needed=True` | **PASS** |
| `SEC-07` | `test_low_grounding_receives_uncertainty_qualification` | Grounding | Prepends `[UNCERTAINTY QUALIFICATION: ...]` for low-overlap claims | **PASS** |
| `SEC-08` | `test_well_grounded_answer_passes_safely` | Grounding | Cleanly emits grounded answers with valid `Citation` metadata | **PASS** |
| `SEC-09` | `test_invalid_citation_passage_id_rejected` | Integrity | Hallucinated passage IDs rejected; triggers retry/abstention | **PASS** |
| `SEC-10` | `test_model_self_reported_unanswerable` | Answerability | Self-reported unanswerable output honored immediately | **PASS** |
| `SEC-11` | `test_full_api_endpoint_integration` | API Route | Full FastAPI `/query` endpoint validates schema with patched generator | **PASS** |
| `SEC-12` | `test_crosslingual_enforcement` | Multilingual | Hindi & Hinglish queries maintain language codes and prompt instructions | **PASS** |

### Complete Test Suite Accounting
- Baseline tests: **142**
- Phase 2B tests: **21**
- Phase 3 tests: **12**
- **Total Passing Tests:** **175** (`pytest backend/tests` completed in 46.39s with 0 failures).

---

## 5. Pre/Post-Patch Enforcement Delta on Pilot Queries ($N=29$)

Results file: [`backend/data/experiments/m6/m6_phase3_enforcement_results.csv`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m6/m6_phase3_enforcement_results.csv).

| Metric | Pre-Patch (Phase 2C Diagnostic) | Post-Patch (Phase 3 Enforced) | Delta / Remediation |
|---|---|---|---|
| **Direct Contradiction Leakage Rate** | 3.45% (1/29 queries leaked contradiction) | **0.00%** (0/29 queries leaked) | **100% Contradictions Suppressed** |
| **Ungrounded Zero-Citation Output** | Permitted via bypass | **0.00%** (Requires strict retry or abstention) | **Eliminated Bypass** |
| **Clarification Preservation Rate** | Vulnerable to `ANSWERED` fallback | **100.0%** (Mapped to `CLARIFICATION_NEEDED`) | **Deterministic Handling** |
| **Direct Answer Coverage** | 58.62% (17/29) | 58.62% (17/29) | Preserved safe valid answers |
| **Correct Answer Rate** | 58.62% (17/29) | 58.62% (17/29) | Maintained grounded accuracy |

---

## 6. Conclusion and Next Steps

Phase 3 successfully hardens the runtime answer generation layer against ungrounded and contradictory claim emission. The system now enforces evidence-backed answerability deterministically across all six evidence states.

