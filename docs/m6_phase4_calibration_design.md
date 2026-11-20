# IndicRAG-QA — M6 Phase 4: Calibration Design & Framework Specification

**Document Title:** Theory-Anchored Exploratory Calibration Framework for Multilingual Regulatory RAG  
**Milestone:** M6 — Evidence Reliability and Answerability  
**Phase:** Phase 4 (Exploratory Calibration & Milestone Synthesis)  
**Date:** 2026-11-11  
**Author:** Senior RAG Evaluation Researcher, Statistical Calibration Specialist & Evidence Reliability Engineer  
**Authorization State:** `PHASE_4_AUTHORIZED_EXPLORATORY_ONLY`  

---

## 1. Executive Summary and Authorization Boundaries

Milestone M6 Phase 4 investigates whether evidence-retrieval scores and heuristic confidence metrics can be reliably mapped to empirical answerability probabilities on the IndicRAG-QA benchmark.

Under strict adherence to the authorization mandate (**`PHASE_4_AUTHORIZED_EXPLORATORY_ONLY`**):
1. **No Production Claims:** This implementation is an offline, research-only diagnostic tool. No claim of production-grade calibration or universal statistical validity is asserted.
2. **Safety Rule Invariance:** The calibrated probabilities do **NOT** modify or replace runtime EvidenceController logic. Deterministic contradiction suppression, version-conflict disclaimers, ungrounded claim purges, and zero-citation short-circuits remain unconditionally authoritative over any continuous score.
3. **No Conflation of Confidence and Correctness:** Retrieval confidence, evidence sufficiency, and factual answer accuracy represent distinct orthogonal dimensions and are evaluated separately.

---

## 2. Cohort Lineage and Dataset Partitioning

To avoid data leakage, double-counting, and spurious calibration fits, all benchmark items across the project lifecycle are strictly partitioned into distinct provenance cohorts:

| Partition Cohort | Source Dataset | Candidate Count | Answerable ($N_{\text{pos}}$) | Unanswerable ($N_{\text{neg}}$) | Target B Calibration Status | Rationale & Handling |
|---|---|---|---|---|---|---|
| **Pilot Primary Eligible** | `m6_expanded_benchmark_n60.csv` | **29** | 27 | 2 | **ELIGIBLE** | Auto-validated in Phase 2A audit; audited expected states. |
| **Pilot Quarantined Excluded** | `m6_expanded_benchmark_n60.csv` | **31** | 13 | 18 | **EXCLUDED** | Fails independent verification or has unconfirmed labels. Quarantined. |
| **Qualified Negatives** | `m6_phase3_negative_candidates.csv` | **22** | 0 | 22 | **ELIGIBLE** | Certified missing/out-of-domain/unindexed policies. |
| **Qualified Answerable Controls** | `m6_phase3_negative_candidates.csv` | **5** | 5 | 0 | **ELIGIBLE** | Certified direct corpus refutations and explicit precedence cases. |
| **Unresolved Adjudication Negatives** | `m6_phase3_negative_candidates.csv` | **6** | 0 | 6 (unresolved) | **EXCLUDED** | Ambiguous student cohort dependency; excluded from primary calibration. |
| **Total Universe** | — | **93** | **45** | **48** | **56 Active / 37 Excluded** | Complete reconciliation without overlap or double counting. |

The effective sample size for Target B calibration is exactly **$N = 56$** ($N_{\text{pos}} = 32$, $N_{\text{neg}} = 24$, class prevalence: $57.1\%$ answerable vs $42.9\%$ unanswerable).

---

## 3. Calibration Targets Specification

We formalize three distinct calibration targets:

### Target A: Retrieval Relevance
- **Objective:** Evaluate whether raw retrieval scores predict passage-level semantic relevance.
- **Score Types Examined:** BM25 lexical score, Dense FAISS cosine similarity, Reciprocal Rank Fusion (RRF) scores, and Cross-Encoder reranker logits.
- **Methodological Rule:** Never pool scores across different scoring scales or different retrieval modalities into a single unnormalized distribution.

### Target B: Evidence Sufficiency and Answerability
- **Objective:** Map query-level evidence indicators to the empirical probability that the query is answerable from the institutional corpus.
- **Predictors Evaluated:**
  1. *Heuristic CECI:* The composite index combining top-1 relevance, score margin, modality consensus, keyword coverage, and regulatory fit.
  2. *Top-1 Raw Retrieval Score:* The maximum hybrid score of the retrieved passages.
  3. *F1 Relevance Component:* The normalized cross-encoder top-1 feature.
- **Ground Truth Mapping:** Binary answerability ($y \in \{0, 1\}$) defined strictly by qualified audit labels ($1 = \text{answerable}$, $0 = \text{unanswerable}$). Multi-state transitions (e.g. `CLARIFICATION_REQUIRED`, `CONFLICTING`) are reported in separate confusion sub-analyses.

### Target C: Claim-Level Factual Grounding
- **Objective:** Predict whether an emitted answer claim is `ENTAILED`, `CONTRADICTED`, or `INSUFFICIENT_SUPPORT`.
- **Sample Limitation:** Across the 29 eligible pilot queries, only 3 claims are non-entailed (1 contradicted, 2 insufficient support). Fitting a parametric calibrator on 3 minority examples is statistically indefensible. Target C is therefore certified as a descriptive grounding audit, not an empirical probability model.

---

## 4. Exploratory Platt Scaling Formulation

For a scalar feature $s \in [0, 1]$, Platt scaling models the posterior probability via the logistic sigmoid:
$$P(Y = 1 \mid s) = \sigma(A \cdot s + B) = \frac{1}{1 + \exp(-(A \cdot s + B))}$$
where:
- $A \in \mathbb{R}$ is the calibration slope (discriminative scaling).
- $B \in \mathbb{R}$ is the calibration intercept (base-rate log-odds offset).

### Preventing Overfitting and Leakage:
1. **Out-of-Fold Cross-Validation:** Out-of-fold predictions are generated using Stratified 3-Fold Cross-Validation (ensuring $\ge 7$ negative examples per fold). A 5-fold split was rejected as it yields only 4 negatives per fold, producing extreme variance and degenerate fits.
2. **Grouping by Source Document:** Folds are stratified to prevent source passage and template leakage across train and validation splits.
3. **Parameter Clamping & Numerical Stability:** All logits $z = A \cdot s + B$ are computed with numerically stable sigmoids to avoid floating-point overflow. Missing scores default safely to $p = 0.5$ with an explicit metadata flag (`is_fallback: True`).

