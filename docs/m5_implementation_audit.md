# IndicRAG-QA — M5 Architecture and Implementation Audit

**Milestone:** M5 — Advanced RAG and E1–E12 Experiments  
**Audit Date:** 2026-11-10  
**Baseline Corpus:** 142 child passages, 30 parent passages (172 rows in SQLite `indicrag.db`), 142 FAISS vectors  
**Corpus Deterministic Hash:** `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d`  
**Verified Benchmark:** `backend/data/dataset/final_verified_dataset.csv` ($N=15$: 13 answerable, 2 unanswerable)  
**Baseline Test Suite:** 116/116 tests passing  

---

## 1. Executive Summary

Following the completion of Milestone 4 (Retrieval Baselines and Metrics), the repository contains an established baseline:
- **Baseline A (BM25):** Hit@1 = 0.3077, Hit@5 = 0.6923, MRR = 0.4808, nDCG@5 = 0.5210
- **Baseline B (Dense FAISS):** Hit@1 = 0.2308, Hit@5 = 0.6154, MRR = 0.3718, nDCG@5 = 0.3691
- **Baseline C (Hybrid RRF, $k=60$):** Hit@1 = 0.1538, Hit@5 = 0.9231, MRR = 0.4705, nDCG@5 = 0.5561

A critical finding from M4 was the cross-lingual divide: Devanagari Hindi (`hi`) queries achieved **0.0000 Hit@1** across all baselines because official regulatory documents are drafted in English, whereas Hybrid RRF achieved **0.7500 Hit@5** by leveraging multilingual embeddings.

The objective of Milestone 5 is to evaluate advanced RAG strategies (E1–E12) to address this gap, elevate top-1 precision, enforce regulatory version-awareness, and control evidence-based abstention.

---

## 2. Component-by-Component Architectural Audit

### 2.1 Multi-Query Retrieval (MQR)
- **File:** [`backend/app/retrieval/engine.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L370-L381)
- **Current State:** Implemented. When `use_mqr=True`, `retrieve()` checks `query_analysis.sub_questions` and `query_analysis.translated_query`. If present, it executes BM25 and Dense search for each variant and fuses candidates via RRF.
- **Audit Assessment:** Working as a deterministic rule-based expansion mechanism.
- **Gap:** Currently limited to sub-questions extracted by regex in `processor.py`; local LLM query paraphrasing/expansion is not connected, preventing MQR from generating cross-lingual synonyms.

### 2.2 Language Identification & Query Translation
- **File:** [`backend/app/query/processor.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/query/processor.py#L26-L98)
- **Current State:** Implemented. Uses a hybrid approach combining Unicode script analysis (`_has_devanagari`), Latin character ratio (`_latin_ratio`), Hinglish keyword regular expressions (`_HINGLISH_RE`), and `langdetect` fallback.
- **Audit Assessment:** Robust and verified with 22 dedicated tests in `test_query_processor.py`. Correctly classifies English, Devanagari Hindi, Code-mixed Hinglish, and Romanized Hindi.
- **Gap:** `QueryAnalysis.translated_query` is defined in the schema but set to `None` (marked as placeholder for IndicTrans2). Because official documents are in English, lack of translation leaves Devanagari queries dependent solely on sub-word dense embeddings, explaining the 0.0000 Hit@1 in M4.

### 2.3 Parent Document Retrieval (PDR)
- **File:** [`backend/app/retrieval/engine.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L289-L316)
- **Current State:** Implemented in `expand_to_parents()`. For every child passage hit in the retrieved list, it looks up the `parent_passage_id`, fetches the parent passage text, and appends it with `_is_pdr_expanded=True` and a discounted score ($score \times 0.9$).
- **Audit Assessment:** Correctly preserves exact child passage citations while offering expanded context for generation.
- **Gap:** Currently expands unconditionally for every unique parent ID without context window deduplication or length pruning.

### 2.4 Cross-Encoder Reranking
- **File:** [`backend/app/retrieval/engine.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L43-L69) and [`rerank()`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L264-L287)
- **Current State:** Implemented using `sentence_transformers.CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")`. Computes pairwise logits between query and retrieved passage texts.
- **Audit Assessment:** Functional and loads cleanly in Anaconda Python 3.13.
- **Limitation:** `ms-marco-MiniLM-L-6-v2` is an English monolingual cross-encoder trained on MS MARCO. For Devanagari Hindi and transliterated Hinglish queries, it may score cross-lingual pairs poorly. E4 will measure this exact degradation.

### 2.5 Regulatory Version Validation
- **File:** [`backend/app/retrieval/engine.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L320-L344)
- **Current State:** Implemented in `validate_versions()`. Demotes superseded passages by $0.3\times$ and non-current passages by $0.6\times$.
- **Audit Assessment:** Prevents hard deletion of historical regulations while flagging superseded clauses.
- **Gap:** The `academic_year` parameter passed into `retrieve()` is not actively evaluated against passage metadata `academic_year` (e.g. distinguishing `2022-23 onwards` from `2017-18`).

### 2.6 Evidence and Answerability Controller
- **File:** [`backend/app/retrieval/evidence_controller.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/evidence_controller.py#L29-L140)
- **Current State:** Implemented. Evaluates retrieval score thresholds (`evidence_min_score`), minimum evidence count (`evidence_sufficient_count`), version conflicts, and sub-question coverage. Produces `SUFFICIENT`, `PARTIAL`, `INSUFFICIENT`, `CONFLICTING`, or `MISSING`.
- **Audit Assessment:** Completely rule-based and transparent; does not rely on uncalibrated LLM confidence.
- **Status:** Fully ready for E10 (Evidence-Based Abstention).

### 2.7 Query Decomposition & Intent Complexity
- **File:** [`backend/app/query/processor.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/query/processor.py#L137-L215)
- **Current State:** Implemented. `decompose_query()` splits multi-part questions on conjunctions (`and`, `aur`, `tatha`, `evam`, `additionally`) and calculates `complexity_score` (0.0 to 1.0).
- **Audit Assessment:** Deterministic and fast.
- **Status:** Ready for E9 (Query Decomposition).

---

## 3. Canonical E1–E12 Experiment Plan

| Experiment ID | Title | Baseline Configuration | Experimental Configuration | Primary Metrics | Key Controlled Variable |
|---|---|---|---|---|---|
| **E1** | BM25 vs Dense vs Hybrid | BM25 (Okapi) | Dense FAISS vs Hybrid RRF ($k=60$) | Hit@1, Hit@5, MRR, nDCG@5 | Retrieval paradigm on frozen corpus |
| **E2** | Fixed Hybrid vs Adaptive Routing | Fixed Hybrid RRF for all queries | Adaptive Router: BM25 for English acronyms, Dense for Romanized, Hybrid+MQR for Devanagari | Hit@1, Hit@5, MRR, Latency | Query-dependent routing policy |
| **E3** | Direct vs Translation-Assisted | Direct input query retrieval | Query translated to English via local Ollama LLM (`qwen2.5:3b`) prior to retrieval | Hit@1, Hit@5, MRR across `hi`, `hi-en`, `hi-Latn` | Query translation vs raw query |
| **E4** | Cross-Encoder Reranking | Fused Hybrid RRF without reranker | Hybrid RRF + `ms-marco-MiniLM-L-6-v2` reranker | Hit@1, Hit@5, MRR by language | Cross-encoder relevance scoring |
| **E5** | Structure-Aware vs Fixed Chunking | Structure-aware parent-child chunks (142 child passages) | Fixed-size token chunking (300 tokens, 50 token overlap) without structure | Hit@1, Hit@5, Passage boundary integrity | Document chunking strategy |
| **E6** | Multi-Query Retrieval (MQR) | Single query retrieval | MQR query expansion with sub-questions and LLM paraphrases | Hit@5, Candidate diversity, Latency | Query expansion on/off |
| **E7** | Parent Document Retrieval (PDR) | Child passage retrieval only | PDR context expansion to parent passages ($score \times 0.9$) | Gold quote context coverage, Token count | Parent context expansion on/off |
| **E8** | Regulatory Version Validation | Retrieval without version filtering | Version-aware filtering matching query academic year and supersession | Hit@1 on temporal queries, Version accuracy | Temporal & cohort metadata filtering |
| **E9** | Query Decomposition | Direct retrieval of full query string | Decomposed sub-question retrieval with multi-evidence fusion | Sub-question coverage, Hit@5 on multi-part | Conjunction decomposition on/off |
| **E10** | Evidence-Based Abstention | Always-answer generation baseline | `EvidenceController` gate (Abstain on INSUFFICIENT/MISSING) | Answerability Precision, Recall, False-Answer Rate | Evidence thresholding gate |
| **E11** | Adaptive vs Fixed Retrieval Budget | Fixed budget ($k=5$ for all queries) | Adaptive budget (dynamic $k \in [3, 10]$ based on complexity and score slope) | Hit@k, Total retrieved passages, Latency | Dynamic top-$k$ cutoff policy |
| **E12** | Full Architecture vs Ablations | Full System (Hybrid + MQR + Rerank + PDR + Version) | Leave-one-out ablations (No-Rerank, No-Dense, No-BM25, No-MQR, No-PDR, No-Version) | Hit@1, Hit@5, MRR, System Latency | Feature contribution isolation |

---

## 4. Implementation Readiness & Execution Strategy

1. **Reusability & Components Completed in Phase 2:**
   - **Adaptive Router (`backend/app/retrieval/router.py`):** Deterministic policy routing queries to BM25 lexical, Dense semantic, Cross-lingual MQR, or Translation-assisted routes with safe fallback to Hybrid RRF (E2).
   - **Translation Module (`backend/app/query/processor.py`):** `translate_query_to_english()` wired via local Ollama `qwen2.5:3b`, preserving original query while gracefully handling timeouts and fallback (E3).
   - **Adaptive Retrieval Budget (`backend/app/retrieval/adaptive_budget.py`):** `AdaptiveBudgetRetriever` dynamically bounding $k \in [3, 10]$ with score elbow pruning while recording fixed $k=5$ control baseline (E11).
   - **Fixed-Window Chunking Index (`backend/data/indexes/fixed_window`):** 165 fixed-stride passages generated across all 4 official PDFs without modifying the structure-aware corpus (E5).
   - **Academic Year Version Validation (`backend/app/retrieval/engine.py`):** Enhanced `validate_versions` with explicit academic-year matching and demotion without silent deletion (E8).
2. **Verification & Regression:**
   - 19 new tests in `backend/tests/test_m5_advanced_rag.py`.
   - Full test suite: **135/135 tests PASSING** in 26.87s.
   - Official corpus SHA-256 verified unchanged: `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d`.
3. **Safety & Integrity Commitments:**
   - Zero modification to existing M3 candidate validation decisions.
   - Identical query inputs and gold passage mappings across all comparative experiments.
   - All 15 candidates ($N=15$) preserved with transparent subgroup sizes ($N=4$ for `en` & `hi`, $N=3$ for `hi-en`, $N=2$ for `hi-Latn`, $N=2$ for unanswerable).
   - Strict reporting of actual measurements without fabricated statistics.

