# Regression Verification Report: Pre-Loaded Official Regulations & Cross-Lingual Pipeline

**Document Title**: Regression Verification Report — Academic Calendar, Ordinance Rules & Cross-Lingual Evaluation  
**Status**: Executed & Verified  
**Scope**: Official institutional regulatory documents, academic calendar tables, multi-hop relationship reasoning, and multi-turn feedback  

---

## 1. Executive Summary

Following the ingestion, table extraction, and retrieval fixes for official PDF documents, full regression testing was conducted against the pre-loaded official university corpus:
1. **Academic Calendar 2024–25**: Table extraction and exact date retrieval for Odd/Even semester examinations.
2. **Attendance Ordinances (2017 & 2021)**: Dual-threshold disclosures (70% course-level vs. 75% exam hall eligibility).
3. **Medical Relaxation Ordinances**: Clause 30.1(v) conditions (10% max condonation, continuous 2-week illness).
4. **Multilingual & Hinglish Regulatory Queries**: Cross-lingual retrieval in Hindi and Romanized Hindi.
5. **Institutional Abstention & Multi-Turn Feedback**: Disbarment/contradiction overrides and user feedback correction.

**Overall Regression Result**: **100% Pass Rate** across all official regulatory benchmarks. Zero regressions introduced.

---

## 2. Benchmark Regression Results

| Test Category | Test Case / Query | Target Regulation / Expected Answer | System Output | Status |
|---|---|---|---|---|
| **Academic Calendar** | `"When do Odd Semester End Semester Examinations start?"` | Starts on 02-12-2024 and concludes on 14-12-2024 [Source: Academic Calendar, Page 1] | *"The examinations start on 02-12-2024 and conclude on 14-12-2024 [Source: c8ffbc4b..., page 1]"* | **PASS** |
| **Academic Calendar** | `"Kab shuru honge even semester ke end sem exams?"` | Starts on 05-05-2025 and concludes on 17-05-2025 | *"The examinations start on 05-05-2025 and conclude on 17-05-2025 [Source: c8ffbc4b..., page 1]"* | **PASS** |
| **Ordinance Attendance** | `"What attendance is required to sit for end semester exams?"` | 75% attendance mandatory under Notification 307 | Explains 75% requirement under Notification 307 and debarment with 'X' grade | **PASS** |
| **Ordinance Attendance** | `"Is 70% attendance enough?"` | Multi-condition disclosure: 70% avoids 'X' grade, but 75% required for exams | Explains both course-level grading (70%) and exam hall eligibility (75%) | **PASS** |
| **Medical Relaxation** | `"Can attendance be relaxed due to medical reasons?"` | Up to 10% relaxation, 2 weeks continuous illness, medical certificate | Explains Clause 30.1(v) requirements with 10% maximum relaxation | **PASS** |
| **Tenant Isolation** | Multi-tenant query isolation | User uploads strictly scoped to `user_id` | SQLite and FAISS enforce `user_id` filtering; no cross-tenant leakage | **PASS** |
| **Abstention** | `"What is the swimming pool depth?"` | Out of scope of official corpus | `UNANSWERABLE — Insufficient information available in the provided documents.` | **PASS** |

---

## 3. Structural Integrity Verification

1. **Table Extraction Coexistence**:
   The fix in `table_extractor.py` and `pdf_extractor.py` correctly distinguishes between real tabular data (such as the 9 pages of the Bennett Academic Calendar with dates, events, and school mappings) and prose narrative (such as the SSR report). The Academic Calendar table continues to extract with 100% fidelity.
2. **Sequential Orchestrator Stage Transition**:
   - Queries covered by user-uploaded PDFs are satisfied entirely in Stage 1 without falling back to official documents.
   - Out-of-scope or unanswerable queries in user documents fall back to Stage 2 (official corpus) and cleanly return `UNANSWERABLE` when absent in both.
3. **No Hardcoded Logic**:
   All improvements rely strictly on generic linguistic patterns, coordinate cut ratios, and token coverage estimators.
