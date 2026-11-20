# IndicRAG-QA — M6 Phase 2A Reconciliation Report: Benchmark Qualification Audit

**Date:** 2026-11-11 09:48:24  
**Milestone:** M6 — Evidence Reliability and Answerability  
**Phase:** Phase 2A Reconciliation: Benchmark Qualification Audit  
**Authoritative Evaluator:** Senior RAG Evaluation Researcher & Dataset Integrity Auditor  
**Corpus SHA-256:** `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d` (142 child passages, 30 parent sections)  
**Frozen M3 Baseline SHA-256:** `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` ($N=15$ verified immutable)  
**M6 Phase 2A Benchmark SHA-256:** `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` ($N=60$ verified immutable)  

---

## 1. Executive Summary

Following the completion of M6 Phase 2A, an exhaustive audit was conducted across all 60 benchmark instances to establish record-level scientific qualification before advancing to Phase 2B. 

### Key Audit Findings:
1. **Status Totals Reconciled:** 
   - `auto_validated`: **29 records** (15 frozen M3 + 14 new candidates).
   - `needs_review`: **24 records** (0 frozen M3 + 24 new candidates: 13 answerable, 11 unanswerable).
   - `auto_rejected`: **7 records** (0 frozen M3 + 7 new candidates: all 7 unanswerable).
   - `human_verified`: **0 records** (100% of records retain `review_status = 'pending'`; zero automated approvals converted to human verification).
2. **Provisional Evaluation Eligibility ($N=29$):**
   - **Eligible Answerables:** **27 instances** (13 M3 + 14 new M6).
   - **Eligible Unanswerables:** **2 instances** (2 M3: PhD dissertation fee and hostel mess refund; **0** new M6 candidates).
3. **Severe Class Imbalance in Eligible Set:**
   - The provisional eligible set contains **27 positive (answerable) and only 2 negative (unanswerable)** records.
4. **Calibration Feasibility Verdict: INFEASIBLE FOR EMPIRICAL FITTING:**
   - **Nested 5-fold cross-fitting is mathematically impossible on $N=2$ unanswerables.** Under a 5-fold partition of 2 negative instances, at least 3 folds will contain zero negative instances in their test or train splits. Fitting empirical Platt scaling, logistic regression, or empirical threshold optimization on zero negatives yields non-convergent optimization, infinite odds ratios, and degenerate Wilson confidence intervals.
   - **Recommendation:** Designate the dataset as a **Pilot Benchmark**. For Phase 2B, use **theory-anchored heuristic thresholds** (e.g. standard sigmoid inflection $\alpha=0.5$ and normalized rank thresholds) for rule-based evidence gating, rather than empirically fitting parameters to 2 negative examples.

---

## 2. Benchmark Qualification Ledger ($N=60$)

The complete audit ledger has been written to [`backend/data/dataset/m6_benchmark_qualification.csv`](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/dataset/m6_benchmark_qualification.csv).

| Category | Answerable | Unanswerable | Total Count | Scientific Eligibility Status |
|---|---|---|---|---|
| **`auto_validated` (M3 Core)** | 13 | 2 | **15** | `ELIGIBLE_PROVISIONAL` |
| **`auto_validated` (M6 New)** | 14 | 0 | **14** | `ELIGIBLE_PROVISIONAL` |
| **`needs_review` (M6 New)** | 13 | 11 | **24** | `EXCLUDED_NEEDS_REVIEW` |
| **`auto_rejected` (M6 New)** | 0 | 7 | **7** | `EXCLUDED_AUTO_REJECTED` |
| **TOTAL** | **40** | **20** | **60** | **29 Eligible, 31 Excluded** |

---

## 3. Stratification Breakdown of Eligible Subset ($N=29$)

### By Language Modality:
- **English (`en`):** 14 (13 answerable, 1 unanswerable)
- **Natural Devanagari Hindi (`hi`):** 10 (9 answerable, 1 unanswerable)
- **Code-Mixed Hinglish (`hi-en`):** 3 (3 answerable, 0 unanswerable)
- **Romanized Hindi (`hi-Latn`):** 2 (2 answerable, 0 unanswerable)
- **Total:** **29**

### By Semantic Taxonomy:
- **Direct Factual Regulatory:** 13 (all answerable)
- **Numerical & Tabular:** 8 (all answerable)
- **Multi-Part Procedures:** 3 (all answerable)
- **Conditional Debarment & Exceptions:** 2 (all answerable)
- **Temporal & Calendar Versioning:** 1 (all answerable)
- **Out-of-Domain Unanswerable:** 2 (`b0a1c010`, `b0a1c011`)
- **Absent Policy / Clarification / Contradiction Unanswerable:** **0**

---

## 4. Root-Cause Analysis of Excluded Records ($N=31$)

### Why Did 0 New Unanswerable Candidates Qualify as `auto_validated`?
Among the 18 new unanswerable candidates generated in Phase 2A, 11 were assigned `needs_review` and 7 were assigned `auto_rejected`. Zero candidates achieved dual `ACCEPT` verifier consensus.
1. **Verifier Prompt Asymmetry:** The automated verifier prompt (`_VERIFIER_USER_PROMPT_TEMPLATE`) assesses `evidence_support: bool`. When an unanswerable query has `(No evidence passages cited)`, `qwen2.5:3b` strictly returns `REJECT` because "no supporting evidence passages are provided", while `llama3.2:3b` either concurs or generates `UNCERTAIN`.
2. **Ambiguity Over Unanswerability Explication:** In cases where reference answers explained why a policy is missing ("UNANSWERABLE — The official regulations do not contain pet policies..."), `llama3.2:3b` occasionally flagged this as a factual statement, returning `REJECT` under the belief that the query is "answerable" by the explanation itself.
3. **Research Implication:** Automated LLM verifiers exhibit high precision on positive factual retrieval, but exhibit systematic prompt-induced failure on negative/unanswerable queries. Human adjudication is strictly mandatory before negative examples can be elevated to gold status.

### Why Were 13 Answerable Candidates Placed in `needs_review`?
1. **JSON Extraction Anomaly (1 instance):** Candidate `c60a-e09` suffered a model output formatting failure where nested quotation characters in the LLM output broke the regex/json parser, triggering fallback `UNCERTAIN` verdicts.
2. **Strict Verifier Divergence on Non-English Modalities (12 instances):** For candidates 16 through 27 (Hinglish and Romanized Hindi), `qwen2.5:3b` consistently rejected candidates on strict literal phrasing or morphological differences, whereas `gemma:2b` or `llama3.2:3b` accepted them. Under conservative research protocol, any verifier disagreement mandates `needs_review`.

---

## 5. Claim, Passage Grounding, and Applicability Audit

For all 27 eligible answerable candidates:
1. **Exact Quotation Containment:** 
   - 100% of the 14 new M6 eligible answerables possess exact, verbatim substring matches in SQLite `passages.text`.
   - The 13 M3 core answerables possess verified semantic grounding in SCSET UG Rules / SEAS Ordinances (7 exact verbatim matches, 6 with minor whitespace/newline normalization or cross-ordinance provenance).
2. **Numerical & Date Verification:**
   - Verified 75% minimum attendance requirement (Notification 307/2022).
   - Verified 70% historical attendance requirement (2017 Ordinance, Clause 30.1).
   - Verified 30 marks start threshold for 'D' grade (Clause 15.7).
   - Verified 4 years minimum duration for B.Tech (Clause 1).
   - Verified 5 days makeup examination submission window (Clause 16.1).
   - Verified 2 weeks course withdrawal window (Clause 8.7).
   - Verified 1 week course add/drop window (Clause 8.7).
   - Verified 03-12-2026 teaching end date and 30-11-2026 condonation deadline (Calendar 2026-27).
   - Verified 21 days continuous absence roll strike-off (2017 Ordinance, Clause 31.1).
3. **Negations & Exceptions Verified:**
   - "Any student, who has been awarded X grade... shall not be allowed to take the supplementary Examination" (verified exact).
   - "In case a student misses the make-up Examination also, then no further chance will be provided" (verified exact).
4. **Applicability Scopes Verified:**
   - Academic cohorts, program scopes (Undergraduate B.Tech, BCA, B.Sc), and superseding notifications are accurately tagged.

---

## 6. Scientific Feasibility Assessment for Phase 2B

### Formal Question: Is Phase 2B Empirical Fitting Feasible?
**No. Statistical calibration (nested 5-fold cross-fitting, empirical Platt scaling, or empirical ROC threshold optimization) cannot be scientifically conducted on the qualified set.**

### Mathematical & Methodological Rationale:
1. **Sample Size Breakdown:** The qualified benchmark contains $N=29$ instances with $N_{pos}=27$ and $N_{neg}=2$.
2. **Fold Degeneracy:** In a 5-fold cross-validation scheme, 3 out of 5 folds will have $0$ negative instances in their test or validation splits.
3. **Optimizer Non-Convergence:** Maximum likelihood estimation for Platt scaling parameters $(A, B)$ in $\sigma(A \cdot s + B)$ with 0 or 1 negative instance fails to converge ($A \to \infty$ or degenerate probabilities).
4. **Wilson Confidence Interval Collapse:** With $N=2$ unanswerables, the Wilson 95% score interval for unanswerable recall spans $[0.342, 1.000]$ (if 2/2 correct) or $[0.095, 0.905]$ (if 1/2 correct), providing zero statistical discriminative power.

### Recommended Scientific Protocol for Phase 2B:
1. **Designate Benchmark as Pilot ($N=29$ Qualified / $N=60$ Full):** Acknowledge that the current benchmark is a pilot benchmark for directional architectural evaluation.
2. **Theory-Anchored / Heuristic Calibration:** Implement Phase 2B score normalization and the CECI estimator using **rule-based, theoretical anchors**:
   - BM25: Anchored sigmoid using median score threshold ($\mu=15.0, s=3.0$).
   - Dense & Cross-Encoder: Pre-calibrated cosine / logit mappings ($A=1.0, B=0.0$).
   - RRF: Normalized rank index $[0, 1]$.
    - Evidence Controller: 6 canonical states gated by fixed heuristic thresholds (tau_suff=0.65, tau_insuff=0.35) rather than overfitted empirical cutoffs.
3. **Future Formal Calibration:** Defer empirical nested cross-fitting until human adjudication resolves the 24 `needs_review` candidates.

---

## 7. Deliverables & Artifacts Generated

1. [**`backend/data/dataset/m6_benchmark_qualification.csv`**](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/dataset/m6_benchmark_qualification.csv) (Complete 60-row qualified audit ledger).
2. [**`backend/data/experiments/m6/m6_phase2a_reconciliation_manifest.json`**](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m6/m6_phase2a_reconciliation_manifest.json) (Machine-readable audit manifest).
3. [**`docs/m6_phase2a_reconciliation_report.md`**](file:///C:/Users/anish/Desktop/IndicRAG-QA/docs/m6_phase2a_reconciliation_report.md) (This report).
