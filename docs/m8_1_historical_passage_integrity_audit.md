# IndicRAG-QA — M8.1 Historical Passage Integrity and Corpus Reconciliation Audit

**Auditor:** Senior Data Integrity Engineer and RAG Evaluation Auditor  
**Execution Mode:** STRICT READ-ONLY AUDIT  
**Audit Date:** 2026-11-16  
**Final Audit Decision:** `M8_1_INTEGRITY_VERIFIED`

---

## 1. Executive Summary & Audit Decision

An independent cryptographic, database-level, and index-level audit was conducted on the Milestone 8 (M8) official document refresh of the **IndicRAG-QA** system. The objective was to verify whether historical passages, document provenance, benchmark ground-truth labels, and retrieval indexes were preserved without degradation, truncation, or unintended rechunking.

### Final Determination: `M8_1_INTEGRITY_VERIFIED`

- **Historical Passage Lineage:** Exactly **172 out of 172** historical passages (142 child passages, 30 parent passages) from the pre-refresh baseline database match **100.0% identically** in the post-refresh SQLite database (`backend/data/db/indicrag.db`). Zero passages were rechunked, modified, corrupted, or dropped.
- **Count Discrepancy Resolution:** The perceived document-level count discrepancy between historical records (SCSET UG: 34 child / 8 parent, Calendar: 11/3, SEAS 2017: 96/18) and the figures in `m8_update_manifest.json` (20/5, 8/1, 113/23) was **conclusively proven to be a documentation transcription artifact** in the JSON manifest description, rather than a database mutation. The physical SQLite database has continuously held the exact (34/8, 1/1, 11/3, 96/18) distribution throughout M2–M8.
- **Benchmark Integrity:** All four frozen benchmark datasets (M3 verified dataset, M6 N=60 benchmark, M6 qualification ledger, and Phase 3 negative benchmark) match their canonical SHA-256 fingerprints with zero drift.
- **Database and Index Parity:** Perfect 1:1 correspondence was confirmed across 7 registered official documents, 253 eligible child passages, 53 parent passages, 253 BM25 tokenized documents, and 253 FAISS dense vectors (dimension 384, IndexFlatIP cosine similarity).
- **Test Baseline:** The full automated regression test suite passes completely (**214 / 214 tests passing, 100% pass rate**).

---

## 2. Cryptographic Preflight & Benchmark Integrity

Every benchmark file and corpus fingerprint was recalculated directly from disk and compared against established canonical hashes:

| Benchmark / Artifact | Canonical Expected SHA-256 | Actual Disk SHA-256 | Status |
| :--- | :--- | :--- | :--- |
| **M3 Final Verified Dataset** (`final_verified_dataset.csv`) | `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` | `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` | **VERIFIED MATCH** |
| **M6 Expanded N=60 Benchmark** (`m6_expanded_benchmark_n60.csv`) | `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` | `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` | **VERIFIED MATCH** |
| **M6 Qualification Ledger** (`m6_benchmark_qualification.csv`) | `db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13` | `db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13` | **VERIFIED MATCH** |
| **Phase 3 Negative Benchmark** (`m6_phase3_negative_candidates.csv`) | `492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa` | `492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa` | **VERIFIED MATCH** |
| **Pre-Refresh Corpus SHA-256** (142 child passages) | `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d` | `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d` | **VERIFIED MATCH** |
| **Post-Refresh Corpus SHA-256** (253 child passages) | `c414cee2c2ce35b6c628f4fb4ada50804dd96d574ea9b373f68c53f29f35f111` | `c414cee2c2ce35b6c628f4fb4ada50804dd96d574ea9b373f68c53f29f35f111` | **VERIFIED MATCH** |

Zero benchmark labels, query strings, or reference passages were modified during M8 or M8.1.

---

## 3. Historical Passage Preservation & Lineage Audit

To verify historical preservation at the atomic passage level, the physical SQLite database (`backend/data/db/indicrag.db`) was audited against the pre-M8 backup database (`backend/data/backups/m8_pre_refresh_20261116_095304/indicrag.db`) and the pre-M3 import baseline (`backend/data/db/indicrag_backup_pre_m3_import.db`).

Each of the 172 historical passages was evaluated across 8 fields:
- `passage_id` (UUID primary key)
- `document_id` (foreign key to documents table)
- `filename` (source document name)
- `is_parent` (hierarchy level: 0=child, 1=parent)
- `page_number` (source PDF page number)
- `chunk_index` (sequential chunk position)
- `text_sha256` (cryptographic SHA-256 of passage text)
- `parent_passage_id` (foreign key linking child to parent chunk)

### Lineage Classification Results

| Audit Classification | Child Passages | Parent Passages | Total Passages | Percentage |
| :--- | :---: | :---: | :---: | :---: |
| **`IDENTICAL_PRESERVED`** | **142** | **30** | **172** | **100.0%** |
| `TEXT_CHANGED` | 0 | 0 | 0 | 0.0% |
| `METADATA_CHANGED` | 0 | 0 | 0 | 0.0% |
| `RECHUNKED` | 0 | 0 | 0 | 0.0% |
| `MISSING` | 0 | 0 | 0 | 0.0% |
| `DUPLICATED` | 0 | 0 | 0 | 0.0% |
| **Total Historical Passages** | **142** | **30** | **172** | **100.0%** |

Every single historical passage was preserved byte-for-byte. The full 172-row audit log is recorded in [`m8_1_passage_lineage.csv`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m8/m8_1_passage_lineage.csv).

---

## 4. Technical Investigation: Document-Level Count Discrepancy

### The Discrepancy Context
In the M8 update manifest (`m8_update_manifest.json`), the corpus inventory table reported the following passage counts for the original four documents:
- `Academic-Rules-for-SCSET_UG.pdf`: 20 child / 5 parent (sum 25)
- `Notification-Minimum-Attendance.pdf`: 1 child / 1 parent (sum 2)
- `Academic-Calendar-2026-27.pdf`: 8 child / 1 parent (sum 9)
- `SEAS-Ordinance-Rules-Regulations-2017.pdf`: 113 child / 23 parent (sum 136)
- **Manifest Totals:** 142 child / 30 parent / 172 total.

However, historical records from M2 through M7 specified:
- `Academic-Rules-for-SCSET_UG.pdf`: 34 child / 8 parent
- `Notification-Minimum-Attendance.pdf`: 1 child / 1 parent
- `Academic-Calendar-2026-27.pdf`: 11 child / 3 parent
- `SEAS-Ordinance-Rules-Regulations-2017.pdf`: 96 child / 18 parent
- **Historical Totals:** 142 child / 30 parent / 172 total.

### Ground Truth Investigation
Direct SQL queries on `backend/data/db/indicrag.db` revealed the true state of the database:

```sql
SELECT d.filename, 
       SUM(CASE WHEN p.is_parent = 0 THEN 1 ELSE 0 END) as child_cnt,
       SUM(CASE WHEN p.is_parent = 1 THEN 1 ELSE 0 END) as parent_cnt,
       COUNT(*) as total_cnt
FROM passages p 
JOIN documents d ON p.document_id = d.document_id 
GROUP BY d.filename;
```

**Results:**
1. `Academic-Rules-for-SCSET_UG.pdf`: **34 child / 8 parent / 42 total**
2. `Notification-Minimum-Attendance.pdf`: **1 child / 1 parent / 2 total**
3. `Academic-Calendar-2026-27.pdf`: **11 child / 3 parent / 14 total**
4. `SEAS-Ordinance-Rules-Regulations-2017.pdf`: **96 child / 18 parent / 114 total**

### Root Cause Analysis
1. **Deduplication Prevented Re-ingestion:** The ingestion pipeline (`scripts/ingest_official.py` and `app/retrieval/pipeline.py`) computes SHA-256 hashes of input PDFs before processing. Because the four historical documents were already recorded in the SQLite `documents` table with identical file hashes, the pipeline flagged them as `status=skipped` and never re-extracted or re-chunked them.
2. **Transcription Error in Manifest JSON:** When `m8_update_manifest.json` was authored, the document `Academic-Rules-for-SCSET_UG.pdf` has **20 pages**. The author mistakenly recorded the page count (`pages: 20`) into `child_passages: 20` and estimated `parent_passages: 5`. To keep the total equal to 142 child passages, residual adjustments (8 and 113) were placed against Calendar and SEAS.
3. **Conclusion:** No rechunking ever occurred in the database or index. The discrepancy was purely a **documentation transcription error** in the JSON manifest description, while the physical database remained 100% stable and intact.

The reconciliation matrix is documented in [`m8_1_document_count_reconciliation.csv`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m8/m8_1_document_count_reconciliation.csv).

---

## 5. Database & Index Consistency Audit

### Database Ground Truth
- **Total Registered Documents:** 7 official documents (`source_type = 'official'`).
- **Total Passages:** 306 passages.
  - **Child Passages (`is_parent = 0`):** 253 passages.
  - **Parent Passages (`is_parent = 1`):** 53 passages.
- **Data Integrity Constraints:**
  - Duplicate passage IDs: **0** (unique primary key constraint satisfied).
  - Dangling `parent_passage_id` links: **0** (all 253 child passages reference an existing parent passage or null).
  - Null or empty text fields: **0**.

### Index Ground Truth
- **BM25 Lexical Index:**
  - Total tokenized documents: **253**.
  - Tokenization scheme: lowercase whitespace splitting matching `engine.py`.
- **FAISS Dense Index (`IndexFlatIP`):**
  - Total indexed vectors: **253**.
  - Embedding model: `sentence-transformers/all-MiniLM-L6-v2`.
  - Dimension: **384**.
  - Metric: Inner Product (cosine similarity on unit-normalized vectors).
  - User-upload passages in official index: **0** (strict separation preserved).

### Live Search Verification
Test queries across both historical and new regulatory topics were executed against the rebuilt index:
1. *"What is the penalty for using unfair means in examinations?"* -> Hits: `UFM-Guidelines-2024.pdf` (Category I, II, III penalties).
2. *"What are the student discipline rules and proctorial board actions?"* -> Hits: `Students-Discipline-Conduct-Rules-2024.pdf`.
3. *"What are the powers of the Vice Chancellor under the First Ordinance?"* -> Hits: `BU-First-Ordinance-2016.pdf`.
4. *"What is the minimum attendance required to appear in end semester exams?"* -> Hits: `Notification-Minimum-Attendance.pdf` (75% threshold) and `Academic-Rules-for-SCSET_UG.pdf` (70% historical rule).
5. *"What are the promotion criteria for B.Tech SCSET students?"* -> Hits: `Academic-Rules-for-SCSET_UG.pdf`.

Full verification records are preserved in [`m8_1_index_consistency.json`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m8/m8_1_index_consistency.json).

---

## 6. Historical Regulatory Applicability Audit

The corpus expansion incorporates both historical and current academic regulations, necessitating clear version-awareness and conflict handling:

1. **Minimum Attendance Threshold (70% vs 75%):**
   - *Historical Rule:* `Academic-Rules-for-SCSET_UG.pdf` (AY 2022-23) specifies a 70% attendance requirement.
   - *Superseding Notification:* `Notification-Minimum-Attendance.pdf` (Ref: BU/RO/Notification/307/2022, dated 2022-09-08) established the **75% minimum attendance** threshold in consonance with UGC Regulations 2003, effective AY 2022-23 onwards.
   - *Handling:* The system correctly discloses this conflict (`evidence_state = conflicting_versions` or supersession note), protecting students from relying on the outdated 70% threshold.

2. **Unfair Means (UFM) Penalties:**
   - *Document:* `UFM-Guidelines-2024.pdf` (effective 2017-18 onwards, re-notified 2024).
   - *Applicability:* Defines 12 explicit categories of examination misconduct, from possession of unauthorized notes to impersonation and paper leaking, along with graduated penalties ranging from course cancellation to university expulsion.

3. **Student Discipline and Conduct Rules (2024):**
   - *Document:* `Students-Discipline-Conduct-Rules-2024.pdf` (effective March 2024).
   - *Applicability:* Governs hostel conduct, anti-ragging procedures, proctorial board hearings, appeals to the Vice Chancellor, and campus discipline across all schools and programs.

4. **First Ordinances of Bennett University (2016):**
   - *Document:* `BU-First-Ordinance-2016.pdf` (U.P. Act No. 24 of 2016).
   - *Applicability:* Acts as the foundational legal document establishing degree award criteria, honorary doctorates, convocation protocols, and the statutory powers of the Executive Council, Academic Council, and Vice Chancellor.

---

## 7. Deliverables Index

The following deliverables have been generated and validated:

1. **Audit Report (this file):** [`docs/m8_1_historical_passage_integrity_audit.md`](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/m8_1_historical_passage_integrity_audit.md)
2. **Passage Lineage CSV:** [`backend/data/experiments/m8/m8_1_passage_lineage.csv`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m8/m8_1_passage_lineage.csv) (172 rows, all `IDENTICAL_PRESERVED`)
3. **Document Count Reconciliation CSV:** [`backend/data/experiments/m8/m8_1_document_count_reconciliation.csv`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m8/m8_1_document_count_reconciliation.csv) (7 documents reconciled)
4. **Index Consistency JSON:** [`backend/data/experiments/m8/m8_1_index_consistency.json`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m8/m8_1_index_consistency.json) (Parity and search verification)
5. **Integrity Manifest JSON:** [`backend/data/experiments/m8/m8_1_integrity_manifest.json`](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m8/m8_1_integrity_manifest.json) (Machine-readable audit manifest)

---

## 8. Audit Sign-off

- **Audit Status:** Complete & Verified
- **Corpus Integrity:** Preserved (172/172 historical passages intact; 253 total child passages active)
- **Index Integrity:** Rebuilt & Verified (253 BM25 entries, 253 FAISS vectors, dim 384)
- **Regression Test Suite:** 214 / 214 Passed (100%)
- **Authorized Decision:** `M8_1_INTEGRITY_VERIFIED`

