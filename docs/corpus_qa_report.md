# IndicRAG-QA — M2 Corpus QA Report

**Generated:** 2026-11-10  
**Milestone:** M2 — Document Ingestion and Corpus QA  
**Backend:** pypdf 6.21.2 (PyMuPDF DLL blocked by Application Control)

---

## Corpus Summary

| Document | Pages | Child Passages | Parent Passages | Ingestion Status | sha256 (prefix) |
|---|---|---|---|---|---|
| `Academic-Rules-for-SCSET_UG.pdf` | 20 | 34 | 8 | completed | `e5773eb92e1e2752` |
| `Notification-Minimum-Attendance.pdf` | 1 | 1 | 1 | completed | `df8f30914e33ecf5` |
| `Academic-Calendar-2026-27.pdf` | 9 | 11 | 3 | completed | `9ca6719687fbf09a` |
| `SEAS-Ordinance-Rules-Regulations-2017.pdf` | 81 | 96 | 18 | completed | `f6170bdcea0f9f37` |
| **TOTAL** | **111** | **142** | **30** | — | — |

---

## Per-Document Extraction Notes

### 1. Academic-Rules-for-SCSET_UG.pdf
- **Source:** `https://www.bennett.edu.in/wp-content/uploads/2022/03/Academic-Rules-for-SCSET_UG.pdf`
- **Pages extracted:** 20/20 ✅
- **Child passages:** 34 | **Parent passages:** 8
- **Extraction quality:** Good — section headings detected, grading table extracted, attendance rules readable.
- **Spot-checked content (confirmed present):**
  - Clause 15: "Examination/Evaluation System — continuous evaluation policy"
  - Clause 20.4: Grade table O/A+/A/B+/B/C+/C/D/F with grade points
  - Clause 30: "Attendance Requirements"
  - Clause 25: "Conditions for promotion" (CGPA-based)
  - Clause 28: "B.Tech with Minors" (CGPA 7.0 minimum)
- **Issues:** No explicit effective date on cover page. `is_current=None` — cannot confirm if superseded.

### 2. Notification-Minimum-Attendance.pdf
- **Source:** `https://www.bennett.edu.in/wp-content/uploads/2022/09/Notification-for-Minimum-Attendance-for-Students.pdf`
- **Pages extracted:** 1/1 ✅ (Remediated via ONNX-based RapidOCR)
- **Child passages:** 1 | **Parent passages:** 1
- **Extraction quality:** ✅ EXCELLENT — 33 lines of clean text extracted, validated against original high-resolution page rendering.
- **Reference & Regulatory Provisions:**
  - Notification Reference: `BU/RO/Notification/ 307/ 2022`, Date: `08th September, 2022`
  - Approved by 13th Academic Council Meeting (29 July 2022), aligned with UGC Regulations 2003.
  - Signed by Col Guljit Singh Chadha, Retd (Registrar).
  - **Key Rule:** Mandates a minimum attendance of **75%** to be eligible for End Semester Examinations effective AY 2022-23 (odd semester onwards). Biometric and CollPoll attendance marked as official records.
  - **Corpus Context:** Amends/supersedes the earlier 70% attendance requirement in Clause 30.1 of `Academic-Rules-for-SCSET_UG.pdf`.
- **Status:** **REMEDIATED & SEARCHABLE** — Registered in SQLite and indexed in BM25 and FAISS.

### 3. Academic-Calendar-2026-27.pdf
- **Source:** `https://d2xwywryb7yxbo.cloudfront.net/s3bucket-images/Academic-Calendar-2026-27.pdf`
- **Pages extracted:** 9/9 ✅
- **Child passages:** 11 | **Parent passages:** 3
- **Extraction quality:** Good — tabular date data extracted row by row.
- **Spot-checked content (confirmed present):**
  - July 2026: Registration for Even Semester Make-up Exam
  - August 2026: Freshman reporting dates
  - November 2026: Convocation (Tentative), Mid-Term mark submission
  - December 2026: Admit Card issuance, Odd Semester End Term Practical start
- **Issues:** Calendar dates extracted as plain text strings, not structured date objects. Acceptable for retrieval.

### 4. SEAS-Ordinance-Rules-Regulations-2017.pdf
- **Source:** `https://www.bennett.edu.in/wp-content/uploads/2017/08/SEAS-Ord_Rules-Reg_01-Nov.pdf`
- **Pages extracted:** 81/81 ✅
- **Child passages:** 96 | **Parent passages:** 18
- **Extraction quality:** Good — comprehensive extraction across all 81 pages.
- **Issues:**
  - `is_current=False` — historical document from 2017.
  - `superseded_by=None` — supersession by SCSET UG rules not formally confirmed; may still apply to pre-2022 students.
  - Some pages are text-heavy ordinance language with dense legal numbering — chunking may split across clause boundaries.

---

## Known Issues and Blockers

| Issue | Severity | Impact | Resolution |
|---|---|---|---|
| `Notification-Minimum-Attendance.pdf` was scanned | **RESOLVED** | Remediated via RapidOCR (ONNX runtime); 1 child passage added | Fully searchable in BM25 and FAISS |
| `Academic-Rules-for-SCSET_UG.pdf` has no effective date | MEDIUM | Cannot confirm date-based validity | Human review required |
| `SEAS-Ordinance-Rules-Regulations-2017.pdf` supersession unclear | MEDIUM | May conflict with SCSET UG rules | Human review: compare clauses |
| Paths were relative, not absolute | FIXED | DB/indexes written to repo root instead of backend/ | Fixed in `config.py` with absolute paths |
| PyMuPDF DLL blocked | LOW | Using pypdf fallback — no table structure extraction | pypdf works; tables extracted as text |

---

## Spot-Check Results

### SCSET UG Rules — attendance/exam passages present ✅
- Clause 30 "Attendance Requirements" found on page 19
- Clause 15 "Examination/Evaluation System" found on page 8
- Grade table (O=10, A+=10, A=9, B+=8 …) found on page 14
- CGPA conditions (minimum 7.5 for Honors) found on page 18

### Academic Calendar — date events present ✅
- Exam registration dates, freshman reporting, convocation, admit cards all readable

### Historical Ordinance — coverage present ✅
- 81-page document produced 96 child passages covering all major sections

---

## Retrieval Readiness

| Component | Status |
|---|---|
| BM25 index | ✅ Built — 142 child passages |
| FAISS dense index | ✅ Built — 142 embeddings (paraphrase-multilingual-MiniLM-L12-v2) |
| DB passages table | ✅ 142 child + 30 parent = 172 total rows |
| Parent-child linkage | ✅ Verified via spot-check |
| Version metadata | ✅ effective_date, academic_year, is_current, superseded_by stored per passage |

---

## Missing Documents (Human Confirmation Needed)

The following document categories from AGENT_INSTRUCTIONS.md were not acquired — they may not exist publicly, or were not found on the Bennett University website:

1. **Grading/progression amendment notices** (post-2022) — not found on registrar page
2. **Student handbook** — not found as a standalone PDF
3. **Examination policy circular** (separate from SCSET UG rules) — not found
4. **Admission/batch-specific regulation updates** — not found as public PDFs

**Recommended human action:** Check the Bennett University Registrar notices page (`https://www.bennett.edu.in/notices-registrar-office/`) for recent PDF notices that may contain attendance, grading, or exam rule updates.

---

## M1 Completion Status

| Criterion | Status |
|---|---|
| ≥1 official PDF acquired and verified | ✅ 4 PDFs |
| Source registry updated with provenance | ✅ |
| SHA-256 hashes recorded | ✅ |
| Academic year and program applicability recorded | ✅ |
| Scanned docs flagged honestly | ✅ |
| Historical vs current status flagged | ✅ |
| Documents requiring human confirmation flagged | ✅ |

**M1 status: COMPLETED** (with caveats — see human confirmation items above)

## M2 Completion Status

| Criterion | Status |
|---|---|
| PDF extraction completed | ✅ 4/4 (including remediated scanned PDF) |
| Passage counts recorded | ✅ |
| Parent-child hierarchy built | ✅ |
| Version metadata stored per passage | ✅ |
| BM25 + FAISS indexes built | ✅ |
| Spot-check of key content | ✅ |
| OCR for scanned pages | ✅ Remediated via RapidOCR (ONNX runtime) |
| Corpus QA report | ✅ This document |

**M2 status: COMPLETED** (All 4 documents fully extracted, indexed, and verified)

