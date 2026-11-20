# M10 Phase G: Exact Two-Sided Power Recalculation & Correction Audit

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-POWER-CORRECTION`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Software Environment:** Python 3.13.5, SciPy 1.15.1, NumPy 2.4.6  
**Executable Script:** [backend/experiments/m10/reproduce_power_and_cluster_tests.py](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/experiments/m10/reproduce_power_and_cluster_tests.py)  
**Audit Status:** Completed  

---

## 1. Executive Summary

This audit re-examines the statistical power calculation reported in earlier Milestone M10 Phase G documents, specifically the claim that an exact two-sided binomial test with $n_D = 23$ discordant pairs achieves $80.34\%$ power at significance level $\alpha = 0.05$ under $H_0: p = 0.50$ versus $H_1: p = 0.75$.

### Key Audit Findings & Corrections:
1. **The 80.34% Claim is One-Sided:** The reported $80.34\%$ power corresponds strictly to a **one-sided** binomial test with critical rejection threshold $C \ge 16$ (unrounded one-sided $\alpha = 0.0465698242$, power $= 0.8036966850 \approx 80.37\%$), or alternatively a two-sided test with an inflated significance level of $\alpha = 0.0931396484 \approx 9.3\%$.
2. **True Exact Two-Sided Power at $n_D = 23$ is 65.37%:** Under an exact **two-sided** binomial test at $\alpha \le 0.05$, the symmetric critical rejection region is $C \le 6 \cup C \ge 17$ (unrounded two-sided size $\alpha = 0.0346896648$). The true exact two-sided power under conditional win probability $\pi = 0.75$ is **$0.6537277951 \approx 65.37\%$**, falling substantially short of the $80\%$ target.
3. **Correct Two-Sided Conditional Requirement ($n_D = 30$):** To achieve $\ge 80\%$ power in an exact two-sided test at $\alpha \le 0.05$, a minimum of **$n_D = 30$ discordant pairs** is required (critical region $C \le 9 \cup C \ge 21$, unrounded null rejection probability $\alpha = 0.0427739453$, unrounded power $= 0.8034069188 \approx 80.34\%$).
4. **Standardized M11 Sample Size Requirement ($N = 225 - 230$ Total Intents):** When discordance is treated realistically as a random variable $D \sim \text{Binomial}(N, p_D = 0.15)$, an independent intent sample of $N = 150$ achieves only **$60.1062\%$** unconditional two-sided power. To guarantee $\ge 80\%$ unconditional two-sided power under stochastic discordance, the confirmatory benchmark must contain **$N = 225 - 230$ independent semantic intent groups in total** ($900 - 920$ query records across four parallel language formulations).
5. **Clarification of Planning Assumptions:** The discordance probability $p_D = 0.15$ and conditional win probability $\pi = 0.75$ (Odds Ratio $\psi = 3.00$) are explicitly designated as **planning assumptions**, not empirical constants.

---

## 2. Exact Binomial Distribution under $H_0$ and $H_1$ ($n_D = 23$)

Consider the exact distribution of discordant successes $C \sim \text{Binomial}(n_D = 23, p)$:
- Under $H_0: p = 0.50$ (symmetric null)
- Under $H_1: p = 0.75$ (target alternative, odds ratio $\psi = 3.00$)

### 2.1 Complete Binomial Tail Probabilities ($n_D = 23$)

Computed using Python 3.13.5 and `scipy.stats.binom`:

| $k$ | $P(C = k \mid H_0)$ | $P(C \le k \mid H_0)$ | $P(C \ge k \mid H_0)$ | $P(C = k \mid H_1)$ | $P(C \ge k \mid H_1)$ |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.000000 | 0.000000 | 1.000000 | 0.000000 | 1.000000 |
| 1 | 0.000003 | 0.000003 | 1.000000 | 0.000000 | 1.000000 |
| 2 | 0.000030 | 0.000033 | 0.999997 | 0.000000 | 1.000000 |
| 3 | 0.000211 | 0.000244 | 0.999967 | 0.000000 | 1.000000 |
| 4 | 0.001056 | 0.001300 | 0.999756 | 0.000000 | 1.000000 |
| 5 | 0.004011 | 0.005311 | 0.998700 | 0.000001 | 0.999999 |
| **6** | **0.012034** | **0.017345** | **0.994689** | 0.000008 | 0.999998 |
| **7** | **0.029225** | **0.046570** | **0.982655** | 0.000057 | 0.999990 |
| 8 | 0.058450 | 0.105020 | 0.953430 | 0.000307 | 0.999933 |
| 9 | 0.097417 | 0.202436 | 0.894980 | 0.001288 | 0.999626 |
| 10 | 0.136383 | 0.338820 | 0.797564 | 0.004380 | 0.998338 |
| 11 | 0.161180 | 0.500000 | 0.661180 | 0.012411 | 0.993958 |
| 12 | 0.161180 | 0.661180 | 0.500000 | 0.029587 | 0.981547 |
| 13 | 0.136383 | 0.797564 | 0.338820 | 0.059174 | 0.951960 |
| 14 | 0.097417 | 0.894980 | 0.202436 | 0.098623 | 0.892786 |
| 15 | 0.058450 | 0.953430 | 0.105020 | 0.139716 | 0.794163 |
| **16** | **0.029225** | **0.982655** | **0.046570** | **0.164372** | **0.803697** (One-Sided Power $\ge 16 = 80.37\%$) |
| **17** | **0.012034** | **0.994689** | **0.017345** | **0.155251** | **0.653728** (Two-Sided Power $\ge 17 = 65.37\%$) |
| 18 | 0.004011 | 0.998700 | 0.005311 | 0.114343 | 0.498477 |
| 19 | 0.001056 | 0.999756 | 0.001300 | 0.062889 | 0.384134 |
| 20 | 0.000211 | 0.999967 | 0.000244 | 0.023958 | 0.321245 |
| 21 | 0.000030 | 0.999997 | 0.000033 | 0.005445 | 0.297287 |
| 22 | 0.000003 | 1.000000 | 0.000003 | 0.000592 | 0.291842 |
| 23 | 0.000000 | 1.000000 | 0.000000 | 0.000000 | 0.291250 |

---

## 3. Dissecting the Rejection Regions and Power Discrepancy

### 3.1 Two-Sided Binomial Rejection Region at $\alpha \le 0.05$

For a symmetric two-sided test under $H_0: p = 0.50$, the critical region partitions $\alpha$ equally into lower and upper tails ($\alpha / 2 \le 0.025$):
- **Lower tail:** Largest $c_{\text{low}}$ such that $P(C \le c_{\text{low}} \mid H_0) \le 0.025$.
  - At $k = 6$: $P(C \le 6 \mid H_0) = 0.0173449516 \le 0.025$.
  - At $k = 7$: $P(C \le 7 \mid H_0) = 0.0465698242 > 0.025$.
  - Therefore, $c_{\text{low}} = 6$.
- **Upper tail:** By symmetry, $c_{\text{high}} = n_D - c_{\text{low}} = 23 - 6 = 17$.
  - At $k = 17$: $P(C \ge 17 \mid H_0) = 0.0173449516 \le 0.025$.
- **Total Unrounded Exact Two-Sided Size ($\alpha_{\text{exact}}$):**
  $$\alpha_{\text{exact}} = P(C \le 6) + P(C \ge 17) = 2 \times 0.0173449516 = \mathbf{0.0346896648 \quad (3.4690\%)}$$

### 3.2 Exact Two-Sided Power Calculation

Power is the probability of rejecting $H_0$ under $H_1: p = 0.75$:
$$\text{Power}_{\text{two-sided}} = P(C \le 6 \mid p = 0.75) + P(C \ge 17 \mid p = 0.75)$$
$$\text{Term}_{\text{lower}} = P(C \le 6 \mid p = 0.75) = 1.172886 \times 10^{-6}$$
$$\text{Term}_{\text{upper}} = P(C \ge 17 \mid p = 0.75) = 0.6537272822$$
$$\text{Power}_{\text{two-sided}} = \mathbf{0.6537277951 \quad (65.3728\%)}$$

### 3.3 The Origin of the "80.34%" Figure

- For a **one-sided** alternative $H_1: p > 0.50$ at $\alpha \le 0.05$:
  - Upper rejection threshold is $C \ge 16$ ($P(C \ge 16 \mid H_0) = 0.0465698242 \le 0.05$).
  - One-sided power:
    $$\text{Power}_{\text{one-sided}} = P(C \ge 16 \mid p = 0.75) = \mathbf{0.8036966850 \quad (80.3697\%)}$$
- If $C \le 7 \cup C \ge 16$ is evaluated as two-sided:
  - Significance level: $\alpha = 2 \times 0.0465698242 = \mathbf{0.0931396484} \approx 9.3\%$.

**Conclusion:** The reported $80.34\%$ was **not** two-sided power at $\alpha = 0.05$. It was strictly **one-sided power ($80.37\%$)**. True two-sided power at $n_D = 23$ is **$65.37\%$**.

---

## 4. Reconciliation of $n_D = 30$ Two-Sided Power & Null Rejection Probability

To reach $\ge 80\%$ power under an exact two-sided test at $\alpha \le 0.05$:

### 4.1 Exact Null Rejection Probability at $n_D = 30$
- Rejection Region: $C \le 9 \cup C \ge 21$.
- Lower tail: $P(C \le 9 \mid H_0) = \mathbf{0.0213869726} \le 0.025$.
- Upper tail: $P(C \ge 21 \mid H_0) = \mathbf{0.0213869726} \le 0.025$.
- **Exact Unrounded Null Rejection Probability ($\alpha$):**
  $$\alpha = P(C \le 9) + P(C \ge 21) = \mathbf{0.0427739453 \quad (4.2774\%)}$$
  *(Reconciled: This unrounded value of $0.0427739453$ was rounded to $0.0428$ in reports).*

### 4.2 Exact Two-Sided Power at $n_D = 30$
- Upper tail under $H_1$: $P(C \ge 21 \mid p = 0.75) = \mathbf{0.8034066369}$.
- Lower tail under $H_1$: $P(C \le 9 \mid p = 0.75) = \mathbf{2.818325 \times 10^{-7}}$.
- **Exact Unrounded Two-Sided Power:**
  $$\text{Power}_{\text{two-sided}} = \mathbf{0.8034069188 \quad (80.3407\%)}$$

**Conclusion:** Exactly $n_D = 30$ discordant pairs guarantees two-sided power $\ge 80\%$ at exact $\alpha = 0.0428 \le 0.05$.

---

## 5. Unconditional Power under Random Discordance: $D \sim \text{Binomial}(N, 0.15)$

The number of discordant pairs $D$ is random:
$$D \sim \text{Binomial}(N, p_D = 0.15)$$
Unconditional power is the weighted expectation:
$$\text{Power}_{\text{unconditional}}(N) = \sum_{d=1}^N P(D = d) \times \text{Power}_{\text{two-sided}}(d)$$

### 5.1 Unrounded Unconditional Power Values

| Independent Intent Groups ($N$) | Expected Discordant Pairs ($E[D] = 0.15N$) | Unconditional Two-Sided Power | Unconditional One-Sided Power |
|---:|---:|---:|---:|
| 150 (Previous target) | 22.50 | 0.601062 (60.11%) | 0.727298 (72.73%) |
| 180 | 27.00 | 0.692164 (69.22%) | 0.804812 (80.48%) |
| 200 | 30.00 | 0.745005 (74.50%) | 0.845892 (84.59%) |
| 220 | 33.00 | 0.791441 (79.14%) | 0.878988 (87.90%) |
| **225** | **33.75** | **0.802042 (80.20%)** | **0.885814 (88.58%)** |
| **230** | **34.50** | **0.812236 (81.22%)** | **0.892410 (89.24%)** |
| 240 | 36.00 | 0.831397 (83.14%) | 0.905098 (90.51%) |
| 250 | 37.50 | 0.848930 (84.89%) | 0.916012 (91.60%) |

---

## 6. Standardized M11 Benchmark Requirement

To resolve all ambiguity, the M11 confirmatory sample size requirement is standardized as:
1. **$N = 225 - 230$ independent semantic intent groups in total.**
2. **Each intent group is instantiated across four parallel language formulations** (`en`, `hi`, `hi-Latn`, `en-hi`).
3. **Total Benchmark Size:** At $N = 230$ intent groups, the benchmark contains exactly **$230 \times 4 = 920$ query records**.
4. **Clarification:** The number $230$ is **not** required separately for each language. Sampling $230$ total intent groups automatically provides $230$ paired query instances in each language.
5. **Planning Assumptions:** Discordance probability $p_D = 0.15$ and conditional win probability $\pi = 0.75$ ($\psi = 3.00$) are explicitly designated as planning assumptions.
