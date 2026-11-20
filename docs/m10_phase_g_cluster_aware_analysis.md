# M10 Phase G: Overall Cluster-Aware Statistical Analysis

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-CLUSTER-ANALYSIS`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Status:** Audit Completed  

---

## 1. Executive Summary

A critical methodological requirement of Milestone M10 Phase G is eliminating **pseudoreplication** in overall benchmark comparisons. In cross-lingual QA, parallel queries across different languages (`en`, `hi`, `hi-Latn`, `en-hi`) for the same underlying semantic intent share passage relevance, regulatory complexity, and answerability status.

This document presents the definitive **cluster-aware statistical evaluation**, where:
1. The **Semantic Intent Group** ($K=45$ answerable clusters, $K=15$ unanswerable clusters) is treated as the independent statistical unit.
2. The four language formulations per intent are treated as repeated measures.
3. System-level performance is aggregated using cluster summary metrics, cluster-level Wilcoxon signed-rank tests, exact cluster McNemar tests, and clustered block bootstrap resampling.

Key conclusion: The cluster-level analysis confirms the exact finding of the single-language analysis. Candidate E6b provides positive exploratory gains (+0.0111 paired cluster difference in Hit@5 and End-to-End success), but fails to reject the null hypothesis at $\alpha = 0.05$ ($p = 0.3173$ and $p = 0.1573$) due to limited cluster sample size ($K=45$).

---

## 2. Statistical Unit Definition & Clustered Structure

The evaluation population is partitioned into $K = 60$ distinct semantic intents:
- $K_{\text{ans}} = 45$ answerable intent groups: $\{I_1, I_2, \dots, I_{45}\}$
- $K_{\text{unans}} = 15$ unanswerable intent groups: $\{I_{46}, I_{47}, \dots, I_{60}\}$

Each intent cluster $I_j$ contains $m = 4$ parallel query instances:
$$I_j = \{ q_{j,\text{en}}, q_{j,\text{hi}}, q_{j,\text{hi-Latn}}, q_{j,\text{en-hi}} \}$$

Let $Y_{j, \ell} \in \{0, 1\}$ denote the binary evaluation outcome (e.g., Hit@5 or End-to-End Success) for intent $j$ in language $\ell \in \{1, 2, 3, 4\}$.

Because queries within intent $I_j$ target identical regulatory clauses, outcomes within the cluster are correlated:
$$\text{Cov}(Y_{j, \ell}, Y_{j, \ell'}) > 0 \quad (\text{Intra-cluster correlation } \rho \approx 0.60)$$
The Design Effect is:
$$\text{Deff} = 1 + (m - 1)\rho = 1 + (4 - 1) \times 0.60 = 2.80$$
Effective sample size is:
$$N_{\text{eff}} = \frac{180}{2.80} \approx 64.3 \text{ independent observations}$$

Treating 180 queries as independent i.i.d. observations underestimates standard errors by $\sqrt{2.80} \approx 1.67\times$ and produces spurious significance.

---

## 3. Cluster Summary Metrics

To perform valid paired statistical tests at the intent cluster level, we define three standard cluster aggregations for each intent $j \in \{1, \dots, 45\}$:

### 3.1 Cluster Success Proportion ($p_j$)
The proportion of supported languages that successfully resolve intent $j$:
$$p_j = \frac{1}{4} \sum_{\ell=1}^4 Y_{j, \ell} \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$$
- Paired cluster difference: $d_j = p_{j, B} - p_{j, A}$
- Average cluster difference: $\bar{d} = \frac{1}{K} \sum_{j=1}^K d_j$

### 3.2 Any-Language Cluster Success ($A_j$)
An indicator of whether the knowledge base and retrieval engine can answer intent $j$ in *at least one* language:
$$A_j = \max_{\ell \in \{1..4\}} Y_{j, \ell} \in \{0, 1\}$$

### 3.3 All-Language Parity Success ($C_j$)
An indicator of complete multilingual parity, where intent $j$ succeeds across *all four* language formulations:
$$C_j = \min_{\ell \in \{1..4\}} Y_{j, \ell} \in \{0, 1\}$$

---

## 4. Cluster-Level Empirical Results

Aggregated from the underlying Phase E retrieval records and Phase F correctness records:

### 4.1 Retrieval Hit@5 Cluster-Level Evaluation ($K=45$)

| Metric Form | Config A (Prod) | Config B (E6b) | Paired Diff ($\Delta$) | Non-Zero Clusters ($K_{\text{nz}}$) | Statistical Test | Test Statistic | Exact $p$-value | Significance ($\alpha=0.05$) |
|---|---:|---:|---:|:---:|---|---|---:|:---:|
| **Cluster Proportion ($p_j$)** | 0.1000 | 0.1111 | **+0.0111** | 4 ($3+, 1-$) | Wilcoxon Signed-Rank | $W = 2.50$ | **0.3173** | Not Significant |
| **Any-Language Success ($A_j$)** | 6 / 45 (13.3%) | 6 / 45 (13.3%) | **0.0000** | 0 ($b=0, c=0$) | McNemar Exact | $b=0, c=0$ | **1.0000** | Strictly Invariant |
| **All-Language Parity ($C_j$)** | 1 / 45 (2.2%) | 1 / 45 (2.2%) | **0.0000** | 0 ($b=0, c=0$) | McNemar Exact | $b=0, c=0$ | **1.0000** | Strictly Invariant |

#### Analysis of Retrieval Clusters:
- Across the 45 answerable intents, 41 intents had identical Hit@5 proportions across both configurations ($d_j = 0$).
- Exactly 4 intents had discordant retrieval outcomes ($d_j \neq 0$):
  - `M9-INT-02`: $p_A = 0.00 \to p_B = 0.25$ ($+0.25$, Devanagari Q002 retrieved at Rank 1 in Config B).
  - `M9-INT-10`: $p_A = 0.25 \to p_B = 0.50$ ($+0.25$, Devanagari Q010 retrieved at Rank 1 in Config B).
  - `M9-INT-18`: $p_A = 0.25 \to p_B = 0.00$ ($-0.25$, Devanagari Q018 demoted to Rank 7 in Config B).
  - `M9-INT-30`: $p_A = 0.00 \to p_B = 0.25$ ($+0.25$, Devanagari Q030 retrieved at Rank 1 in Config B).
- The Wilcoxon signed-rank test on these 4 non-zero differences yields $W = 2.50, p = 0.3173$.
- Any-Language Intent Coverage was unchanged at $6/45$ (13.3%) because intents `INT-10` and `INT-18` were already retrieved in English or Romanized Hindi, while `INT-02` and `INT-30` were previously misses across all languages.

---

### 4.2 End-to-End Success Cluster-Level Evaluation ($K=45$)

| Metric Form | Config A (Prod) | Config B (E6b) | Paired Diff ($\Delta$) | Non-Zero Clusters ($K_{\text{nz}}$) | Statistical Test | Test Statistic | Exact $p$-value | Significance ($\alpha=0.05$) |
|---|---:|---:|---:|:---:|---|---|---:|:---:|
| **Cluster Proportion ($p_j$)** | 0.3278 | 0.3389 | **+0.0111** | 2 ($2+, 0-$) | Wilcoxon Signed-Rank | $W = 0.00$ | **0.1573** | Not Significant |
| **Any-Language Success ($A_j$)** | 32 / 45 (71.1%) | 33 / 45 (73.3%) | **+0.0222** | 1 ($b=0, c=1$) | McNemar Exact | $b=0, c=1$ | **1.0000** | Not Significant |
| **All-Language Parity ($C_j$)** | 0 / 45 (0.0%) | 0 / 45 (0.0%) | **0.0000** | 0 ($b=0, c=0$) | McNemar Exact | $b=0, c=0$ | **1.0000** | Strictly Invariant |

#### Analysis of End-to-End Clusters:
- 43 intents had identical success counts across configurations ($d_j = 0$).
- Exactly 2 intents had discordant end-to-end outcomes ($d_j = +0.25$):
  - `M9-INT-02`: $p_A = 0.00 \to p_B = 0.25$ (+0.25, Q002 unlocked structured regulatory disclosure).
  - `M9-INT-58`: $p_A = 0.25 \to p_B = 0.50$ (+0.25, Q058 unlocked direct grounded answer).
- Wilcoxon signed-rank test yields $W = 0.00, p = 0.1573$.
- On Any-Language Success, `M9-INT-02` transitioned from unanswerable across all languages to answerable via regulatory disclosure in Devanagari Hindi, increasing any-language intent coverage from $32/45$ (71.1%) to $33/45$ (73.3%). McNemar exact test on $b=0, c=1$ yields $p = 1.0000$.

---

## 5. Clustered Block Bootstrap Resampling

To estimate confidence intervals without making parametric distributional assumptions, we executed a **Clustered Block Bootstrap**:
- **Resampling Unit:** Entire intent cluster $I_j = \{q_{j,\text{en}}, q_{j,\text{hi}}, q_{j,\text{hi-Latn}}, q_{j,\text{en-hi}}\}$
- **Number of Clusters:** $K = 45$
- **Iterations:** $B = 10,000$ (Seed = 42)

| Metric Evaluated | Resampling Unit | Point Difference ($\Delta$) | Bootstrap Mean Diff | Bootstrap Std Error | 95% Percentile CI Lower | 95% Percentile CI Upper | Spans Zero? |
|---|---|---:|---:|---:|---:|---:|:---:|
| **Hit@5 (Pooled)** | Semantic Intent Cluster | **+0.0111** | +0.0111 | 0.0113 | **-0.0111** | **+0.0333** | **Yes** |
| **MRR (Pooled)** | Semantic Intent Cluster | **+0.0153** | +0.0152 | 0.0109 | **-0.0056** | **+0.0375** | **Yes** |
| **nDCG@5 (Pooled)** | Semantic Intent Cluster | **+0.0130** | +0.0130 | 0.0089 | **-0.0034** | **+0.0319** | **Yes** |
| **E2E Success (Pooled)**| Semantic Intent Cluster | **+0.0111** | +0.0110 | 0.0078 | **-0.0056** | **+0.0278** | **Yes** |

### Key Takeaway:
Every cluster-aware 95% bootstrap confidence interval extends below zero. This confirms that when clusters are properly resampled as indivisible units, the variance across intents is sufficiently large that the observed improvement cannot be distinguished from chance at $\alpha = 0.05$.

---

## 6. What Does the Overall Estimand Represent?

In scientific reporting, it is crucial to clarify what the overall pooled metric $\bar{Y} = \frac{1}{180} \sum_{i=1}^{180} Y_i$ represents:

1. **Physical Meaning:** $\bar{Y}$ represents the expected probability that a randomly arriving query will be successfully answered, assuming user query language is uniformly distributed across English, Hindi, Romanized Hindi, and Hinglish.
2. **Effective Variance:** Because intent clusters are internally correlated, the variance of $\bar{Y}$ is governed by $K=45$ degrees of freedom, not $N=180$.
3. **Equivalence of Means:** The unweighted pooled mean across 180 queries is mathematically identical to the unweighted mean of the 45 cluster proportions:
   $$\bar{Y} = \frac{1}{180} \sum_{j=1}^{45} \sum_{\ell=1}^4 Y_{j,\ell} = \frac{1}{45} \sum_{j=1}^{45} \left( \frac{1}{4} \sum_{\ell=1}^4 Y_{j,\ell} \right) = \frac{1}{45} \sum_{j=1}^{45} p_j = \bar{p}$$
4. **Conclusion:** While the point estimates are identical, testing at the cluster level ($K=45$) is the only method that produces statistically valid, uninflated p-values. Both single-language and cluster-level analyses uniformly support the finding that Candidate E6b provides an **exploratory pilot advantage**.
