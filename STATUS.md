# IndicRAG-QA Project Status & Server Health Ledger

## Current Status: OPERATIONAL (Production-Ready)

**Last Updated:** November 27, 2026  
**Environment:** Windows 11 / Anaconda Python 3.13  
**Server Launcher:** `python run.py` (or `python run.py --port 8080`)  

---

## 1. Incident Report: FAISS Application Control Startup Failure

### Root Cause
When executing `python run.py`, the backend unconditionally imported `faiss` in `backend/app/retrieval/engine.py`. Under Windows Application Control or restricted host execution environments, loading the binary C/C++ extension `_swigfaiss.pyd` was blocked:
```text
import faiss
ImportError: DLL load failed while importing _swigfaiss:
An Application Control policy has blocked this file.
```
This hard dependency prevented FastAPI, Uvicorn, and all retrieval endpoints from initializing.

---

## 2. Implemented Architecture Fix: Safe Optional FAISS with NumPy Dense Fallback

### Core Principles
1. **Optional FAISS Dependency:** Wrapped `import faiss` in safe exception handling. FAISS is no longer mandatory for server startup.
2. **High-Performance NumPy Fallback:** When FAISS is unavailable or blocked, dense semantic retrieval computes cosine similarity using vector dot product over L2-normalized embeddings:
   $$\text{sim}(q, p) = q_{\text{norm}} \cdot p_{\text{norm}}$$
   Because SentenceTransformer embeddings are normalized upon creation, this is mathematically identical to FAISS `IndexFlatIP`.
3. **Zero Loss of Dense Retrieval:** The engine never silently drops to BM25-only retrieval. Dense scores, rank fusion (RRF), parent document retrieval (PDR), cross-encoder reranking, and relationship expansions operate at 100% capacity.
4. **Resilient Index Storage & Loading:**
   - Both `faiss.index` and `embeddings.npy` are supported.
   - If `embeddings.npy` is present, it loads in milliseconds without rebuilding.
   - If missing, embeddings are reconstructed from FAISS or computed on the fly from passage texts.
5. **Robust Fault Tolerance:** Handled empty indexes, dimension mismatches, missing embedding files, and multi-tenant user isolation without crashing.

---

## 3. Files Modified & Added

- **`backend/app/retrieval/engine.py`**:
  - Made `faiss` optional via `_FAISS_AVAILABLE` and `is_faiss_available()`.
  - Added `set_faiss_force_disabled()` runtime toggle for testing.
  - Implemented dual-backend `dense_search()`: FAISS `IndexFlatIP` when available; vectorized NumPy cosine similarity as fallback.
  - Updated `build()`, `save()`, `load()`, and `is_ready()` to manage both FAISS and NumPy embedding states safely.
- **`backend/app/api/main.py`**:
  - Added dual route `@app.get("/api/health")` and `@app.get("/health")` returning standard `HealthResponse`.
- **`backend/tests/test_dense_retrieval_fallback.py`**:
  - Added comprehensive test suite covering FAISS toggle, NumPy fallback dense search, score equivalence, RRF fusion, empty indexes, dimension mismatches, and multi-tenant isolation.

---

## 4. Verification & Test Results

### A. Dedicated Dense Fallback Test Suite
Ran `pytest backend/tests/test_dense_retrieval_fallback.py -v`:
- `test_is_faiss_available_toggle`: **PASSED**
- `test_dense_search_with_numpy_fallback`: **PASSED**
- `test_faiss_and_numpy_ranking_equivalence`: **PASSED** (scores identical within $\Delta < 1e-4$)
- `test_hybrid_rrf_with_numpy_fallback`: **PASSED**
- `test_empty_index_handling`: **PASSED**
- `test_dimension_mismatch_handling`: **PASSED**
- `test_numpy_fallback_tenant_isolation`: **PASSED**
**Summary: 7 / 7 PASSED (100%)**

### B. Live Server Startup & Endpoint Verification (`python run.py`)
Started server with `python run.py --port 8000` and probed all key endpoints:
1. `GET http://127.0.0.1:8000/api/health` -> **HTTP 200 OK**
   ```json
   {
     "status": "ok",
     "version": "0.1.0",
     "ollama_reachable": true,
     "embedding_model_loaded": true,
     "document_count": 24,
     "passage_count": 1471,
     "child_passage_count": 1338,
     "parent_passage_count": 133
   }
   ```
2. `GET http://127.0.0.1:8000/health` -> **HTTP 200 OK**
3. `GET http://127.0.0.1:8000/api/docs` -> **HTTP 200 OK** (Swagger UI rendered)
4. `GET http://127.0.0.1:8000/` -> **HTTP 200 OK** (Web Chat UI rendered)

---

## 5. End-to-End Query Verification: Bennett University SSR (Green Spaces)

Tested query: `"How many acres are dedicated to green spaces"`
- **Retrieval Pipeline Result:**
  - Status: `SUFFICIENT`
  - Valid passages: 10 retrieved (Top hit: `UPUNGN113496_SSR_BU.pdf`, Page 102, Section 7.1.4)
  - Extracted Evidence: *"BU campus boasts over 12 acres of green space dedicated to greenery. This includes over 2,000 fully grown trees as well as shrubs, ground covers, seasonal flowers..."*
- **End-to-End LLM Generation (`qwen2.5:3b`):**
  - **Status:** `answered`
  - **Evidence Status:** `sufficient`
  - **Answer:** *"Over 12 acres of the campus are dedicated to green spaces."*
  - **Attributed Citation:** `UPUNGN113496_SSR_BU.pdf`, Page 102 (claim verified & supported)

