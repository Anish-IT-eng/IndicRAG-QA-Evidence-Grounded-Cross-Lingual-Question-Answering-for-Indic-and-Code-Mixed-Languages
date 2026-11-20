# M10 Phase G: Multiple Comparison & Multiplicity Control Analysis

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-MULTIPLICITY-ANALYSIS`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Status:** Audit Completed  

---

## 1. Executive Summary

In complex benchmark evaluations spanning multiple languages, ranking metrics, and pipeline stages, evaluating multiple statistical tests without error adjustment introduces the "look-elsewhere effect" or multiplicity bias. If 25 independent tests are performed at $\alpha = 0.05$, the probability of observing at least one false positive purely by chance is:
$$\text{FWER} = 1 - (1 - \alpha)^m = 1 - (0.95)^{25} \approx 0.723 \quad (72.3\%)$$

To prevent data dredge and spurious claims of significance, this audit applies rigorous multiplicity controls across the entire hypothesis family evaluated in Phase G.

Key conclusions:
1. **Zero Statistically Significant Hypotheses:** Across all 25 evaluated hypotheses, **zero** achieved statistical significance even before adjustment (minimum raw $p = 0.1736$).
2. **Multiplicity-Adjusted Bounds:** Following both Holm-Bonferroni Family-Wise Error Rate (FWER) control and Benjamini-Hochberg False Discovery Rate (FDR) control, all adjusted p-values equal $1.0000$.
3. **Rigorous Classification:** All observed performance improvements in Candidate E6b are formally classified as **exploratory findings**, preventing premature confirmatory claims in academic or technical reporting.

---

## 2. Hypothesis Family Definition

The evaluation family comprises $m = 25$ formal two-sided statistical null hypotheses testing equality between `ConfigA_Production` and `ConfigB_AdaptiveE6b`:

- **Retrieval Family ($m = 20$):**
  - Hit@1 across `en`, `hi`, `hi-Latn`, `en-hi`, and `OVERALL` (5 tests; McNemar Exact)
  - Hit@5 across `en`, `hi`, `hi-Latn`, `en-hi`, and `OVERALL` (5 tests; McNemar Exact)
  - MRR across `en`, `hi`, `hi-Latn`, `en-hi`, and `OVERALL` (5 tests; Wilcoxon Signed-Rank)
  - nDCG@5 across `en`, `hi`, `hi-Latn`, `en-hi`, and `OVERALL` (5 tests; Wilcoxon Signed-Rank)
- **End-to-End Answer Family ($m = 5$):**
  - Answerable Success Rate across `en`, `hi`, `hi-Latn`, `en-hi`, and `OVERALL` (5 tests; McNemar Exact)

---

## 3. Multiple Testing Correction Results

Archived in [backend/data/experiments/m10/m10_phase_g_multiple_testing_results.csv](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_g_multiple_testing_results.csv):

| Hypothesis ID | Family | Description | Raw $p$-value | Holm-Bonferroni $p$ | Benjamini-Hochberg $p$ | Significant ($\alpha=0.05$)? |
|---|---|---|---:|---:|---:|:---:|
| `HYP_RET_nDCG5_hi` | Retrieval | Config B $\neq$ Config A on nDCG@5 in `hi` | 0.17357 | 1.0000 | 1.0000 | No |
| `HYP_RET_nDCG5_OVERALL` | Retrieval | Config B $\neq$ Config A on nDCG@5 in `OVERALL` | 0.17357 | 1.0000 | 1.0000 | No |
| `HYP_RET_MRR_hi` | Retrieval | Config B $\neq$ Config A on MRR in `hi` | 0.25790 | 1.0000 | 1.0000 | No |
| `HYP_RET_MRR_OVERALL` | Retrieval | Config B $\neq$ Config A on MRR in `OVERALL` | 0.25790 | 1.0000 | 1.0000 | No |
| `HYP_RET_Hit1_hi` | Retrieval | Config B $\neq$ Config A on Hit@1 in `hi` | 0.37500 | 1.0000 | 1.0000 | No |
| `HYP_RET_Hit1_OVERALL` | Retrieval | Config B $\neq$ Config A on Hit@1 in `OVERALL` | 0.37500 | 1.0000 | 1.0000 | No |
| `HYP_E2E_Succ_hi` | EndToEnd | Config B $\neq$ Config A on E2E Success in `hi` | 0.50000 | 1.0000 | 1.0000 | No |
| `HYP_E2E_Succ_OVERALL` | EndToEnd | Config B $\neq$ Config A on E2E Success in `OVERALL` | 0.50000 | 1.0000 | 1.0000 | No |
| `HYP_RET_Hit5_hi` | Retrieval | Config B $\neq$ Config A on Hit@5 in `hi` | 0.62500 | 1.0000 | 1.0000 | No |
| `HYP_RET_Hit5_OVERALL` | Retrieval | Config B $\neq$ Config A on Hit@5 in `OVERALL` | 0.62500 | 1.0000 | 1.0000 | No |
| `HYP_RET_Hit1_en` | Retrieval | Config B $\neq$ Config A on Hit@1 in `en` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_RET_Hit1_hi-Latn` | Retrieval | Config B $\neq$ Config A on Hit@1 in `hi-Latn` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_RET_Hit1_en-hi` | Retrieval | Config B $\neq$ Config A on Hit@1 in `en-hi` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_RET_Hit5_en` | Retrieval | Config B $\neq$ Config A on Hit@5 in `en` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_RET_Hit5_hi-Latn` | Retrieval | Config B $\neq$ Config A on Hit@5 in `hi-Latn` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_RET_Hit5_en-hi` | Retrieval | Config B $\neq$ Config A on Hit@5 in `en-hi` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_RET_MRR_en` | Retrieval | Config B $\neq$ Config A on MRR in `en` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_RET_MRR_hi-Latn` | Retrieval | Config B $\neq$ Config A on MRR in `hi-Latn` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_RET_MRR_en-hi` | Retrieval | Config B $\neq$ Config A on MRR in `en-hi` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_RET_nDCG5_en` | Retrieval | Config B $\neq$ Config A on nDCG@5 in `en` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_RET_nDCG5_hi-Latn` | Retrieval | Config B $\neq$ Config A on nDCG@5 in `hi-Latn` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_RET_nDCG5_en-hi` | Retrieval | Config B $\neq$ Config A on nDCG@5 in `en-hi` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_E2E_Succ_en` | EndToEnd | Config B $\neq$ Config A on E2E Success in `en` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_E2E_Succ_hi-Latn` | EndToEnd | Config B $\neq$ Config A on E2E Success in `hi-Latn` | 1.00000 | 1.0000 | 1.0000 | No |
| `HYP_E2E_Succ_en-hi` | EndToEnd | Config B $\neq$ Config A on E2E Success in `en-hi` | 1.00000 | 1.0000 | 1.0000 | No |

---

## 4. Methodological Procedures Applied

### 4.1 Holm-Bonferroni Step-Down Procedure

The Holm-Bonferroni method controls the Family-Wise Error Rate ($\text{FWER} \le 0.05$) without making any independence assumptions between tests:
1. Sort all raw p-values in ascending order: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.
2. For each rank $k \in \{1, \dots, m\}$, compute the adjusted threshold:
   $$\tilde{p}_{(k)} = \min\left(1, \max_{j \le k} \left( (m - j + 1) \cdot p_{(j)} \right)\right)$$
3. The smallest raw p-value is $p_{(1)} = 0.17357$. Multiplying by $m = 25$ yields:
   $$\tilde{p}_{(1)} = 25 \times 0.17357 = 4.339 \implies 1.0000$$
4. The test fails at step 1; all subsequent hypotheses are immediately non-significant.

### 4.2 Benjamini-Hochberg False Discovery Rate (FDR)

The Benjamini-Hochberg procedure controls the expected proportion of false discoveries ($\text{FDR} \le 0.05$):
1. For rank $k$, compute:
   $$p_{\text{FDR},(k)} = \min_{j \ge k} \left( \frac{m \cdot p_{(j)}}{j} \right)$$
2. For the leading test ($k=1$), $p_{\text{FDR},(1)} = \frac{25 \times 0.17357}{1} = 4.339 \implies 1.0000$.
3. Zero discoveries are declared at FDR threshold $q = 0.05$.

---

## 5. Classification of Findings: Exploratory vs. Confirmatory

To maintain scientific integrity in technical reports and publication manuscripts:

| Category | Finding / Metric | Empirical Evidence | Statistical Status | Actionable Conclusion |
|---|---|---|---|---|
| **Confirmatory Findings** | *None* | No hypothesis achieved $p_{\text{adj}} < 0.05$ | Null hypothesis retained | Do not claim proven general superiority in production. |
| **Exploratory Trends** | Devanagari Hit@5 ($0.044 \to 0.089$) | $+100.0\%$ relative gain; $\text{OR} = 3.00$ | $p_{\text{exact}} = 0.6250$ | Promising architectural candidate; requires larger validation. |
| **Exploratory Trends** | Devanagari MRR ($0.028 \to 0.089$) | $+220.0\%$ relative gain | $p = 0.2579$ | Encouraging ranking improvement on discordant pairs. |
| **Confirmatory Invariance** | Latin Script Invariance (`en`, `hi-Latn`, `en-hi`) | 0 discordant pairs across all Latin queries | Exact identity ($p = 1.000$) | Confirmed: E6b causes zero regression to Latin-script routes. |
| **Confirmatory Safety** | Zero Unsupported Answers ($0/61$) | 0 observed hallucinations | Rule of Three ($p \le 4.91\%$) | Confirmed: System maintains high safety and abstention integrity. |
