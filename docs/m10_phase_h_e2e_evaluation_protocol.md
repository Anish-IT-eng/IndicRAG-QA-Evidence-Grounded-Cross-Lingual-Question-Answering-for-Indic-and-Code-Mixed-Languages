# M10 Phase H — End-to-End Evaluation Protocol

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** H — Cross-Lingual End-to-End Answer Quality, Citation & Grounding Audit  
**Date:** November 17, 2026  
**Status:** Audit Complete — Target Determination: `M10_PHASE_H_VERIFIED_WITH_LIMITATIONS`  

---

## 1. Executive Summary & Objective

The objective of **Milestone M10 Phase H** is to conduct an independent, controlled, and rigorous end-to-end evaluation comparing:
1. **Config A (`E1_PROD_MSMARCO_D10`):** The existing production retrieval pipeline (Hybrid BM25 + FAISS with Reciprocal Rank Fusion, reranked by `cross-encoder/ms-marco-MiniLM-L-6-v2` at depth 10).
2. **Config B (`E6b_ADAPTIVE_BI_ENCODER`):** The experimental candidate identified in Phase E, which dynamically routes Hindi Devanagari queries directly to bi-encoder dense retrieval scores to avoid cross-encoder language starvation, while preserving the full production pipeline for Latin-script queries (English, Romanized Hindi, and Hinglish).

This milestone is an **independent audit and research evaluation**. It is **not** a production deployment milestone. In strict accordance with the project charter:
- The production default in [backend/app/retrieval/engine.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L395) remains `"production"`.
- Phase I (production promotion review) has **not** been initiated.
- No application code, retrieval algorithms, prompts, models, embeddings, database records, or frozen datasets were modified.

---

## 2. Evaluation Population & Statistical Unit

### 2.1 Frozen M9 Benchmark Population
The evaluation was executed against the frozen M9 benchmark dataset located at [backend/data/experiments/m9/m9_evaluation_dataset.jsonl](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m9/m9_evaluation_dataset.jsonl):
- **Total Semantic Intent Groups ($N$):** 60 independent intent groups.
  - **Answerable Intent Groups:** 45 intent groups (180 query records).
  - **Unanswerable Intent Groups:** 15 intent groups (60 query records).
- **Formulations per Intent Group:** Exactly 4 parallel language formulations:
  - `en`: Standard English.
  - `hi`: Hindi written in Devanagari script.
  - `hi-Latn`: Romanized Hindi written in Latin script.
  - `en-hi`: Code-mixed Hinglish written in Latin script.
- **Total Evaluated Query Records:** $60 \times 4 = 240$ queries.
- **Total Comparative Evaluations:** $240 \times 2 = 480$ end-to-end execution traces.

### 2.2 Independent Statistical Unit
The **semantic intent group** is strictly treated as the independent statistical unit ($N=60$ total; $N=45$ for answerable queries). Under no circumstances are the four language variants of a single intent treated as four independent observations, as they share identical underlying factual answers, target documents, and semantic contexts.

---

## 3. Strict Scope & Environment Constraints

### 3.1 Preservation & Immutability Guarantees
- **No Production Mutation:** The runtime default in `backend/app/retrieval/engine.py` line 395 remains `rerank_strategy: str = "production"`.
- **Database & Corpus Immutability:** SQLite database [backend/data/db/indicrag.db](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/db/indicrag.db) (306 passages, 7 official documents) and FAISS index [backend/data/indexes/official/faiss.index](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/indexes/official/faiss.index) (253 child vectors) were verified via SHA-256 and kept read-only.
- **Prompt & Model Freezing:** The generation prompt template, temperature ($0.1$), top-$p$, max tokens ($384$), and model checkpoint (`qwen2.5:3b`) were held completely invariant between Config A and Config B.

### 3.2 Hardware & Execution Environment
- **Inference Runtime:** Local Ollama daemon running on `127.0.0.1:11434`.
- **Generator Model:** `qwen2.5:3b` (Digest: `357c53fb659c`, Size: 1.9 GB).
- **Execution Strategy:** Strictly sequential execution to prevent GPU/CPU memory pressure and avoid OOM aborts. Peak RAM was measured at $\approx 1,180$ MB.
- **Network Boundaries:** No paid APIs, cloud services, Docker, or external web requests were used.

---

## 4. End-to-End Pipeline Architecture

```
User Query (en, hi, hi-Latn, en-hi)
                  │
                  ▼
         Query Processor (app/query/processor.py)
         - Script & Language Detection
         - Normalization (NFC, Unicode, Whitespace)
         - Complexity & Decomposition Analysis
                  │
                  ▼
         Retrieval Routing (app/retrieval/engine.py)
         ├─────────────────────────────────────────┐
         │                                         │
    [Config A: Production]                [Config B: Adaptive E6b]
    - Hybrid BM25 + Dense FAISS           - If Hindi Devanagari (`hi`):
    - RRF Fusion (k=60)                     Direct dense bi-encoder ranking
    - MS-MARCO Cross-Encoder Rerank (D10) - If Latin (`en`, `hi-Latn`, `en-hi`):
         │                                  Preserve Hybrid + MS-MARCO Rerank
         └─────────────────────────────────────────┤
                  │
                  ▼
         Top-5 Retrieved Passages
                  │
                  ▼
         Evidence Controller (app/retrieval/evidence_controller.py)
         - Cross-Encoder CECI Entailment Evaluation
         - Decision: SUFFICIENT / INSUFFICIENT / CLARIFICATION_REQUIRED
                  │
                  ▼
         Generator (`qwen2.5:3b` via Ollama)
         - Strict Evidence-Grounded Prompting
         - Citation Insertion: [UUID] (Page X)
                  │
                  ▼
         Verification & Safety Gate
         - Claim Extraction & Verification
         - Contradiction Detection
         - Safe Abstention Enforcement
```

---

## 5. Regression Test Suite Verification

Prior to performing the evaluation audit, the full regression test suite was executed against the codebase:
- **Test Command:** `pytest backend/tests/ -q`
- **Total Test Cases:** 260
- **Passed:** 260
- **Failed:** 0
- **Skipped:** 0
- **Execution Time:** 89.89 seconds
- **Verification Result:** Zero regressions detected across ingestion, database, retrieval baselines, query processor, model verifier, and API endpoints.

---

## 6. Audit Data Deliverables Overview

The audit produced 4 primary machine-readable artifacts in [backend/data/experiments/m10/](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/):
1. `m10_phase_h_per_query_results.csv`: 480 per-query records across both configurations.
2. `m10_phase_h_claim_audit.csv`: 167 decomposed atomic claims audited for factual grounding.
3. `m10_phase_h_citation_audit.csv`: 111 individual citations audited for UUID validity and page correctness.
4. `m10_phase_h_metrics.json`: Hierarchical JSON file containing all granular metrics.
5. `m10_phase_h_manifest.json`: Cryptographic integrity manifest.
