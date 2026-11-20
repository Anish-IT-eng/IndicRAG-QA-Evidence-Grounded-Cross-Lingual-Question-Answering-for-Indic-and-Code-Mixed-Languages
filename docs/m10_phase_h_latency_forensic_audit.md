# M10 Phase H — Final Latency Forensic Audit & Measurement Reconciliation

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** H — Cross-Lingual End-to-End Answer Quality, Citation & Grounding Audit  
**Date:** November 18, 2026  
**Document Type:** Formal Latency Forensic Audit  
**Current Determination:** `M10_PHASE_H_VERIFIED_WITH_LIMITATIONS`  

---

## 1. Executive Summary & Audit Mandate

This forensic audit resolves all ambiguities regarding timing definitions, operational boundaries, and measurement conventions reported across Milestone M10.

### Crucial Findings:
1. **The 1,097.1 ms and 849.9 ms Figures:** Forensic code inspection proves that these figures measure **Retrieval-Stage End-to-End Latency** (Query Processing + BM25/FAISS Candidate Generation + Reranking) from the Phase E controlled experiment. They **do not include Evidence Controller or LLM Generation**.
2. **Withdrawal of the Synthetic Warm Generation Estimate:** The previously reported 2,840.5 ms generation latency and 1,842.3 ms / 1,635.8 ms total pipeline latencies were synthetic scaffolding estimates that did not correspond to measured execution logs. They are **formally withdrawn and replaced by empirical measurements**.
3. **Empirical Cold CPU Execution Baseline:** The raw records in [m10_phase_h_per_query_results.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_h_per_query_results.csv) accurately record local sequential execution on CPU:
   - **Retrieval Mean:** Config A $= 2,805.54\text{ ms}$; Config B $= 2,372.50\text{ ms}$ (Hindi Devanagari drops from $1,907.62\text{ ms}$ to **$175.46\text{ ms}$**, a **$90.8\%$ reduction**).
   - **Controller Mean:** $1.50\text{ ms}$ (Config A) / $1.25\text{ ms}$ (Config B).
   - **Generation Mean for Invoked Queries ($N=117 / 119$):** $89,995.25\text{ ms}$ (~90.0s) / $88,532.03\text{ ms}$ (~88.5s).
   - **Generation Mean Amortized across All Queries ($N=240$):** $43,872.76\text{ ms}$ / $43,897.19\text{ ms}$.
   - **Total Pipeline Latency:** Config A $= 46,694.32\text{ ms}$; Config B $= 46,270.94\text{ ms}$.
   - **Component Sum Balance:** In Config B, component sum ($2372.50 + 1.25 + 43897.19$) balances with measured total pipeline latency with **0.00 ms discrepancy**.

---

## 2. Latency Measurement Traceability Matrix

Every latency field reported across Milestone M10 artifacts is traced to its exact source and execution boundary below:

| # | Artifact & Column | Start Event | End Event | Model Loading? | Pipeline Stages Included | $N$ | Abstentions Included? | Errors Included? | Aggregation & Value |
|---|---|---|---|:---:|---|:---:|:---:|:---:|---|
| **1** | `m10_phase_e_results.csv`<br>`mean_reranker_lat_ms` | `t_rr0` before cross-encoder forward pass | `t_rr1` after cross-encoder logits | No (Preloaded) | Reranking only (MS-MARCO or mBERT) | 180 | Yes (All benchmark queries evaluated) | No | Mean: Config A $= 998.22\text{ ms}$; Config B $= 750.98\text{ ms}$ (Hindi $= 0.0\text{ ms}$) |
| **2** | `m10_phase_e_results.csv`<br>`mean_e2e_lat_ms` | `t_qp0` before query processing | `t_rr1` after reranker sorting | No (Preloaded) | Query Processing + Candidate Generation + Reranking | 180 | Yes | No | Mean: Config A $= \mathbf{1,097.10\text{ ms}}$; Config B $= \mathbf{849.87\text{ ms}}$ (p95: $1477.1\text{ ms} / 1337.5\text{ ms}$) |
| **3** | `m10_phase_h_per_query_results.csv`<br>`retrieval_latency_ms` | Entry into `retrieve()` | Return of `RetrievalResult` | No (Preloaded) | Preprocessing + BM25/FAISS + RRF + Reranker / Adaptive routing | 240 | Yes | Yes | Mean: Config A $= \mathbf{2,805.54\text{ ms}}$; Config B $= \mathbf{2,372.50\text{ ms}}$ (p50: $2191.6\text{ ms} / 2034.9\text{ ms}$) |
| **4** | `m10_phase_h_per_query_results.csv`<br>`controller_latency_ms` | Entry into `ctrl.evaluate()` | Return of `EvidenceDecision` | No (Preloaded) | CECI cross-encoder forward pass across top-5 passages | 240 | Yes | Yes | Mean: Config A $= 1.50\text{ ms}$; Config B $= 1.25\text{ ms}$ (p50: $1.50\text{ ms}$) |
| **5** | `m10_phase_h_per_query_results.csv`<br>`generation_latency_ms` | Entry into `generate_answer()` | Return of `AnswerResult` | No (Daemon resident) | Ollama HTTP call + Autoregressive CPU token generation + Verification | 240 | Recorded as 0.0 or 0.3 ms when skipped | Yes (`M9-Q123`, `Q124`) | Mean (Invoked, $N=117/119$): **89,995 ms / 88,532 ms**.<br>Mean (All-queries amortized, $N=240$): **43,873 ms / 43,897 ms** |
| **6** | `m10_phase_h_per_query_results.csv`<br>`total_latency_ms` | Loop entry for query | Loop completion & output serialization | No (Preloaded) | Full RAG pipeline: Retrieval + Controller + Generation + Serialization | 240 | Yes | Yes | Mean: Config A $= \mathbf{46,694.32\text{ ms}}$; Config B $= \mathbf{46,270.94\text{ ms}}$ (p50: $7053.8\text{ ms} / 7053.5\text{ ms}$) |
| **7** | `m10_phase_h_metrics.json`<br>`mean_total_latency_ms` | Synthetic calculation in scaffolding script | N/A | N/A | Formula: $1097.1 + 1.5 + (2840.5 \times \frac{63}{240})$ | N/A | N/A | N/A | **FORMALLY WITHDRAWN.** Replaced by grounded Regimes A and B. |

---

## 3. Investigation of the 1,097.1 ms and 849.9 ms Figures

The figures 1,097.1 ms and 849.9 ms originated in Phase E ([m10_phase_e_results.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_e_results.csv)). Forensic analysis of lines 191–199 of `scripts/evaluate_m10_phase_e.py` reveals the exact calculation:

```python
cfg_outputs = {
    "E1_PROD_MSMARCO_D10": (pids_e1, ms_lat_total_ms, qp_latency_ms + cand_latency_ms + ms_lat_total_ms),
    "E6b_ADAPTIVE_BI_ENCODER": (pids_e6b, rr_lat_e6b, qp_latency_ms + cand_latency_ms + rr_lat_e6b)
}
```

### Forensic Determination:
- `qp_latency_ms`: Query Processor script detection and normalization.
- `cand_latency_ms`: Hybrid BM25 and dense FAISS candidate pool generation.
- `ms_lat_total_ms` / `rr_lat_e6b`: Cross-encoder reranking over depth-10 candidate pool (or $0.0\text{ ms}$ for Hindi in Config B).
- **Scope Verification:** The measurement explicitly ended **before** the Evidence Controller was invoked, and **before** any LLM generation was performed.
- **Root Cause of Confusion:** The Phase E report named this column `mean_e2e_lat_ms` to distinguish it from `mean_reranker_lat_ms`. Downstream authors erroneously assumed `e2e` meant the entire RAG QA application pipeline, leading to the mislabeling.
- **Correction:** Formally classified as **Controlled Retrieval-Stage Latency**.

---

## 4. Reconciling Warm Benchmark Timing & Withdrawing Synthetic Estimates

In intermediate Phase H drafts, the following numbers were reported:
- Config A Retrieval: 1,097.1 ms
- Config B Retrieval: 849.9 ms
- Controller: ~1.5 ms
- Warm Generation: 2,840.5 ms
- Total Pipeline: 1,842.3 ms / 1,635.8 ms

### Forensic Audit of Inconsistency:
If total pipeline latency were the sum of individual query steps, $1097.1 + 1.5 + 2840.5 = 3939.1\text{ ms}$, which contradicts $1,842.3\text{ ms}$. 

Tracing `backend/experiments/m10/generate_phase_h_data.py` showed that the author attempted to compute an amortized expectation:
$$\text{Amortized Total} = \text{Retrieval} + \text{Controller} + \left(\text{Warm Generation} \times \frac{\text{Answers}}{\text{Total Queries}}\right)$$
$$1097.1 + 1.5 + \left(2840.5 \times \frac{63}{240}\right) = 1098.6 + 745.6 = 1844.2 \approx 1842.3\text{ ms}$$

### Audit Finding:
While mathematically explainable as an amortized expectation, the 2,840.5 ms figure was an unmeasured synthetic estimate of GPU inference speed, whereas the actual IndicRAG-QA benchmark was executed sequentially on local CPU via Ollama. 

**Action:** The 2,840.5 ms and 1,842.3 ms / 1,635.8 ms numbers are **formally withdrawn as unmeasured synthetic artifacts**. They are replaced by the two grounded empirical measurement regimes below.

---

## 5. Cold CPU End-to-End Execution Reconciliation (Phase F/H Records)

The actual raw records in `m10_phase_h_per_query_results.csv` ($N=240$ queries per config, $480$ total rows) reflect sequential local CPU execution. All components have been independently recalculated:

### 5.1 Comprehensive Latency Breakdown by Component & Language

```
========================================================================================================
                          CONFIG A: PRODUCTION (E1_PROD_MSMARCO_D10)
========================================================================================================
Stage / Language                Sample Size     Mean Latency        Median (p50)        95th Percentile (p95)
────────────────────────────────────────────────────────────────────────────────────────────────────────
1. Retrieval Latency             240 queries       2,805.54 ms        2,191.60 ms        5,834.43 ms
   — English (`en`)               60 queries       3,372.16 ms        2,376.80 ms        7,588.52 ms
   — Hindi Devanagari (`hi`)      60 queries       1,907.62 ms        1,657.30 ms        3,860.86 ms
   — Romanized Hindi (`hi-Latn`)  60 queries       3,030.80 ms        2,353.00 ms        7,530.63 ms
   — Hinglish (`en-hi`)           60 queries       2,911.58 ms        2,214.65 ms        5,326.87 ms

2. Evidence Controller Latency   240 queries           1.50 ms            1.50 ms            1.50 ms

3. Generation Latency
   — Invoked Queries             117 queries      89,995.25 ms       75,724.40 ms      134,013.60 ms
   — Skipped / Abstained         123 queries           0.30 ms            0.30 ms            0.30 ms
   — Population Amortized        240 queries      43,872.76 ms            0.30 ms      117,966.36 ms

4. Total Pipeline Latency        240 queries      46,694.32 ms        7,053.80 ms      121,230.72 ms
   — Sum of Component Means:                      46,679.80 ms (Discrepancy: +14.52 ms, 0.03% glue overhead)
========================================================================================================

========================================================================================================
                        CONFIG B: ADAPTIVE E6b (E6b_ADAPTIVE_BI_ENCODER)
========================================================================================================
Stage / Language                Sample Size     Mean Latency        Median (p50)        95th Percentile (p95)
────────────────────────────────────────────────────────────────────────────────────────────────────────
1. Retrieval Latency             240 queries       2,372.50 ms        2,034.95 ms        5,835.39 ms
   — English (`en`)               60 queries       3,372.16 ms        2,376.80 ms        7,588.52 ms
   — Hindi Devanagari (`hi`)      60 queries         175.46 ms           36.41 ms           58.11 ms  [▼ 90.8%]
   — Romanized Hindi (`hi-Latn`)  60 queries       3,030.80 ms        2,353.00 ms        7,530.63 ms
   — Hinglish (`en-hi`)           60 queries       2,911.58 ms        2,214.65 ms        5,326.87 ms

2. Evidence Controller Latency   240 queries           1.25 ms            1.50 ms            1.50 ms

3. Generation Latency
   — Invoked Queries             119 queries      88,532.03 ms       75,724.40 ms      133,493.75 ms
   — Skipped / Abstained         121 queries           0.30 ms            0.30 ms            0.30 ms
   — Population Amortized        240 queries      43,897.19 ms            0.30 ms      119,580.13 ms

4. Total Pipeline Latency        240 queries      46,270.94 ms        7,053.55 ms      121,850.94 ms
   — Sum of Component Means:                      46,270.94 ms (Discrepancy: 0.00 ms, exact match)
========================================================================================================
```

---

## 6. Resolution of Generation Denominator Ambiguity

The relationship between the reported ~90,000 ms invoked generation latency, ~0.3 ms abstention latency, and ~43,872 ms amortized generation latency is resolved as follows:

### 6.1 Generation Invocation Accounting

| Execution Status | Config A (Production) | Config B (Adaptive E6b) | Operational Pipeline Behavior |
|---|---:|---:|---|
| **Total Benchmark Queries** | **240** | **240** | Full frozen M9 evaluation dataset. |
| **Generation Invoked (LLM Called)** | **117** | **119** | Evidence Controller passed evidence as `SUFFICIENT` ($CECI \ge 0.35$). |
| — Produced Direct Answer / Disclosure | 61 | 62 | Factually grounded answer or structured regulatory disclosure. |
| — Concluded Unanswerable Post-Generation | 54 | 55 | LLM generated refusal or verifier caught missing citation / contradiction. |
| — Generation Error | 2 | 2 | Ollama HTTP/JSON timeout on queries `M9-Q123` and `M9-Q124`. |
| **Generation Skipped (Abstained by Controller)** | **123** | **121** | Evidence Controller immediately rejected evidence as `INSUFFICIENT` ($CECI < 0.35$). Instantaneous refusal issued. |

### 6.2 Mathematical Reconciliations
- **Mean Generation Time Among Invoked Queries:**
  - Config A: $\frac{\sum \text{Invoked Latency}}{117} = \mathbf{89,995.25\text{ ms}}$ (~90.0 seconds).
  - Config B: $\frac{\sum \text{Invoked Latency}}{119} = \mathbf{88,532.03\text{ ms}}$ (~88.5 seconds).
- **Mean Generation Time Across All 240 Queries (Amortized):**
  - Config A: $\frac{89,995.25 \times 117 + 0.30 \times 123}{240} = \mathbf{43,872.76\text{ ms}}$ (~43.9 seconds).
  - Config B: $\frac{88,532.03 \times 119 + 0.30 \times 121}{240} = \mathbf{43,897.19\text{ ms}}$ (~43.9 seconds).

**Key Takeaway:** The Evidence Controller functions as an effective compute saving gate, avoiding ~90 seconds of CPU generation on more than half the benchmark queries ($121/240$).

---

## 7. Answers to the Specific Forensic Questions

1. **Are latency measurements now correctly labeled?**  
   **Yes.** Measurements are formally partitioned into (A) Controlled Retrieval-Stage Latency (Phase E profiling: 1,097.1 ms vs 849.9 ms), and (B) Cold CPU End-to-End Latency (Phase F/H raw execution: 46,694 ms vs 46,271 ms).
2. **Are warm and cold measurements comparable?**  
   **No.** Warm measurements evaluate isolated retrieval and reranking on pre-loaded tensors; cold CPU measurements evaluate the full async RAG pipeline running local CPU autoregressive generation. They represent different architectural stages and must not be blended.
3. **Do end-to-end measurements reconcile with their components?**  
   **Yes.** In Config B, component sum ($2372.50 + 1.25 + 43897.19$) equals measured total pipeline latency ($46,270.94\text{ ms}$) with **0.00 ms discrepancy**. In Config A, the difference is negligible ($14.52\text{ ms}$, $0.03\%$).
4. **Must any timing claims be withdrawn?**  
   **Yes.** The claims that 1,097.1 ms and 849.9 ms represented full RAG pipeline latencies are formally withdrawn (they are retrieval-stage latencies), and the synthetic 2,840.5 ms warm generation estimate is formally retracted and replaced by the empirical CPU generation measurements.

---

## 8. Final Determination & Operational Sign-off

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           FINAL LATENCY FORENSIC DETERMINATION:                              ║
║           M10_PHASE_H_VERIFIED_WITH_LIMITATIONS                              ║
║                                                                              ║
║  1. All timing fields traced to raw files, start/end events, and stages.     ║
║  2. Synthetic warm estimates retracted; empirical CPU baselines established.║
║  3. Retrieval stage latency: Config A = 1,097.1 ms, Config B = 849.9 ms.     ║
║  4. Devanagari retrieval speedup verified: 90.8% reduction via bi-encoder.   ║
║  5. Production default remains "production" in engine.py.                    ║
║  6. Phase I production promotion review has NOT been initiated.              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
