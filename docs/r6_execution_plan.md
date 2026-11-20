# IndicRAG-QA — R6 Staged Execution Plan

**Document Version:** 1.0  
**Phase:** R6 — Integrated Evaluation & Regression  
**Task:** Task 1 — Existing Benchmark Audit, Evaluation Design & Test Readiness  
**Date:** 2026-11-19  
**Status:** PLAN APPROVED (READY FOR EXECUTION)  

---

## 1. Executive Summary

This document specifies the staged, gate-controlled execution plan for Phase R6: Integrated Evaluation & Regression. 

The evaluation encompasses all 8 core architectural dimensions of IndicRAG-QA across 12 sequential stages. To maintain benchmark integrity, every stage operates under strict constraints:
- **Zero API Cost:** Uses local CPU embedding models and local Ollama inference (`qwen2.5:7b-instruct` / `llama3.1:8b`).
- **Prerequisite Gating:** High-cost end-to-end generation stages are only triggered after upstream retrieval, reasoning, and security smoke tests pass.
- **Strict Baseline Preservation:** Historical benchmark files (M3, M6, M9, M10) remain frozen and read-only.
- **Versioned Outputs:** All R6 outputs are saved to dedicated `docs/r6_*.md` and `backend/data/experiments/r6/` paths.

---

## 2. 12-Stage Staged Execution Workflow

```
[Stage 1: Dataset Integrity Audit]
                │
                ▼
[Stage 2: Integrated Smoke Test] ──(Gate: 100% Pass)
                │
                ▼
[Stage 3: Functional Regression (R1-R5)] ──(Gate: 100% Pass)
                │
                ▼
[Stage 4: Retrieval Benchmark (M4/M8/M10)]
                │
                ▼
[Stage 5: Multi-Hop Reasoning (R4/R4.1.1)] ──(Gate: Depth <= 3, |P| <= 12)
                │
                ▼
[Stage 6: Answer & Citation Grounding]
                │
                ▼
[Stage 7: Multilingual Parity (M9 N=240, 60 Intents)]
                │
                ▼
[Stage 8: Abstention & Uncertainty (M6 Negative N=33)]
                │
                ▼
[Stage 9: Conversational Feedback Repair (R5 Subtypes)]
                │
                ▼
[Stage 10: Multi-Tenant Security & Isolation]
                │
                ▼
[Stage 11: Statistical Latency & Resource Profile]
                │
                ▼
[Stage 12: Final Consolidated Synthesis & Audit Report]
```

---

## 3. Detailed Stage Specifications

### Stage 1: Dataset Integrity & Cryptographic Audit
- **Objective:** Verify that all historical benchmark files and database files match their recorded SHA-256 hashes before running evaluations.
- **Inputs:** `docs/r6_dataset_integrity_manifest.json`, `backend/data/dataset/`, `backend/data/experiments/m10/`.
- **Harness:** `scripts/audit_existing_benchmarks.py`.
- **LLM Generation Required:** No (Filesystem & cryptographic hash check).
- **Estimated Runtime:** ~5 seconds.
- **Gating Criterion:** 100% match of frozen benchmark hashes. If any hash fails, halt immediately.

### Stage 2: Integrated End-to-End Smoke Test
- **Objective:** Verify basic pipeline health across query processing, hybrid retrieval, graph traversal, and local Ollama connectivity.
- **Inputs:** 3 representative queries (1 English calendar, 1 Hindi direct, 1 attendance scope).
- **Harness:** `scripts/run_e2e_smoke_tests.py`.
- **LLM Generation Required:** Yes (3 calls).
- **Estimated Runtime:** ~45 seconds on CPU.
- **Gating Criterion:** 3/3 queries return status `ANSWERED` with non-empty text and valid citations.

### Stage 3: Functional Regression Suite (Milestones R1–R5)
- **Objective:** Ensure no regression occurred across foundational subsystems:
  - R1: Table cell reconstruction (21,840 cells intact).
  - R2/R2.1: Relationship database (7,714 records intact).
  - R3: Single-hop relationship-aware retrieval.
  - R4: Multi-hop reasoning engine instantiation.
  - R5: Conversational feedback store and repair routing.
- **Inputs:** SQLite database `indicrag.db`, table index metadata.
- **Harness:** `scripts/test_r1_extraction_and_regression.py`, `scripts/test_r2_1_full_verification_suite.py`, `scripts/test_r3_comprehensive.py`.
- **LLM Generation Required:** No.
- **Estimated Runtime:** ~60 seconds.
- **Gating Criterion:** Zero regressions across R1, R2, R3, R5 test assertions.

### Stage 4: Retrieval Baseline Evaluation (M4, M8, M10)
- **Objective:** Benchmark lexical, dense, hybrid, and reranked retrieval without multi-hop expansion against historical M4/M8/M10 baselines.
- **Inputs:** M6 Expanded Benchmark ($N=60$), M3 Benchmark ($N=15$).
- **Metrics:** Hit@1, Hit@3, Hit@5, MRR, nDCG@5.
- **Harness:** `scripts/evaluate_m10_controlled_baselines.py`.
- **LLM Generation Required:** No (Retrieval and scoring only).
- **Estimated Runtime:** ~3 minutes on CPU.
- **Gating Criterion:** Hit@5 $\ge$ 0.90 on M6 answerable subset; M10 production reranker verified active.

### Stage 5: Multi-Hop Reasoning Benchmark (R4 / R4.1 / R4.1.1)
- **Objective:** Evaluate bounded multi-hop reasoning over the 14 comprehensive scenario checks.
- **Inputs:** `scripts/test_r4_comprehensive.py`.
- **Metrics:** Traversal depth ($d \le 3$), evidence boundary ($|P| \le 12$), cycle pruning (0 duplicates), scope preservation, medical prerequisite chaining.
- **Harness:** `scripts/test_r4_comprehensive.py`.
- **LLM Generation Required:** No.
- **Estimated Runtime:** ~2 minutes on CPU.
- **Gating Criterion:** 14/14 tests pass; strict verification of $|P| \le 12$ and $d \le 3$.

### Stage 6: Answer Quality & Claim Grounding Evaluation
- **Objective:** Measure factual accuracy, atomic claim entailment, unsupported claim rate, and citation page validity on generated responses.
- **Inputs:** M6 Answerable subset ($N=40$).
- **Metrics:** Claim Grounding Ratio ($\text{CGR} \ge 0.85$), Unsupported Claim Rate ($\text{UCR} \le 0.15$), Contradiction Rate ($\text{CR} = 0.0\%$), Citation Page Accuracy ($100\%$).
- **Harness:** `scripts/run_m10_phase_f_full_eval.py`.
- **LLM Generation Required:** Yes ($N=40$ calls).
- **Estimated Runtime:** ~15–20 minutes on CPU.
- **Gating Criterion:** Zero ungrounded hallucinations; 100% cited pages match physical document pages.

### Stage 7: Multilingual Evaluation (M9 $N=240$, 60 Intents)
- **Objective:** Evaluate cross-lingual consistency and parity across English, Devanagari Hindi, Romanized Hindi, and Hinglish.
- **Inputs:** `backend/data/experiments/m9/m9_evaluation_dataset.jsonl` ($N=240$).
- **Grouping Rule:** Grouped analysis across the 60 distinct semantic intents.
- **Metrics:** Language identification accuracy, per-language Hit@5 and MRR, cross-lingual answer consistency.
- **Harness:** `scripts/evaluate_m9_retrieval.py`, `scripts/evaluate_m9_generation.py`.
- **LLM Generation Required:** Yes ($N=240$ calls; can be batched or sampled by intent).
- **Estimated Runtime:** ~45–60 minutes on CPU.
- **Gating Criterion:** Intent-level consistency tracked across all 4 linguistic varieties.

### Stage 8: Abstention, Uncertainty & Clarification Evaluation
- **Objective:** Evaluate system behavior on out-of-domain queries, non-existent policies, ambiguous cohort rules, and contradictory premises.
- **Inputs:** M6 Phase 3 Negative Benchmark ($N=33$), adversarial helicopter/parking queries, unanchored attendance queries.
- **Metrics:** Abstention Precision ($\ge 95\%$), False Abstention Rate ($\le 10\%$), Cohort Clarification Rate ($100\%$ on unanchored dual-ordinance questions).
- **Harness:** `scripts/run_m6_phase3_eval.py`.
- **LLM Generation Required:** Yes (Abstention decision verification).
- **Estimated Runtime:** ~5 minutes on CPU.
- **Gating Criterion:** Complete abstention on non-existent university policies; zero hallucinated rules.

### Stage 9: Conversational Feedback & Answer Repair Evaluation
- **Objective:** Evaluate multi-turn answer repair across all 8 feedback subtypes without loss of prior context.
- **Inputs:** Preceding Q&A turn pairs followed by feedback challenges.
- **Subtypes:** General disagreement, factual correction, missing exception, wrong cohort, source challenge, citation challenge, clarification request, re-explanation.
- **Harness:** `scripts/test_r5_conversational_repair.py`.
- **LLM Generation Required:** Yes ($8 \times 2 = 16$ turns).
- **Estimated Runtime:** ~4 minutes on CPU.
- **Gating Criterion:** 8/8 feedback subtypes successfully processed with evidence-backed repair.

### Stage 10: Multi-Tenant Security & Isolation Audit
- **Objective:** Verify cross-tenant isolation during hybrid retrieval, relationship traversal, and conversational repair.
- **Inputs:** Synthetic tenant test documents (Tenant A vs Tenant B vs Anonymous).
- **Metrics:** Leakage Rate = 0.0%, User own upload access = 100%, Anonymous access to user uploads = 0%.
- **Harness:** `scripts/test_tenant_isolation_sql.py` and Test 9 of `scripts/test_r4_comprehensive.py`.
- **LLM Generation Required:** No.
- **Estimated Runtime:** ~30 seconds.
- **Gating Criterion:** Zero leaked foreign passages across all tenant queries.

### Stage 11: Statistical Latency & Resource Profiling
- **Objective:** Establish formal multi-sample latency distributions on CPU and measure memory utilization.
- **Inputs:** Representative query workload ($N=10$ warm runs + 1 cold start run).
- **Metrics:** Mean, Std Dev, Min, Median (p50), Max for Hybrid Retrieval, Graph BFS Reasoning, and Total Pipeline.
- **Harness:** `scripts/benchmark_r4_performance.py`.
- **LLM Generation Required:** No.
- **Estimated Runtime:** ~1.5 minutes on CPU.
- **Gating Criterion:** Separation of cold start from warm runs; reasoning overhead verified $\le 3\%$.

### Stage 12: Final Consolidated Synthesis & Milestone Audit
- **Objective:** Aggregate all findings, metrics tables, failure case mappings, and statistical distributions into the final R6 milestone deliverable.
- **Deliverable:** `docs/r6_final_integrated_evaluation_report.md`.
- **Gating Criterion:** All 11 upstream stages completed, audited, and synthesized.

---

## 4. Resource, Runtime & Cost Budget

| Resource Category | Constraint | Status |
| :--- | :--- | :---: |
| **API Costs** | \$0.00 (Zero paid API calls; all local inference) | Verified |
| **Compute Hardware** | Local Windows CPU (AMD/Intel multi-core), 16GB+ RAM | Verified |
| **LLM Infrastructure** | Ollama local daemon (`qwen2.5:7b-instruct` / `llama3.1:8b`) | Active |
| **Total Estimated Runtime** | ~90 to 120 minutes for complete 12-stage execution | Feasible |
| **External Dependencies** | None (No Docker, no cloud services, no remote DB) | Verified |

---

## 5. Next Steps for Task 2 (Full Execution)

Upon user review and sign-off of this design and inventory, the exact command to initiate Stage 1 and Stage 2 execution is:

```powershell
& "C:\Users\anish\anaconda3\python.exe" scripts/audit_existing_benchmarks.py
```
followed by the integrated evaluation suite execution.
