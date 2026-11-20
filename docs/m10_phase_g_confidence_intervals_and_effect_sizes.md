# M10 Phase G: Confidence Intervals & Effect Sizes

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-CI-EFFECT-SIZES`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Status:** Audit Completed  

---

## 1. Executive Summary

A common pitfall in empirical AI evaluation is relying solely on point estimates or p-values. A point estimate shows what occurred in a specific benchmark sample, while confidence intervals quantify the range of plausible values in the general population.

Key insights from this analysis:
1. **Substantive Effect Sizes:** Candidate E6b demonstrates substantively meaningful empirical effect sizes on Devanagari Hindi retrieval:
   - Hit@5 Odds Ratio: $\text{OR} = 3.00$; Cohen's $g = 0.250$ (medium effect).
   - Hit@1 Odds Ratio: $\text{OR} = 4.00$; Cohen's $g = 0.300$ (medium-to-large effect).
2. **Wide Confidence Intervals Crossing Zero:** Because $N=45$ and discordance is low ($n_D = 4$), the 95% confidence intervals for paired metric differences span zero:
   - Devanagari Hit@5 Difference: Point $= +0.0444$, 95% CI $[-0.0444, +0.1333]$.
   - Devanagari MRR Difference: Point $= +0.0611$, 95% CI $[-0.0222, +0.1501]$.
3. **Exploratory Status:** Because the confidence intervals encompass both positive gains and zero (or slight negative outcomes), E6b represents an **exploratory pilot improvement** rather than a confirmed population advantage.
4. **Safety Confidence Interval:** The Unsupported Answer Rate is $0.0\%$, with a 95% upper confidence bound of $4.91\%$ under the Rule of Three.

---

## 2. Wilson Score Confidence Intervals for Proportions

Standard Wald confidence intervals ($\hat{p} \pm z \sqrt{\hat{p}(1-\hat{p})/n}$) fail when $\hat{p}$ is close to 0 or 1, producing intervals that violate probability boundaries ($< 0$ or $> 1$). The **Wilson Score Interval** provides asymmetric, bounded, and robust coverage for binomial proportions:
$$w = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1 - \hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$

Archived in [backend/data/experiments/m10/m10_phase_g_confidence_intervals.csv](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_g_confidence_intervals.csv):

| Metric | Language | Configuration | Point Estimate | 95% Wilson CI Lower | 95% Wilson CI Upper |
|---|---|---|---:|---:|---:|
| **Hit@1** | Devanagari (`hi`) | Config A (Prod) | 0.0222 (1/45) | 0.0039 | 0.1157 |
| Hit@1 | Devanagari (`hi`) | Config B (E6b) | 0.0889 (4/45) | 0.0351 | 0.2073 |
| **Hit@5** | Devanagari (`hi`) | Config A (Prod) | 0.0444 (2/45) | 0.0123 | 0.1483 |
| Hit@5 | Devanagari (`hi`) | Config B (E6b) | 0.0889 (4/45) | 0.0351 | 0.2073 |
| Hit@5 | English (`en`) | Both Configs | 0.1111 (5/45) | 0.0484 | 0.2350 |
| Hit@5 | Romanized (`hi-Latn`) | Both Configs | 0.1333 (6/45) | 0.0626 | 0.2618 |
| Hit@5 | Hinglish (`en-hi`) | Both Configs | 0.1111 (5/45) | 0.0484 | 0.2350 |
| Hit@5 | Overall ($N=180$) | Config A (Prod) | 0.1000 (18/180) | 0.0642 | 0.1525 |
| Hit@5 | Overall ($N=180$) | Config B (E6b) | 0.1111 (20/180) | 0.0731 | 0.1654 |
| **Correct Abstention** | Devanagari (`hi`) | Both Configs | 1.0000 (15/15) | 0.7961 | 1.0000 |
| Correct Abstention | English (`en`) | Both Configs | 0.8667 (13/15) | 0.6212 | 0.9626 |
| Correct Abstention | Overall ($N=60$) | Both Configs | 0.9667 (58/60) | 0.8864 | 0.9908 |
| **Unsupported Answer** | Overall ($N=61$) | Config B (E6b) | 0.0000 (0/61) | 0.0000 | **0.0491** |

*Note: The upper bound for Unsupported Answer Rate is computed via the exact Rule of Three ($\approx 3/N$).*

---

## 3. Clustered Block Bootstrap Resampling

To estimate confidence intervals for paired metric differences without assuming asymptotic normality or independent observations across languages, we executed a **Clustered Block Bootstrap** with:
- **Resampling Unit:** Semantic Intent Group ($K=45$ answerable clusters).
- **Iterations:** $B = 10,000$ iterations with pseudo-random seed $42$.
- **Method:** Paired difference per cluster resampled with replacement; 2.5th and 97.5th percentiles define the 95% confidence interval.

Archived in [backend/data/experiments/m10/m10_phase_g_bootstrap_results.csv](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_g_bootstrap_results.csv):

| Metric | Language | Clusters ($K$) | Mean Config A | Mean Config B | Point Diff ($\Delta$) | Bootstrap 95% CI Lower | Bootstrap 95% CI Upper | Spans Zero? |
|---|---|---:|---:|---:|---:|---:|---:|:---:|
| **Hit@1** | Devanagari (`hi`) | 45 | 0.0222 | 0.0889 | **+0.0667** | -0.0222 | +0.1556 | **Yes** |
| **Hit@5** | Devanagari (`hi`) | 45 | 0.0444 | 0.0889 | **+0.0444** | -0.0444 | +0.1333 | **Yes** |
| **MRR** | Devanagari (`hi`) | 45 | 0.0278 | 0.0889 | **+0.0611** | -0.0222 | +0.1501 | **Yes** |
| **nDCG@5** | Devanagari (`hi`) | 45 | 0.0195 | 0.0717 | **+0.0522** | -0.0136 | +0.1275 | **Yes** |
| **Hit@1** | English (`en`) | 45 | 0.0889 | 0.0889 | 0.0000 | 0.0000 | 0.0000 | Identical |
| **Hit@5** | English (`en`) | 45 | 0.1111 | 0.1111 | 0.0000 | 0.0000 | 0.0000 | Identical |
| **Hit@1** | Overall Pooled | 45 | 0.0889 | 0.1056 | **+0.0167** | -0.0056 | +0.0389 | **Yes** |
| **Hit@5** | Overall Pooled | 45 | 0.1000 | 0.1111 | **+0.0111** | -0.0111 | +0.0333 | **Yes** |
| **MRR** | Overall Pooled | 45 | 0.0931 | 0.1083 | **+0.0153** | -0.0056 | +0.0375 | **Yes** |
| **nDCG@5** | Overall Pooled | 45 | 0.0784 | 0.0914 | **+0.0130** | -0.0034 | +0.0319 | **Yes** |

### 3.1 Interpretation of Bootstrap Findings

1. In every evaluated metric, the point estimate of the difference $\Delta = \bar{X}_B - \bar{X}_A$ is strictly positive ($\Delta > 0$).
2. In every evaluated metric, the 95% bootstrap confidence interval extends below zero (e.g., Hit@5 lower bound is $-0.0444$).
3. This occurs because in resampled pseudo-datasets where intent `INT-018` (the single regression where Config A succeeded and Config B failed) is sampled multiple times while intents `INT-002`, `INT-010`, and `INT-030` are omitted, Config A outperforms Config B.
4. Hence, while the expected trend is favorable, the current benchmark size cannot rule out zero difference at the 95% confidence level.

---

## 4. Effect Size Measures for Paired Binary Outcomes

To characterize the practical magnitude of the retrieval recovery independent of sample size:

### 4.1 Cohen's $g$

For paired binary data evaluated under McNemar's test, **Cohen's $g$** measures the departure of discordant pairs from symmetry ($p = 0.5$):
$$g = \frac{c - b}{2(b + c)}$$
- Standard thresholds: small ($g = 0.05$), medium ($g = 0.15$), large ($g = 0.25$).

For Devanagari Hindi:
- **Hit@1 ($b=1, c=4$):**
  $$g = \frac{4 - 1}{2(1 + 4)} = \frac{3}{10} = \mathbf{0.300} \quad (\text{Large effect})$$
- **Hit@5 ($b=1, c=3$):**
  $$g = \frac{3 - 1}{2(1 + 3)} = \frac{2}{8} = \mathbf{0.250} \quad (\text{Medium-to-large effect})$$

### 4.2 Odds Ratio ($\text{OR}$)

The paired odds ratio represents the odds of success in Configuration B relative to Configuration A among discordant intents:
$$\psi = \frac{c}{b}$$
- **Hit@1:** $\psi = \frac{4}{1} = \mathbf{4.00}$ (Candidate B is $4\times$ more likely to succeed when configurations disagree).
- **Hit@5:** $\psi = \frac{3}{1} = \mathbf{3.00}$ (Candidate B is $3\times$ more likely to succeed when configurations disagree).

### 4.3 Synthesis: Magnitude vs. Certainty

The juxtaposition of a **large effect size** ($\text{OR} = 3.00$, Cohen's $g = 0.250$) with a **non-significant p-value** ($p = 0.6250$) and **wide confidence intervals spanning zero** is a textbook indicator of an underpowered experiment. The intervention has strong potential utility, but the sample size of discordant observations ($n_D = 4$) is insufficient to confirm it beyond chance.
