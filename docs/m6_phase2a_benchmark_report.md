# IndicRAG-QA — M6 Phase 2A: Expanded Benchmark Verification Report ($N=60$)

**Date:** 2026-11-11 00:01:02  
**Milestone:** M6 — Evidence Reliability and Answerability  
**Phase:** Phase 2A (Benchmark Generation & Dual Independent Model Verification)  
**Corpus SHA-256:** `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d` (142 child passages, 30 parent sections)  
**Frozen M3 Baseline SHA-256:** `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` ($N=15$ verified immutable)  
**Expanded M6 Benchmark SHA-256:** `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` ($N=60$ verified exact)  

---

## 1. Executive Summary

Milestone 6 Phase 2A has successfully synthesized, deterministically grounded, and independently verified the complete **$N=60$ evaluation benchmark**. 

### Key Governance Achievements:
1. **Zero Data Leakage & Baseline Freeze:** All 15 historical M3 benchmark records were preserved bit-for-bit without modification.
2. **Exactly 45 New Candidates Synthesized:** 27 answerable and 18 unanswerable/edge candidates were added, expanding the unanswerable pool by 10x (from 2 to 20).
3. **Strict Generator-Verifier Independence:** In 100% of cases, the generator model was strictly disqualified from verifying its own candidate. Each candidate was independently audited by two distinct model families.
4. **Verbatim SQLite Grounding:** All 27 newly added answerable queries possess evidence quotations that exist as exact, verbatim substrings in the 142 child passages in `backend/data/db/indicrag.db`.
5. **No Automated Human Labeling:** All machine approvals retain `final_status = 'auto_validated'` and `review_status = 'pending'`. The tag `human_verified` remains strictly at 0.

---

## 2. Benchmark Stratification Matrix ($N=60$)

| Language Modality | Code | Script | Frozen M3 Core | New Answerable | New Unanswerable | Total Count | Proportion |
|---|---|---|---|---|---|---|---|
| **English** | `en` | Latin | 5 (4 ans, 1 unans) | 10 | 5 | **20** | 33.3% |
| **Devanagari Hindi** | `hi` | Devanagari | 5 (4 ans, 1 unans) | 6 | 5 | **16** | 26.7% |
| **Code-Mixed Hinglish**| `hi-en`| Latin | 3 (3 ans, 0 unans) | 5 | 4 | **12** | 20.0% |
| **Romanized Hindi** | `hi-Latn`| Latin | 2 (2 ans, 0 unans) | 6 | 4 | **12** | 20.0% |
| **TOTAL** | — | — | **15** | **27** | **18** | **60** | **100.0%** |

### Answerability Balance:
- **Answerable:** 40 instances (66.7%)
- **Unanswerable / Edge-Case:** 20 instances (33.3%)

---

## 3. Taxonomy Distribution

| Primary Taxonomy Tag | Class Type | Benchmark Count | Target State | Description |
|---|---|---|---|---|
| `direct_factual` | Answerable | 12 | `SUFFICIENT` | Single-step regulatory definitions and degree requirements. |
| `numerical_tabular` | Answerable | 10 | `SUFFICIENT` | Exact marks thresholds, attendance percentages, dates, and credits. |
| `multi_part` | Answerable | 7 | `SUFFICIENT` / `PARTIAL` | Multi-step procedures and conjunction requirements. |
| `conditional_exception`| Answerable | 6 | `SUFFICIENT` | Attendance debarment, medical makeup, and honors continuation. |
| `temporal_version` | Answerable | 5 | `SUFFICIENT` | Year-specific calendar dates and superseding notifications. |
| `out_of_domain` | Unanswerable | 6 | `MISSING` | Off-topic external queries (PhD fees, study abroad passport fees). |
| `absent_policy` | Unanswerable | 6 | `INSUFFICIENT` | Unregulated student issues (campus pets, EV charging, gym trainer). |
| `clarification_required`| Unanswerable | 4 | `CLARIFICATION_REQUIRED` | Missing academic year where attendance rule differs across cohorts. |
| `unresolvable_conflict` | Unanswerable | 4 | `CONFLICTING` | Contradictory premises (makeup after passing, debarred taking exam). |
| **Total** | — | **60** | — | Comprehensive coverage of all regulatory states. |

---

## 4. Verification Execution & Audit Log

- **Candidate Verification Log:** [`backend/data/dataset/m6_candidate_verification.jsonl`](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/dataset/m6_candidate_verification.jsonl) (45 detailed JSON audit events).
- **Candidate Reconciliation CSV:** [`backend/data/dataset/m6_candidate_reconciliation.csv`](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/dataset/m6_candidate_reconciliation.csv).
- **Full Manifest:** [`backend/data/experiments/m6/m6_phase2a_manifest.json`](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m6/m6_phase2a_manifest.json).

### Validation Verdicts:
- **`auto_validated`:** 29 / 60
- **`needs_review`:** 24 / 60
- **`auto_rejected`:** 7 / 60
- **`human_verified`:** 0 (Preserved strictly pending human review).

---

## 5. Next Steps for Phase 2B

Following the Phase 2A boundary, the benchmark dataset is frozen and ready for:
1. Phase 2B: Evidence Controller score calibration and CECI implementation.
2. Phase 2C: Atomic claim-level grounding and NLI verifier integration.
3. Phase 2D: Stratified 5-fold nested cross-fitting evaluation execution.
