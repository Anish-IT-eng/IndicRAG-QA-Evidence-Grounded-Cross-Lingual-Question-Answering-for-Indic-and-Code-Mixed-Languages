# M10 Phase G: Answerable-Success Raw-Data Verification & Evidence Provenance

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-SUCCESS-VERIFICATION`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Audit Status:** Completed  

---

## 1. Executive Summary & Evidence Provenance

This document provides row-level evidence verification for Milestone M10 Phase G, explicitly distinguishing **report-based narrative claims** from **independently reproduced raw-data verification**.

### Provenance Audit Statement:
- **Raw Artifacts Available:** The underlying CSV datasets, test logs, database files, and execution scripts were fully available in the local repository and were directly inspected row-by-row during this audit.
- **Independent Checksum Verification:** SHA-256 checksums of all input datasets and scripts were independently computed against the actual files on disk and verified to match the repository integrity records:
  - `backend/data/experiments/m9/m9_evaluation_dataset.jsonl` (SHA-256: `f1829bdcad4512b6481005a944ab65da6dbd2858de5cc83a4a289d15bd506c2f`)
  - `backend/data/experiments/m10/m10_phase_e_per_intent_results.csv` (SHA-256: `2ce231deb133c4c985a5055a7b8ea88cf9409c66fbb2279d49500102fa39ca58`)
  - `backend/data/experiments/m10/m10_phase_f_end_to_end_results.csv` (SHA-256: `60a108f448ff9756601a0669c930e48b0186fab7b5920be26e1359c8581a7ebf`)
  - `backend/data/experiments/m10/m10_phase_f_answer_correctness.csv` (SHA-256: `870b88febfe1bf241c2372f093bd1e80492f014bd0ad427146741f08d9004269`)
  - `backend/experiments/m10/reproduce_power_and_cluster_tests.py` (SHA-256: `28c73ca3200f9c4228f454ecfe38dd32e6dcd73f1e43b26177dfa3252c71d06d`)

All metrics reported below represent **independently reproduced raw-data computations**, not inherited report claims.

---

## 2. Row-Level Evidence by Language Formulation

Every query outcome in [m10_phase_f_answer_correctness.csv](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_f_answer_correctness.csv) was extracted and classified:

### 2.1 English (`en`, $N=45$ Answerable Queries)

Evaluated under both `ConfigA_Production` and `ConfigB_AdaptiveE6b`:

#### `CORRECT_ANSWERED` (25 Queries):
`M9-Q005`, `M9-Q009`, `M9-Q013`, `M9-Q017`, `M9-Q025`, `M9-Q029`, `M9-Q033`, `M9-Q037`, `M9-Q045`, `M9-Q049`, `M9-Q053`, `M9-Q057`, `M9-Q073`, `M9-Q109`, `M9-Q113`, `M9-Q121`, `M9-Q125`, `M9-Q133`, `M9-Q137`, `M9-Q145`, `M9-Q153`, `M9-Q161`, `M9-Q165`, `M9-Q169`, `M9-Q173`.

#### `REGULATORY_DISCLOSURE` (3 Queries):
- `M9-Q021`: Unanchored attendance query; emitted structured disclosure of Clause 30.1 (70%) and Notification 307 (75%).
- `M9-Q065`: Condonation query with multi-regulatory boundaries; emitted structured disclosure.
- `M9-Q141`: Probation overlap with course repetition; emitted structured disclosure.

#### `UNNECESSARY_ABSTENTION` (17 Queries):
`M9-Q001`, `M9-Q061`, `M9-Q069`, `M9-Q077`, `M9-Q081`, `M9-Q085`, `M9-Q089`, `M9-Q093`, `M9-Q097`, `M9-Q101`, `M9-Q105`, `M9-Q117`, `M9-Q129`, `M9-Q149`, `M9-Q157`, `M9-Q177`, `M9-Q181`.

#### Total English Summary:
$$25 \text{ (CA)} + 3 \text{ (RD)} + 17 \text{ (UA)} = \mathbf{45 \text{ queries (100% accounted for)}}$$
- Strict Direct Answer Rate: $25 / 45 = \mathbf{55.56\%}$
- Combined Regulatory Success Rate: $28 / 45 = \mathbf{62.22\%}$

---

### 2.2 Devanagari Hindi (`hi`, $N=45$ Answerable Queries)

#### Under `ConfigA_Production`:
- `CORRECT_ANSWERED`: $0$
- `REGULATORY_DISCLOSURE`: $0$
- `UNNECESSARY_ABSTENTION`: $45$ queries
- **Success: 0 / 45 (0.00%)**

#### Under `ConfigB_AdaptiveE6b`:
- **`CORRECT_ANSWERED` (1 Query):**
  - `M9-Q058` (Intent 58): *"CGPA की गणना के लिए संचयी ग्रेड प्वाइंट औसत का फॉर्मूला क्या है?"*
    - *Retrieved Passage:* `f6d95cc5-2c08-4aee-ba5c-7242...` (Clause 22.1).
    - *Evidence Controller:* ACCEPTED (entailment score 0.812).
    - *Final Answer:* Grounded calculation formula with verified citation.
- **`REGULATORY_DISCLOSURE` (1 Query):**
  - `M9-Q002` (Intent 02): *"एंड सेमेस्टर परीक्षा में बैठने के लिए न्यूनतम कितनी उपस्थिति आवश्यक है?"*
    - *Retrieved Passages:* `0280358a` (Notification 307 75% rule) at Rank 1; `f88ec726` (SCSET Clause 30.1 70% rule) at Rank 3.
    - *Evidence Controller:* `CLARIFICATION_REQUIRED` ($CECI = 0.80$).
    - *Final Answer:* Structured disclosure explaining both the 70% course rule and 75% exam hall rule.
- **`UNNECESSARY_ABSTENTION` (43 Queries):** 43 remaining queries safely abstained.

#### Total Devanagari Summary:
$$1 \text{ (CA)} + 1 \text{ (RD)} + 43 \text{ (UA)} = \mathbf{45 \text{ queries (100% accounted for)}}$$
- Strict Direct Answer Rate: $1 / 45 = \mathbf{2.22\%}$
- Combined Regulatory Success Rate: $2 / 45 = \mathbf{4.44\%}$

---

### 2.3 Romanized Hindi (`hi-Latn`, $N=45$ Answerable Queries)

Evaluated under both configurations (Strict Invariance):
- **`CORRECT_ANSWERED` (13 Queries):** `M9-Q007`, `M9-Q011`, `M9-Q015`, `M9-Q039`, `M9-Q059`, `M9-Q115`, `M9-Q119`, `M9-Q127`, `M9-Q139`, `M9-Q151`, `M9-Q163`, `M9-Q167`, `M9-Q171`.
- **`REGULATORY_DISCLOSURE` (1 Query):** `M9-Q023`.
- **`UNNECESSARY_ABSTENTION` (31 Queries):** 31 queries.
- **Total:** $13 + 1 + 31 = \mathbf{45 \text{ queries}}$.
- Strict Direct Answer Rate: $13 / 45 = \mathbf{28.89\%}$
- Combined Regulatory Success Rate: $14 / 45 = \mathbf{31.11\%}$

---

### 2.4 Hinglish (`en-hi`, $N=45$ Answerable Queries)

Evaluated under both configurations (Strict Invariance):
- **`CORRECT_ANSWERED` (14 Queries):** `M9-Q008`, `M9-Q012`, `M9-Q016`, `M9-Q028`, `M9-Q076`, `M9-Q116`, `M9-Q120`, `M9-Q128`, `M9-Q132`, `M9-Q140`, `M9-Q148`, `M9-Q152`, `M9-Q168`, `M9-Q176`.
- **`REGULATORY_DISCLOSURE` (3 Queries):** `M9-Q072`, `M9-Q144`, `M9-Q172`.
- **`UNNECESSARY_ABSTENTION` (28 Queries):** 28 queries.
- **Total:** $14 + 3 + 28 = \mathbf{45 \text{ queries}}$.
- Strict Direct Answer Rate: $14 / 45 = \mathbf{31.11\%}$
- Combined Regulatory Success Rate: $17 / 45 = \mathbf{37.78\%}$

---

## 3. Dissecting the Phase F Narrative Discrepancies

### 3.1 Report-Based Narrative Claims vs. Independently Reproduced Raw Data

| Stratum | Narrative Report Claim | Raw Data Verified Count | Reconciliation Resolution |
|---|---|---|---|
| **English** | "26 Grounded Answered, 15 Abstentions" | **25 CA + 3 RD = 28 Successes, 17 Abstentions** | The Phase F narrative table had a transcription defect ($26 + 15 = 41 \neq 45$). The raw dataset has 25 strict answered + 3 regulatory disclosures = 28 total successes, and 17 abstentions ($28 + 17 = 45$). |
| **Devanagari** | "1 Regulatory Disclosure" | **1 CA + 1 RD = 2 Combined Successes** | Phase F narrative audited `M9-Q002` (RD) manually. Automated execution also yielded `M9-Q058` (CA). Raw dataset contains both ($1 + 1 = 2$). |
| **Overall Config A** | "53 Grounded Answered" | **52 CA (Strict) / 59 Combined** | Direct answers: $25 + 0 + 13 + 14 = 52$; adding 7 disclosures yields **59**. |
| **Overall Config B** | "54 Grounded Answered" | **53 CA (Strict) / 61 Combined** | Direct answers: $25 + 1 + 13 + 14 = 53$; adding 8 disclosures yields **61**. |

Both operational definitions are independently confirmed directly from the raw records.
