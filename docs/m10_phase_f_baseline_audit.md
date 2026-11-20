# Milestone M10 Phase F — Baseline Answer & Infrastructure Audit

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** F — End-to-End Answer Recovery & Generation Grounding Audit  
**Artifact:** Baseline Answer & Generation Infrastructure Audit  
**Date:** 2026-11-17  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary

Milestone M10 Phase F evaluates whether the retrieval improvements demonstrated by experimental candidate `E6b_ADAPTIVE_BI_ENCODER` (adaptive bi-encoder routing for Devanagari Hindi while preserving English cross-encoder reranking) translate into improved end-to-end question answering performance without compromising factual grounding, regulatory validity, citation integrity, or safe abstention.

Prior to evaluating end-to-end generation under Candidate E6b, this audit comprehensively benchmarks and inspects the baseline production infrastructure (Configuration A) established in Milestone M9 and Phase E.

### Key Audit Findings

1. **Complete Devanagari Answer Collapse in Production Baseline:**
   Under production Configuration A (`E1_PROD_MSMARCO_D10` / production cross-encoder), exactly **0 out of 45 answerable Devanagari Hindi queries** produced an answered response (0.0% Answerable Recall). All 60 Devanagari queries returned `UNANSWERABLE`. While the 15 unanswerable queries were correctly rejected, all 45 answerable queries failed due to retrieval starvation caused by the English-centric cross-encoder.
2. **Reconciliation of English Hit@5 Discrepancy (0.1333 vs 0.1111):**
   The apparent difference between M9 English Hit@5 (0.1333) and Phase E E1 Hit@5 (0.1111) was traced to candidate retrieval depth:
   - Production / M9 uses candidate depth $k_{pool} = \text{top\_k} \times 2 = 20$. In query `M9-Q029`, relevant passage `f88ec726` ranked 14th in the initial hybrid pool, entered the reranker, and was elevated to Rank 1 (Score 5.85), achieving $6/45 = 0.1333$.
   - Phase E strictly isolated candidate depth to $k_{pool} = 10$. Rank 14 was excluded, yielding $5/45 = 0.1111$. Both figures are verified and mathematically consistent with their respective pool boundaries.
3. **Verified Generation Environment:**
   Local LLM generation is powered by `qwen2.5:3b` served via Ollama (`http://localhost:11434`), operating at temperature 0.1, max tokens 384, and timeout 120s. The test suite baseline confirms 257 passing unit and integration tests across the repository.

---

## 2. Baseline Answer Performance Matrix (M9 Production)

The frozen baseline records recovered from `backend/data/experiments/m9/answer_generation_results.csv` comprise 240 queries across 60 semantic intent groups:

| Metric | English (`en`) | Hindi Devanagari (`hi`) | Romanized Hindi (`hi-Latn`) | Hinglish (`en-hi`) | Overall |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Total Queries** | 60 | 60 | 60 | 60 | 240 |
| **Answerable Gold Queries** | 45 | 45 | 45 | 45 | 180 |
| **Unanswerable Gold Queries** | 15 | 15 | 15 | 15 | 60 |
| **Generated ANSWERED** | 26 | **0** | 13 | 14 | 53 |
| **Generated UNANSWERABLE** | 30 | 60 | 45 | 42 | 177 |
| **CONFLICTING_VERSIONS** | 4 | 0 | 1 | 3 | 8 |
| **ERROR / Pipeline Failure** | 0 | 0 | 1 | 1 | 2 |
| **Answerable Recall** | 57.8% (26/45) | **0.0% (0/45)** | 28.9% (13/45) | 31.1% (14/45) | 29.4% (53/180) |
| **Correct Abstention Rate** | 100.0% (15/15) | 100.0% (15/15) | 93.3% (14/15) | 86.7% (13/15) | 95.0% (57/60) |
| **Unnecessary Abstentions** | 15 | **45** | 31 | 28 | 119 |
| **Status Correctness** | 63.3% (38/60) | 25.0% (15/60) | 46.7% (28/60) | 48.3% (29/60) | 45.8% (110/240) |

### Core Observations
- **The Hindi Starvation Bottleneck:** Because Devanagari queries achieved only 0.0444 Hit@5 at retrieval, the Evidence Controller correctly classified the evidence as `INSUFFICIENT` ($CECI < 0.35$ or zero relevant passages) on 100% of answerable queries. The controller safely prevented hallucinations, but at the cost of total functional failure for Hindi users.
- **Latin Query Performance:** English, Romanized Hindi, and Hinglish queries achieved between 28.9% and 57.8% Answerable Recall, demonstrating that the production generator functions properly when relevant evidence is delivered to the Evidence Controller.

---

## 3. Retrieval Candidate Depth Reconciliation

A critical question raised prior to Phase F was why Phase E reported English Hit@5 as 0.1111 (5/45) under Configuration E1, whereas M9 reported 0.1333 (6/45).

### Detailed Root-Cause Analysis

1. **Production Engine Candidate Pool Formulation:**
   In [engine.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L438-L440):
   ```python
   bm25_hits = idx.bm25_search(q, top_k * 2)
   dense_hits = idx.dense_search(q, top_k * 2)
   fused = _rrf_fuse(bm25_hits, dense_hits)
   ```
   For `top_k = 10`, `top_k * 2 = 20` initial lexical and dense candidates are retrieved. The fused pool sent to `rerank()` contains up to 20 candidate passages.

2. **Phase E Ablation Candidate Pool Formulation:**
   In Phase E, to rigorously isolate the reranker's reordering capability without conflating pool expansion, the candidate depth was set to exactly $k_{pool} = 10$ candidates.

3. **Query M9-Q029 Case Study:**
   - Query: *"What is the minimum attendance required in a course to avoid an 'X' grade?"*
   - Expected Relevant Passage: `f88ec726` (SCSET Clause 30.1(iv), 70% rule, page 7).
   - In hybrid RRF fusion, passage `f88ec726` was ranked at **Position 14**.
   - Under $k_{pool} = 20$ (Production / M9): Passage `f88ec726` entered the cross-encoder candidate list. The cross-encoder assigned it a logit score of $+5.85$, elevating it to **Rank 1**. Result: Hit@5 = 1 (Hit).
   - Under $k_{pool} = 10$ (Phase E Ablation): Passage `f88ec726` was at Position 14, outside the top 10 pool, and was never seen by the reranker. Result: Hit@5 = 0 (Miss).
   - Difference across 45 queries: Exactly 1 query ($1/45 = 0.0222$).
   - $5/45 = 0.1111$ vs $6/45 = 0.1333$.

**Resolution:** Both figures are completely accurate within their specified retrieval configurations. In Phase F end-to-end evaluation, the candidate pool depth is held constant at the production default ($top\_k \times 2 = 20$) for both Configuration A and Configuration B.

---

## 4. Generation Pipeline & Guardrails Audit

The production answer generator in [generator.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/generation/generator.py) enforces strict evidentiary guardrails:

```
User Query
   │
   ▼
Retrieval Engine (Hybrid BM25 + Dense + RRF + Reranker)
   │
   ▼
Evidence Controller (CECI + Regulatory Precedence Hierarchy)
   │
   ├── [MISSING / INSUFFICIENT] ──► Safe Abstention (UNANSWERABLE, zero LLM calls)
   ├── [CLARIFICATION_REQUIRED]  ──► Clarification Prompt (zero LLM calls)
   ├── [CONFLICTING]             ──► Conflict Disclosure Prompt
   └── [SUFFICIENT / PARTIAL]    ──► Ollama (qwen2.5:3b) Grounded Generation
                                       │
                                       ▼
                                 Citation Extraction ([Source: <uuid>, page X])
                                       │
                                       ├── [Zero Citations] ──► 1-Bounded Retry Prompt
                                       │                         │
                                       │                         ├── [Retry Citations Valid] ──► Proceed
                                       │                         └── [Still Zero Citations]  ──► UNANSWERABLE
                                       ▼
                                 Claim Grounding & Contradiction Detection
                                       │
                                       ├── [Contradiction Detected] ──► Suppress & CONFLICTING_VERSIONS
                                       └── [Grounded Claims]        ──► Structured QueryResponse (ANSWERED)
```

### Verified Model Parameters
- **Model:** `qwen2.5:3b`
- **Inference Temperature:** 0.1
- **Max Tokens:** 384
- **Timeout:** 120s
- **Citation Format:** `[Source: <passage_id>, page X]`
- **System Prompt:** Preserves Bennett University academic regulations, mandates evidence-only answers, and enforces safe UNANSWERABLE output when evidence is incomplete.

---

## 5. Pre-Experiment Verification Sign-Off

- [x] Pytest baseline test execution passed (257/257 passed in 72.81s, logged to `m10_phase_f_test_execution.log`).
- [x] Configuration snapshot and integrity hashes generated (`m10_phase_f_baseline_snapshot.json`).
- [x] Baseline answers recorded and verified (`m10_phase_f_baseline_answers.csv`).
- [x] Ollama server active and responsive with `qwen2.5:3b`.
- [x] FAISS index and SQLite regulatory database verified and intact.

Baseline audit is concluded. Authorization granted to proceed with Step 2 (E6b Experimental Integration and Routing Validation).
