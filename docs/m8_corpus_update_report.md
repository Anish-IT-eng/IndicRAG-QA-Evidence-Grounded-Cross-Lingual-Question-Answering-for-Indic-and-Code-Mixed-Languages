# IndicRAG-QA — Milestone M8: Corpus Update Report

**Role:** Senior RAG Ingestion & Pipeline Reliability Engineer  
**Milestone:** M8 — Corpus Document Refresh  
**Date:** 2026-11-16  
**Status:** Complete  

---

## 1. Corpus Expansion Breakdown

The ingestion pipeline executed deterministic structure-aware chunking for all approved documents, creating parent and child passages while preserving historical passages.

### Summary Metrics:

| Metric | Pre-Refresh (M7) | Added in M8 | Post-Refresh Total (M8) | Growth |
| :--- | :--- | :--- | :--- | :--- |
| **Official Documents** | 4 | +3 | **7** | +75.0% |
| **Total Ingested Pages** | 111 | +85 | **196** | +76.58% |
| **Total Passages in SQLite** | 172 | +134 | **306** | +77.91% |
| **Child Passages (Indexed)** | 142 | +111 | **253** | +78.17% |
| **Parent Passages (PDR Context)** | 30 | +23 | **53** | +76.67% |
| **Deduplicated / Skipped Files** | 0 | 4 | 4 | 100% deduplication |

---

## 2. Ingestion Details by Document

1. **`Students-Discipline-Conduct-Rules-2024.pdf`**
   - Ingestion method: Native digital text extraction via PyMuPDF (fitz).
   - Pages extracted: 23 pages (47,754 characters).
   - Chunks generated: 6 parent chunks, 41 child chunks = 47 passages.
   - Status: `COMPLETED`.

2. **`BU-First-Ordinance-2016.pdf`**
   - Ingestion method: Native digital text extraction via PyMuPDF (fitz).
   - Pages extracted: 55 pages (118,120 characters).
   - Chunks generated: 15 parent chunks, 61 child chunks = 76 passages.
   - Status: `COMPLETED`.

3. **`UFM-Guidelines-2024.pdf`**
   - Ingestion method: PyMuPDF + RapidOCR (all 7 pages scanned images).
   - Pages recovered: 7 pages (100% recovery, 12,050 characters).
   - Chunks generated: 2 parent chunks, 9 child chunks = 11 passages.
   - Status: `COMPLETED`.

4. **Historical Cohort (4 documents)**
   - `Academic-Rules-for-SCSET_UG.pdf` (25 passages) -> `SKIPPED` (hash match).
   - `Notification-Minimum-Attendance.pdf` (2 passages) -> `SKIPPED` (hash match).
   - `Academic-Calendar-2026-27.pdf` (9 passages) -> `SKIPPED` (hash match).
   - `SEAS-Ordinance-Rules-Regulations-2017.pdf` (136 passages) -> `SKIPPED` (hash match).

---

## 3. Cryptographic Corpus Fingerprints

- **Pre-Refresh Corpus SHA-256 (142 child passages):**  
  `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d`
- **Post-Refresh Corpus SHA-256 (253 child passages):**  
  `c414cee2c2ce35b6c628f4fb4ada50804dd96d574ea9b373f68c53f29f35f111`

