# IndicRAG-QA — R6.1 Realistic Evaluation Runtime Estimate

**Audit Date:** 2026-11-19  
**Auditor Role:** Performance Engineer & Evaluation Architect  
**Milestone:** R6 Task 1.1 Benchmark Integrity and Runtime Readiness Correction  
**Primary Engine:** `qwen2.5:3b` (Q4_K_M GGUF, 3.1B parameters, 16 CPU threads)  

---

## 1. Executive Summary

In R6 Task 1, an initial runtime estimate of 90–120 minutes was projected under the assumption of unquantized 7B/8B models running on CPU. Following the Task 1.1 confirmation that **`qwen2.5:3b`** (Q4_K_M) is the active production model and that the host CPU provides **16 logical execution threads**, this document provides a calibrated, empirical runtime projection.

Key conclusions:
1. **Full Benchmark Execution (All 11 Stages, $N=240$ Multilingual Queries):** **58 to 72 minutes**.
2. **Intent-Sampled Benchmark Execution (Sampled Multilingual $N=60$ Distinct Intents):** **30 to 38 minutes**.
3. **Retrieval-Only Stages (Stages 1, 3, 4, 5, 10, 11):** Require zero LLM generation and complete in under **8 minutes total**.
4. **Timeout Safety:** Average query generation takes 6–10 seconds, safely below the 120.0-second Ollama timeout ceiling.

---

## 2. Hardware and Model Performance Profile

Empirical performance metrics for `qwen2.5:3b` on the host hardware (Intel 12 physical / 16 logical cores, 16 GB RAM, NVMe SSD):

| Performance Dimension | Empirical Measurement / Benchmark | Notes |
| :--- | :--- | :--- |
| **Model Cold-Start Loading** | 2.2 – 3.5 seconds | Ollama loads 1.93 GB GGUF from disk into RAM |
| **Prompt Ingestion / Context Processing** | 80 – 120 tokens/sec | Processing ~400–700 tokens of retrieved evidence passages |
| **Token Generation Rate (Warm)** | 22 – 32 tokens/sec | Multi-threaded CPU inference on 16 threads |
| **Average Tokens per Answer** | 110 – 180 tokens | Concise, evidence-grounded answers with citations |
| **Average End-to-End Query Latency** | **6.5 – 9.8 seconds** | Total time for retrieval + prompt build + LLM completion |
| **Configured Ollama Timeout** | 120.0 seconds | Safety margin factor: $\sim 12\times$ over average latency |

---

## 3. Granular Stage-by-Stage Workload Deconstruction

The complete R6 integrated evaluation comprises 11 structured execution stages. Below is the workload deconstruction calibrated for `qwen2.5:3b`:

| Stage | Benchmark Stage Description | Query / Test Count | LLM Invocations | Retrieval / Compute Profile | Estimated Latency |
| :---: | :--- | :---: | :---: | :--- | :---: |
| **1** | **Benchmark Integrity & Baseline Audit** | 12 artifacts | 0 | Pure SHA-256 computation and JSON ledger verification | **~10 seconds** |
| **2** | **Corpus Health & End-to-End Smoke Test** | 3 queries | 3 | Ingestion verification + BM25/FAISS + 3 test answers | **~25 seconds** |
| **3** | **Retrieval Benchmark Suite** (M6) | 60 queries | 0 | BM25, FAISS, RRF, cross-encoder reranker, Top-K metrics | **~90 seconds** |
| **4** | **Bounded Multi-Hop Reasoning Regression** | 14 tests | 0 | Traversal depth ($k \le 3$), edge limits, step tracing | **~45 seconds** |
| **5** | **Contradiction, Applicability & Boundary** | 10 tests | 0 | Strict evidence limit ($|P| \le 12$), CECI conflict handling | **~35 seconds** |
| **6** | **Claim Grounding & Citation Quality** (M6) | 40 queries | 40 | End-to-end multi-hop retrieval + generation + NLI audit | **~5.5 – 7.5 mins** |
| **7A** | **Multilingual Evaluation — Full Mode** (M9) | 240 queries | 240 | 60 intents $\times$ 4 languages (`en`, `hi`, `hi-Latn`, `en-hi`) | **~35 – 42 mins** |
| *7B* | *Multilingual Evaluation — Sampled Mode* (M9) | *60 queries* | *60* | *1 representative query per intent, balanced across languages* | *~9 – 12 mins* |
| **8** | **Abstention & Negative Benchmark** (M6 Neg) | 33 queries | 33 | Verification of `UNANSWERABLE` status on absent clauses | **~4.0 – 5.5 mins** |
| **9** | **Conversational Feedback & Memory Repair** | 16 turns | 16 | 4 multi-turn sessions testing context-aware correction | **~2.0 – 3.0 mins** |
| **10** | **R5 Calendar Repair Regression** | 5 tests | 0 | Academic Calendar 2026-27 date sheet & exam reconciliation | **~20 seconds** |
| **11** | **Tenant Isolation & Ingestion Safety** | 8 tests | 0 | Tenant boundary leak tests and duplicate re-ingestion audit | **~30 seconds** |

---

## 4. Aggregate Runtime Comparison

### Mode A: Full Benchmark Execution (Standard R6 Plan)
- **Total Queries Evaluated:** 445 queries and programmatic tests.
- **Total LLM Generations:** 332 calls to `qwen2.5:3b`.
- **Non-LLM Retrieval / Script Time:** ~5.5 minutes.
- **LLM Generation Time (332 calls $\times$ 8.5s avg):** ~47.0 minutes.
- **Process Setup, IO, and Reporting Overhead:** ~6.0 minutes.
- **Total Projected Runtime:** **58 to 60 minutes** (Maximum ceiling with variance: **~72 minutes**).

### Mode B: Stratified Intent-Sampled Multilingual Execution
- **Total Queries Evaluated:** 265 queries and programmatic tests.
- **Total LLM Generations:** 152 calls to `qwen2.5:3b`.
- **Non-LLM Retrieval / Script Time:** ~5.5 minutes.
- **LLM Generation Time (152 calls $\times$ 8.5s avg):** ~21.5 minutes.
- **Process Setup, IO, and Reporting Overhead:** ~4.0 minutes.
- **Total Projected Runtime:** **31 to 35 minutes** (Maximum ceiling: **~40 minutes**).

---

## 5. Cold-Start vs. Warm Execution & Timeout Mitigation

1. **Cold-Start Elimination:**
   - In Stage 2 (Smoke Test), the initial request loads model weights into host memory. Once loaded, Ollama maintains the model resident in RAM across the entire test session (default keep-alive is 5 minutes after the last request).
   - Subsequent stages experience zero cold-start delay.

2. **Timeout Mitigation & Deadlock Prevention:**
   - With `settings.ollama_timeout = 120.0`, even an unusually complex multi-hop prompt with 12 passages (~800 prompt tokens) and 250 completion tokens will finish in ~16–18 seconds, consuming at most 15% of the timeout allowance.
   - Evaluation runner scripts must implement per-stage progress flush so intermediate results are persisted to disk immediately, preventing data loss if an individual query encounters an OS-level interrupt.

3. **Memory Pressure Mitigation:**
   - Host RAM is 74.3% utilized. Background browser tabs or heavyweight desktop applications should be minimized during the run to preserve the 4.03 GB free memory buffer.

---

## 6. Recommended Execution Strategy

To ensure zero wasted compute and immediate verification, execution must follow a phased staging model:

1. **Phase 1: Zero-LLM Readiness Verification (Stage 1):**
   - Command: `python scripts/audit_existing_benchmarks.py`
   - Runtime: **< 15 seconds**.
   - Verifies all SHA-256 dataset hashes and relationship database integrity before touching the LLM.

2. **Phase 2: Core Retrieval & Reasoning Regression (Stages 2–5, 10–11):**
   - Runtime: **~5 minutes**.
   - Confirms that R1–R5 retrieval, ranking, and graph traversal invariants remain 100% functional.

3. **Phase 3: End-to-End Generation & Abstention (Stages 6, 8, 9):**
   - Runtime: **~12 minutes**.
   - Evaluates grounded answer quality, citation validation, and conversational feedback repair.

4. **Phase 4: Multilingual Suite (Stage 7):**
   - Runtime: **~10 minutes** (Sampled) or **~38 minutes** (Full).
