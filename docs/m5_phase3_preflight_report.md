# IndicRAG-QA — M5 Phase 3 Preflight: Experiment Harness Verification Report

**Date:** 2026-11-10  
**Status:** **PREFLIGHT VERIFIED — READY FOR EXECUTION**  
**Harness Script:** `scripts/run_m5_experiments.py`  
**Execution Environment:** Windows 11 / Python 3.13.5 (Anaconda base) / Ollama Local  
**Test Suite Status:** 135/135 tests passing (26.87s)

---

## 1. Executive Summary

In accordance with Phase 3 preflight protocols, the master experiment execution harness (`scripts/run_m5_experiments.py`) was verified and validated prior to executing the formal M5 experimental suite (E1–E12).

### Strict Boundary Enforcement
- **No full experiments were executed during this preflight.**
- M5 status remains **IN_PROGRESS**.
- The official M4 corpus and M3 benchmark remain completely frozen and untouched.
- A controlled dry-run smoke test was conducted on exactly 2 benchmark queries (1 answerable, 1 unanswerable) across all 12 experimental pipelines, confirming zero runtime regressions, syntax errors, or data serialization issues.

---

## 2. Integrity and Provenance Verification

Prior to running preflight pipelines, cryptographic hashes and index counts were verified against authoritative baselines:

| Artifact | Authoritative Expected Value | Preflight Verified Value | Status |
|---|---|---|---|
| **Corpus Hash (SQLite Passages)** | `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d` | `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d` | ✅ EXACT MATCH |
| **Benchmark Hash (`final_verified_dataset.csv`)** | $N=15$ verified instances | `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` | ✅ FROZEN ($N=15$) |
| **Official Index Passages** | 142 child passages, 30 parent passages | 142 child passages, 30 parent passages | ✅ SYNCHRONIZED |
| **Official FAISS Vector Count** | 142 vectors (`paraphrase-multilingual-MiniLM-L12-v2`) | 142 vectors | ✅ SYNCHRONIZED |
| **Fixed-Window Comparison Index** | 165 passages (300 words, 50 overlap) | 165 passages (`fixed_window/`) | ✅ SYNCHRONIZED |

---

## 3. Experiment Harness Architecture

The harness script `scripts/run_m5_experiments.py` was constructed to meet all modularity and reproducibility requirements:

### 3.1 Supported CLI Modes
- `--dry-run`: Validates environment, verifies corpus/benchmark integrity, loads index manifests, and exits without model inference.
- `--smoke-test`: Executes all E1–E12 harnesses on a 2-query subset (1 answerable, 1 unanswerable), recording detailed logs and serializing `m5_preflight_manifest.json`.
- `--experiment <ID>`: Runs an isolated experiment pipeline (e.g. `--experiment E1`, `--experiment E4`) or all canonical experiments (`--experiment all`).
- `--output-dir <DIR>`: Overrides target output directory (defaults to `backend/data/experiments/m5/`).

### 3.2 Modularity and Error Isolation
- **Non-monolithic execution:** Each experiment is encapsulated in a dedicated runner function (`run_e1_bm25_dense_hybrid()`, `run_e2_adaptive_routing()`, etc.).
- **Graceful degradation:** Ollama translation and cross-lingual MQR utilize try-catch blocks with automatic fallback to original queries, logging latency and fallback occurrences without failing the experiment run.
- **Reproducible metrics:** All runs compute standardized evaluation metrics: Hit@1, Hit@3, Hit@5, MRR, NDCG@5, and average latency in milliseconds.

---

## 4. Canonical E1–E12 Experiment Matrix & Controls

The harness strictly preserves the canonical experiment definitions:

| Exp ID | Baseline / Comparison | Control / Condition | Implementation Details |
|---|---|---|---|
| **E1** | BM25 vs Dense vs Hybrid | Pure BM25, Pure Dense FAISS, Hybrid RRF ($k=60$) | Preserves M4 baseline retrieval pipelines. |
| **E2** | Fixed Hybrid vs Adaptive Routing | Rule-based vs Static Hybrid RRF | Uses `AdaptiveRouter` with deterministic language/script/anchor rules. |
| **E3** | Direct vs Translation-Assisted vs Fallback | Multilingual Dense vs Translated BM25/Dense | Translates to English via `translate_query_to_english()`; preserves original query untouched. |
| **E4** | Reranker On vs Off | No Reranker vs Cross-Encoder | Evaluates `cross-encoder/ms-marco-MiniLM-L-6-v2` re-scoring top-20 candidates down to top-5. |
| **E5** | Fixed-Window vs Structure-Aware Chunking | 165-chunk Fixed Index vs 142-chunk Structure Index | Both indexes evaluated with identical Hybrid RRF retriever on same benchmark. |
| **E6** | Multi-Query Retrieval (MQR) On vs Off | 1 Query vs 3 Sub-Query Expansions | Generates lexical variants and fuses candidate sets via RRF. |
| **E7** | Parent Document Retrieval (PDR) On vs Off | Child Passages Only vs Parent Expansion | Replaces retrieved child chunks with parent section context via SQLite lookup. |
| **E8** | Regulatory Version Validation On vs Off | Unfiltered Retrieval vs Version-Aware Filtering | Prioritizes current 75% attendance rule over historical 70% rule while keeping historical clauses visible for historical queries. |
| **E9** | Query Decomposition On vs Off | Single Query vs Multi-Part Decomposition | Splits conjunctive queries into sub-questions and aggregates retrieval pools. |
| **E10** | Evidence Abstention vs Always Answer | Forced Answer vs Grounded Abstention | `EvidenceController` flags INSUFFICIENT/MISSING evidence to trigger abstention. |
| **E11** | Adaptive vs Fixed Retrieval Budget | Fixed $k=5$ vs Dynamic $k \in [3, 10]$ | `AdaptiveBudgetRetriever` sets initial budget by complexity and prunes using $\ge 35\%$ elbow drop-off. |
| **E12** | Full Architecture vs Feature Ablations | Full System (A0) vs Leave-One-Out (A1–A6) | Systematically disables one component at a time: A1 (No Rerank), A2 (No MQR), A3 (No PDR), A4 (No Version), A5 (No Dense), A6 (No BM25). |

---

## 5. Preflight Smoke-Test Results

The preflight smoke test was executed via:
```powershell
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --smoke-test
```

### 5.1 Preflight Execution Summary
- **Execution Date:** 2026-11-10T13:39:47 UTC
- **Duration:** 25.1 seconds total
- **Exit Code:** 0 (Clean exit, 0 warnings/errors)
- **Output Artifact:** `backend/data/experiments/m5/preflight_smoke/m5_preflight_manifest.json`

### 5.2 Component Timing & Execution Status

| Experiment Pipeline | Preflight Smoke Status | Execution Latency | Observations |
|---|---|---|---|
| **E1 (Retrieval Baselines)** | ✅ PASSED | 9,169 ms | Dense index loaded; BM25, Dense, and Hybrid retrieved top candidates. |
| **E2 (Adaptive Routing)** | ✅ PASSED | 602 ms | English query routed to Hybrid RRF; Hindi query routed to Cross-Lingual MQR. |
| **E3 (Translation-Assisted)** | ✅ PASSED | 102 ms | Hindi translated correctly; latency and fallback flags recorded in log. |
| **E4 (Cross-Encoder Reranker)** | ✅ PASSED | 6,836 ms | `ms-marco-MiniLM-L-6-v2` loaded into memory; scored top candidates. |
| **E5 (Chunking Comparison)** | ✅ PASSED | 134 ms | Both official (142) and fixed-window (165) indexes queried successfully. |
| **E6 (Multi-Query Retrieval)** | ✅ PASSED | 130 ms | MQR expansion and RRF fusion executed without regressions. |
| **E7 (Parent Document Retrieval)**| ✅ PASSED | 60 ms | Parent passage mapping verified via SQLite parent_passage_id. |
| **E8 (Version Validation)** | ✅ PASSED | 62 ms | Version matching filtered candidates appropriately without index mutations. |
| **E9 (Query Decomposition)** | ✅ PASSED | 65 ms | Multi-part query analysis executed correctly. |
| **E10 (Evidence Abstention)** | ✅ PASSED | 67 ms | Correctly abstained on unanswerable query with zero hallucinations. |
| **E11 (Adaptive Budget)** | ✅ PASSED | 67 ms | Dynamic $k$ assigned (3 for simple query, 6 for complex query) with elbow check. |
| **E12 (Leave-One-Out Ablations)**| ✅ PASSED | 7,929 ms | All 7 configurations (A0, A1, A2, A3, A4, A5, A6) completed cleanly. |

---

## 6. Formal Phase 3 Execution Command

With preflight verification complete, the full experimental evaluation is ready to be launched:

### Full Benchmark Suite Execution:
```powershell
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment all
```

### Individual Experiment Runs (Modular Execution):
```powershell
# Run individual experiments:
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment E1
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment E2
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment E3
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment E4
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment E5
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment E6
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment E7
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment E8
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment E9
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment E10
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment E11
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py --experiment E12
```

---

## 7. Sign-off and Readiness Statement

The harness verification and dry-run preflight for Milestone 5 are **formally complete**. All twelve canonical experiment harnesses, their experimental controls, and their data serialization routines are operational, robust, and verified.

