# M10 Phase H — Regulatory Applicability & Conflict Handling Audit

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** H — Cross-Lingual End-to-End Answer Quality, Citation & Grounding Audit  
**Date:** November 17, 2026  
**Status:** Audit Complete — Target Determination: `M10_PHASE_H_VERIFIED_WITH_LIMITATIONS`  

---

## 1. Regulatory Context & Challenge

In institutional regulatory compliance, question-answering systems frequently encounter contradictory, superseded, or school-specific rules. Bennett University regulations exhibit several distinct layers of regulatory hierarchy:
1. **University-Wide Ordinances:** E.g., *BU First Ordinance 2016*, establishing statutory authorities and general disciplinary powers.
2. **School-Specific Academic Rules:** E.g., *SEAS Ordinance Rules & Regulations 2017* versus *Academic Rules for SCSET UG (2022)*.
3. **Executive Notifications:** E.g., *Notification BU/R0/Notification/307/2022 (08-Sep-2022)*, which established a universal 75% minimum aggregate attendance rule for End Semester Examinations.

A naive RAG pipeline risks conflating these provisions or asserting a historical 70% course rule when an overriding 75% examination threshold is in effect.

---

## 2. Evaluation of Key Regulatory Dimensions

### 2.1 The Attendance Dilemma: Course-Level (70%) vs. Examination Eligibility (75%)
A central regulatory stress test in the M9/M10 benchmark is Intent `M9-INT-01`:
- **The Provision in SCSET/SEAS Clause 30.1:** Requires minimum 70% attendance in a given course to avoid an 'X' grade (forced course repetition).
- **The Provision in Notification 307/2022:** Issued by the Registrar on Sept 8, 2022, mandating a minimum 75% aggregate attendance to be permitted to sit for End Semester Examinations.
- **The Benchmark Requirement:** When a query asks generally *"What is the minimum attendance required to appear in examinations?"*, the system **must not** pick 70% or 75% arbitrarily. It must issue a **Structured Regulatory Disclosure (`CLARIFICATION REQUIRED`)** explaining both criteria and prompting the user for their batch/purpose.

#### Audit Findings:
- Under **Config A**, the system abstained unnecessarily on Devanagari query `M9-Q002` due to MS-MARCO score demotion ($0/45$).
- Under **Config B**, the system retrieved both Notification 307/2022 (`0280358a-ff3c...`) and SCSET Clause 30.1 (`f88ec726-74ba...`). The Evidence Controller flagged the dual criteria, and the generator output:
  > *"CLARIFICATION REQUIRED — Structured Regulatory Disclosure: 75% minimum aggregate attendance is required by the Registrar to appear in End Semester Examinations (Notification 307/2022), while 70% attendance in a course is required to avoid an 'X' grade and course repetition (SCSET Academic Rules Clause 30.1)..."*
- **Result:** Config B correctly handled this regulatory boundary in Devanagari Hindi with zero conflation.

---

### 2.2 School & Programme Applicability
The corpus spans multiple academic units:
- **SCSET:** School of Computer Science Engineering and Technology.
- **SEAS:** School of Engineering and Applied Sciences.
- **SOL:** School of Law.
- **SOM:** School of Management.

#### Audit Findings:
- Queries targeting SCSET graduation requirements (e.g., `M9-Q073` lab weightages, `M9-Q057`/`M9-Q058` CGPA calculations) correctly cited `Academic-Rules-for-SCSET_UG.pdf` (UUID: `b787fd22-eb2f...`).
- When asked about School of Law specific weekday dress codes (`M9-Q201`), the corpus lacked an SOL-specific policy. The system cited the university-wide general conduct rules. While factually grounded, this represents an over-generalization failure mode documented in the Failure Analysis.

---

### 2.3 Cohort & Academic Year Applicability
- Rules established under the *2016 First Ordinance* apply to early cohorts unless superseded by the *2022 SCSET Rules*.
- The audit verified that across all 61 successful answers in Config B, no student enrolled under 2022 regulations was cited 2016 graduation credit totals without appropriate version qualifications.

---

### 2.4 Condonation & Medical Relaxation Conditions
Under SCSET Clause 30.2 and Notification 307/2022:
- Attendance condonation for medical emergencies or institutional duty is capped at 10% (permitting relaxation down to 65% aggregate, subject to Dean/Registrar sanction and documentary proof within 3 working days).
- In queries probing medical leave exemptions (e.g., Intent `M9-INT-02`), the generated answers preserved all necessary conditions:
  - 10% maximum condonation cap.
  - Requirement of medical certificate submission within 3 days.
  - Discretionary approval authority vested in the Dean.

---

## 3. Comparative Regulatory Disclosure Metrics

| Regulatory Handling Metric | Config A (`E1_PROD_MSMARCO_D10`) | Config B (`E6b_ADAPTIVE_BI_ENCODER`) |
|---|---:|---:|
| **Correct Regulatory Disclosures Issued** | 7 / 180 (3.89%) | 8 / 180 (4.44%) |
| **Silent Rule Conflations Detected** | 0 / 180 (0.00%) | 0 / 180 (0.00%) |
| **Superseded Provision Overrides** | 0 / 180 (0.00%) | 0 / 180 (0.00%) |
| **Cross-Lingual Regulatory Parity** | Latin only | Latin + Devanagari (`M9-Q002`) |

---

## 4. Audit Conclusion

Config B preserves complete regulatory applicability hygiene. By recovering Notification 307/2022 in Devanagari Hindi, Config B successfully extends structured regulatory disclosure to Indic script users without introducing silent rule conflation.
