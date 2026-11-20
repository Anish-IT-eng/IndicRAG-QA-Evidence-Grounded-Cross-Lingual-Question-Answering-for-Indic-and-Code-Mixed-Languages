# M10 Phase G: Non-Inferiority Terminology & Protocol Review

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-NONINFERIORITY-REVIEW`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Audit Status:** Completed  

---

## 1. Executive Summary

This audit critically reviews non-inferiority claims, paired confidence interval formulations, and protocol validity concerning Latin-script retrieval performance (English, Romanized Hindi, Hinglish) under Candidate `E6b_ADAPTIVE_BI_ENCODER`.

### Key Audit Findings:
1. **Invalidity of the Symmetrized Wilson Interval:** The previously reported interval $[-0.0789, +0.0789]$ was obtained by reflecting the Wilson score interval of a single binomial proportion ($[0, 0.0787]$ for $0/45$) around zero. This is a heuristic reflection, **not a formally derived confidence interval for paired differences** (such as Tango's score interval or Newcombe's paired method). It is formally removed from the project's statistical claims.
2. **Post-Hoc Margin Invalidation:** The $8\%$ non-inferiority margin ($\Delta_{\text{NI}} = 0.08$) cited in earlier reports was **not** pre-specified prior to data inspection. Selecting a non-inferiority margin post-hoc violates regulatory and statistical testing standards.
3. **Formal Non-Inferiority Retracted:** Because no pre-specified margin was established in the protocol and paired confidence interval bounds at $N=45$ are wide, all claims of "formal statistical non-inferiority" are formally retracted.
4. **Authoritative Standardized Terminology:** All project documentation must strictly use the empirical formulation:
   > **"Zero observed regressions in the evaluated Latin-script sample."**

---

## 2. Statistical Principles of Non-Inferiority Testing

In clinical and algorithmic evaluation (FDA/ICH E9 guidelines; Walker & Nowacki, 2011), a test of non-inferiority seeks to demonstrate that a new intervention (Config B) is not unacceptably worse than a reference standard (Config A) by more than a pre-specified margin $\Delta_{\text{NI}} > 0$:
$$H_0: p_B - p_A \le -\Delta_{\text{NI}} \quad \text{vs} \quad H_1: p_B - p_A > -\Delta_{\text{NI}}$$

Non-inferiority is formally established if and only if the **lower bound** of the two-sided $(1 - 2\alpha)$ or one-sided $(1 - \alpha)$ confidence interval for $(p_B - p_A)$ lies entirely above $-\Delta_{\text{NI}}$:
$$\text{CI}_{\text{lower}} > -\Delta_{\text{NI}}$$

### 2.1 The Requirement of Pre-Specification

A fundamental rule of non-inferiority trials is that $\Delta_{\text{NI}}$ must be defined **a priori** based on domain justification, completely independent of the observed experimental outcome:
1. If an analyst observes an empirical interval bound and subsequently declares $\Delta_{\text{NI}} = 0.080$ so that the interval fits within it, the test is circular and invalid.
2. An $8\%$ margin on an evaluation metric with baseline prevalence of $11.1\%$ (Hit@5) would allow a relative degradation of $\frac{0.08}{0.111} \approx 72\%$, which is substantive and unacceptable for production deployment.

---

## 3. Protocol Audit for Pre-Specified Margins

We inspected all previous milestone specifications and project documentation:
- M8.8 Closure Report (`docs/m8_8_reconciliation_audit.md`)
- M9 Cross-Lingual Evaluation Protocol (`docs/m9_cross_lingual_evaluation_report.md`)
- M10 Phase A Problem Specification (`scripts/audit_m10_phase_a.py`)
- M10 Phase E Experimental Plan (`docs/m10_phase_e_multilingual_reranker_report.md`)
- M10 Phase F Evaluation Protocol (`scripts/run_m10_phase_f_full_eval.py`)

### Audit Finding:
**Zero pre-specified non-inferiority margins exist in any protocol document.**
The $8\%$ threshold appeared for the first time in Milestone M10 Phase G. Consequently, it represents a post-hoc observation, not a pre-specified statistical hypothesis.

---

## 4. Empirical Reality: What the Data Actually Shows

The empirical data across the 45 English, 45 Romanized Hindi, and 45 Hinglish answerable queries ($135$ Latin-script queries total) shows:
- **Discordant Pairs:** $b = 0$ (Config A success, Config B failure), $c = 0$ (Config B success, Config A failure).
- **Concordant Pairs:** All $135$ paired evaluations produced identical outputs ($a = 18, d = 117$).
- **Sample Difference:** $\Delta = 0.0000$ (0.0%).
- **Exact Paired Test:** $p = 1.0000$.

### 4.1 Corrected Reporting Standard

| Unacceptable Claim | Correct Scientific Statement |
|---|---|
| *"Candidate E6b is statistically proven non-inferior on Latin scripts within an 8% margin."* | *"Zero observed regressions in the evaluated Latin-script sample."* |
| *"95% paired confidence interval [-0.0789, +0.0789] proves non-inferiority."* | *"The symmetrized single-proportion Wilson bound is retracted as a paired interval. Formal statistical non-inferiority is unproven due to the absence of a pre-specified margin."* |

---

## 5. Verification Determination

The post-hoc 8% non-inferiority claim and the symmetrized Wilson interval are formally **retracted**. Project reporting will strictly maintain the verified statement:
> **"Zero observed regressions in the evaluated Latin-script sample."**
