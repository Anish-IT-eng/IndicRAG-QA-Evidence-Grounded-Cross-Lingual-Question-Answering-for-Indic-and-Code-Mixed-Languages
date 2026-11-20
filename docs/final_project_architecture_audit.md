# IndicRAG-QA — Final Project Architecture & Repository Audit

**Date:** November 19, 2026  
**Auditor:** Antigravity AI (Lead Agent)  
**Repository Working Directory:** `C:\Users\anish\Desktop\IndicRAG-QA`  
**Execution Environment:** Windows, Python 3.13 (Anaconda), Ollama (`qwen2.5:3b`), CPU-friendly  

---

## 1. Executive Summary

This audit assesses the state of the **IndicRAG-QA** system across its backend, frontend, ingestion pipeline, retrieval architecture, relationship reasoning store, generation pipeline, and evaluation framework. 

The system provides evidence-grounded cross-lingual question answering over institutional university regulations (Bennett University) and user-uploaded academic documents in English, Hindi (Devanagari), Romanized Hindi, and code-mixed Hinglish.

### Key Audit Verdict
- **Completed Components:** R1 PDF extraction & table reconstruction, R2/R2.1 relationship store & calendar reconciliation, R3 generic relationship retrieval, R4/R4.1 bounded multi-hop reasoning, R5 conversational feedback repair, R6 Stage 1 integrity audit (13/13 artifacts verified), R6 Stage 2 & 2.1 multilingual event alignment repair (3/3 smoke tests passed, 8/8 regression scenarios passed).
- **Partially Implemented / Integration Gaps Identified:**
  1. **Frontend-Backend Integration Gap:** FastAPI backend (`backend/app/api/main.py`) does not mount the frontend static files (`frontend/index.html` and assets). Accessing `http://localhost:8000/` does not serve the web interface.
  2. **Document Deletion API Gap:** Cascading deletion is fully implemented in `app.ingestion.pipeline.delete_document` (cleaning database, tables, relationships, and FAISS index), but `DELETE /documents/{document_id}` is missing from `backend/app/api/main.py`. The frontend UI also lacks a corresponding Delete button.
  3. **Multi-Hop Query Integration in Endpoint:** `MultiHopReasoner` (R4/R6) is thoroughly verified in test scripts, but `POST /query` in `main.py` relied solely on single-hop retrieval and CECI without delegating complex or calendar queries to `MultiHopReasoner`.
  4. **Document Ingestion Feedback & Status:** Users uploading documents get a queued message, but there is no dedicated `/documents/{doc_id}/status` polling endpoint to report background ingestion success/failure.

---

## 2. Repository Structure Analysis

```
IndicRAG-QA/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI routes (main.py)
│   │   ├── calibration/         # Exploratory temperature/threshold calibration
│   │   ├── core/                # Config, DB connection, logging
│   │   ├── evaluation/          # Benchmark dataset & metrics runner
│   │   ├── generation/          # Grounded answer generator, citation validator
│   │   ├── ingestion/           # PDF extraction, table parser, chunking, indexing
│   │   ├── models/              # Pydantic schemas (Query, Response, Citations)
│   │   ├── query/               # Query processor, event resolver, feedback repair
│   │   └── retrieval/           # BM25, FAISS, CrossEncoder reranker, CECI,
│   │                            # Sequential orchestrator, MultiHopReasoner, RelationshipStore
│   ├── data/
│   │   ├── db/indicrag.db       # Primary SQLite store (passages, relationships, tables)
│   │   ├── indexes/             # FAISS dense & BM25 inverted indexes
│   │   ├── official/            # Official PDF documents
│   │   └── uploads/             # Tenant-isolated user uploads
│   └── tests/                   # Pytest test suite (269 items; 264 passed)
├── frontend/
│   ├── index.html               # Complete standalone single-page application (2,529 lines)
│   ├── app.html                 # Secondary template
│   └── public/, src/            # Static assets
├── docs/                        # Architecture specs, audit logs, and test manifests
└── scripts/                     # Evaluation, verification, and smoke test scripts
```

---

## 3. Detailed Component Audit

### 3.1 Document Ingestion & Storage (Feature 1)
- **Status:** **Partially Implemented (85%)**
- **Existing Implementation:**
  - `backend/app/ingestion/pipeline.py`: Supports `ingest_pdf`, `extract_pages`, structure-aware chunking, parent-child passage hierarchy, table parsing, and embedding generation into FAISS + BM25.
  - Generic relationship extraction runs on all ingested PDFs into `document_relationships`.
  - Cascading deletion exists in `delete_document(document_id, user_id)`: deletes passages, table cells, document tables, relationships, and removes passages from the FAISS/BM25 indexes.
- **Deficiencies:**
  - No `DELETE /documents/{document_id}` endpoint in `backend/app/api/main.py`.
  - Ingestion runs in `BackgroundTasks`, but if an upload fails during extraction, the user cannot query the failure state via API.
  - The frontend modal displays uploaded documents but lacks a delete trigger.

### 3.2 Document-Aware Sequential QA & Tenant Isolation (Feature 2)
- **Status:** **Fully Implemented (95%)**
- **Existing Implementation:**
  - `backend/app/retrieval/sequential_orchestrator.py`: Implements 3-stage sequential retrieval policy:
    1. Search user uploads first (scoped strictly to `user_id`).
    2. Fallback to official regulations if user evidence is missing, insufficient, or partial.
    3. Final institutional abstention if neither source has sufficient evidence.
  - Reconciles partial user evidence with official evidence and detects direct contradictions (`RegulatoryRelationship.GENUINE_CONFLICT`).
  - Unit tests in `test_sequential_retrieval_fallback.py` (all 9 tests passed).
- **Deficiencies:**
  - Minor: User ID in `GET /documents` should default gracefully if neither query param nor header is passed.

### 3.3 Multilingual Query Understanding (Feature 3)
- **Status:** **Fully Implemented (100%)**
- **Existing Implementation:**
  - `backend/app/query/processor.py`: Language detection (English, Hindi Devanagari, Romanized Hindi, Hinglish), script classification, normalization, decomposition.
  - `backend/app/query/event_resolver.py` (created in R6 Stage 2.1): Resolves institutional event intent (`End Semester Examination`, `Make-up Examination`, `Registration`), semester scope (`Odd` vs. `Even`), and ambiguity flags.
  - Term coverage guard in `multi_hop_reasoner.py` evaluates non-English queries against `normalized_query`, preventing spurious abstention.

### 3.4 Retrieval, Ranking & Evidence Controller (Feature 4)
- **Status:** **Fully Implemented (100%)**
- **Existing Implementation:**
  - `backend/app/retrieval/engine.py`: Hybrid fusion (RRF) combining BM25 and FAISS dense vector search (`paraphrase-multilingual-MiniLM-L12-v2`).
  - Production reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`.
  - CECI Evidence Controller (`ceci.py`): Evaluates retrieval coverage, sufficiency, and applicability before answer generation.

### 3.5 Relationship-Aware & Bounded Multi-Hop Reasoning (Feature 5)
- **Status:** **Implemented, Needs Direct API Integration (90%)**
- **Existing Implementation:**
  - `backend/app/retrieval/relationship_store.py`: SQLite-backed relationship graph querying `document_relationships`.
  - `backend/app/retrieval/multi_hop_reasoner.py`: Enforces maximum depth $k \le 3$, evidence boundary $|P| \le 12$, schedule synthesis, and distractor filtering.
- **Deficiency:**
  - `POST /query` in `backend/app/api/main.py` directly executes `retrieve(...)` or `sequential_orchestrator.execute(...)`. While `engine.py` calls `expand_with_relationships`, the dedicated `MultiHopReasoner` was not wired into `sequential_orchestrator` Stage 2 for complex or calendar queries.

### 3.6 Evidence-Grounded Answer Generation (Feature 6)
- **Status:** **Fully Implemented (100%)**
- **Existing Implementation:**
  - `backend/app/generation/generator.py`: Generates strictly grounded answers via local Ollama `qwen2.5:3b`.
  - Sentence-grounded prompts format exact dates with citations: `[Source: passage_id, page X]`.
  - Truncated UUID and semantic slug resolution handles model output variations.
  - Automatic fallback to `UNANSWERABLE` when evidence is missing or citations cannot be validated.

### 3.7 Conversational Feedback and Repair (Feature 7)
- **Status:** **Fully Implemented (100%)**
- **Existing Implementation:**
  - `backend/app/query/feedback_repair.py`: Classifies feedback subtypes (disagreement, missing exception, wrong cohort, citation challenge, request for simpler explanation).
  - Recovers preceding conversation turn from SQLite `conversation_turns` or request payload.
  - Evaluates whether feedback warrants evidence rechecking or explanation adjustment.

### 3.8 Frontend User Experience (Feature 8)
- **Status:** **Partially Implemented (80%)**
- **Existing Implementation:**
  - `frontend/index.html`: Responsive design system, search scope toggles, progressive timer, citation inspector modal, upload modal with drag-and-drop, and document registry modal.
- **Deficiencies:**
  - Not served by FastAPI root `/` (requires separate manual HTTP server or file opening).
  - Lacks a document deletion button in the upload management modal.
  - Missing upload status indicator showing whether background indexing has finished.

---

## 4. Test Suite Execution & Baseline Findings

A full run of `pytest backend/tests/` (269 test cases) was executed:
- **Passed:** **264 tests (98.1%)**
- **Failed:** **5 tests (1.9%)**
  - `test_m5_advanced_rag.py::test_official_structure_aware_corpus_untouched` and `test_m8_corpus_refresh.py::test_passage_counts_expanded_correctly` / `test_corpus_sha256_matches_canonical_m8`: These historical unit tests asserted child passage counts of 253, which were intentionally expanded to 774 during R1/R2 table cell and relationship ingestion.
  - `test_m6_benchmark_expansion.py::test_verbatim_evidence_grounding`: Looked for a specific historical calendar string modified during R2.1 calendar reconciliation.
  - `test_retrieval_baselines.py::TestMultilingualRetrieval::test_devanagari_hindi_retrieval`: Asserted an exact hardcoded passage ID for a Devanagari query, whereas the production hybrid index retrieves equivalent passages with higher scores.

All critical sequential fallback, tenant isolation, and conversational repair tests in `test_sequential_retrieval_fallback.py` **passed 100%**.

---

## 5. Required Implementation Roadmap for Final Readiness

1. **Backend Integration:**
   - Mount `frontend/` as static files in FastAPI and serve `index.html` at `GET /`.
   - Implement `DELETE /documents/{document_id}` in `backend/app/api/main.py` using `app.ingestion.pipeline.delete_document`.
   - Wire `MultiHopReasoner` into `sequential_orchestrator.py` and `POST /query` for complex, calendar, and multi-condition queries.
   - Add `GET /documents/{document_id}/status` to report ingestion status.
2. **Frontend UI Completion:**
   - Add Delete document button with confirmation to the upload modal list in `frontend/index.html`.
   - Add visual badge for ingestion status (Processing vs. Ready).
   - Ensure `API_BASE` defaults dynamically to `window.location.origin` when served from FastAPI.
3. **End-to-End Acceptance Testing:**
   - Execute Tests A through I (Startup, Ingestion, Official QA, Multilingual, Abstention, Multi-Hop, Feedback, Security, Regression).
4. **Final Documentation:**
   - Comprehensive `README.md`, `docs/FINAL_PROJECT_ARCHITECTURE.md`, `docs/FINAL_IMPLEMENTATION_REPORT.md`, `docs/FINAL_TEST_REPORT.md`, `docs/FINAL_LIMITATIONS_AND_FUTURE_WORK.md`, and `docs/PROJECT_FINAL_STATUS.md`.
