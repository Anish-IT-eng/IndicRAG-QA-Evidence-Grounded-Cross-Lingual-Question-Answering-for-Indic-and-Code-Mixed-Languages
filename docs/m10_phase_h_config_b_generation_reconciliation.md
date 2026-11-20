# M10 Phase H — Config B Generation Outcome & Abstention Reconciliation

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** H — Cross-Lingual End-to-End Answer Quality, Citation & Grounding Audit  
**Date:** November 18, 2026  
**Document Type:** Final Generation & Abstention Reconciliation Report (Config B)  
**Current Determination:** `M10_PHASE_H_VERIFIED_WITH_LIMITATIONS`  
**Production Runtime Default:** Verified invariant as `"production"` in [backend/app/retrieval/engine.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L395)  

---

## 1. Executive Summary & Audit Mandate

This report resolves the final one-query accounting discrepancy in Config B (`E6b_ADAPTIVE_BI_ENCODER`) between generation invocation counts ($62$ vs $63$) and execution-stage abstentions ($176$ vs $175$).

### The Discrepancy Identified & Resolved:
The single record responsible for both differences is **`M9-Q002`** (Hindi Devanagari, Intent `M9-INT-01`):
1. **The 62 vs. 63 Generated Output Discrepancy:**
   - Filtering execution traces by `generation_latency_ms > 1.0` counted only queries where the local LLM (`qwen2.5:3b`) was executed on CPU ($N=62$).
   - However, `M9-Q002` triggered `EvidenceStatus.CLARIFICATION_REQUIRED` in the Evidence Controller, which emitted an authoritative structured regulatory disclosure immediately via `generator.py` line 324 (`# Handle clarification required immediately (no LLM call)`), with latency `0.1 ms`.
   - While `M9-Q002` did not invoke the LLM, it **did produce an authoritative generated disclosure**.
   - Total generated outputs: **$62 \text{ (LLM-invoked)} + 1 \text{ (Controller-direct `M9-Q002`)} = \mathbf{63}$** (61 answerable successes + 2 unanswerable failures).
2. **The 176 vs. 175 Abstention Discrepancy:**
   - Queries with `generation_latency_ms <= 1.0` totaled $121$.
   - Previous summaries incorrectly treated all 121 as execution-stage abstentions, yielding $121 + 55 = 176$.
   - However, `M9-Q002` was one of those 121 queries! `M9-Q002` was a **regulatory disclosure**, not an abstention.
   - True controller-bypassed abstentions $= 121 - 1 = \mathbf{120}$.
   - Summing controller-bypassed abstentions ($120$) and post-generation abstentions ($55$) yields:
     $$120 + 55 = \mathbf{175\text{ total abstentions}}$$
   - This matches the audited final outcome:
     $$117 \text{ unnecessary abstentions} + 58 \text{ correct abstentions} = \mathbf{175\text{ total abstentions}}$$

---

## 2. Forensic Profile of the Three Pivotal Edge-Case Queries

To ensure complete empirical transparency, the three queries involved in non-standard execution paths are profiled directly from the raw records:

### 2.1 Query `M9-Q002` (The One-Record Reconciliation Query)
- **Query ID:** `M9-Q002` (Hindi Devanagari)
- **Query Text:** *"एंड सेमेस्टर परीक्षा में बैठने के लिए न्यूनतम कितनी उपस्थिति आवश्यक है?"*
- **Expected Status:** `ANSWERED`
- **Response Status:** `clarification_needed`
- **Final Outcome Classification:** `REGULATORY_DISCLOSURE` (Combined Regulatory Success)
- **Evidence Controller Status:** `clarification_required` (CECI Score: $0.8000$)
- **LLM Invocation Status:** **Bypassed (No LLM Call).** Handled deterministically by `generate_answer()` line 324.
- **Generation Latency:** `0.10 ms`
- **Generated Answer Text:**
  > *"CLARIFICATION REQUIRED — Structured Regulatory Disclosure: 75% minimum aggregate attendance is required by the Registrar to appear in End Semester Examinations (Notification 307/2022), while 70% attendance in a course is required to avoid an 'X' grade and course repetition (SCSET Academic Rules Clause 30.1). Query lacks student cohort or admission year parameter. Please specify student batch or regulatory purpose."*
- **Role in Discrepancy:** Its sub-millisecond latency caused it to be grouped with bypassed abstentions ($121$) while being omitted from LLM-invoked outputs ($62$).

### 2.2 Query `M9-Q201` (Unanswerable False Answer)
- **Query ID:** `M9-Q201` (English)
- **Query Text:** *"What is the mandatory uniform or dress code for School of Law students on weekdays?"*
- **Expected Status:** `UNANSWERABLE` (No SOL-specific uniform policy exists in the corpus)
- **Response Status:** `answered`
- **Final Outcome Classification:** `INCORRECT_ANSWER` (Unanswerable False Answer)
- **Evidence Controller Status:** `partial` (CECI Score: $0.3688 \ge 0.35$)
- **LLM Invocation Status:** **Invoked on CPU.**
- **Generation Latency:** `86,273.60 ms` (~86.3 seconds)
- **Generated Answer Text:** General university dress decorum rules from Student Discipline regulations.

### 2.3 Query `M9-Q229` (Unanswerable Adversarial Conflict Warning)
- **Query ID:** `M9-Q229` (English)
- **Query Text:** *"Why is 50% attendance allowed for final examinations at Bennett University?"*
- **Expected Status:** `UNANSWERABLE` (False premise: 50% is never allowed)
- **Response Status:** `conflicting_versions`
- **Final Outcome Classification:** `INCORRECT_ANSWER` (Unanswerable Regulatory Warning)
- **Evidence Controller Status:** `partial` (CECI Score: $0.4228 \ge 0.35$)
- **LLM Invocation Status:** **Invoked on CPU.**
- **Generation Latency:** `78,075.80 ms` (~78.1 seconds)
- **Post-Generation Verifier Action:** Flagged discrepancy because the token '50' from the generator's refutation claim was absent in evidence, converting the response into a `conflicting_versions` disclosure.

---

## 3. Mutually Exclusive Per-Query Transition Table (Config B, $N=240$)

Every one of the 240 Config B records in [m10_phase_h_per_query_results.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_h_per_query_results.csv) maps to exactly one of the six transition paths:

| Transition Path # | Execution-Stage Transition | Query Count | Percentage | Representative / Exhaustive Query IDs |
|---|---|---:|---:|---|
| **Path 1** | **Controller Bypassed LLM $\to$ Final Abstention** | 120 | 50.00% | `M9-Q001`, `M9-Q003`, `M9-Q004`, `M9-Q006`, `M9-Q010`, `M9-Q014`, `M9-Q018`, `M9-Q022`, ..., `M9-Q240` (120 queries where Evidence Controller evaluated $CECI < 0.35$ and bypassed LLM) |
| **Path 2** | **Controller Bypassed LLM $\to$ Direct Regulatory Disclosure** | 1 | 0.42% | `M9-Q002` (Deterministic structured regulatory disclosure emitted via `generator.py` line 324 without LLM) |
| **Path 3** | **Controller Invoked LLM $\to$ Correct Answer / Disclosure** | 60 | 25.00% | 53 Direct Answers (`M9-Q005`, `M9-Q007`, `M9-Q008`, ..., `M9-Q176`, `M9-Q058`) + 7 Regulatory Disclosures (`M9-Q021`, `M9-Q023`, `M9-Q065`, `M9-Q072`, `M9-Q141`, `M9-Q144`, `M9-Q172`) |
| **Path 4** | **Controller Invoked LLM $\to$ Post-Generation Abstention** | 55 | 22.92% | `M9-Q027`, `M9-Q031`, `M9-Q032`, `M9-Q035`, `M9-Q043`, `M9-Q047`, `M9-Q051`, `M9-Q061`, `M9-Q063`, ..., `M9-Q239` (55 queries where LLM was called, but output lacked support or verifier forced abstention) |
| **Path 5** | **Controller Invoked LLM $\to$ Incorrect Output on Unanswerable** | 2 | 0.83% | `M9-Q201` (Law school dress code direct answer) and `M9-Q229` (False premise attendance conflict warning) |
| **Path 6** | **Controller Invoked LLM $\to$ Pipeline Execution Error** | 2 | 0.83% | `M9-Q123` (`hi-Latn`) and `M9-Q124` (`en-hi`) (Ollama JSON parsing error during generation) |
| **Total** | **All Config B Benchmark Records** | **240** | **100.0%** | **$120 + 1 + 60 + 55 + 2 + 2 = 240$. 100% unique and complete.** |

---

## 4. Reconciled Accounting Summaries

### 4.1 Reconciled Output Accounting ($N=240$)
- **Total Non-Abstaining Answers / Disclosures:**
  $$\text{Path 2 } (1) + \text{Path 3 } (60) + \text{Path 5 } (2) = \mathbf{63\text{ outputs}}$$
  *(Comprising 61 answerable successes + 2 unanswerable failures).*
- **Total Final Abstentions:**
  $$\text{Path 1 } (120) + \text{Path 4 } (55) = \mathbf{175\text{ abstentions}}$$
  *(Comprising 117 unnecessary abstentions + 58 correct abstentions).*
- **Total Pipeline Execution Errors:**
  $$\text{Path 6 } = \mathbf{2\text{ errors}}$$
- **Exhaustive Sum:**
  $$63 \text{ outputs} + 175 \text{ abstentions} + 2 \text{ errors} = \mathbf{240\text{ queries}}$$

### 4.2 Reconciled Execution-Stage Accounting ($N=240$)
- **LLM Generation Invoked:**
  $$\text{Path 3 } (60) + \text{Path 4 } (55) + \text{Path 5 } (2) + \text{Path 6 } (2) = \mathbf{119\text{ queries}}$$
- **LLM Generation Bypassed:**
  $$\text{Path 1 } (120) + \text{Path 2 } (1) = \mathbf{121\text{ queries}}$$
- **Exhaustive Sum:**
  $$119 \text{ invoked} + 121 \text{ bypassed} = \mathbf{240\text{ queries}}$$

---

## 5. Re-Verification of Latency Aggregates

Because `M9-Q002` recorded `generation_latency_ms = 0.10 ms` (bypassed), all timing calculations based on `generation_latency_ms > 1.0` remain mathematically exact:

| Timing Metric | Population / Subset Evaluated | Config A (Production) | Config B (Adaptive E6b) | Discrepancy Status |
|---|---|---:|---:|---|
| **Retrieval Mean** | All 240 benchmark queries | 2,805.54 ms | 2,372.50 ms | Exact |
| — Hindi Devanagari Retrieval Mean | 60 Hindi queries | 1,907.62 ms | **175.46 ms** | **Exact (90.8% reduction)** |
| **Controller Mean** | All 240 benchmark queries | 1.50 ms | 1.25 ms | Exact |
| **Invoked Generation Mean** | 117 queries (Config A) / 119 queries (Config B) | **89,995.25 ms** | **88,532.03 ms** | **Exact (Conditional on LLM call)** |
| **Amortized Generation Mean** | All 240 queries (including bypassed zeros) | **43,872.76 ms** | **43,897.19 ms** | **Exact (Population amortized)** |
| **Total Pipeline Mean** | All 240 benchmark queries | **46,694.32 ms** | **46,270.94 ms** | **Exact match ($2372.5 + 1.25 + 43897.2$)** |

---

## 6. Answers to the Specific Reconciliation Questions

1. **What was the exact query responsible for the discrepancy?**  
   **`M9-Q002`** (Hindi Devanagari, Intent `M9-INT-01` — Attendance Requirements).
2. **What are its correct execution-stage and final-outcome classifications?**  
   - *Execution-Stage Classification:* **Controller-Bypassed Direct Disclosure** (`latency = 0.10 ms`, no LLM called).
   - *Final-Outcome Classification:* **`REGULATORY_DISCLOSURE`** (Combined Regulatory Success).
3. **Do any latency aggregates change?**  
   **No.** The conditional invoked mean ($88,532.03\text{ ms}$ across 119 queries), population-amortized mean ($43,897.19\text{ ms}$ across 240 queries), and total pipeline mean ($46,270.94\text{ ms}$) already accounted for `M9-Q002` as a $0.10\text{ ms}$ observation.
4. **Do all 240 Config B records now reconcile?**  
   **Yes, 100%.** Every single one of the 240 records is mapped to an exhaustive 6-path transition table, resolving both $62 \to 63$ and $176 \to 175$ balances.

---

## 7. Final Determination & Sign-off

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           FINAL RECONCILIATION DETERMINATION:                                ║
║           M10_PHASE_H_VERIFIED_WITH_LIMITATIONS                              ║
║                                                                              ║
║  1. Single-query discrepancy in M9-Q002 identified and fully resolved.      ║
║  2. Mutually exclusive transition table partitions all 240 records.          ║
║  3. Reconciled output total (63) and abstention total (175) verified.        ║
║  4. Latency aggregates verified invariant.                                   ║
║  5. Production default remains "production" in engine.py.                    ║
║  6. Phase I production promotion review has NOT been initiated.              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
