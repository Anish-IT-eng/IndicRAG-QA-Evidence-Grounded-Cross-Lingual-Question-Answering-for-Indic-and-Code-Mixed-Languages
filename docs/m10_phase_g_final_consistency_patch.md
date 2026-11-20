# M10 Phase G: Final Documentation Consistency Patch

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-FINAL-PATCH`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Patch Type:** Documentation-Only Consistency Patch  
**Final Determination:** `M10_PHASE_G_VERIFIED_WITH_LIMITATIONS`  

---

## 1. Scope & Execution Safeguards

This patch resolves the remaining documentation and statistical consistency issues identified during the Milestone M10 Phase G audit. In strict accordance with experimental integrity instructions:
- **Zero Code Modification:** Application code, retrieval engines, models, prompts, and configurations remain unmodified.
- **Production Runtime Default:** The runtime default in [engine.py](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py) remains strictly `"production"`.
- **Frozen Benchmarks Intact:** Datasets M3, M6, M8, M9, Phase E, and Phase F remain completely read-only and preserved.
- **Scientific Claims Calibrated:** No claim of confirmatory statistical significance is made for Devanagari retrieval; no post-hoc claim of formal statistical non-inferiority is made for Latin-script queries.

---

## 2. Resolution Summary of the Five Patch Directives

### Directive 1: Standardized M11 Sample-Size Wording
- **Total Independent Statistical Units:** **$225 - 230$ independent semantic intent groups in total**.
- **Query Architecture:** Each intent group is instantiated across four parallel language formulations (`en`, `hi`, `hi-Latn`, `en-hi`).
- **Total Query Records:** At $N = 230$ total intent groups, the benchmark contains exactly **$230 \times 4 = 920$ query records**.
- **Explicit Clarification:** The number $230$ is **not required separately for each language**. Sampling $230$ total intent groups automatically provides $230$ paired query instances in each language stratum.
- **Explicit Labeling of Planning Assumptions:** The discordance probability $p_D = 0.15$ and conditional win probability $\pi = 0.75$ (Odds Ratio $\psi = 3.00$) are explicitly designated as **planning assumptions**, not empirical constants.

---

### Directive 2: Exact Power Reproducibility & Unrounded Reconciliation
- **Executable Reproducibility Script:** [backend/experiments/m10/reproduce_power_and_cluster_tests.py](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/experiments/m10/reproduce_power_and_cluster_tests.py).
  - Executable under Python 3.13.5, SciPy 1.15.1, NumPy 2.4.6.
- **Reconciliation of $n_D = 30$ Null Rejection Probability:**
  - Critical Rejection Region: $C \le 9 \cup C \ge 21$.
  - Lower Tail: $P(C \le 9 \mid H_0) = \mathbf{0.0213869726} \le 0.025$.
  - Upper Tail: $P(C \ge 21 \mid H_0) = \mathbf{0.0213869726} \le 0.025$.
  - Exact Null Rejection Probability: $\alpha = 0.0213869726 + 0.0213869726 = \mathbf{0.0427739453}$ (rounded to $0.0428$ in narrative summaries).
  - Exact Two-Sided Power: $P(C \ge 21 \mid H_1) + P(C \le 9 \mid H_1) = 0.8034066369 + 2.8183 \times 10^{-7} = \mathbf{0.8034069188 \quad (80.34\%)}$.
- **Reconciliation of $n_D = 23$ One-Sided vs. Two-Sided Power:**
  - One-Sided Power ($C \ge 16$): $P(C \ge 16 \mid H_1) = \mathbf{0.8036966850 \quad (80.37\%)}$ at one-sided $\alpha = 0.0465698242$.
  - True Two-Sided Power ($C \le 6 \cup C \ge 17$): $P(C \ge 17 \mid H_1) + P(C \le 6 \mid H_1) = \mathbf{0.6537277951 \quad (65.37\%)}$ at two-sided $\alpha = 0.0346896648$.
- **Unconditional Power Values under $D \sim \text{Binomial}(N, 0.15)$:**
  - $N = 150 \implies \mathbf{0.601062 \quad (60.11\%)}$
  - $N = 220 \implies \mathbf{0.791441 \quad (79.14\%)}$
  - $N = 225 \implies \mathbf{0.802042 \quad (80.20\%)}$
  - $N = 230 \implies \mathbf{0.812236 \quad (81.22\%)}$

---

### Directive 3: Paired Confidence Interval & Non-Inferiority Terminology
- **Removal of Pseudo-Paired Interval:** The symmetrized single-proportion Wilson bound $[-0.0789, +0.0789]$ is formally removed as a paired confidence interval claim.
- **Preservation of Post-Hoc Retraction:** The post-hoc $8\%$ non-inferiority margin claim is formally retracted due to lack of a priori protocol pre-specification.
- **Retained Empirical Standard:** All reporting strictly maintains the verified observation:
  > **"Zero observed regressions in the evaluated Latin-script sample."**

---

### Directive 4: Evidence Provenance & Independent Raw-Data Verification
- **Verification Hierarchy:**
  - Narrative report claims were distinguished from raw dataset verification.
  - The transcription error in Phase F narrative Table 2 ($26 + 15 = 41 \neq 45$) was identified.
  - Raw dataset [m10_phase_f_answer_correctness.csv](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_f_answer_correctness.csv) was verified row-by-row:
    - English: $25\text{ CA} + 3\text{ RD} = \mathbf{28}$ combined successes, $17\text{ UA}$ (Total $45$).
    - Devanagari Config B: $1\text{ CA (Q058)} + 1\text{ RD (Q002)} = \mathbf{2}$ combined successes, $43\text{ UA}$ (Total $45$).
    - Romanized: $13\text{ CA} + 1\text{ RD} = \mathbf{14}$ combined successes, $31\text{ UA}$ (Total $45$).
    - Hinglish: $14\text{ CA} + 3\text{ RD} = \mathbf{17}$ combined successes, $28\text{ UA}$ (Total $45$).
    - Overall Config A: $52\text{ CA (Strict)} \ / \ 59\text{ Combined}$ ($121\text{ UA}$, Total $180$).
    - Overall Config B: $53\text{ CA (Strict)} \ / \ 61\text{ Combined}$ ($119\text{ UA}$, Total $180$).
- **Direct Checksum Verification:** SHA-256 hashes of all input files were computed on the physical files on disk and verified to match.

---

### Directive 5: Final Determination & Milestone Status
- **Final Determination Retained:** **`M10_PHASE_G_VERIFIED_WITH_LIMITATIONS`**.
- **Production Default:** The runtime default in [engine.py](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py) remains `"production"`.
- **Sign-off Condition:** Phase H has not been started. All statistical corrections and limitations are fully documented and archived.
