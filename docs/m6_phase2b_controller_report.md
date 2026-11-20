# IndicRAG-QA — M6 Phase 2B: Six-State Evidence Controller Report

**Milestone:** M6 — Evidence Reliability and Answerability  
**Status:** PHASE 2B DELIVERABLE (Approved Implementation)  
**Corpus SHA-256:** `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d`  
**Module:** `backend/app/retrieval/evidence_controller.py`  

---

## 1. Executive Summary & Architectural Purpose

The **Evidence Controller** serves as the authoritative decision gate between retrieval and generation. Rather than delegating hallucination prevention to LLM self-assessment, the controller deterministically evaluates retrieved context against university regulations, enforcing strict failure modes and clarifying ambiguities.

### Architectural Core Invariant
**High CECI score CAN NEVER override:**
1. Missing mandatory cohort parameters
2. Competing regulatory version conflicts
3. Contradictory user premises
4. Zero valid citations or zero intent keyword coverage

---

## 2. Six Canonical Evidence States

```mermaid
flowchart TD
    Q[Retrieved Evidence Pool & Query Analysis] --> S1{Missing Mandatory Cohort Parameter?}
    S1 -- Yes --> StateCR[CLARIFICATION_REQUIRED]
    S1 -- No --> S2{Competing Version Conflict?}
    S2 -- Yes --> StateCONF[CONFLICTING]
    S2 -- No --> S3{Zero Passages or Out-of-Domain?}
    S3 -- Yes --> StateMISS[MISSING]
    S3 -- No --> S4{Contradictory User Premise?}
    S4 -- Yes --> StateINSUF1[INSUFFICIENT (Premise Block)]
    S4 -- No --> S5{Zero Valid Passages or Zero Keyword Match?}
    S5 -- Yes --> StateINSUF2[INSUFFICIENT (Zero Coverage)]
    S5 -- No --> S6[Compute CECI: Psi]
    S6 --> T1{Psi >= 0.65?}
    T1 -- Yes --> CovCheck{Multi-Part and Coverage < 0.60?}
    CovCheck -- Yes --> StatePART1[PARTIAL]
    CovCheck -- No --> StateSUFF[SUFFICIENT]
    T1 -- No --> T2{Psi >= 0.35?}
    T2 -- Yes --> StatePART2[PARTIAL]
    T2 -- No --> StateINSUF3[INSUFFICIENT]
```

| State Code | Canonical State Name | Trigger Conditions | Downstream Action |
| :--- | :--- | :--- | :--- |
| **CR** | `CLARIFICATION_REQUIRED` | Query asks about cohort-dependent rule (e.g. attendance threshold) but omits admission batch/year. | Generation abstains; prompt user for student cohort. |
| **CONF** | `CONFLICTING` | Top evidence contains competing provisions from different documents (e.g. 2017 vs 2022 ordinances). | Generate answer disclosing specific version conflict. |
| **MISS** | `MISSING` | Zero passages retrieved or query is completely out-of-domain with respect to university rules. | Fast abstention without LLM call; return out-of-scope notice. |
| **INSUF** | `INSUFFICIENT` | Contradictory user premise, zero intent keywords matched, or $\Psi < \tau_{\text{insuff}} = 0.35$. | Fast abstention without LLM call; prompt retry or explain invalid premise. |
| **PART** | `PARTIAL` | CECI in $[0.35, 0.65)$, or high CECI but multi-part query has incomplete sub-question coverage ($<0.60$). | Generate answer addressing answered portions; disclose ungrounded clauses. |
| **SUFF** | `SUFFICIENT` | CECI $\ge \tau_{\text{suff}} = 0.65$, coverage $\ge 0.60$, citations valid, no override triggers. | Full generation with verified passage citations. |

---

## 3. Deterministic Override Precedence Specification

Execution order is strictly sequential: earlier checks unconditionally override subsequent evaluations:

### Step 1: Missing Mandatory Cohort Parameter Override
- **Trigger:** Query touches cohort-varying topics (e.g. minimum attendance percentage, condonation caps) without containing any cohort identifier (`2017`, `2022`, `batch`, `cohort`), AND retrieved passages contain multi-ordinance variance (e.g. both Ordinance 2017 [80%] and Notification 307 [75%]).
- **Outcome:** `CLARIFICATION_REQUIRED`.
- **Reasoning:** Providing a single number without knowing whether the student was admitted under 2017 or 2022 rules constitutes misinformation.

### Step 2: Competing Version Conflict Override
- **Trigger:** Both valid and conflicting (superseded/demoted) passages are retrieved, AND either:
  1. The top passage itself is flagged as superseded/non-current, OR
  2. A conflicting passage closely rivals the top valid passage score ($\text{score}_{\text{conf}} \ge 0.80 \cdot \text{score}_{\text{valid}}$) from a different source document.
- **Outcome:** `CONFLICTING`.
- **Reasoning:** Lower-ranked demoted historical passages do not cause conflict if the system successfully prioritizes current regulations; conflict is only asserted when active competition exists at the top of the ranking.

### Step 3: Zero Evidence / Out-of-Domain Override
- **Trigger:** $|D| = 0$, or query matches out-of-domain lexicon (e.g. sports, cooking, astrophysics).
- **Outcome:** `MISSING`.
- **Reasoning:** Zero evidence cannot be enriched by LLM generation.

### Step 4: Contradictory User Premise Override
- **Trigger:** User query presupposes a condition strictly forbidden by university statutes:
  - Debarment with 'X' grade $\to$ requesting makeup or supplementary examination.
  - Course passed with grade A/B/C $\to$ requesting makeup examination.
  - Academic suspension / expulsion $\to$ requesting semester course registration.
- **Outcome:** `INSUFFICIENT` with explanatory note.
- **CRITICAL SAFEGUARD:** High retrieval score or high CECI can **NEVER** override an invalid premise.

### Step 5: Zero Valid Passages or Zero Keyword Coverage Override
- **Trigger:** No valid non-superseded passages exist, OR query has intent keywords but the retrieved text contains zero matching intent terms ($\text{coverage} = 0.0$).
- **Outcome:** `INSUFFICIENT`.
- **Reasoning:** Prevents hallucinated generations when retrieval returns completely off-topic passages.

### Step 6: CECI Confidence Thresholding
- Evaluates the 5-feature convex combination $\Psi \in [0.0, 1.0]$.
- **High Evidence Region ($\Psi \ge 0.65$):**
  - If multi-part query and sub-question coverage $< 0.60 \implies$ `PARTIAL`.
  - Otherwise $\implies$ `SUFFICIENT`.
- **Moderate Evidence Region ($0.35 \le \Psi < 0.65$):** $\implies$ `PARTIAL`.
- **Low Evidence Region ($\Psi < 0.35$):** $\implies$ `INSUFFICIENT`.

---

## 4. Atomic Claim-Level Grounding Architecture

Implemented in `backend/app/generation/claim_grounding.py`:

```
Generated Answer
       │
       ▼
[Atomic Claim Decomposition]
       │
       ├──> Deterministic Numeric Verification (Regex percentage/cutoff extraction)
       ├──> Deterministic Date/Temporal Verification (Academic year/month extraction)
       └──> Deterministic Polarity/Negation Verification (Topic permission vs prohibition)
       │
       ▼
[Independent Semantic Entailment Engine]
(Generator-Verifier Separation: gemma:2b output verified by llama3.2:3b / qwen2.5:3b)
       │
       ▼
Formal Claim Verdict: ENTAILED | CONTRADICTED | INSUFFICIENT_SUPPORT
```

### Deterministic Sub-Verifier Rules
1. **Numeric Verification:** Every number, percentage, or credit cutoff appearing in the generated claim must have an exact or normalized representation in the cited evidence passage. If the claim asserts "60% attendance" when the passage states "75%", `numeric_verified = False` and verdict becomes `CONTRADICTED`.
2. **Polarity Verification:** If evidence contains strict prohibitions on a topic ("shall not be permitted to take makeup examination") and the claim asserts affirmative permission ("student can take makeup with Dean approval"), `negation_verified = False` and verdict becomes `CONTRADICTED`.
3. **Citation Validation:** In `generator.py`, the legacy hardcoded `claim_supported = True` is replaced with `claim_supported = bool(not claim_res.contains_contradiction and (claim_res.grounding_ratio >= 0.4 or claim_res.total_claims == 0))`.

---

## 5. Verification & Regression Analysis

The six-state Evidence Controller and override precedence were verified in `backend/tests/test_m6_phase2b_scoring_and_controller.py`:
- `test_override_step1_clarification_required`: Verified missing cohort on attendance query triggers `CLARIFICATION_REQUIRED`.
- `test_override_step2_conflicting_versions`: Verified competing documents trigger `CONFLICTING`.
- `test_override_step3_zero_retrieved_missing`: Verified zero retrieval triggers `MISSING`.
- `test_override_step4_contradictory_premise_blocks_high_ceci`: Verified makeup exam after 'X' grade triggers `INSUFFICIENT` despite high scores.
- `test_state_sufficient_on_high_ceci`: Verified high CECI triggers `SUFFICIENT`.
- `test_state_partial_on_multi_part_incomplete_coverage`: Verified multi-part coverage gaps trigger `PARTIAL`.
- `test_e10_defect_regression`: Verified weak retrieval triggers `INSUFFICIENT` and retry flag.

