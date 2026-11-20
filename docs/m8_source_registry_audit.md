# IndicRAG-QA — Milestone M8: Source Registry Audit Report

**Role:** Senior Metadata and Document Intelligence Auditor  
**Milestone:** M8 — Corpus Document Refresh  
**Date:** 2026-11-16  
**Status:** Complete  

---

## 1. Registry Schema Compliance

The official registry at `backend/app/ingestion/source_registry.py` defines each source entry using the canonical `SourceEntry` schema:

```python
@dataclass
class SourceEntry:
    filename: str
    title: str
    description: str
    source_url: Optional[str] = None
    effective_date: Optional[str] = None
    academic_year: Optional[str] = None
    program_applicability: list[str] = field(default_factory=list)
    superseded_by: Optional[str] = None
    supersedes: Optional[str] = None
    is_current: Optional[bool] = None
    verified: bool = False
    notes: str = ""
```

---

## 2. Audit of Registered Entries

All 7 entries in the updated registry were verified:

1. **`Academic-Rules-for-SCSET_UG.pdf`**
   - **Title:** Academic Rules for Undergraduate Programs — SCSET
   - **Academic Year:** 2022-23 | **Effective Date:** Unstated on cover (inferred August 2022)
   - **Scope:** B.Tech SCSET
   - **Current Status:** `is_current = None` (Active rulebook for B.Tech cohorts)
   - **Verified:** `True`

2. **`Notification-Minimum-Attendance.pdf`**
   - **Title:** Notification for Minimum Attendance for Students (Ref No: BU/RO/Notification/307/2022)
   - **Effective Date:** 2022-09-08 | **Academic Year:** 2022-23 onwards
   - **Scope:** B.Tech, Undergraduate, All Students
   - **Current Status:** `is_current = True` (Current authoritative attendance policy: 75%)
   - **Verified:** `True`

3. **`Academic-Calendar-2026-27.pdf`**
   - **Title:** Academic Calendar for A.Y. 2026-27
   - **Effective Date:** 2026-07-01 | **Academic Year:** 2026-27
   - **Scope:** All Students
   - **Current Status:** `is_current = True`
   - **Verified:** `True`

4. **`SEAS-Ordinance-Rules-Regulations-2017.pdf`**
   - **Title:** Ordinances, Rules and Regulations for UG Engineering Programs — 2017 Onwards
   - **Effective Date:** 2017-11-01 | **Academic Year:** 2017-18
   - **Scope:** B.Tech (2017 cohort)
   - **Current Status:** `is_current = False` (Historical baseline, partially superseded)
   - **Verified:** `True`

5. **`Students-Discipline-Conduct-Rules-2024.pdf` [NEW]**
   - **Title:** Students' Discipline and Conduct Rules (2024)
   - **Effective Date:** 2024-03-01 | **Academic Year:** 2023-24 onwards
   - **Scope:** All Students across all schools and programs
   - **Current Status:** `is_current = True`
   - **Verified:** `True`

6. **`BU-First-Ordinance-2016.pdf` [NEW]**
   - **Title:** First Ordinances of Bennett University (U.P. Act No 24 of 2016)
   - **Effective Date:** 2016-09-01 | **Academic Year:** 2016-17 onwards
   - **Scope:** University-wide (B.Tech, MBA, PhD)
   - **Current Status:** `is_current = True` (Foundational statutory governance)
   - **Verified:** `True`

7. **`UFM-Guidelines-2024.pdf` [NEW]**
   - **Title:** Instructions and Penalty for Use of Unfair Means (UFM)
   - **Effective Date:** 2017-12-11 | **Academic Year:** 2017-18 onwards
   - **Scope:** All Students appearing in examinations
   - **Current Status:** `is_current = True`
   - **Verified:** `True`

---

## 3. Physical Directory and Registry Reconciliation

Running `python scripts/verify_corpus.py`:
- Registered entries: 7
- PDF files in `backend/data/official/`: 7
- Unregistered files: 0
- Missing registered files: 0
- Hash mismatch: 0
- Verification result: **ALL ENTRIES AUDITED AND SYNCHRONIZED**.

