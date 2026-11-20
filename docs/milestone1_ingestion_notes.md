# Milestone 1 — Ingestion Pipeline: Technical Notes

**Status:** Implementation complete — awaiting human-obtained official documents.  
**Date:** 2026-11-02  
**Environment:** Python 3.13.5 (Anaconda), Windows 11, Intel Core i7-1360P, 16 GB RAM.

---

## What Was Built

### 1. PDF Extraction (`app/ingestion/pdf_extractor.py`)

Multi-backend extractor with automatic fallback chain:

```
fitz (PyMuPDF 1.24.13) → pypdf 6.21 → pdfplumber
```

**Why PyMuPDF 1.24.13 specifically:**  
PyMuPDF 2.x ships a DLL (`_mupdf.pyd`) that is blocked by the Windows Application Control policy on this machine. Version 1.24.13 uses a different DLL layout that passes the policy check. `pypdf` is a pure-Python fallback with no native DLLs.

**`RawPage` fields preserved per page:**
- `page_number` (1-indexed)
- `text` (selectable text only; OCR not invoked — documents are assumed to have selectable text)
- `has_selectable_text` (flag; if False, OCR would be needed — not yet implemented)
- `tables` (list of `{headers, rows}` dicts; via `page.find_tables()` in fitz)
- `headings` (lines matching heading heuristics: ALL-CAPS short lines, or `N.N.N` prefix)

### 2. Structure-Aware Chunking

Two-level parent/child hierarchy:

| Level | Token target | Purpose |
|-------|-------------|---------|
| Parent | `parent_chunk_size_tokens = 1200` | Context for answer generation |
| Child  | `chunk_size_tokens = 400`, overlap `80` | Unit of retrieval |

Every child stores its `parent_chunk_index` so PDR (Parent Document Retrieval) can expand hits to the wider context at generation time.

### 3. Ingestion Pipeline (`app/ingestion/pipeline.py`)

| Step | Detail |
|------|--------|
| Hash check | SHA-256; unchanged files are SKIPPED (no re-processing) |
| Page extraction | Multi-backend as above |
| Chunking | Parent+child with metadata from each page |
| Passage storage | SQLite `passages` table with `INSERT OR IGNORE` |
| Index update | BM25 rebuild + FAISS encoding + save to `indexes_dir` |
| Document record | `documents` table with `UPSERT` on `document_id` |
| Version metadata | `effective_date`, `academic_year`, `is_current`, `superseded_by`, `program_applicability` |

### 4. Source Registry (`app/ingestion/source_registry.py`)

Manually-curated. All entries are `verified=False` until a human has:
1. Downloaded the PDF from an official university URL.
2. Read the document cover page to confirm its effective date.
3. Verified it has not been superseded.
4. Set `verified=True` and `source_url=<download URL>` in the registry.

**No automatic downloading is implemented.** This is intentional — university document URLs are unstable, and ingesting an unverified or superseded document would corrupt research results.

### 5. Scripts

| Script | Purpose |
|--------|---------|
| `scripts/discover_sources.py` | Prints known official URL entry points; does NOT download |
| `scripts/verify_corpus.py` | Checks registry against `data/official/`; flags missing/unregistered/unverified files |
| `scripts/ingest_official.py` | Ingests only `verified=True` registry entries; supports `--dry-run` |

---

## Test Results

### Existing tests (pre-Milestone 1 work): 60/60 PASS
### Smoke test (`tests/test_ingestion_smoke.py`): 32 tests

The smoke test builds a real multi-page PDF from scratch using only the Python standard library (no reportlab, no internet), then verifies every pipeline stage:

| Test class | Tests | What it verifies |
|-----------|-------|-----------------|
| `TestSyntheticPDFCreation` | 3 | PDF header, EOF marker, byte size |
| `TestHashComputation` | 3 | SHA-256 hex format, determinism, content sensitivity |
| `TestPageExtraction` | 5 | Page count, text presence, 1-indexed page numbers, attendance-rule text, attribute types |
| `TestChunking` | 5 | Child and parent production, page numbers, non-empty text, monotone indices |
| `TestFullPipeline` | 5 | COMPLETED status, DB record, passages stored, version metadata, page count |
| `TestDeduplication` | 2 | SKIPPED on re-ingest, COMPLETED on `--force` |
| `TestPassagePageNumbers` | 1 | All passages have `page_number ≥ 1` |
| `TestParentChildLinkage` | 2 | Children point to real parents in same doc |
| `TestKeyTextRetrievability` | 2 | Attendance rule and grading text survive to DB |
| `TestSourceRegistryStructure` | 4 | Dataclass fields, no placeholder verified, notes on unverified entries |

---

## Known Issues — Milestone 1

### 1. No official documents in `data/official/`
**Status: Critical blocker for all retrieval experiments.**  
The corpus is empty. All experiments (E1–E12) require at least one verified official document.

**Action required:** See `scripts/discover_sources.py` and `docs/official_document_checklist.md`.

### 2. `requirements.txt` listed wrong PyMuPDF version
**Status: Fixed.**  
`PyMuPDF==2.0` → `PyMuPDF==1.24.13` with `pypdf>=6.0.0` fallback.

### 3. Embedding model download on first pipeline run
The sentence-transformers multilingual-MiniLM-L12-v2 (~470 MB) is downloaded from HuggingFace on first use. Subsequent runs use the local cache. No HuggingFace account required — the model is open-weight.

### 4. `has_selectable_text=False` pages not handled
If a scanned PDF is ingested, pages with no selectable text will produce empty chunks. OCR integration (via pytesseract or fitz OCR) is listed as a future enhancement. Current guidance: only ingest PDFs with selectable text.

### 5. Table extraction limited to fitz backend
`pypdf` and `pdfplumber` fallbacks return `tables=[]`. If the fitz backend is unavailable, table structure is lost (text is still extracted). For the Bennett University regulations, most content is prose/numbered lists — tables are used for grading schemes and are lower priority.

---

## Resource Usage (measured)

| Operation | Time | Notes |
|-----------|------|-------|
| Synthetic PDF build (4 pages) | < 0.1 s | Pure Python |
| PDF extraction (4 pages, fitz) | ~0.3 s | |
| Chunking (4 pages) | ~0.05 s | |
| Embedding model cold start | ~60–90 s | Downloads ~470 MB on first run |
| Embedding model warm start | ~5 s | From cache |
| FAISS index build (10 passages) | < 1 s | |
| BM25 build (10 passages) | < 0.1 s | |
| SQLite writes (10 passages) | < 0.1 s | WAL mode |

**RAM estimate for 50-page regulation PDF (~500 passages):**
- Embedding model: ~800 MB
- FAISS index (384-dim, 500 passages): ~0.75 MB
- BM25 in-memory: ~5 MB
- Total additional RAM: ~1 GB — within 16 GB constraint.

---

## Compliance with Milestone 1 Requirements

| Requirement | Status |
|-------------|--------|
| Preserve page numbers | ✅ 1-indexed, stored in DB and passage metadata |
| Preserve passage IDs | ✅ UUIDs assigned at ingest time |
| Preserve headings | ✅ Detected and stored in `heading` field |
| Preserve document provenance | ✅ `source_url`, `filename`, SHA-256 hash |
| Preserve academic-year metadata | ✅ `academic_year`, `effective_date`, `is_current`, `superseded_by` |
| Version status | ✅ `is_current=None` = unknown; never assumed current |
| No duplicate ingestion | ✅ SHA-256 deduplication |
| Official vs upload separation | ✅ `source_type = 'official' | 'upload'` |
| No automatic document downloading | ✅ All download steps are manual |
| Do not mark unverified sources as verified | ✅ `verified=False` on all placeholders |
| Ollama integration | ✅ Configurable via `.env`; not called during ingestion |
| No large local models during ingestion | ✅ Embedding model only; no LLM loaded |

---

## Next Steps

1. Obtain official Bennett University B.Tech academic regulation PDFs manually.
2. Run `python scripts/verify_corpus.py` to confirm they are placed correctly.
3. Update `source_registry.py` with verified metadata for each document.
4. Run `python scripts/ingest_official.py --dry-run` to preview.
5. Run `python scripts/ingest_official.py` to ingest.
6. Spot-check passages: verify that page 7 in the PDF matches `page_number=7` in the database.
7. Proceed to Milestone 2 (QA dataset annotation).

