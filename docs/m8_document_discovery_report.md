# IndicRAG-QA — Milestone M8: Official Document Discovery Report

**Role:** Senior Academic Regulation Researcher & Corpus Discovery Lead  
**Milestone:** M8 — Corpus Document Refresh  
**Date:** 2026-11-16  
**Status:** Complete  

---

## 1. Discovery Scope and Sources Inspected

In accordance with Section 2 of the M8 specification, discovery was conducted across the official web portals of Bennett University:

### 1.1 Registrar Office (`https://www.bennett.edu.in/notices-registrar-office/`)
- **Inspection Focus:** Academic rules, student notices, attendance notifications, student code of conduct, and academic calendars.
- **Key Findings:**
  - `STUDENTS-DISCIPLINE-AND-CONDUCT-RULES_compressed.pdf`: Published March 2024. Contains 23 pages of detailed rules on university-wide student discipline, proctorial committees, hostel rules, penalties, and appellate procedures.
  - `Academic-Rules-for-SCSET_UG.pdf`: March 2022 edition remains the current linked document for undergraduate B.Tech rules in SCSET.
  - `Notification-for-Minimum-Attendance-for-Students.pdf`: September 2022 notification (Ref 307/2022) establishing 75% minimum attendance remains active and unamended.
  - Academic Calendars: Past calendars for 2024-25 and 2025-26 inspected; AY 2026-27 calendar remains the furthest future official calendar.

### 1.2 Rules, Regulations, Statutes and Ordinances (`https://www.bennett.edu.in/ordinances-statutes-rules-and-regulations/`)
- **Inspection Focus:** First Ordinances, Ordinance amendments, and statutory frameworks.
- **Key Findings:**
  - `BU-First-Ordinance-2016.pdf`: Re-hosted in May 2024. 55 pages covering foundational university-wide statutory provisions under UP Act No 24 of 2016, Clause 29 (admissions, degree requirements, programs of study, medium of instruction, medals).

### 1.3 Examination Department (`https://www.bennett.edu.in/examination-department/`)
- **Inspection Focus:** Examination manuals, rules, unfair means notifications, and makeup examination policies.
- **Key Findings:**
  - `UFM.pdf` (`UFM-Guidelines-2024.pdf`): Published May 2024. 7 pages setting out Instructions and Penalty for Use of Unfair Means (UFM categories 2.1 to 2.6, penalties, reporting forms).
  - `Exam-Manual.pdf`: 40 pages scanned manual uploaded May 2024. Quarantined for dedicated batch OCR due to image-only format.

---

## 2. Discovered Documents Inventory & Classification

Every discovered document was evaluated against the formal taxonomy:

| Document Title | Local Filename | URL | Pages | Category | Classification | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Academic Rules for SCSET UG** | `Academic-Rules-for-SCSET_UG.pdf` | `.../2022/03/Academic-Rules-for-SCSET_UG.pdf` | 20 | Rules | `UNCHANGED` | Preserved in Corpus |
| **Minimum Attendance Notification** | `Notification-Minimum-Attendance.pdf` | `.../2022/09/Notification-for-Minimum-Attendance...` | 1 | Notice | `UNCHANGED` | Preserved in Corpus |
| **Academic Calendar 2026-27** | `Academic-Calendar-2026-27.pdf` | `.../s3bucket-images/Academic-Calendar-2026-27.pdf` | 9 | Calendar | `UNCHANGED` | Preserved in Corpus |
| **SEAS Ordinances 2017** | `SEAS-Ordinance-Rules-Regulations-2017.pdf` | `.../2017/08/SEAS-Ord_Rules-Reg_01-Nov.pdf` | 81 | Ordinance | `HISTORICAL` | Preserved in Corpus |
| **Students' Discipline & Conduct** | `Students-Discipline-Conduct-Rules-2024.pdf` | `.../2024/03/STUDENTS-DISCIPLINE-AND-CONDUCT...` | 23 | Conduct | `NEW_DOCUMENT` | **Approved & Ingested** |
| **First Ordinances of BU** | `BU-First-Ordinance-2016.pdf` | `.../2024/05/BU-First-Ordinance-2016.pdf` | 55 | Ordinance | `NEW_DOCUMENT` | **Approved & Ingested** |
| **Unfair Means (UFM) Guidelines** | `UFM-Guidelines-2024.pdf` | `.../2024/05/UFM.pdf` | 7 | Exam Rules | `NEW_DOCUMENT` | **Approved & Ingested** |
| **Examination Manual** | `Exam-Manual.pdf` | `.../2024/05/Exam-Manual.pdf` | 40 | Manual | `UNVERIFIED` | Quarantined (Batch OCR) |
| **Academic Calendar 2024-25** | `Academic-Calender-2024-25.pdf` | `.../2024/06/Academic-Calender-2024-25.pdf` | 6 | Calendar | `HISTORICAL` | Quarantined (Preceding) |
| **Academic Calendar 2025-26** | `Academic-Calendar-2025-26.pdf` | `.../2025/07/Academic-Calendar-for-A.Y.-2025-26...` | 7 | Calendar | `HISTORICAL` | Quarantined (Preceding) |

---

## 3. Provenance and Cryptographic Verification

All documents were validated via SHA-256 and byte-length verification directly from official server responses. No documents were obtained from third-party or unverified mirrors.

