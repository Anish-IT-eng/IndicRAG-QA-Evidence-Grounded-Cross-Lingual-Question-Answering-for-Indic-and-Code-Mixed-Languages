# IndicRAG-QA — Milestone M8: Official Corpus Document Refresh & Repository Expansion Report

**Role:** Senior RAG Ingestion Engineer, Provenance Auditor, and Evidence Reliability Lead  
**Milestone:** M8 — Corpus Document Refresh and Official Repository Expansion  
**Date:** 2026-11-16  
**Final Status:** `M8_DOCUMENT_REFRESH_COMPLETED`  

---

## 1. Executive Summary

Milestone M8 successfully updated the official IndicRAG-QA regulatory corpus with latest authoritative documents from Bennett University's official web domain (`bennett.edu.in`) and its verified CDN endpoints.

All operations strictly adhered to the research protocol:
- **Historical Document Preservation:** 100% of historical documents (4/4) and their SQLite database records were preserved without overwriting, modifying, or resetting.
- **Benchmark Dataset Preservation:** All frozen evaluation datasets (M3 verified dataset, M6 expanded 60-query benchmark, M6 qualification ledger, and M6 Phase 3 negative benchmark) were verified byte-for-byte unchanged against their canonical SHA-256 fingerprints.
- **Provenance Verification:** All prospective documents were authenticated against `bennett.edu.in` and validated for page counts, digital text extractability, and SHA-256 content hashes.
- **Deduplication:** Hash-based deduplication verified that all 4 existing documents were safely skipped, preventing duplicate entries.
- **Corpus Expansion:** 3 newly approved official documents (85 pages total) were ingested through the structure-aware chunking pipeline (digital extraction and RapidOCR), creating 134 new passages (111 child retrieval units, 23 parent context units).
- **Index Rebuild:** BM25 and dense FAISS indexes were rebuilt and verified over all 253 child passages (dimension: 384).
- **Regression Testing:** The complete test suite of 197 tests passed cleanly (100% pass rate).

---

## 2. Integrity and Provenance Preflight

### 2.1 Benchmark Preservation Audit

Prior to and following the corpus update, all canonical evaluation datasets were audited for cryptographic integrity:

| Benchmark Dataset | File Path | Canonical Expected SHA-256 | Actual Post-Refresh SHA-256 | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| **M3 Final Verified Dataset** | `backend/data/dataset/final_verified_dataset.csv` | `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` | `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` | **VERIFIED INTACT** |
| **M6 Expanded Benchmark (N=60)** | `backend/data/dataset/m6_expanded_benchmark_n60.csv` | `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` | `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` | **VERIFIED INTACT** |
| **M6 Qualification Ledger** | `backend/data/dataset/m6_benchmark_qualification.csv` | `db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13` | `db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13` | **VERIFIED INTACT** |
| **Phase 3 Negative Benchmark** | `backend/data/dataset/m6_phase3_negative_candidates.csv` | `492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa` | `492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa` | **VERIFIED INTACT** |

### 2.2 Canonical Corpus Fingerprint Evolution

Corpus child passage SHA-256 calculation (`SELECT passage_id, text FROM passages WHERE parent_passage_id IS NOT NULL ORDER BY passage_id`):
- **Pre-Refresh Baseline (142 child passages):** `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d`
- **M8 Post-Refresh Canonical (253 child passages):** `c414cee2c2ce35b6c628f4fb4ada50804dd96d574ea9b373f68c53f29f35f111`

---

## 3. Official Source Discovery and Provenance Audit

Live discovery on `bennett.edu.in` evaluated the Bennett University Registrar notices, Examination Department publications, and university ordinances:

### 3.1 Newly Approved Official Documents (Added)

1. **`Students-Discipline-Conduct-Rules-2024.pdf`**
   - **Title:** Students' Discipline and Conduct Rules (2024)
   - **Originating Authority:** Vice Chancellor, Bennett University (under BU Statutes)
   - **Canonical URL:** `https://www.bennett.edu.in/wp-content/uploads/2024/03/STUDENTS-DISCIPLINE-AND-CONDUCT-RULES_compressed.pdf`
   - **Publication Date:** March 2024 | **Effective:** AY 2023-24 onwards
   - **Scope:** All Students across all schools (SCSET, SOL, SOM, etc.)
   - **Physical Specs:** 23 pages, 223,636 bytes, 47,754 characters of clean digital text
   - **SHA-256:** `1325facb0517e640ebf634e8d30ffe3d2fcd1122a676e7cfba49db9a8fa3bb2d`
   - **Ingestion Result:** 6 parent chunks, 41 child chunks (47 total passages)
   - **Document ID:** `f110a0e9-e299-4f4a-9dd9-b879ecbbdc36`

2. **`BU-First-Ordinance-2016.pdf`**
   - **Title:** First Ordinances of Bennett University (U.P. Act No 24 of 2016)
   - **Originating Authority:** State Legislature of Uttar Pradesh & Bennett University Court/Council (under clause 29 of Act 24 of 2016)
   - **Canonical URL:** `https://www.bennett.edu.in/wp-content/uploads/2024/05/BU-First-Ordinance-2016.pdf`
   - **Publication / Re-host Date:** May 2024 | **Effective:** 2016-09-01 onwards
   - **Scope:** University-wide foundational statutory governance (Admissions, Degrees, B.Tech, MBA, PhD, Medals, Fees)
   - **Physical Specs:** 55 pages, 731,965 bytes, 118,120 characters of clean digital text
   - **SHA-256:** `b657822edb6148b7e9b6a276b9065dab1f9d66bd4a81a58432f425498e47be05`
   - **Ingestion Result:** 15 parent chunks, 61 child chunks (76 total passages)
   - **Document ID:** `8e3b751a-5728-4af0-bf6c-5418b578af7b`

3. **`UFM-Guidelines-2024.pdf`**
   - **Title:** Instructions and Penalty for Use of Unfair Means (UFM)
   - **Originating Authority:** Examination Department, Bennett University
   - **Canonical URL:** `https://www.bennett.edu.in/wp-content/uploads/2024/05/UFM.pdf`
   - **Publication / Re-host Date:** May 2024 | **Effective:** 2017-12-11 onwards
   - **Scope:** All University End-Term, Mid-Term, and Practical Examinations
   - **Physical Specs:** 7 pages, 4,926,812 bytes, scanned document
   - **OCR Extraction:** 7/7 pages extracted via RapidOCR (100% recovery)
   - **SHA-256:** `450363b66826637de2123c86570d571d11c3dde576bab890b278143d60768f04`
   - **Ingestion Result:** 2 parent chunks, 9 child chunks (11 total passages)
   - **Document ID:** `d741f37d-c2db-4463-b9fa-fe59ab749960`

---

### 3.2 Historical Documents Preserved (Unchanged)

| Document Filename | Status | Original Pages | Total Passages | Child Passages | SHA-256 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Academic-Rules-for-SCSET_UG.pdf` | Current B.Tech Rules (AY 2022-23) | 20 | 25 | 20 | `787c88b0eb03e5c70bb8d591b61905307b0ecdaecb700f074d0ea203b8e4e082` |
| `Notification-Minimum-Attendance.pdf` | Current Attendance Notification (Ref 307/2022) | 1 | 2 | 1 | `81f181be3c42e975a6c66cf1bb2a842f10b777a8fcff92ffdc39f285fb70c8ad` |
| `Academic-Calendar-2026-27.pdf` | Latest Academic Calendar (AY 2026-27) | 9 | 9 | 8 | `e36e6ba6fcbf2a35368a5ca4eb3bca4fdf2463e26084931a0e14a275e7a9121a` |
| `SEAS-Ordinance-Rules-Regulations-2017.pdf` | Historical Ordinances (AY 2017-18) | 81 | 136 | 113 | `cffb041cfdd924f707f1859bf557924c5ddccce5c678516d2eaec4b5b7863e46` |

All 4 files matched existing records in `backend/data/db/indicrag.db` and were skipped automatically by content hash deduplication.

---

### 3.3 Quarantined & Preceding Documents Evaluated

| Candidate Filename | Evaluated Source URL | Pages | Assessment & Quarantine Justification |
| :--- | :--- | :--- | :--- |
| `Exam-Manual.pdf` | `https://www.bennett.edu.in/wp-content/uploads/2024/05/Exam-Manual.pdf` | 40 | **QUARANTINED:** 40-page image-only scan without selectable text. Ingestion deferred to dedicated offline batch OCR to maintain pipeline efficiency. Substantive exam hall rules and penalties are covered by `UFM-Guidelines-2024.pdf`. |
| `Academic-Calender-2024-25.pdf` | `https://www.bennett.edu.in/wp-content/uploads/2024/06/Academic-Calender-2024-25.pdf` | 6 | **NOT INGESTED:** Calendar for AY 2024-25. Preceded by current AY 2026-27 calendar already present in corpus. |
| `Academic-Calendar-for-A.Y.-2025-26...` | `https://www.bennett.edu.in/wp-content/uploads/2025/07/Academic-Calendar-for-A.Y.-2025-26-All-Returning-Students_Updated.pdf` | 7 | **NOT INGESTED:** Calendar for AY 2025-26. Preceded by current AY 2026-27 calendar already present in corpus. |

---

## 4. Ingestion, Chunking & Deduplication Metrics

The pipeline processed all verified documents using parent-child structure-aware chunking:
- **Parent Chunks:** Broad context sections (major headings, statutory articles).
- **Child Chunks:** Granular operational retrieval units (individual clauses, sub-clauses, specific penalties).

```
================================================================================
                    Corpus Passage Expansion Breakdown
================================================================================
Metric                      Pre-Refresh (M0-M7)    Added (M8)    Post-Refresh Total
Total Documents                     4                  +3                7
Total Pages Ingested              111                 +85              196
Total Passages                    172                +134              306
  - Child Passages (Index units)  142                +111              253
  - Parent Passages (PDR units)    30                 +23               53
================================================================================
```

---

## 5. Index Rebuild & Retrieval Verification

### 5.1 Index Architecture

The official hybrid index was rebuilt from scratch across all 253 child passages:
- **Lexical Index:** BM25Okapi over whitespace-normalized lowercased tokens (253 passages).
- **Dense Vector Index:** FAISS `IndexFlatIP` (inner product cosine similarity after L2 normalization), dimension = 384, total vectors = 253.
- **Embedding Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.

### 5.2 Retrieval Sanity Testing

Retriever performance was verified across both historical and new regulatory topics:

1. **Attendance Policy (`"What is the minimum attendance requirement?"`)**
   - Retrieves `SEAS-Ordinance-Rules-Regulations-2017.pdf` Clause 30 (70% attendance) alongside `Notification-Minimum-Attendance.pdf` (75% attendance).
   - Preserves version conflict detection for downstream evidence controller.
2. **Unfair Means (`"What are the penalties for unfair means during examinations?"`)**
   - Correctly retrieves `UFM-Guidelines-2024.pdf` Page 6 and Section V of 2017 regulations.
3. **Student Discipline (`"What is the role of the Proctorial Committee in student discipline?"`)**
   - Retrieves `Students-Discipline-Conduct-Rules-2024.pdf` Pages 4 and 5 detailing proctorial inquiry powers and suspension authority.
4. **Degree Requirements (`"What are the requirements for the award of a B.Tech degree in the First Ordinances?"`)**
   - Retrieves `BU-First-Ordinance-2016.pdf` Page 16 (Ordinance 4C) establishing statutory credit requirements and minimum CGPA criteria.

---

## 6. Regression Testing & Reliability Verification

Following corpus expansion and index updates, the test suite was executed:
- **Baseline Test Suite:** 197 tests in `backend/tests/`.
- **Pass Rate:** 197 / 197 passing (100.0%).
- **Failures / Errors:** 0.

Key areas verified:
- API endpoint health, document listing, and query execution.
- SQLite schema integrity and passage-to-parent foreign key resolution.
- PDF extraction with PyMuPDF and RapidOCR fallback.
- BM25, FAISS, and hybrid RRF ranking bounds.
- Evidence controller six-state classification contract (`SUFFICIENT`, `PARTIALLY_SUFFICIENT`, `INSUFFICIENT`, `CONTRADICTORY`, `CONFLICTING`, `CLARIFICATION_REQUIRED`).
- Cross-lingual queries (Hindi, Hinglish, Romanized Hindi, English).
- Claim-level citation validation and numeric verification (preventing UUID / passage ID false contradictions).

---

## 7. Artifacts & Audit Files Created

1. **Source Registry:** `backend/app/ingestion/source_registry.py` (updated with 3 new verified entries).
2. **Experiment Manifest:** `backend/data/experiments/m8/m8_update_manifest.json` (machine-readable audit trail).
3. **Corpus Hash Script:** `scripts/compute_m8_corpus_fingerprint.py` (fingerprint & benchmark verification).
4. **Verification Script:** `backend/data/temp_m8/verify_m8.py` (SQLite, index, and retrieval validation).
5. **Milestone Report:** `docs/m8_document_refresh_report.md` (this report).

---

## 8. Final Decision

$$\mathbf{M8\_DOCUMENT\_REFRESH\_COMPLETED}$$

The official IndicRAG-QA corpus has been refreshed with authoritative documents from Bennett University, historical documents and evaluation benchmarks remain preserved, retrieval operates over 253 structure-aware passages, and all 197 regression tests pass.

