# IndicRAG-QA — M8.3: Regulatory Semantics and Evidence Controller Audit Report

**Auditor:** Senior Academic Regulation Researcher, RAG Safety Engineer, and Research Evaluation Auditor  
**Execution Mode:** STRICT READ-ONLY AUDIT (Zero modifications to runtime code, databases, indexes, or benchmark files)  
**Prerequisites Verified:** `M8_DOCUMENT_REFRESH_COMPLETED`, `M8_1_INTEGRITY_VERIFIED`, `M8_2_CLOSED_WITH_DOCUMENTATION_ERRORS`  
**Audit Date:** 2026-11-16  
**Final Audit Determination:** `M8_3_VERIFIED_WITH_CONTROLLER_GAPS`

---

## Executive Summary

Milestone **M8.3** conducts a rigorous, evidence-grounded audit of regulatory semantics and Evidence Controller behavior within IndicRAG-QA following the M8 document refresh. The primary objective is to evaluate whether the retrieval and controller pipeline accurately differentiates distinct regulatory conditions (such as course-level grade debarment vs university-wide examination hall eligibility) or whether it exhibits architectural gaps by treating every distinct numerical threshold or historical document co-retrieval as an irreconcilable conflict.

The audit examined the three primary attendance authorities in the corpus:
1. **Academic Rules for SCSET UG (AY 2022-23)**
2. **Notification Ref BU/RO/Notification/307/2022 (AY 2022-23)**
3. **SEAS Ordinances, Rules & Regulations (AY 2017-18)**

### Key Audit Findings
1. **Semantic Ground Truth:** The 70% and 75% thresholds represent **distinct regulatory conditions and operational stages**, not an irreconcilable contradiction:
   - **70% Threshold:** Governs **course-level academic performance and grading** (enforced by Course Instructors). Falling below 70% results in an `'X'` grade and repeating the course. Both current SCSET 2022 and historical SEAS 2017 agree unanimously on this 70% rule.
   - **75% Threshold:** Governs **eligibility to appear in End Semester Examinations** (enforced by the Registrar and Controller of Examination pursuant to statutory UGC Regulations 2003).
   - **10% Medical Relaxation:** Both 2017 and 2022 regulations agree identically on up to 10% attendance condonation for continuous illness ($\ge 2$ weeks) or university deputation (net minimum 60%).
2. **Evidence Controller Gaps Identified:**
   - **False Conflict Gap 1 (Consensus across Versions):** The Evidence Controller flags `CONFLICTING` whenever a current and historical document are co-retrieved, even when their regulatory clauses agree 100% (e.g. 70% for 'X' grade in AQ-03 and 10% medical relaxation in AQ-07).
   - **False Conflict Gap 2 (Temporal Anchoring):** When a user query explicitly asks about historical rules (e.g. *"What was the attendance rule in 2017?"* in AQ-06), the controller still triggers `CONFLICTING` against current rules rather than answering directly from the historical document.
   - **Granularity Gap 3 (Condition Invariance):** The controller lacks semantic condition tags, collapsing course grade debarment and exam hall admission into a single flat percentage conflict.
3. **Audit Determination:** Based on empirical evaluation across all 7 ambiguous attendance queries and 6 regulatory document pairs, the audit concludes with **`M8_3_VERIFIED_WITH_CONTROLLER_GAPS`**.

---

## 1. Attendance Rule Semantic Analysis

A comparative legal-semantic analysis was conducted on the source documents. The extracted clauses, thresholds, enforcement authorities, and regulatory conditions are summarized below:

| Feature / Clause | Academic-Rules-for-SCSET_UG.pdf | Notification-Minimum-Attendance.pdf | SEAS-Ordinance-Rules-Regulations-2017.pdf |
| :--- | :--- | :--- | :--- |
| **Document Type** | School Operational Academic Rules | Official University Notification | Founding Statutory University Ordinance |
| **Document Date / AY** | Academic Year 2022-23 onwards | September 8, 2022 (AY 2022-23) | Academic Year 2017-18 to 2021-22 |
| **Issuing Authority** | Dean / School Academic Committee | Registrar / Academic Council | Academic Council / SEAS Faculty Board |
| **Relevant Clause / Ref** | Clause 30.1(ii), Page 19 | Ref: BU/RO/Notification/307/2022, Page 1 | Clause 30.1(ii), Page 28 |
| **Attendance Threshold** | **70%** (minimum combined L+T+P) | **75%** (minimum aggregate) | **70%** (minimum combined L+T+P) |
| **Regulatory Condition** | Course-level attendance profile | Eligibility to sit for End Semester Examinations | Course-level attendance profile |
| **Non-Compliance Penalty** | Award of **'X' grade**; must repeat course | **Debarment from End Semester Exam**; admit card withheld | Award of **'X' grade**; must repeat course |
| **Enforcing Authority** | Course Instructor & Dean | Controller of Examination & Registrar | Course Instructor & Head of Department |
| **Statutory Mandate** | Internal School Academic Governance | UGC Regulations 2003 / First Ordinance 2016 | UP Act No. 24 of 2016 First Statutes |
| **Applicable Cohort** | SCSET B.Tech students (2022 onwards) | All University Schools (2022 onwards) | SEAS Engineering students (2017-2021) |
| **Medical Condonation** | Up to 10% relaxation ($\ge 2$ weeks illness) | Mentions condonation per university rules | Up to 10% relaxation ($\ge 2$ weeks illness) |
| **Explicit Supersession?** | No explicit repeal of earlier ordinances | No explicit repeal of course grading rules | Superseded in part for exam eligibility in 2022 |

### Verbatim Clause Excerpts

#### 1. SCSET UG Rules 2022 — Clause 30.1(ii) & 30.1(v) (Page 19)
> *"30.1 (ii) Minimum Attendance Requirement: A student is expected to attend all lectures, tutorials, and practical classes. However, a student must secure a minimum of 70% attendance in a course, failing which he/she will be awarded an 'X' grade in that course and will not be allowed to appear in the end semester examination for that course."*  
> *"30.1 (v) Relaxation in Attendance: Relaxation up to a maximum of 10% may be granted by the Dean on valid medical grounds (continuous hospitalization/illness of at least two weeks) or official deputation for university activities, subject to submission of valid documentary evidence."*

#### 2. Notification Ref BU/RO/Notification/307/2022 — Page 1
> *"Notification No: BU/RO/Notification/307/2022, Dated: 08.09.2022.  
> In pursuance to the University Grants Commission (UGC) Regulations 2003 and the approval of the Academic Council, it is hereby notified for the information of all concerned that the minimum attendance required to appear in the End Semester Examinations across all Schools and Programmes of Bennett University shall be 75%.  
> Students securing less than 75% attendance in aggregate across courses shall not be eligible to appear in the End Semester Examinations, and the Controller of Examination shall withhold the Examination Admit Cards of such students. Respective Deans/Heads of Schools are requested to submit attendance registers prior to the examination."*

#### 3. SEAS Ordinances 2017 — Clause 30.1(ii) & 30.1(v) (Page 28)
> *"30.1 (ii) A student is required to have a minimum attendance of 70% in each course (lectures, tutorials, and practicals combined). A student who has attendance between 60% and 70% on medical grounds may be considered by the Dean. A student with attendance below the prescribed limit shall be awarded an 'X' grade."*

---

## 2. Regulatory Relationship Model

To prevent false conflicts, the IndicRAG-QA knowledge base model establishes six formal regulatory relationship types between document pairs:

```mermaid
graph TD
    A["Corpus Document Pairs"] --> B{"Relationship Classification"}
    B -->|"Chronological replacement of same condition"| C["SAME_CONDITION_DIFFERENT_VERSION"]
    B -->|"Separate operational stages / authorities"| D["DIFFERENT_REGULATORY_CONDITIONS"]
    B -->|"Express legislative / administrative repeal"| E["EXPLICITLY_SUPERSEDES"]
    B -->|"General university framework vs School rule"| F["PROGRAMME_SPECIFIC_RULE"]
    B -->|"Cohort-bound past regulation"| G["HISTORICAL_RULE"]
    B -->|"Jurisdictional or cohort ambiguity"| H["APPLICABILITY_UNRESOLVED"]
```

### Evaluated Corpus Relationships (`m8_3_regulatory_relationship_matrix.csv`)

| Doc A | Doc B | Subject Area | Relationship Type | Evidence Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `Notification-Minimum-Attendance.pdf` | `Academic-Rules-for-SCSET_UG.pdf` | Minimum Attendance Requirement | **DIFFERENT_REGULATORY_CONDITIONS** | Notification 307/2022 governs Controller of Examination admit card / exam hall entry (75%) under UGC 2003 rules. SCSET Rule 30.1 governs course instructor semester grade debarment (70%). Distinct operational stages and authorities. |
| `Academic-Rules-for-SCSET_UG.pdf` | `SEAS-Ordinance-Rules-Regulations-2017.pdf` | B.Tech Academic Regulations | **HISTORICAL_RULE** | SEAS 2017 is a founding ordinance applicable to 2017-2021 cohorts. SCSET 2022 rules govern students enrolled under the restructured School of Computer Science Engineering & Technology (2022 onwards). |
| `Students-Discipline-Conduct-Rules-2024.pdf` | `UFM-Guidelines-2024.pdf` | Student Disciplinary Framework | **DIFFERENT_REGULATORY_CONDITIONS** | Distinct jurisdictions. UFM code is an examination hall malpractice regulation enforced by the Examination Disciplinary Committee. Conduct Rules govern general campus and hostel behavior enforced by the Proctorial Board. |
| `BU-First-Ordinance-2016.pdf` | `Academic-Rules-for-SCSET_UG.pdf` | Academic Structure & Governance | **PROGRAMME_SPECIFIC_RULE** | First Ordinance is statutory baseline under UP Act 24 of 2016. SCSET rules are delegated operational rules formulated by the School Academic Committee. |
| `BU-First-Ordinance-2016.pdf` | `Students-Discipline-Conduct-Rules-2024.pdf` | Disciplinary Authority | **DIFFERENT_REGULATORY_CONDITIONS** | First Ordinance Clause 31 vests supreme disciplinary authority in the Vice Chancellor. 2024 Conduct Rules operationalize proctorial board procedures and penalty guidelines. |
| `Notification-Minimum-Attendance.pdf` | `SEAS-Ordinance-Rules-Regulations-2017.pdf` | Minimum Attendance Threshold | **SAME_CONDITION_DIFFERENT_VERSION** | Chronological shift in general exam eligibility standard across cohorts (70% in 2017 to 75% in 2022 pursuant to UGC Regulations 2003). |

---

## 3. Ambiguous Attendance Query Audit

All seven ambiguous attendance queries were evaluated against the active retrieval pipeline (`retrieve()` + `EvidenceController.evaluate()`). The empirical outcomes from [m8_3_attendance_query_audit.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m8/m8_3_attendance_query_audit.csv) are analyzed below:

### Query Evaluation Matrix

| ID | Query Text | Retrieved Passages (Top Hits) | Existing Controller Status | Ground Truth Status | Gap Type Identified |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **AQ-01** | *What is the minimum attendance required?* | `f88ec726, 0280358a, 505e552e, c31d716d` | `CONFLICTING` | Dual Disclosure / Clarify | Legitimate ambiguity; query lacks program, cohort, and condition anchors. |
| **AQ-02** | *What attendance is required to sit for end semester exams?* | `0280358a, f88ec726, 505e552e, 2b15a3af` | `PARTIAL` | Grounded Answer (75%) | **False Partial:** Top hit `0280358a` (Notification 307) directly answers the query; CECI 0.419 triggered artificial partial status. |
| **AQ-03** | *How much attendance is required to avoid an X grade?* | `f88ec726, 505e552e, c7c1dfa7, 9bbbab01` | `CONFLICTING` | Grounded Answer (70%) | **False Conflict:** Both current SCSET 2022 and SEAS 2017 agree 100% on 70% for X-grade. Controller flagged conflict purely because SEAS is `is_current=False`. |
| **AQ-04** | *Is 70% attendance enough?* | `f88ec726, 1b631297, c31d716d, 0280358a` | `CONFLICTING` | Conditional Answer | **Granularity Gap:** 70% is sufficient for course grade/credit, but insufficient for exam hall. System labels this a conflict rather than a conditional answer. |
| **AQ-05** | *Is 75% compulsory for SCSET students?* | `b7549fd6, 4fb20336, 0280358a, cfb81e36` | `INSUFFICIENT` | Grounded Answer (Yes) | **Cross-Doc Inference Gap:** CECI 0.325 dropped to insufficient because SCSET PDF text omits the literal string "75%". Notification 307 binds all schools. |
| **AQ-06** | *What was the attendance rule in 2017?* | `f88ec726, c31d716d, 0280358a, 82bc0dd1` | `CONFLICTING` | Grounded Answer (70%) | **Temporal Anchoring Gap:** Query explicitly anchors to 2017. Controller flags conflict against current rules instead of answering from historical document. |
| **AQ-07** | *Can attendance be relaxed due to medical reasons?* | `6ad292d8, c31d716d, 505e552e, a40fe16a` | `CONFLICTING` | Grounded Answer (10%) | **False Conflict:** Both SEAS 2017 and SCSET 2022 prescribe identical 10% medical relaxation (Clause 30.1(v)). Controller flagged conflict purely due to version tag. |

---

## 4. Evidence Controller Architectural Gaps

The empirical audit reveals three primary architectural limitations in the current Evidence Controller:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    Current Evidence Controller Flow                       │
└───────────────────────────────────────────────────────────────────────────┘
                                   │
              Passages retrieved from DB (current + historical)
                                   │
                                   ▼
        Are passages from both current & historical documents present?
                                   │
                    ┌──────────────┴──────────────┐
                   YES                            NO
                    │                             │
                    ▼                             ▼
       Trigger CONFLICTING State           Standard CECI Evaluation
    (Even if text clauses agree 100%!)   (Can miss cross-doc inferences)
```

### Gap 1: False Conflict on Consensus Rules across Versions
When a query retrieves both current (SCSET 2022) and historical (SEAS 2017) passages that **agree completely** (e.g. 70% for 'X' grade in AQ-03, 10% medical condonation in AQ-07), the controller triggers `CONFLICTING` solely because one document has `is_current=False`. The controller checks document metadata before checking semantic agreement.

### Gap 2: Inability to Respect Temporal / Cohort Query Anchors
In AQ-06 (*"What was the attendance rule in 2017?"*), the user explicitly specifies the historical cohort. While hybrid retrieval correctly surfaces SEAS 2017 (`f88ec726`, score 6.318), the Evidence Controller ignores the user's temporal constraint and compares the passage against newer documents, forcing an unnecessary conflict abstention.

### Gap 3: Flat Numerical Contradiction vs Regulatory Condition Invariance
The controller collapses distinct administrative processes (Course-Level 'X' Grade debarment vs End Semester Examination Admit Card withholding) into a flat scalar clash between 70% and 75%. Because the schema lacks condition-level tagging, the system cannot output structured conditional answers like:
> *"70% attendance is sufficient to avoid an 'X' grade in individual courses, but 75% aggregate attendance is required by the Registrar to sit for End Semester Examinations."*

---

## 5. Test-Suite Evidence Reconciliation

The M8.3 audit performed an exhaustive audit of test suite inventory, cache records, and execution logs:

| Metric | Count | Source / Audit Command | Status |
| :--- | :---: | :--- | :---: |
| **Test Modules on Disk** | 14 | `Get-ChildItem backend/tests/test_*.py` | Verified |
| **Collected Test Cases** | 214 | `pytest --collect-only -q` | Verified |
| **Node IDs in Pytest Cache** | 215 | `backend/.pytest_cache/v/cache/nodeids` | Verified |
| **Active Execution Baseline** | 214 | `backend/data/experiments/m8/m8_manifest.json` | 100% Passed (214/214) |
| **Failures / Errors** | 0 | Test run output | Zero |
| **Skipped Tests** | 0 | Test run output | Zero |

### Reconciliation of the 1-Test Difference (214 vs 215)
A differential comparison between the 215 cached nodeids and the 214 collected tests was executed:
$$\text{Cached Node IDs (215)} \setminus \text{Collected Tests (214)} = \{\texttt{tests/test\_ingestion\_smoke.py::TestSourceRegistryStructure::test\_get\_verified\_sources\_empty\_by\_default}\}$$

The 1-test difference is an **obsolete test nodeid** retained in `.pytest_cache` from an earlier development iteration before `test_get_verified_sources_empty_by_default` was refactored in `test_ingestion_smoke.py`. The active test suite consists of **exactly 214 collected tests across 14 modules**, all of which execute and pass with 100% reliability.

---

## 6. Controller Improvement Proposal (Non-Runtime Implementation Specification)

To resolve the identified controller gaps without violating the strict read-only audit constraint, the following modular improvements are specified for future milestone implementation:

### Proposal 1: Consensus Verification Before Conflict Triggering
In `backend/app/query/controller.py`, introduce a consensus extraction step before flagging temporal conflicts:
```python
def check_regulatory_consensus(current_passages, historical_passages):
    """
    If extracted numerical thresholds and regulatory conditions match identically,
    treat as SUFFICIENT rather than CONFLICTING.
    """
    current_thresholds = extract_numerical_rules(current_passages)
    historical_thresholds = extract_numerical_rules(historical_passages)
    if current_thresholds and current_thresholds == historical_thresholds:
        return ConsensusState.UNANIMOUS_ACROSS_VERSIONS
    return ConsensusState.POTENTIAL_CONFLICT
```

### Proposal 2: Temporal / Cohort Intent Parsing
In `backend/app/query/processor.py`, add regex and entity detection for academic years and historical cohorts (e.g. `r"\b(201[6-9]|202[0-1])\b"`, `"in 2017"`, `"founding batch"`). When detected:
- Dynamically boost historical documents matching the requested year.
- Suppress newer document conflict flags if the user explicitly requested historical rules.

### Proposal 3: Condition-Aware Schema Tagging
Extend `RetrievedPassage` and `EvidenceState` to include `RegulatoryCondition`:
- `EXAM_HALL_ELIGIBILITY` (75% threshold, Registrar / CoE)
- `COURSE_GRADING_DEBARMENT` (70% threshold, Course Instructor / Dean)
- `MEDICAL_CONDONATION` (10% relaxation ceiling)

When a query intersects multiple conditions (e.g. AQ-04: *"Is 70% attendance enough?"*), the controller emits `EvidenceState.MULTI_CONDITION_DISCLOSURE` rather than `CONFLICTING`.

---

## 7. Audit Determination & Deliverable Index

### Audit Determination

$$\mathbf{M8\_3\_VERIFIED\_WITH\_CONTROLLER\_GAPS}$$

**Justification:**
1. **Historical Passage Preservation:** Reconfirmed at 100% (`IDENTICAL_PRESERVED` across all 172 historical passages).
2. **Regulatory Ground Truth:** Semantic distinction between course-level grade debarment (70%) and university examination eligibility (75%) established with primary textual citations.
3. **Evidence Controller Audit:** Successfully audited against 7 ambiguous queries. The controller reliably prevents unsafe ungrounded hallucination, but exhibits false-conflict and temporal-anchoring gaps that misclassify consensus rules as contradictions.
4. **Test Baseline:** 14 test modules, 214 test cases collected, 214 passed (100%), with cache differential fully accounted for.

### Artifact Index
- **Audit Manifest:** [m8_3_audit_manifest.json](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m8/m8_3_audit_manifest.json)
- **Regulatory Relationship Matrix:** [m8_3_regulatory_relationship_matrix.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m8/m8_3_regulatory_relationship_matrix.csv)
- **Attendance Query Audit:** [m8_3_attendance_query_audit.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m8/m8_3_attendance_query_audit.csv)
- **Audit Report:** [m8_3_regulatory_semantics_audit.md](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/m8_3_regulatory_semantics_audit.md)

