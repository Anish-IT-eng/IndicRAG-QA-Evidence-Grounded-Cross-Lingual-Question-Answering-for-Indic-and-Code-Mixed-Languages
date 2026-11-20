# M10 Phase G: Independent Statistical Unit & Design Effect Audit

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-INDEPENDENT-UNIT-AUDIT`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Audit Status:** Completed  

---

## 1. Executive Summary

This audit establishes the rigorous mathematical demarcation of statistical units in multilingual regulatory benchmarking, resolving ambiguities surrounding repeated measures, design effects, and effective sample sizes.

### Key Audit Findings:
1. **Parallel Translations are Clustered Repeated Measures:** The four query formulations (`en`, `hi`, `hi-Latn`, `en-hi`) for each semantic intent group are **repeated observations** of the exact same underlying regulatory problem. They share gold target passage IDs, regulatory clause ambiguities, and answerability status.
2. **Correct Unit Counts in Frozen Benchmark M9:**
   - Unique Independent Semantic Intent Groups: **60** ($45$ answerable, $15$ unanswerable).
   - Total Query Records: **240** ($60$ queries $\times$ $4$ language formulations).
   - Language-Specific Paired Observations: **45** paired queries per language.
   - Independent Statistical Units for Pooled Cluster Analysis: **45 clusters** ($K = 45$).
3. **Correction of the $N_{\text{eff}} = 214$ Design Effect Fallacy:** The formula $N_{\text{eff}} = \frac{600}{\text{Deff}} = \frac{600}{2.80} \approx 214$ measures the variance equivalence of a survey sample of 600 clustered queries relative to simple random sampling. It must **not** be construed as generating $214$ independent intent groups from a $150$-intent sample. Sampling $150$ intent groups provides exactly **$150$ independent statistical degrees of freedom**, regardless of how many parallel translations are evaluated per intent.
4. **Standardized M11 Confirmatory Benchmark Requirement:**
   - The requirement is **$225 - 230$ independent semantic intent groups in total**.
   - Each intent group is instantiated across four parallel language formulations (`en`, `hi`, `hi-Latn`, `en-hi`).
   - At $N = 230$ total intent groups, the benchmark contains exactly **$230 \times 4 = 920$ query records**.
   - The number $230$ is **not required separately for each language**. Sampling $230$ total intent groups automatically provides $230$ paired query instances in each language.
   - The discordance probability $p_D = 0.15$ and conditional win probability $\pi = 0.75$ (Odds Ratio $\psi = 3.00$) are explicitly designated as **planning assumptions**, not empirical constants.

---

## 2. Statistical Unit Demarcation

In statistical inference, an **independent statistical unit** is an entity whose selection and outcome are statistically independent of all other entities in the sample:
$$\text{Cov}(U_i, U_j) = 0 \quad \text{for } i \neq j$$

### 2.1 Four Distinct Levels of Granularity

| Level | Definition | Benchmark Count (M9/M10) | Statistical Property | Valid Inference Scope |
|---|---|---:|---|---|
| **Level 1: Query Record** | Individual string sent to the pipeline (e.g., `M9-Q002`) | **240 records** | Clustered repeated measures within intent groups. Non-independent ($\rho \approx 0.60$). | Unpooled regression models with cluster-robust standard errors only. |
| **Level 2: Language-Specific Paired Observation** | Single-language comparison of Config A vs Config B (e.g., Devanagari Hindi) | **45 pairs per language** | Independent observations within the specific language stratum. | Exact paired McNemar and Wilcoxon tests within a single language. |
| **Level 3: Semantic Intent Group (Cluster)** | The underlying regulatory question and its 4 parallel translations | **60 total (45 answerable)** | **The True Independent Statistical Unit.** $\text{Cov}(I_j, I_{j'}) = 0$. | Clustered block bootstrap, cluster Wilcoxon, and Any-Language McNemar tests. |
| **Level 4: Corpus Document / Clause** | Regulatory PDFs (SCSET 2022, SEAS 2017, Notification 307) | **7 documents (306 passages)** | Corpus population from which passages are retrieved. | Finite population coverage metrics. |

---

## 3. Re-evaluating the Design Effect and $N_{\text{eff}}$

In earlier Milestone M10 documentation, the following calculation was presented:
$$\text{Deff} = 1 + (m - 1)\rho = 1 + (4 - 1) \times 0.60 = 2.80$$
$$N_{\text{eff}} = \frac{600}{\text{Deff}} = \frac{600}{2.80} \approx 214.3$$

This calculation requires strict methodological clarification to prevent erroneous claims of statistical power.

### 3.1 The Meaning of Design Effect ($\text{Deff}$) in Survey Sampling

The Design Effect ($\text{Deff}$) originates in survey sampling (Kish, 1965). It compares the variance of an estimator under cluster sampling to the variance of an estimator under **simple random sampling (SRS) of the same total number of observations**:
$$\text{Deff} = \frac{\text{Var}_{\text{cluster}}(\bar{Y})}{\text{Var}_{\text{SRS}}(\bar{Y})}$$
If an analyst possesses a clustered sample of $N_{\text{total}} = 600$ query evaluations ($150$ clusters of size $m = 4$), the variance of the sample mean is:
$$\text{Var}(\bar{Y}) = \text{Deff} \times \frac{\sigma^2}{600} = 2.80 \times \frac{\sigma^2}{600} = \frac{\sigma^2}{214.3}$$
Thus, estimating the mean over $600$ clustered queries has the same sampling variance as estimating the mean over $214$ independent random queries drawn from the population.

### 3.2 The Methodological Limitation

**Crucial Correction:** The fact that $N_{\text{eff}} = 214$ for estimation of the pooled mean does **not** mean that the study contains $214$ independent intent groups!
1. The number of independent regulatory problems evaluated is strictly **$K = 150$**.
2. Degrees of freedom for hypothesis testing at the cluster level are bounded by $K - 1 = 149$, not $213$.
3. When testing language-specific hypotheses (e.g., "Does E6b improve Devanagari Hindi retrieval?"), each intent yields exactly **one** Devanagari observation. The sample size for that test is strictly **$N = 150$**, not $214$ or $600$.
4. Claiming $N_{\text{eff}} = 214 > 150$ to justify that a $150$-intent sample is "overpowered" is methodologically invalid.

---

## 4. Standardized Sampling Structure for Confirmatory Milestone M11

To avoid underpowered evaluations, the confirmatory evaluation protocol for Milestone M11 must adhere to a clearly structured sampling plan:

### 4.1 Sampling Architecture

$$\begin{array}{rcl}
N_{\text{intents}} & = & \mathbf{225 - 230 \text{ unique, independent semantic intent groups in total}} \\
& & (175 \text{ answerable intents}, 55 \text{ unanswerable intents at } N=230) \\
m & = & 4 \text{ parallel formulations per intent} \\
& & (\text{English, Hindi Devanagari, Romanized Hindi, Hinglish}) \\
N_{\text{total queries}} & = & 230 \times 4 = \mathbf{920 \text{ total query records}}
\end{array}$$

### 4.2 Independent Statistical Unit Ledger for M11

| Evaluation Layer | Statistical Unit | Sample Size ($N$) | Expected Discordant Pairs ($p_D=0.15$) | Power at $\pi=0.75, \alpha \le 0.05$ | Status |
|---|---|---:|---:|---:|:---:|
| **Devanagari Hindi Paired Test** | Answerable Intent Group | **175 pairs** | $E[D] = 175 \times 0.15 = 26.25$ | $\ge 72.5\%$ (Conditional) | Feasible |
| **Full Two-Sided Unconditional Target** | Answerable Intent Group | **230 pairs** | $E[D] = 230 \times 0.15 = 34.50$ | **$81.22\%$ (Unconditional)** | **Statistically Confirmatory** |
| **Pooled Cluster Analysis** | Intent Group Cluster | **230 clusters** | All $4$ languages resampled as blocks | $80.5\%$ | Valid Cluster Inference |
| **Single-Language Sub-tests** | Intent Group | **230 per language** | $n_D \ge 30$ in each language | $\ge 80.3\%$ | Confirmatory Across All Languages |

### 4.3 Conclusion on Unit Independence

The four language formulations cannot be treated as separate independent intent groups. In Milestone M11, the target must be **225–230 independent semantic intent groups in total**, which automatically provides 225–230 paired observations in each language and 900–920 parallel query executions.
