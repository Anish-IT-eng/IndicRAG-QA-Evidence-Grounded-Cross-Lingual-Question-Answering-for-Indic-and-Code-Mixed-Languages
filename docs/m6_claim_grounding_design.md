# IndicRAG-QA — M6 Atomic Claim-Level Grounding Specification (Phase 1B)

**Milestone:** M6 — Evidence Reliability and Answerability  
**Phase:** Phase 1B (Methodological Correction & Implementation Specification)  
**Date:** 2026-11-10  
**Author:** Senior RAG Evaluation Researcher & Evidence Reliability Engineer  
**Target File for Phase 2 Implementation:** `backend/app/generation/generator.py` & `backend/app/evaluation/metrics.py`  
**Defect Addressed:** Replacement of hardcoded `claim_supported = True` (in `generator.py` line 151) with rigorous atomic claim verification  

---

## 1. Executive Summary & Defect Remediation

In the Milestone 5 generation pipeline (`backend/app/generation/generator.py`), citation validation verified only whether the parsed `passage_id` existed in the retrieved passage dictionary (`passage_map`). If the ID was present, the citation object was instantiated with:
```python
claim_supported = True  # <--- CRITICAL ARCHITECTURAL DEFECT
```
Under this implementation, if an LLM generates a hallucinated statement (e.g. *"Students require only 40% attendance"*) and cites a valid retrieved passage that actually says *"Students require 75% attendance"*, the pipeline marks the citation as `claim_supported = True`.

This document specifies the algorithmic replacement for this defect: a **Natural Language Inference (NLI) & Symbolic Claim-Grounding Verifier** that decomposes generated answers into atomic factual claims, evaluates 3-way semantic entailment against cited passage text, enforces strict numerical and negation consistency, and triggers safe response fallbacks when claims are ungrounded.

---

## 2. Claim-Grounding Architecture Overview

```
                 Generated Text from LLM
                            │
                            ▼
          ┌───────────────────────────────────┐
          │   1. Atomic Claim Decomposition   │
          │  Sentence / Clause Normalization  │
          │    C={c_1, c_2, ..., c_m}         │
          └─────────────────┬─────────────────┘
                            │
                            ▼
          ┌───────────────────────────────────┐
          │   2. Citation & Evidence Mapping  │
          │   Link each c_j -> Passage(s) P_j │
          └─────────────────┬─────────────────┘
                            │
                            ▼
          ┌───────────────────────────────────┐
          │   3. Dual-Layer Claim Verifier    │
          │   - Layer A: Symbolic Consistency │
          │     (Numbers, Negation, Dates)    │
          │   - Layer B: Semantic Entailment  │
          │     (ENTAILED / CONTRADICTED /    │
          │      INSUFFICIENT_SUPPORT)        │
          └─────────────────┬─────────────────┘
                            │
                            ▼
          ┌───────────────────────────────────┐
          │   4. Safe Fallback & Response Gating
          │   - All Core Entailed -> Output   │
          │   - Contradiction -> Abstain      │
          │   - Partial -> Filter & Disclose  │
          └───────────────────────────────────┘
```

---

## 3. Algorithmic Workflow Specification

### 3.1 Step 1: Atomic Claim Decomposition

The generated answer text $\hat{A}$ is normalized and segmented into a set of discrete, atomic factual claims:
$$\mathcal{C}(\hat{A}) = \{c_1, c_2, \dots, c_m\}$$

#### Decomposition Rules:
1. **Punctuation & Sentence Splitting:** Sentences are split on standard sentence boundaries (`.`, `!`, `?`, `।` [Devanagari danda]).
2. **Conjunction Splitting:** Sentences containing coordinating conjunctions (*"and"*, *"or"*, *"aur"*, *"tatha"*) joined with independent clauses are split into atomic propositions.
3. **Citation Anchor Tracking:** Each extracted claim preserves its immediate trailing citation marker `[Source: pid, page X]`.

### 3.2 Step 2: Evidence Mapping

For each atomic claim $c_j$, identify the cited passage $P_j$:
$$\mathcal{M}: c_j \mapsto P_j \in \mathcal{D}_{\text{retrieved}}$$
- If a claim has no explicit citation marker, it inherits the citation of the governing sentence, or is marked as `UNCITED`.
- If a claim cites multiple passages, $P_j$ is the union of cited passages.

### 3.3 Step 3: Dual-Layer Claim Verification

Each pair $(c_j, P_j)$ undergoes two-tier verification:

#### Layer A — Symbolic Regulatory Consistency:
Regulatory QA failure often occurs in discrete entities that embedding models blur. We enforce strict symbolic verification:
1. **Numerical Entity Invariance:**
   - Extract all numerical tokens, percentages, and marks from $c_j$ and $P_j$: $\mathcal{N}(c_j)$ and $\mathcal{N}(P_j)$.
   - Condition: Every number mentioned in $c_j$ must exist in $P_j$ or be an exact arithmetical consequence (e.g. *"75%"* in claim must exist as *"75%"* in passage).
   - If $\mathcal{N}(c_j) \not\subseteq \mathcal{N}(P_j) \implies$ Flagged as `NUMERICAL_MISMATCH` $\implies$ `CONTRADICTED`.
2. **Negation & Polarity Invariance:**
   - Detect negation operators: `{"not", "never", "no", "nahi", "debared", "prohibited", "ineligible"}`.
   - If $c_j$ asserts an affirmative action (e.g. *"can take exam"*) while $P_j$ contains explicit negation (e.g. *"shall not be allowed to take the supplementary examination"*), polarity check fails $\implies$ `CONTRADICTED`.
3. **Temporal & Date Invariance:**
   - Any date strings (e.g. *"03-12-2026"*, *"30-11-2026"*, *"5 days"*) in $c_j$ must match $P_j$ character-for-character.

#### Layer B — 3-Way Semantic Entailment:
If Layer A passes, evaluate semantic entailment $E(c_j, P_j) \in \{\text{ENTAILED}, \text{CONTRADICTED}, \text{INSUFFICIENT\_SUPPORT}\}$:
- **`ENTAILED` (Supported):** The factual premise of $c_j$ is directly stated or strictly entailed by $P_j$.
- **`CONTRADICTED`:** $P_j$ asserts facts that directly falsify $c_j$.
- **`INSUFFICIENT_SUPPORT` (Ungrounded):** $P_j$ does not contain enough information to prove or disprove $c_j$ (extrapolation or hallucination).

---

## 4. Grounding Metrics and Mathematical Formulations

Let an answer $\hat{A}$ contain $m$ atomic claims $\{c_1, \dots, c_m\}$.

1. **Claim Support Rate / Entailment Ratio ($S_{\text{claim}}$):**
   $$S_{\text{claim}} = \frac{1}{m} \sum_{j=1}^{m} \mathbb{I}(E(c_j, P_j) == \text{ENTAILED})$$
   Measures the fraction of generated factual claims grounded in official evidence. **Target: $1.00$ ($100\%$)**.

2. **Contradiction Rate ($R_{\text{contra}}$):**
   $$R_{\text{contra}} = \frac{1}{m} \sum_{j=1}^{m} \mathbb{I}(E(c_j, P_j) == \text{CONTRADICTED})$$
   Measures the fraction of claims that actively contradict official university regulations. **Target: $0.00$ ($0\%$)**.

3. **Unsupported Claim Rate ($R_{\text{unsupported}}$):**
   $$R_{\text{unsupported}} = \frac{1}{m} \sum_{j=1}^{m} \mathbb{I}(E(c_j, P_j) == \text{INSUFFICIENT\_SUPPORT})$$

4. **Citation Precision ($P_{\text{cit}}$):**
   $$P_{\text{cit}} = \frac{|\mathcal{C}_{\text{cited}} \cap \mathcal{G}_{\text{gold}}|}{|\mathcal{C}_{\text{cited}}|}$$

5. **Citation Coverage ($C_{\text{cit}}$):**
   $$C_{\text{cit}} = \frac{|\mathcal{C}_{\text{cited}} \cap \mathcal{G}_{\text{gold}}|}{|\mathcal{G}_{\text{gold}}|}$$

---

## 5. Safe Response Fallback Policy

When an answer exhibits partial grounding, the generator enforces a strict safety contract:

```
                      Verified Claims Evaluation
                                   │
                   ┌───────────────┴───────────────┐
                   ▼                               ▼
       Any Claim CONTRADICTED?         Any Claim INSUFFICIENT?
       ├── Yes                         ├── Yes
       │   ▼                           │   ▼
       │ [ IMMEDIATE ABSTENTION ]      │ Is Unsupported Claim Core?
       │ Output: "UNANSWERABLE —       │ ├── Yes ──► [ ABSTAIN ]
       │ Generated claims contradict   │ └── No  ──► [ FILTER & DISCLOSE ]
       │ official university rules."   │             Emit only verified claims;
       └── No                          │             disclose unverified aspects.
                                       └── No
                                           ▼
                                   [ EMIT GROUNDED ANSWER ]
```

### Safety Rules:
1. **Zero-Tolerance on Contradiction:** If even a single claim $c_j$ is marked `CONTRADICTED`, the entire answer is suppressed. The system abstains and logs an alert.
2. **Core vs. Auxiliary Claim Gating:**
   - If the main answer verb/clause is `INSUFFICIENT_SUPPORT`, the system transitions to `EvidenceStatus.INSUFFICIENT` and abstains.
   - If an auxiliary clause is ungrounded (e.g. conversational filler or unmentioned deadline), the generator purges the ungrounded sentence and outputs only the verified subset with an explicit caveat.

