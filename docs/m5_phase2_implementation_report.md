# IndicRAG-QA — M5 Phase 2 Controlled Implementation Report

**Milestone:** M5 — Advanced RAG and E1–E12 Experiments (Phase 2: Controlled Implementation)  
**Date:** 2026-11-10  
**Status:** **PHASE 2 COMPLETED — READY FOR PHASE 3 EXPERIMENT EXECUTION**  
**Official Corpus SHA-256:** `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d` (Verified Identical)  
**Verified Benchmark Dataset:** `backend/data/dataset/final_verified_dataset.csv` ($N=15$, Frozen)  
**Total Test Suite:** **135 passed in 26.87s** (100% passing)  

---

## 1. Executive Summary

Milestone 5 Phase 2 implements the algorithmic and architectural gaps identified in [`docs/m5_implementation_audit.md`](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/m5_implementation_audit.md) without launching the final E1–E12 experimental evaluation suite.

All implementations strictly adhere to the project's research integrity guidelines:
- **No Corpus Mutation:** The official structure-aware index (142 child passages, 30 parent passages) and its SHA-256 hash remain completely untouched.
- **No Benchmark Alteration:** The M3 verified benchmark ($N=15$) and its gold evidence mappings remain frozen.
- **Deterministic Fallbacks:** Every advanced component (adaptive router, translation module, dynamic budget) features safe fallbacks to standard hybrid retrieval.

---

## 2. Inventory of Implemented Components vs. Reused Code

### 2.1 E2 — Adaptive Query Routing (`backend/app/retrieval/router.py`)
- **Type:** Newly Created Component.
- **Interface:** `AdaptiveRouter.route(query_analysis)` and `route_query(query_analysis) -> RoutingDecision`.
- **Policy Rules:**
  1. *Devanagari Hindi with Translation:* Routes to `TRANSLATION_ASSISTED` hybrid retrieval.
  2. *Devanagari Hindi without Translation:* Routes to `CROSS_LINGUAL_MQR` (dense semantic search + multi-query expansion).
  3. *High Complexity or Multi-Part:* Routes to `CROSS_LINGUAL_MQR` for composite evidence coverage.
  4. *English with Exact Anchors:* (e.g. Clause 30.1, 70%, 75%, specific dates) routes to `BM25_LEXICAL` for maximum exact-match precision.
  5. *Conversational Romanized Hindi:* Routes to `DENSE_SEMANTIC` vector retrieval.
  6. *Default / Ambiguous:* Safe fallback to `HYBRID_RRF`.
- **Outputs:** Strategy, detailed human-readable explanation, and machine-readable feature dictionary.

### 2.2 E3 — Translation-Assisted Retrieval (`backend/app/query/processor.py`)
- **Type:** Implemented into Query Processor.
- **Interface:** `translate_query_to_english(query, source_lang, model_name="qwen2.5:3b", ...) -> TranslationResult`.
- **Features:**
  - Non-English queries are translated into concise English queries using local Ollama (`qwen2.5:3b`).
  - Preserves technical identifiers, numbers, dates, grade letters (`O, A+, A, B+, B, C+, C, D, F, I, X`), percentages, and regulation terms.
  - Full exception handling for `httpx.TimeoutException`, connection failure, HTTP errors, and empty responses.
  - Fallback flag (`fallback_occurred=True`) and latency measurement (`latency_ms`) recorded.
  - Original query string is **never overwritten** (`analysis.original_query` remains unchanged; translated text is stored in `analysis.translated_query`).

### 2.3 E5 — Fixed-Window Chunking Comparison Index (`scripts/build_fixed_window_index.py`)
- **Type:** Newly Created Independent Pipeline & Index.
- **Storage:** `backend/data/indexes/fixed_window/` (`faiss.index` + `meta.pkl`).
- **Characteristics:**
  - Uses the identical 4 official source PDFs.
  - Generates 165 fixed-stride chunks (300 words chunk size, 50 words overlap) without respecting clause/heading boundaries.
  - Manifest recorded in `backend/data/experiments/m5/e5_fixed_window_manifest.json`.
  - Fully isolates the fixed-window ablation from the official structure-aware index (142 child passages).

### 2.4 E8 — Version-Aware Academic Year Filtering (`backend/app/retrieval/engine.py`)
- **Type:** Enhanced Existing Component.
- **Changes in `validate_versions()`:**
  - Added active inspection of query-specified `academic_year` against passage metadata `academic_year`.
  - Passages matching the requested academic year or designated `"onwards"` retain full score.
  - Mismatched historical passages (e.g. 2017-18 ordinance when query specifies 2026-27) are demoted by $0.5\times$ and tagged with `_version_flag="academic_year_mismatch"`.
  - Historical regulations are **never silently deleted**, preserving conflict detection and historical retrieval.

### 2.5 E11 — Adaptive Retrieval Budget (`backend/app/retrieval/adaptive_budget.py`)
- **Type:** Newly Created Component.
- **Interface:** `AdaptiveBudgetRetriever.determine_candidate_budget(analysis)` and `prune_by_score_elbow(candidates, initial_budget)`.
- **Rules:**
  - Bounds depth $k \in [3, 10]$ (default baseline $k=5$).
  - Simple direct English queries tighten budget to $k=3$ for low latency.
  - Multi-part or high-complexity queries expand initial candidate pool to $k=8$.
  - Post-retrieval score slope / elbow detection prunes candidates when adjacent rank relative drop $\ge 35\%$.

---

## 3. Files Created and Modified

| File | Action | Purpose |
|---|---|---|
| [`backend/app/retrieval/router.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/router.py) | **Created** | Deterministic adaptive router for E2. |
| [`backend/app/retrieval/adaptive_budget.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/adaptive_budget.py) | **Created** | Dynamic candidate budgeting and elbow pruning for E11. |
| [`scripts/build_fixed_window_index.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/scripts/build_fixed_window_index.py) | **Created** | Fixed-window chunking index builder for E5. |
| [`backend/tests/test_m5_advanced_rag.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/tests/test_m5_advanced_rag.py) | **Created** | 19 unit & regression tests for router, translation, budget, and chunking. |
| [`backend/app/query/processor.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/query/processor.py) | **Modified** | Implemented `translate_query_to_english()` with Ollama and error fallback (E3). |
| [`backend/app/retrieval/engine.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py) | **Modified** | Enhanced `validate_versions` with academic-year matching logic (E8). |
| [`backend/app/retrieval/__init__.py`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/__init__.py) | **Modified** | Clean package exports for new retrieval modules. |
| [`STATUS.md`](file:///c:/Users/anish/Desktop/IndicRAG-QA/STATUS.md) | **Updated** | Corrected M3 title, updated canonical E1–E12 grouping, updated test counts. |
| [`docs/m5_implementation_audit.md`](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/m5_implementation_audit.md) | **Updated** | Updated readiness status post-Phase 2. |

---

## 4. Test Suite and Regression Results

Ran complete regression suite:
```
============================ 135 passed in 26.87s =============================
- test_api.py                  10/10 PASSING
- test_database.py              4/4  PASSING
- test_ingestion_smoke.py      32/32 PASSING
- test_metrics.py              18/18 PASSING
- test_model_verifier.py       12/12 PASSING
- test_query_processor.py      22/22 PASSING
- test_retrieval_baselines.py  12/12 PASSING
- test_m5_advanced_rag.py      19/19 PASSING
```
Zero test failures, zero warnings/errors.

---

## 5. Corpus & Benchmark Integrity Confirmation

- **Official Corpus Snapshot:** 142 child passages, 30 parent passages (172 rows in SQLite `indicrag.db`).
- **Official Corpus Deterministic SHA-256:** `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d` (Verified strictly identical to M4 baseline).
- **Verified Benchmark Dataset:** 15 candidate records in `backend/data/dataset/final_verified_dataset.csv` (Verified strictly identical to M3/M4 baseline).

---

## 6. Execution Command for Phase 3 (E1–E12 Experiments)

Phase 2 is complete and all modules are ready. To launch the full automated E1–E12 experiment suite in Phase 3:

```powershell
C:\Users\anish\Anaconda3\python.exe scripts/run_m5_experiments.py
```
*(The experiment runner script will execute all 12 experiments, record query-level logs and language breakdowns in `backend/data/experiments/m5/`, and generate `docs/m5_experiment_report.md`.)*

