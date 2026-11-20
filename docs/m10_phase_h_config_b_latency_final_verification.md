# M10 Phase H — Final Config B Latency Arithmetic Verification

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** H — Cross-Lingual End-to-End Answer Quality, Citation & Grounding Audit  
**Date:** November 18, 2026  
**Document Type:** Final Raw-Data Latency Arithmetic Verification (Config B)  
**Current Determination:** `M10_PHASE_H_VERIFIED_WITH_LIMITATIONS`  
**Production Runtime Default:** Verified invariant as `"production"` in [backend/app/retrieval/engine.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L395)  

---

## 1. Executive Summary & Audit Mandate

Following the reconciliation of query `M9-Q002`, this document provides the final, raw-data arithmetic verification of all latency aggregates for **Config B (`E6b_ADAPTIVE_BI_ENCODER`)**.

Every calculation in this report was computed directly from the 240 raw query records in [m10_phase_h_per_query_results.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_h_per_query_results.csv) using exact `Decimal` arithmetic.

### Summary of Audit Results:
1. **Invocation Counts Verified:** Exactly **119** queries invoked LLM generation, and **121** queries bypassed LLM generation ($119 + 121 = \mathbf{240}$).
2. **Bypassed Latency Distribution Verified:** Bypassed records do not assume zero or a constant; all 121 bypassed queries exhibit measured sub-millisecond execution times ranging from $0.05\text{ ms}$ to $0.30\text{ ms}$, with an exact raw sum of **$14.35\text{ ms}$**.
3. **M9-Q002 Treatment Verified:** `M9-Q002` recorded `generation_latency_ms = 0.10 ms` (instantaneous deterministic clarification template via `generator.py` line 324).
4. **Conditional Generation Mean Verified:** The conditional mean across the 119 actual LLM invocations is **$88,532.03\text{ ms}$** (~88.5 seconds).
5. **Population-Amortized Generation Mean Verified:** The population-amortized mean across all 240 benchmark queries is **$43,897.19\text{ ms}$** (~43.9 seconds).
6. **Total Pipeline Mean & Component Sum Verification:**
   $$\text{Retrieval Mean } (2,372.50\text{ ms}) + \text{Controller Mean } (1.25\text{ ms}) + \text{Amortized Generation Mean } (43,897.19\text{ ms}) = \mathbf{46,270.94\text{ ms}}$$
   This matches the raw measured Total Pipeline Mean (**$46,270.94\text{ ms}$**) with an exact residual of **$-0.00008333\text{ ms}$** ($-0.02\text{ ms}$ aggregate difference across 240 queries), attributable entirely to per-query rounding to two decimal places.
7. **Aggregate Invariance Confirmed:** **Zero displayed aggregate metrics change.** All figures reported in the Phase H final reconciliation are mathematically verified.

---

## 2. Granular Inspection of All 240 Config B Records

### 2.1 Distribution of Generation Latency Observations

Across all 240 records in `m10_phase_h_per_query_results.csv`:

| Latency Observation Range | Execution Description | Query Count | Percentage | Exact Raw Latency Sum |
|---|---|---:|---:|---:|
| **Zero ms (`0.00 ms`)** | Unrecorded / Missing | 0 | 0.00% | 0.00 ms |
| **Sub-1-ms (`0.05 ms` to `0.30 ms`)** | Bypassed by Evidence Controller (`INSUFFICIENT`) or Deterministic Clarification (`M9-Q002`) | 121 | 50.42% | 14.35 ms |
| **Actual LLM Invocations ($\ge 1.0\text{ ms}$)** | Autoregressive CPU Generation via Ollama (`qwen2.5:3b`) | 119 | 49.58% | 10,535,311.13 ms |
| **Total** | **All Config B Benchmark Records** | **240** | **100.00%** | **10,535,325.48 ms** |

### 2.2 Granular Frequency of the 121 Sub-1-ms Bypassed Latencies

Rather than assuming a constant, the 121 bypassed queries reflect actual measured event-loop return times:
- `0.10 ms`: 40 queries (including `M9-Q002`)
- `0.20 ms`: 29 queries
- `0.08 ms`: 15 queries
- `0.07 ms`: 14 queries
- `0.09 ms`: 13 queries
- `0.06 ms`: 5 queries
- `0.30 ms`: 2 queries
- `0.05 ms`: 1 query
- `0.14 ms`: 1 query
- `0.11 ms`: 1 query
- **Sum of Bypassed Observations:** $40(0.10) + 29(0.20) + 15(0.08) + \dots = \mathbf{14.35\text{ ms}}$.

---

## 3. Exact Raw Arithmetic Verification

All sums and means were computed in Python using arbitrary-precision `decimal.Decimal`:

### 3.1 Exact Raw Sums

| Metric Field | Raw Column Name in CSV | Sum Across 240 Records (Decimal) | Exact Denominator | Raw Arithmetic Mean | Displayed (Rounded) |
|---|---|---:|:---:|---:|---:|
| **Retrieval Latency** | `retrieval_latency_ms` | 569,399.95 ms | 240 | 2,372.49979166... ms | **2,372.50 ms** |
| **Controller Latency** | `controller_latency_ms` | 299.37 ms | 240 | 1.24737500... ms | **1.25 ms** |
| **Invoked Generation** | `generation_latency_ms` | 10,535,311.13 ms | 119 | 88,532.02630252... ms | **88,532.03 ms** |
| **Amortized Generation** | `generation_latency_ms` | 10,535,325.48 ms | 240 | 43,897.18950000... ms | **43,897.19 ms** |
| **Total Pipeline Latency** | `total_latency_ms` | 11,105,024.78 ms | 240 | 46,270.93658333... ms | **46,270.94 ms** |

---

## 4. Component Summation & Residual Analysis

### 4.1 Component Raw Sums vs. Recorded Total Pipeline Sum
- **Component Raw Sums Across All 240 Records:**
  - Retrieval Sum: `569,399.95 ms`
  - Controller Sum: `299.37 ms`
  - Generation Sum: `10,535,325.48 ms`
  - **Component Sum:** `11,105,024.80 ms`
- **Recorded Total Pipeline Sum Across All 240 Records:**
  - **Recorded Total Sum:** `11,105,024.78 ms`
- **Aggregate Discrepancy Across Population:**
  $$11,105,024.78\text{ ms} - 11,105,024.80\text{ ms} = \mathbf{-0.02\text{ ms}}$$

### 4.2 Mean Balance Equation & Residual
$$\text{Sum of Means} = \text{Mean}_{\text{Retrieval}} + \text{Mean}_{\text{Controller}} + \text{Mean}_{\text{Generation (Amortized)}}$$
$$\text{Sum of Means} = 2,372.49979167 + 1.24737500 + 43,897.18950000 = \mathbf{46,270.93666667\text{ ms}}$$
$$\text{Measured Total Mean} = \frac{11,105,024.78\text{ ms}}{240} = \mathbf{46,270.93658333\text{ ms}}$$
$$\text{Mean Residual} = \frac{-0.02\text{ ms}}{240} = \mathbf{-0.0000833333\text{ ms}}$$

### 4.3 Residual Explanation: Per-Query Rounding to Two Decimal Places
- In the evaluation harness (`scripts/run_m10_phase_f_full_eval.py` line 184 and line 206), each query's total latency was recorded as:
  ```python
  tot_lat_ms = ret_lat_ms + ctrl_lat_ms + gen_lat_ms
  e2e_records.append({
      ...
      "total_latency_ms": round(tot_lat_ms, 2),
      ...
  })
  ```
- Because individual component latencies were already formatted and total latency was rounded to two decimal places (`round(..., 2)`), minor round-off differences accumulated across the 240 queries, yielding an aggregate $-0.02\text{ ms}$ difference ($-0.00008333\text{ ms}$ per query).
- **The residual is an artifact of per-query rounding to two decimal places**, not pure IEEE 754 precision, and **not evidence of meaningful unattributed pipeline overhead**. The measured total pipeline mean ($46,270.94\text{ ms}$) balances with the component sum to two decimal places.

---

## 5. Historical Value Preservation & Verification

| Displayed Metric | Value in Previous Phase H Drafts | Re-Verified Raw Arithmetic Value | Status |
|---|---:|---:|:---:|
| **Config B Retrieval Mean** | 2,372.50 ms | 2,372.50 ms | **Invariant (Verified)** |
| — Hindi Devanagari Retrieval Mean | 175.46 ms | 175.46 ms | **Invariant (Verified)** |
| **Config B Controller Mean** | 1.25 ms | 1.25 ms | **Invariant (Verified)** |
| **Conditional Generation Mean ($N=119$)** | 88,532.03 ms | 88,532.03 ms | **Invariant (Verified)** |
| **Amortized Generation Mean ($N=240$)** | 43,897.19 ms | 43,897.19 ms | **Invariant (Verified)** |
| **Total Pipeline Latency Mean** | 46,270.94 ms | 46,270.94 ms | **Invariant (Verified)** |
| **Total Disclosed Outputs** | 63 | 63 | **Invariant (Verified)** |
| **Total Final Abstentions** | 175 | 175 | **Invariant (Verified)** |
| **Execution Errors** | 2 | 2 | **Invariant (Verified)** |

**Finding:** No displayed aggregates change. The previous reconciliation correctly accounted for `M9-Q002`'s $0.10\text{ ms}$ observation.

---

## 6. Final Determination & Operational Sign-off

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           FINAL LATENCY ARITHMETIC DETERMINATION:                            ║
║           M10_PHASE_H_VERIFIED_WITH_LIMITATIONS                              ║
║                                                                              ║
║  1. All 240 Config B records inspected and verified directly from raw CSV.   ║
║  2. Exact sums: Retrieval=569,400ms, Controller=299ms, Generation=10,535,325ms║
║  3. Exact component balance: 2,372.50 + 1.25 + 43,897.19 = 46,270.94 ms.    ║
║  4. Residual is -83 nanoseconds (pure IEEE 754 floating point precision).    ║
║  5. Zero displayed aggregates require alteration.                            ║
║  6. Production default verified invariant as "production" in engine.py.      ║
║  7. Phase I production promotion review has NOT been initiated.              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
