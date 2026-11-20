# M10 Phase G: Metric Definition & Categorization Ledger

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-METRIC-LEDGER`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Status:** Audit Completed  

---

## 1. Executive Summary

During the audit of Milestone M10 Phase F and Phase G, variations in reported success counts (e.g., English $26/45$ vs $28/45$, Devanagari $1/45$ vs $2/45$, and overall $53/180$ vs $59/180$ vs $61/180$) were identified. 

This document establishes the authoritative **Metric Definition Ledger**. It formalizes the classification taxonomy, documents dual operational views of success, traces raw record mappings, and explains the transcription origins of earlier narrative discrepancies.

---

## 2. End-to-End Correctness Categorization Taxonomy

In IndicRAG-QA regulatory question answering, every query outcome is mapped to one of seven formal mutually exclusive categories:

| Category Code | Category Name | Description | Desired on Answerable? | Desired on Unanswerable? |
|---|---|---|:---:|:---:|
| `CA` | `CORRECT_ANSWERED` | Direct factual answer grounded in retrieved regulatory passage with validated citations. | **Yes** | No (False Positive) |
| `RD` | `REGULATORY_DISCLOSURE` | Authoritative structured disclosure delineating conflicting rules or regulatory bounds when a query is unanchored (e.g., 70% course rule vs 75% exam hall rule). | **Yes** | No |
| `UA` | `UNNECESSARY_ABSTENTION` | Conservative refusal (`UNANSWERABLE`) emitted on an answerable query due to retrieval starvation or cross-lingual entailment threshold failure. | **No** (Conservative) | No |
| `CR` | `CORRECT_ABSTENTION` | Compliant refusal (`UNANSWERABLE`) emitted on an unanswerable or out-of-scope query. | No | **Yes** |
| `IA` | `INCORRECT_ANSWER` | Hallucinated assertion, ungrounded claim, or factual contradiction. | No (Severe defect) | No (Severe defect) |
| `CL` | `CLARIFICATION_REQUIRED` | System flags query ambiguity without providing regulatory disclosure text. | Conditional | Conditional |
| `SF` | `SYSTEM_FAILURE` | Unhandled runtime exception, timeout, or pipeline crash. | No (Defect) | No (Defect) |

---

## 3. Dual Operational Definitions of Answerable Performance

In academic benchmarking and production regulatory deployment, "Success" on answerable queries ($N=45$ per language, $N=180$ total) can be formulated under two distinct perspectives:

### Perspective 1: Strict Direct Answer Rate ($S_{\text{strict}}$)
Evaluates whether the system generated a direct, definitive factual answer to the prompt:
$$S_{\text{strict}} = \frac{N(\text{CORRECT\_ANSWERED})}{N_{\text{answerable}}}$$
- Treats `REGULATORY_DISCLOSURE` as non-answers (equivalent to clarifications).
- Provides a strict lower-bound metric.

### Perspective 2: Combined Regulatory Success Rate ($S_{\text{combined}}$)
Evaluates overall system utility and regulatory compliance. In academic regulation, when a user asks an unanchored question spanning multiple distinct rules (e.g., "What is the minimum attendance?"), emitting an authoritative structured disclosure explaining both the 70% course requirement and 75% exam hall requirement is the *legally correct* behavior:
$$S_{\text{combined}} = \frac{N(\text{CORRECT\_ANSWERED}) + N(\text{REGULATORY\_DISCLOSURE})}{N_{\text{answerable}}}$$
- Counts both direct grounded answers and compliant structured disclosures as successes.
- This was the primary success estimand utilized in the Phase G statistical evaluation.

---

## 4. Comprehensive Language-by-Language Reconciliation Ledger

Based on the underlying raw records in [m10_phase_f_answer_correctness.csv](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_f_answer_correctness.csv):

| Language Formulation | Total Answerable ($N$) | Config ID | Strict Answered (`CA`) | Regulatory Disclosure (`RD`) | Unnecessary Abstention (`UA`) | Strict Answer Rate ($S_{\text{strict}}$) | Combined Success Rate ($S_{\text{combined}}$) | Phase F Narrative Report | Phase G Statistical CSV |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| **English (`en`)** | 45 | Config A (Prod) | 25 | 3 | 17 | 25 / 45 (55.6%) | **28 / 45 (62.2%)** | 26 / 45 | **28 / 45 (62.2%)** |
| English (`en`) | 45 | Config B (E6b) | 25 | 3 | 17 | 25 / 45 (55.6%) | **28 / 45 (62.2%)** | 26 / 45 | **28 / 45 (62.2%)** |
| **Devanagari (`hi`)** | 45 | Config A (Prod) | 0 | 0 | 45 | 0 / 45 (0.0%) | **0 / 45 (0.0%)** | 0 / 45 | **0 / 45 (0.0%)** |
| Devanagari (`hi`) | 45 | Config B (E6b) | 1 | 1 | 43 | 1 / 45 (2.2%) | **2 / 45 (4.4%)** | 1 / 45 (Q002 only) | **2 / 45 (4.4%)** |
| **Romanized (`hi-Latn`)**| 45 | Config A (Prod) | 13 | 1 | 31 | 13 / 45 (28.9%) | **14 / 45 (31.1%)** | 13 / 45 | **14 / 45 (31.1%)** |
| Romanized (`hi-Latn`)| 45 | Config B (E6b) | 13 | 1 | 31 | 13 / 45 (28.9%) | **14 / 45 (31.1%)** | 13 / 45 | **14 / 45 (31.1%)** |
| **Hinglish (`en-hi`)** | 45 | Config A (Prod) | 14 | 3 | 28 | 14 / 45 (31.1%) | **17 / 45 (37.8%)** | 14 / 45 | **17 / 45 (37.8%)** |
| Hinglish (`en-hi`) | 45 | Config B (E6b) | 14 | 3 | 28 | 14 / 45 (31.1%) | **17 / 45 (37.8%)** | 14 / 45 | **17 / 45 (37.8%)** |
| **Overall Pooled** | **180** | **Config A (Prod)** | **52** | **7** | **121** | **52 / 180 (28.9%)** | **59 / 180 (32.8%)** | **53 / 180** | **59 / 180 (32.8%)** |
| **Overall Pooled** | **180** | **Config B (E6b)** | **53** | **8** | **119** | **53 / 180 (29.4%)** | **61 / 180 (33.9%)** | **54 / 180** | **61 / 180 (33.9%)** |

### 4.1 Explanation of Discrepancies in Earlier Narrative Reports

1. **English Count Discrepancy ($26$ vs $28$ vs $25$):**
   - The raw dataset contains $25$ direct answers (`CORRECT_ANSWERED`), $3$ regulatory disclosures (`REGULATORY_DISCLOSURE`), and $17$ abstentions ($25 + 3 + 17 = 45$).
   - In the Phase F narrative Table 2, the author manually transcribed English as: "Grounded Answered: 26, Unnecessary Abstentions: 15". This contained a transcription defect ($26 + 15 = 41 \neq 45$).
   - Phase G ingested the underlying CSV records, which correctly yielded $25 + 3 = \mathbf{28}$ combined successes.
2. **Devanagari Count Discrepancy ($1$ vs $2$):**
   - In Phase F Table 2, the author recorded "Regulatory Disclosures: 1" based on the deep-dive manual inspection of query `M9-Q002`.
   - In the full automated pipeline evaluation, query `M9-Q058` also successfully generated a grounded direct answer (`CORRECT_ANSWERED`).
   - Therefore, the dataset contains $1$ direct answer + $1$ regulatory disclosure = $\mathbf{2}$ total successes.
3. **Overall Count Reconciliation ($53$ vs $54$ vs $59$ vs $61$):**
   - The Phase F narrative reported $53 \to 54$ by summing direct answers across languages ($26 + 0 + 13 + 14 = 53$ Config A; $53 + 1 = 54$ Config B).
   - The Phase G statistical evaluation reported $59 \to 61$ by summing combined successes ($52 \text{ direct} + 7 \text{ disclosures} = 59$ Config A; $53 \text{ direct} + 8 \text{ disclosures} = 61$ Config B).

---

## 5. Retrieval Metric Ledger & Candidate-Depth Mapping

| Metric | Mathematical Definition | Candidate Pool Setting | Evaluated Dataset | Phase E Result | Phase F Result | Phase G Result |
|---|---|:---:|---|:---:|:---:|:---:|
| **Hit@k** | $\mathbb{I}(\text{Rank}(\text{gold}) \le k)$ | $k_{pool} = 10$ | `m10_phase_e_per_intent_results.csv` | **0.1111 (en)** | — | **0.1111 (en)** |
| Hit@k | $\mathbb{I}(\text{Rank}(\text{gold}) \le k)$ | $k_{pool} = 20$ (Prod) | Production Pipeline Run | — | **0.1333 (en)** | — |
| **MRR** | $\frac{1}{\text{Rank}(\text{gold})}$ if in Top-5 else 0 | $k_{pool} = 10$ | `m10_phase_e_per_intent_results.csv` | **0.1000 (en)** | — | **0.1000 (en)** |
| **nDCG@5** | $\frac{\text{DCG}@5}{\text{IDCG}@5}$ | $k_{pool} = 10$ | `m10_phase_e_per_intent_results.csv` | **0.0839 (en)** | — | **0.0839 (en)** |

**Key Rule:** Phase G strictly evaluated the controlled $k_{pool}=10$ Phase E dataset to avoid confounding candidate-generation depth with reranker algorithm quality.

---

## 6. Safety & Abstention Metric Ledger

| Metric | Target Population | Formulation | Config A | Config B | 95% Confidence Interval | Method |
|---|---|---|:---:|:---:|:---:|---|
| **Correct Abstention Rate (CAR)** | Unanswerable ($N=60$) | $\frac{N(\text{CORRECT\_ABSTENTION})}{N_{\text{unanswerable}}}$ | 58 / 60 (96.7%) | 58 / 60 (96.7%) | [88.6%, 99.1%] | Wilson Score Interval |
| **Unsupported Answer Rate (UAR)** | Generated Answers ($N_{\text{gen}}$) | $\frac{N(\text{INCORRECT\_ANSWER})}{N_{\text{gen}}}$ | 0 / 59 (0.00%) | 0 / 61 (0.00%) | [0.00%, 4.91%] | Rule of Three ($3/N$) Upper Bound |
| **Citation Precision** | Extracted Citations | $\frac{N(\text{Valid Citations})}{N(\text{Total Citations})}$ | 100.0% | 100.0% | [94.1%, 100.0%] | Wilson Score Interval |
| **Page Verification Rate** | Valid Citations | $\frac{N(\text{Page Matches Clause})}{N(\text{Valid Citations})}$ | 100.0% | 100.0% | [94.1%, 100.0%] | Wilson Score Interval |

Both operational views are preserved in this ledger and traced to their underlying records.
