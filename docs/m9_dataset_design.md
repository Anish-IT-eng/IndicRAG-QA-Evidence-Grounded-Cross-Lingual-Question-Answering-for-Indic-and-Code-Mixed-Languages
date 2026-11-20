# Milestone M9: Cross-Lingual & Code-Mixed Evaluation Dataset Design

**Milestone Identifier:** M9 (Phase B)  
**Role:** Senior Academic Regulation Researcher & RAG Evaluation Auditor  
**Audit Timestamp:** 2026-11-16T19:15:00+05:30  
**Repository:** `C:\Users\anish\Desktop\IndicRAG-QA`  

---

## 1. Executive Summary & Design Scope

Milestone M9 introduces a dedicated, strictly partitioned benchmark dataset designed to evaluate cross-lingual semantic equivalence, multilingual evidence retrieval, citation precision, and answer generation fidelity across four distinct language varieties:
1. **English (EN):** Official institutional language in Latin script.
2. **Hindi (HI-Deva):** Formal Hindi in standard Devanagari script.
3. **Romanized Hindi (HI-Latn):** Conversational Hindi written in Latin script.
4. **Hinglish (EN-HI Code-Mixed):** Intra-sentential code-mixed Hindi-English in Latin/Mixed script.

### Strict Isolation Invariant:
In accordance with mandatory constraints, this dataset is stored in `backend/data/experiments/m9/` and does **not** alter or overwrite the frozen M3 retrieval benchmark (`final_verified_dataset.csv`), the frozen M6 generation benchmark (`m6_expanded_benchmark_n60.csv`), or M8 historical audit datasets.

---

## 2. Dataset Architecture & Intent Distribution

The dataset comprises **60 semantic intent groups** (`M9-INT-01` through `M9-INT-60`), each instantiated in 4 parallel linguistic variants, yielding **240 total evaluated queries** (`M9-Q001` through `M9-Q240`):

```
                               60 Semantic Intent Groups (M9-INT-01 to M9-INT-60)
                                                    │
                 ┌──────────────────────────────────┴──────────────────────────────────┐
                 ▼                                                                     ▼
        45 Answerable Intents (75.0%)                                         15 Unanswerable Intents (25.0%)
           [180 Query Records]                                                    [60 Query Records]
                 │                                                                     │
  ┌──────────────┼──────────────┐                                                      │
  ▼              ▼              ▼                                                      ▼
Regulations &   Discipline &   Academic                                    Out-of-Scope / Contradictory /
Grading (16)    Conduct (12)   Calendar (6)                                Missing Conditions (15)
Attendance (8)  UFM (5)                                                    (No Evidence in Official Corpus)
```

### Semantic Category Breakdown:
1. **Attendance Regulations (Intents 01–08; 32 queries):** Examination eligibility (75%), course-level pass requirement (70%), 10% medical relaxation for 2+ weeks continuous illness, exclusion of short casual absences, dual-condition comparisons (70% vs 75%), historical 2017 SEAS baseline, Dean/VC authority, and combined lecture/practical computation.
2. **Grading System & Academic Performance (Intents 09–16; 32 queries):** Letter grades (O to F), 'X' grade consequence and course repeating, minimum 30-mark threshold for 'D' grade, 'I' grade criteria, 'AU' audit grade and credit rules, Grade Moderation Committee, SGPA/CGPA calculation formula, and 5.0 CGPA degree graduation requirement.
3. **Examination & Make-Up Regulations (Intents 17–22; 24 queries):** Make-up end-semester exam eligibility, supplementary examination policy for F grades, practical evaluation criteria, 5-day deadline for submitting medical evidence, mandatory admit card requirement, and supplementary rules for projects.
4. **Academic Progression & Curriculum (Intents 23–28; 24 queries):** 18–20 week semester duration with 90 teaching days, 3rd-year promotion backlog restrictions (mandatory clearance of 1st-year courses), credit load restrictions under probation, B.Tech with Minor requirements, elective course minimum enrollment thresholds, and Preparatory English Course criteria.
5. **Student Discipline & Conduct Rules 2024 (Intents 29–34; 24 queries):** Zero-tolerance ragging penalties, Proctorial Board jurisdiction, complete campus ban on alcohol/drugs/tobacco, suspension durations, Vice Chancellor appeal procedures, and unauthorized entry of outsiders into hostels.
6. **Unfair Means (UFM) Guidelines 2024 (Intents 35–39; 20 queries):** Mobile phone / electronic gadget possession penalties, impersonation (proxy) in exams, copying from answer books, Committee on Unfair Means convening and hearing procedures, and multi-semester debarment.
7. **Academic Calendar 2026–27 (Intents 40–45; 24 queries):** Make-up exam registration start date (01-07-2026), admit card issuance date (07-12-2026), tentative Convocation date (13-11-2026), mid-term marks ERP submission deadline, and scheduled December holidays.
8. **Unanswerable / Insufficient Evidence (Intents 46–60; 60 queries):** Off-corpus queries including hostel mess menu voting, tuition fee refund schedule after 6 months, international campus placement package records, full-time PhD stipend rates, campus bus pickup routes/timings, mandatory law school dress code, overdue library book daily fines, sports quota admission trial criteria, off-campus flat permissions, corporate internship minimum stipends, semester exchange visa papers, gym personal trainer subscriptions, false premise 50% attendance, false premise 'A' grade with 35% marks, and cross-school branch transfer from Law to B.Tech.

---

## 3. Dataset Record Schema

Each query record in `backend/data/experiments/m9/m9_evaluation_dataset.jsonl` adheres to the formal JSON schema defined in `backend/data/experiments/m9/m9_dataset_schema.json`:

```json
{
  "intent_id": "M9-INT-01",
  "query_id": "M9-Q001",
  "query_text": "What is the minimum attendance required to appear in the End Semester Examination?",
  "query_language": "en",
  "script": "LATIN",
  "query_type": "DIRECT",
  "expected_answer_language": "en",
  "expected_status": "ANSWERED",
  "expected_document_ids": ["40c366dd-41b2-49f6-b5e4-492a8b5bbe8a"],
  "expected_passage_ids": ["0280358a-ff3c-4964-88ab-419a9147b1f0"],
  "expected_claims": ["The minimum attendance criteria to appear in End Semester Examinations is 75%."],
  "expected_answer": "The minimum attendance criteria to appear in the End Semester Examination is 75%.",
  "applicability_constraints": {"purpose": "EXAMINATION_ELIGIBILITY"},
  "human_review_status": "PROVISIONAL_NOT_HUMAN_VERIFIED",
  "reviewer_notes": "Provisional en translation for intent M9-INT-01; requires native bilingual review."
}
```

---

## 4. Human Verification Policy & Integrity Standard

### Mandatory Research Integrity Rule:
Prior milestone audits established that existing benchmark records had zero recorded human verifications. 
For Milestone M9:
1. **No Artificial Claims of Human Verification:** In accordance with Section 4 of the milestone specification, all 240 dataset records are formally stamped with:
   ```
   "human_review_status": "PROVISIONAL_NOT_HUMAN_VERIFIED"
   ```
2. **Explicit Review Workflow Template:** A standardized review template has been generated at:
   `backend/data/experiments/m9/m9_human_review_template.csv`
   The template includes designated auditing columns:
   - `reviewer_correction`: Exact corrected translation text if dialect or phrasing is non-idiomatic.
   - `translation_quality`: Assessment metric (`NATURAL`, `ACCEPTABLE_LITERAL`, `AMBIGUOUS_UNNATURAL`, `SEMANTIC_DRIFT`).
   - `reviewer_notes`: Linguistic commentary on terminology, script conventions, and code-mixing naturalness.
3. **Scientific Reporting:** All subsequent retrieval, generation, and statistical metrics are explicitly designated as **provisional machine-generated benchmark results** pending formal independent bilingual panel sign-off.

---

## 5. Artifact Deliverables Summary

1. **Dataset JSONL:** [m9_evaluation_dataset.jsonl](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m9/m9_evaluation_dataset.jsonl) (240 records, 60 intents)
2. **Schema Definition:** [m9_dataset_schema.json](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m9/m9_dataset_schema.json)
3. **Human Review Workflow:** [m9_human_review_template.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m9/m9_human_review_template.csv) (240 review slots)
