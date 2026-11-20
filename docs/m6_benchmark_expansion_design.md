# IndicRAG-QA — M6 Benchmark Expansion Design Specification ($N=60$) (Phase 1B Corrected)

**Milestone:** M6 — Evidence Reliability and Answerability  
**Phase:** Phase 1B (Methodological Correction & Implementation Specification)  
**Date:** 2026-11-10  
**Author:** Senior RAG Evaluation Researcher & Evidence Reliability Engineer  
**Target Benchmark Size:** $N = 60$ (40 Answerable, 20 Unanswerable)  
**Baseline Preservation:** All 15 M3 benchmark instances preserved immutable (SHA-256: `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520`)  
**Corpus Provenance:** 142 child passages, 30 parent sections (SHA-256: `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d`)  

---

## 1. Objectives & Expansion Principles

The M6 benchmark expands the evaluation capacity of IndicRAG-QA from $N=15$ to **$N=60$** while adhering strictly to research integrity standards:
1. **Core Benchmark Immutability:** The 15 historical M3 benchmark queries are preserved verbatim as the immutable anchor cohort (`m3_frozen_core`).
2. **Exactly 45 New Candidates:** 27 new answerable queries and 18 new unanswerable/edge queries will be generated and validated.
3. **Strict Verifier-Generator Independence:** The generator model that synthesized a candidate is **strictly disqualified from acting as a verifier** for that candidate.
4. **Dual Independent Verification:** Every candidate must be independently evaluated by at least two distinct verifier models.
5. **Exact Grounding in Official 142 Child Passages:** Answerable candidates must map to verified verbatim substring quotes in `backend/data/db/indicrag.db`.
6. **No Automated Human Labeling:** All machine decisions receive `final_status = 'auto_validated'` and `review_status = 'pending'`. The tag `human_verified` is strictly reserved for authenticated manual human inspection.

---

## 2. Benchmark Stratification Matrix ($N=60$)

The expanded benchmark maintains balanced representation across all 4 language modalities:

| Language Modality | Code | Script | Frozen M3 Core | New Answerable | New Unanswerable | Total Answerable | Total Unanswerable | Total Query Count | Proportion |
|---|---|---|---|---|---|---|---|---|---|
| **English** | `en` | Latin | 5 (4 ans, 1 unans) | 10 | 5 | 14 | 6 | **20** | 33.3% |
| **Devanagari Hindi** | `hi` | Devanagari | 5 (4 ans, 1 unans) | 6 | 5 | 10 | 6 | **16** | 26.7% |
| **Code-Mixed Hinglish**| `hi-en`| Latin | 3 (3 ans, 0 unans) | 5 | 4 | 8 | 4 | **12** | 20.0% |
| **Romanized Hindi** | `hi-Latn`| Latin | 2 (2 ans, 0 unans) | 6 | 4 | 8 | 4 | **12** | 20.0% |
| **Total** | — | — | **15** | **27** | **18** | **40** | **20** | **60** | **100.0%** |

---

## 3. Query Taxonomy & Overlapping Label Architecture

Real-world regulatory queries often span multiple categories (e.g. a numerical grade threshold query that also contains an academic year condition). To ensure clean analysis without artificial taxonomy flattening, each instance records:
- `primary_taxonomy`: The governing categorization for stratification.
- `secondary_taxonomies`: JSON list of all secondary properties exhibited by the query.

### 3.1 Answerable Taxonomies ($N=40$)

| Primary Taxonomy Tag | Target Count | Description | Canonical Example |
|---|---|---|---|
| **`direct_factual`** | 12 | Single-step regulatory facts, definitions, and degree options. | *"What are the options available for final semester B.Tech?"* |
| **`numerical_tabular`** | 10 | Specific grade marks thresholds, attendance percentages, dates, and credits. | *"Courses ke liye D grade ki range kitne marks se shuru hoti hai?"* |
| **`multi_part`** | 7 | Queries asking for multiple conditions, procedures, or conjunctions. | *"What is the procedure and deadline to add or drop a course after classes start?"* |
| **`conditional_exception`**| 6 | Debarment exceptions, medical makeup criteria, and attendance condonation rules. | *"Can a student debarred due to attendance take a supplementary exam?"* |
| **`temporal_version`** | 5 | Explicit academic-year rules (e.g. 2026-27 calendar vs Notification 307 vs Clause 30). | *"What is the attendance requirement for academic year 2022-23?"* |

### 3.2 Negative & Edge-Case Taxonomies ($N=20$)

Unanswerables and edge cases are divided into distinct categories to probe specific controller states:

| Primary Taxonomy Tag | Target Count | Expected Decision State | Description | Probed Behavior |
|---|---|---|---|---|
| **`out_of_domain`** | 6 | `MISSING` | Completely outside university regulations (e.g., PhD thesis submission fee, external bank loan policies). | Tests zero-hit detection and complete absence of hallucination. |
| **`absent_policy`** | 6 | `INSUFFICIENT` | Plausible campus student issues that are **unregulated in official documents** (e.g., hostel room transfer fee, pet rules, cooking appliances). | Tests rejection of partial lexical overlap against off-topic academic rules. |
| **`clarification_required`**| 4 | `CLARIFICATION_REQUIRED` | Queries asking for rules that differ across cohorts/years without specifying which year applies. | Tests identification of missing context instead of assuming current rules unilaterally. |
| **`unresolvable_conflict`** | 4 | `CONFLICTING` / `INSUFFICIENT` | Query presents contradictory premises or conflicting regulatory clauses that cannot be satisfied. | Tests disclosure of conflict rather than arbitrary one-sided resolution. |

---

## 4. Multi-Model Verification Protocol with Strict Independence

To ensure that candidate generation and verification are strictly independent, models rotate roles:

```
┌────────────────────────────────────────────────────────┐
│                   Candidate Generator                  │
│       (Rotates among: qwen2.5:3b, llama3.2:3b, gemma:2b)│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             Stage 1: Deterministic Validator           │
│  - Question length >= 5 words                          │
│  - Answer non-empty                                    │
│  - Answerable: Substring match in 142 child passages   │
│  - Unanswerable: Zero quote substring matches          │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│            Stage 2: Linguistic & Script Validator      │
│  - Script matches (Devanagari for 'hi', Latin others)  │
│  - Hinglish Latin token ratio in [0.15, 0.85]          │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│       Stage 3: Dual Independent Model Verification     │
│       **Generator strictly excluded from verifiers**   │
│                                                        │
│   If Generator == qwen2.5:3b:                          │
│       Verifier 1: llama3.2:3b                          │
│       Verifier 2: gemma:2b                             │
│   If Generator == llama3.2:3b:                         │
│       Verifier 1: qwen2.5:3b                           │
│       Verifier 2: gemma:2b                             │
│   If Generator == gemma:2b:                            │
│       Verifier 1: qwen2.5:3b                           │
│       Verifier 2: llama3.2:3b                          │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│            Consensus Decision & Registration           │
│  - Both verifiers agree on Answerability & Evidence:   │
│      final_status = 'auto_validated'                   │
│  - Verifiers disagree or deterministic check fails:     │
│      final_status = 'needs_review' / 'auto_rejected'   │
│  - review_status = 'pending' (NEVER human_verified)    │
└────────────────────────────────────────────────────────┘
```

---

## 5. Extended Benchmark CSV Schema

The expanded benchmark preserves the 20 canonical columns from M3 and appends 6 structured columns for M6:

```
 1. candidate_id             (str, UUID v4 or deterministic hex ID)
 2. original_question        (str, verbatim question text)
 3. query_language           (str, enum: en, hi, hi-en, hi-Latn)
 4. query_script             (str, enum: Latin, Devanagari)
 5. question_type            (str, enum: direct, numerical, multi_part, conditional, temporal)
 6. answerability            (str, enum: answerable, unanswerable)
 7. reference_answer         (str, gold answer or official abstention statement)
 8. source_document_id       (str, document UUID or 'out_of_scope')
 9. clause                   (str, regulatory clause, e.g., '15.7', '30.1', 'N/A')
10. page_number              (int, 1-indexed document page number, or -1)
11. section                  (str, section heading from document hierarchy)
12. gold_evidence_quotes     (str, JSON list of exact quote substrings)
13. academic_year            (str, e.g., '2026-27', 'Current UG Regulations', 'N/A')
14. program_scope            (str, e.g., 'Undergraduate (B.Tech, BCA, B.Sc)', 'All')
15. generator_model          (str, model that generated candidate)
16. verifier_models          (str, comma-separated list of independent verifiers)
17. deterministic_validation (str, enum: PASSED, FAILED)
18. linguistic_validation    (str, enum: VALID, INVALID)
19. final_status             (str, enum: auto_validated, needs_review, auto_rejected)
20. review_status            (str, enum: pending, human_verified, rejected)
-- M6 Extended Attributes --
21. provenance_cohort        (str, enum: m3_frozen_core, m6_expanded_answerable, m6_expanded_unanswerable)
22. primary_taxonomy         (str, enum: direct_factual, numerical_tabular, multi_part, conditional_exception, temporal_version, out_of_domain, absent_policy, clarification_required, unresolvable_conflict)
23. secondary_taxonomies     (str, JSON list of overlapping tags)
24. expected_evidence_state  (str, enum: SUFFICIENT, PARTIAL, INSUFFICIENT, CONFLICTING, MISSING, CLARIFICATION_REQUIRED)
25. gold_passage_ids         (str, JSON list of matching 142 child passage IDs)
26. missing_parameters       (str, JSON list of missing parameters, e.g. ["academic_year"], or [])
```
