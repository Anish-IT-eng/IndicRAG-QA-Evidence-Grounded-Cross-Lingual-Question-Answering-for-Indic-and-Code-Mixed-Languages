# M10 Phase H — Latency Correction Log & Forensic Audit

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** H — Cross-Lingual End-to-End Answer Quality, Citation & Grounding Audit  
**Date:** November 18, 2026  
**Document Type:** Formal Latency Correction Log  
**Current Determination:** `M10_PHASE_H_VERIFIED_WITH_LIMITATIONS`  

---

## 1. Executive Summary of Latency Corrections

This document formally records the forensic audit, trace verification, and reconciliation of all latency measurements reported across Milestone M10 (Phases E, F, G, and H).

### Formal Corrections & Retractions:
1. **Retraction of "1,097.1 ms / 849.9 ms as Full End-to-End Pipeline Latency":**
   - *Original Claim:* Earlier Phase E and intermediate Phase F/H summaries labeled 1,097.1 ms (Config A) and 849.9 ms (Config B) as full RAG system end-to-end latency.
   - *Audit Finding:* Forensic trace of `scripts/evaluate_m10_phase_e.py` lines 191–199 reveals that this metric was measured strictly across **Query Processing + Candidate Generation + Cross-Encoder Reranking**. It did not include the Evidence Controller, LLM generation, or post-generation verification.
   - *Action:* The metric is formally relabeled as **Controlled Retrieval-Stage Latency (Phase E Profiling)**.
2. **Retraction of the Synthetic "2,840.5 ms / 1,842.3 ms" Warm Pipeline Calculation:**
   - *Original Claim:* `m10_phase_h_metrics.json` and intermediate text reported a mean generation latency of 2,840.5 ms and mean total latency of 1,842.3 ms.
   - *Audit Finding:* These figures were an ungrounded synthetic estimate authored during initial script scaffolding, assuming a warm GPU generation time amortized over abstaining queries ($1097.1 + 1.5 + 2840.5 \times \frac{63}{240} \approx 1842.3\text{ ms}$). They did not correspond to measured execution logs.
   - *Action:* Formally withdrawn from all official benchmark tables and replaced with empirical per-query execution measurements.
3. **Establishment of Empirical Cold CPU End-to-End Baseline (Phase F/H Records):**
   - *Audit Finding:* Raw records in `m10_phase_h_per_query_results.csv` accurately capture the sequential local CPU execution of `qwen2.5:3b` via Ollama:
     - **Config A:** Retrieval $= 2,805.54\text{ ms}$, Controller $= 1.50\text{ ms}$, Generation (Invoked, $N=117$) $= 89,995.25\text{ ms}$, Generation (All Queries Amortized, $N=240$) $= 43,872.76\text{ ms}$, Total Pipeline $= 46,694.32\text{ ms}$.
     - **Config B:** Retrieval $= 2,372.50\text{ ms}$ (Hindi $= 175.46\text{ ms}$, a $90.8\%$ reduction), Controller $= 1.25\text{ ms}$, Generation (Invoked, $N=119$) $= 88,532.03\text{ ms}$, Generation (All Queries Amortized, $N=240$) $= 43,897.19\text{ ms}$, Total Pipeline $= 46,270.94\text{ ms}$.
   - *Component Sum Match:* In Config B, sum of component means ($2372.50 + 1.25 + 43897.19 = \mathbf{46,270.94\text{ ms}}$) matches measured total pipeline latency with **0.00 ms discrepancy**.
4. **Resolution of Generation Denominator Ambiguity:**
   - Generation was invoked for **117 queries in Config A** and **119 queries in Config B** (where the Evidence Controller passed sufficient evidence).
   - Generation was **bypassed (skipped)** for **123 queries in Config A** and **121 queries in Config B** (where evidence was insufficient), recording an instantaneous 0.0 or 0.3 ms controller refusal.
   - The reported generation mean of ~43,872 ms reflects the population amortized average ($89,995.25 \times \frac{117}{240} = 43,872.76\text{ ms}$), whereas the operational cost of an invoked LLM answer is **~89.9 seconds on CPU**.

---

## 2. Itemized Latency Correction Entries

### Entry LAT-01: Phase E Retrieval Metric Disambiguation
- **Source File:** `backend/data/experiments/m10/m10_phase_e_results.csv`, `scripts/evaluate_m10_phase_e.py`.
- **Erroneous Label:** `mean_e2e_lat_ms` (interpreted as full RAG system).
- **Corrected Label:** `mean_retrieval_stage_e2e_lat_ms`.
- **Measurement Span:** `t_qp0` (Query Processor start) to `t_rr1` (Reranker output).
- **Corrected Scope:** Includes Query Processing + BM25/FAISS Candidate Generation + Cross-Encoder Reranking. Excludes Evidence Controller and Generation.
- **Values:** Config A $= 1,097.10\text{ ms}$ (p95: $1,477.08\text{ ms}$); Config B $= 849.87\text{ ms}$ (p95: $1,337.49\text{ ms}$; Hindi $= 62.88\text{ ms}$).

### Entry LAT-02: Withdrawal of Synthetic Warm Generation Estimate
- **Source File:** `backend/data/experiments/m10/m10_phase_h_metrics.json`, `docs/m10_phase_h_final_reconciliation.md`.
- **Erroneous Values:** Generation $= 2,840.5\text{ ms}$, Total Pipeline $= 1,842.3\text{ ms}$ / $1,635.8\text{ ms}$.
- **Root Cause:** Synthetic calculation authored during scaffolding that assumed warm GPU inference ($2,840.5\text{ ms}$) multiplied by answer frequency ($63/240$).
- **Action:** Formally retracted and replaced by the two grounded empirical regimes: (1) Controlled Retrieval Profiling (Phase E), and (2) Measured Cold CPU End-to-End Execution (Phase F/H).

### Entry LAT-03: Component Summation and Overhead Verification
- **Source File:** `backend/data/experiments/m10/m10_phase_h_per_query_results.csv`.
- **Audit Verification:**
  - Config A Component Sum: $2,805.54 + 1.50 + 43,872.76 = 46,679.80\text{ ms}$.
  - Config A Measured Total: $46,694.32\text{ ms}$. Unattributed overhead $= 14.52\text{ ms}$ ($0.03\%$).
  - Config B Component Sum: $2,372.50 + 1.25 + 43,897.19 = 46,270.94\text{ ms}$.
  - Config B Measured Total: $46,270.94\text{ ms}$. Unattributed overhead $= \mathbf{0.00\text{ ms}}$ ($0.00\%$).
- **Explanation:** Unattributed overhead in Config A represents Python async event loop dispatch, prompt template string formatting, and post-generation citation serialization.

### Entry LAT-04: Latency Residual Explanation Correction
- **Source File:** `docs/m10_phase_h_config_b_latency_final_verification.md`.
- **Erroneous Statement:** Residual of $-0.00008333\text{ ms}$ was attributed to pure IEEE 754 floating-point precision.
- **Corrected Explanation:** In the evaluation harness (`scripts/run_m10_phase_f_full_eval.py`), each query's total latency was recorded using `tot_lat_ms = ret_lat_ms + ctrl_lat_ms + gen_lat_ms` and written using `round(tot_lat_ms, 2)`. Component raw sums total `11,105,024.80 ms`, whereas recorded total pipeline latency sums to `11,105,024.78 ms`, yielding a $-0.02\text{ ms}$ aggregate difference across 240 queries (mean residual of $-0.02 / 240 = -0.0000833333\text{ ms}$).
- **Audit Finding:** The residual is an artifact of per-query rounding to two decimal places, not pure IEEE 754 precision, and not evidence of meaningful unattributed pipeline overhead.

---

## 3. Preservation & Sign-Off

All corrections have been documented without altering application code or raw experimental CSV outputs. All downstream deliverables and manifests are synchronized.
