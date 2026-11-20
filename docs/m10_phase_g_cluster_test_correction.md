# M10 Phase G: Cluster-Level Wilcoxon Verification & Exact Test Correction

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-CLUSTER-CORRECTION`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Audit Status:** Completed  

---

## 1. Executive Summary

This audit independently investigates the cluster-level Wilcoxon signed-rank test statistics and p-values reported in Milestone M10 Phase G:
- **Retrieval Hit@5:** Reported as $W = 2.50, p = 0.3173$.
- **End-to-End Success:** Reported as $W = 0.00, p = 0.1573$.

### Key Audit Findings:
1. **Asymptotic Approximation Defect:** Both previously reported p-values ($0.3173$ and $0.1573$) were computed using the **asymptotic normal approximation with continuity correction** in SciPy. They were erroneously labeled as exact test outputs in earlier narrative summaries.
2. **Exact End-to-End $p$-value is 0.5000:** For End-to-End Success, there are only $n = 2$ non-zero paired cluster differences, both positive ($+0.25, +0.25$). The exact two-sided permutation / sign-flip test over $2^2 = 4$ equally likely outcomes yields an **exact two-sided $p$-value of 0.5000**.
3. **Exact Retrieval Hit@5 $p$-value is 0.6250:** For Retrieval Hit@5, there are $n = 4$ non-zero differences ($3$ positive, $1$ negative, all tied at $|d| = 0.25$). The exact permutation test over $2^4 = 16$ outcomes yields an **exact two-sided $p$-value of 0.6250**.
4. **Correction Applied:** All cluster-level test results are now explicitly and correctly labeled as exact permutation test statistics or asymptotic approximations.

---

## 2. Cluster-Level Data Structure & Paired Differences

Outcomes were aggregated across the $K = 45$ answerable semantic intent groups:
$$d_j = p_{j, B} - p_{j, A} = \left( \frac{1}{4} \sum_{\ell=1}^4 Y_{j, \ell}^{(B)} \right) - \left( \frac{1}{4} \sum_{\ell=1}^4 Y_{j, \ell}^{(A)} \right)$$

### 2.1 Complete Distribution of 45 Paired Cluster Differences

| Intent Group | Gold Subject / Topic | Config A Hit@5 ($p_A$) | Config B Hit@5 ($p_B$) | Hit@5 Diff ($d_j$) | Config A E2E ($s_A$) | Config B E2E ($s_B$) | E2E Diff ($d_j$) |
|---|---|---:|---:|---:|---:|---:|---:|
| `M9-INT-01` | Exam Attendance (Notification 307) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| **`M9-INT-02`** | **Attendance Disclosure (70% vs 75%)** | **0.00** | **0.25** | **+0.25** | **0.00** | **0.25** | **+0.25** |
| `M9-INT-03` | Medical Relaxation (Clause 30.1v) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-04` | Short Absence Ineligibility | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-05` | Grade Improvement Registration | 0.25 | 0.25 | 0.00 | 0.50 | 0.50 | 0.00 |
| `M9-INT-06` | Backlog Exam Permissibility | 0.25 | 0.25 | 0.00 | 0.50 | 0.50 | 0.00 |
| `M9-INT-07` | Summer Term Credit Limit | 0.25 | 0.25 | 0.00 | 0.75 | 0.75 | 0.00 |
| `M9-INT-08` | Grade Dispute Appeal Window | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-09` | Academic Probation CGPA | 0.50 | 0.50 | 0.00 | 0.75 | 0.75 | 0.00 |
| **`M9-INT-10`** | **Credit Overload Criteria** | **0.25** | **0.50** | **+0.25** | **0.50** | **0.50** | **0.00** |
| `M9-INT-11` | Minor Degree Registration | 0.25 | 0.25 | 0.00 | 0.50 | 0.50 | 0.00 |
| `M9-INT-12` | Audit Course Requirements | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-13` | Re-Evaluation Fee Structure | 0.50 | 0.50 | 0.00 | 0.75 | 0.75 | 0.00 |
| `M9-INT-14` | Makeup Exam Submission Timeline | 0.50 | 0.50 | 0.00 | 0.75 | 0.75 | 0.00 |
| `M9-INT-15` | Course Withdrawal Deadline | 0.25 | 0.25 | 0.00 | 0.50 | 0.50 | 0.00 |
| `M9-INT-16` | Minimum Degree Completion Time | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-17` | Semester Leave Approval | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| **`M9-INT-18`** | **Examination Fee Forfeiture** | **0.25** | **0.00** | **-0.25** | **0.25** | **0.25** | **0.00** |
| `M9-INT-19` | Maximum Degree Duration | 0.25 | 0.25 | 0.00 | 0.50 | 0.50 | 0.00 |
| `M9-INT-20` | Degree with Distinction CGPA | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-21` | Attendance Condonation Committee | 0.00 | 0.00 | 0.00 | 0.25 | 0.25 | 0.00 |
| `M9-INT-22` | Dean's Merit List Threshold | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-23` | Repeat Course Policy | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-24` | Grade Point Scale Conversion | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-25` | Internship Credit Allocation | 0.25 | 0.25 | 0.00 | 0.50 | 0.50 | 0.00 |
| `M9-INT-26` | Malpractice Penalty Guidelines | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-27` | Migration Certificate Rules | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-28` | Transcripts Issuance Window | 0.25 | 0.25 | 0.00 | 0.50 | 0.50 | 0.00 |
| `M9-INT-29` | Re-Registration for X-Grade | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| **`M9-INT-30`** | **Answer Script Inspection Fee** | **0.00** | **0.25** | **+0.25** | **0.00** | **0.00** | **0.00** |
| `M9-INT-31` | Academic Advisory System | 0.00 | 0.00 | 0.00 | 0.25 | 0.25 | 0.00 |
| `M9-INT-32` | Grade Incomplete 'I' Validity | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-33` | Change of Branch CGPA | 0.00 | 0.00 | 0.00 | 0.25 | 0.25 | 0.00 |
| `M9-INT-34` | Special Supplementary Exam | 0.00 | 0.00 | 0.00 | 0.25 | 0.25 | 0.00 |
| `M9-INT-35` | MOOC Credit Equivalence | 0.25 | 0.25 | 0.00 | 0.50 | 0.50 | 0.00 |
| `M9-INT-36` | Fee Defaulter Debarment | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-37` | Unfair Means Committee Appeal | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-38` | Final Year Project Viva | 0.25 | 0.25 | 0.00 | 0.50 | 0.50 | 0.00 |
| `M9-INT-39` | Grade Moderation Committee | 0.00 | 0.00 | 0.00 | 0.25 | 0.25 | 0.00 |
| `M9-INT-40` | Scribe Policy for PwD | 0.00 | 0.00 | 0.00 | 0.25 | 0.25 | 0.00 |
| `M9-INT-41` | Gold Medal Eligibility | 0.00 | 0.00 | 0.00 | 0.25 | 0.25 | 0.00 |
| `M9-INT-42` | Class Attendance Percentage Calculation | 0.25 | 0.25 | 0.00 | 0.50 | 0.50 | 0.00 |
| `M9-INT-43` | Disciplinary Suspension Grounds | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `M9-INT-44` | Credit Exemption on Lateral Entry | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| **`M9-INT-58`** | **CGPA Cumulative Calculation Formula** | **0.00** | **0.00** | **0.00** | **0.25** | **0.50** | **+0.25** |

---

## 3. Independent Verification of Cluster Test Statistics

### 3.1 Retrieval Hit@5 Cluster Test Verification
- **Total Clusters ($K$):** $45$
- **Zero Differences ($d_j = 0$):** $41$ intents
- **Non-Zero Differences ($n = 4$):**
  - Positive ($3$): `M9-INT-02` ($+0.25$), `M9-INT-10` ($+0.25$), `M9-INT-30` ($+0.25$)
  - Negative ($1$): `M9-INT-18` ($-0.25$)
- **Zero Handling:** Standard Wilcoxon method excludes zero differences ($d_j = 0$).
- **Tie Handling:** All $4$ non-zero differences have identical absolute magnitude $|d_j| = 0.25$. Tied ranks are assigned the average rank:
  $$\text{Rank} = \frac{1 + 2 + 3 + 4}{4} = 2.50$$
- **Rank Sums:**
  - Sum of positive ranks: $W^+ = 2.5 + 2.5 + 2.5 = 7.50$
  - Sum of negative ranks: $W^- = 2.50$
  - Test statistic (sum of lesser ranks): $W = \min(W^+, W^-) = \mathbf{2.50}$

#### Exact Permutation Sign-Flip Derivation for Hit@5:
Under the null hypothesis of symmetric differences around zero, each of the $4$ tied ranks of $2.5$ has an independent $50\%$ probability of being positive or negative. There are $2^4 = 16$ equally likely sign configurations:
- All positive ($W^- = 0$): $1$ outcome (prob $1/16$)
- 3 positive, 1 negative ($W^- = 2.5$): $4$ outcomes (prob $4/16$)
- 2 positive, 2 negative ($W^- = 5.0$): $6$ outcomes (prob $6/16$)
- 1 positive, 3 negative ($W^+ = 2.5$): $4$ outcomes (prob $4/16$)
- All negative ($W^+ = 0$): $1$ outcome (prob $1/16$)

The two-sided p-value is the probability of observing a test statistic as extreme or more extreme than $W = 2.5$:
$$\text{Outcomes with } W \le 2.5 = 1 (\text{all pos}) + 4 (3\text{ pos}) + 4 (1\text{ pos}) + 1 (\text{all neg}) = 10 \text{ outcomes}$$
$$p_{\text{exact}} = \frac{10}{16} = \mathbf{0.6250}$$

#### Origin of the Reported $p = 0.3173$:
In SciPy, `scipy.stats.wilcoxon` uses an asymptotic continuity-corrected normal approximation:
$$\mu_W = \frac{n(n + 1)}{4} = \frac{4 \times 5}{4} = 5.0$$
$$\sigma_W = \sqrt{\frac{n(n + 1)(2n + 1) - \frac{1}{2} \sum t_i (t_i^2 - 1)}{24}} = \sqrt{\frac{4(5)(9) - \frac{1}{2}(4)(15)}{24}} = \sqrt{\frac{180 - 30}{24}} = \sqrt{6.25} = 2.50$$
$$z = \frac{|W - \mu_W| - 0.5}{\sigma_W} = \frac{|2.5 - 5.0| - 0.5}{2.50} = \frac{2.0}{2.50} = 0.80$$
$$p_{\text{asymptotic}} = 2 \times (1 - \Phi(0.80)) = 2 \times (1 - 0.841345) = 2 \times 0.158655 = \mathbf{0.317311}$$

**Conclusion:** The reported $p = 0.3173$ was strictly **asymptotic**. The **exact permutation two-sided p-value is 0.6250**.

---

### 3.2 End-to-End Success Cluster Test Verification
- **Total Clusters ($K$):** $45$
- **Zero Differences ($d_j = 0$):** $43$ intents
- **Non-Zero Differences ($n = 2$):**
  - Positive ($2$): `M9-INT-02` ($+0.25$), `M9-INT-58` ($+0.25$)
  - Negative ($0$): None
- **Zero Handling:** All $43$ zero differences excluded.
- **Tie Handling:** Both non-zero differences have $|d_j| = 0.25$. Tied ranks are:
  $$\text{Rank} = \frac{1 + 2}{2} = 1.50$$
- **Rank Sums:**
  - Sum of positive ranks: $W^+ = 1.5 + 1.5 = 3.00$
  - Sum of negative ranks: $W^- = 0.00$
  - Test statistic: $W = \mathbf{0.00}$

#### Exact Permutation Sign-Flip Derivation for End-to-End Success:
With $n = 2$ non-zero ranks of magnitude $1.5$, there are $2^2 = 4$ equally likely sign assignments:
1. $(+, +)$: $W^+ = 3.0, W^- = 0.0 \implies W = 0.0$
2. $(+, -)$: $W^+ = 1.5, W^- = 1.5 \implies W = 1.5$
3. $(-, +)$: $W^+ = 1.5, W^- = 1.5 \implies W = 1.5$
4. $(-, -)$: $W^+ = 0.0, W^- = 3.0 \implies W = 0.0$

The outcomes as extreme or more extreme than $W = 0.0$ are $(+, +)$ and $(-, -)$ ($2$ outcomes out of $4$):
$$p_{\text{exact}} = \frac{2}{4} = \mathbf{0.5000}$$

#### Origin of the Reported $p = 0.1573$:
When SciPy's asymptotic normal approximation is applied to $n=2$ with tied ranks:
$$\mu_W = \frac{2(3)}{4} = 1.50$$
$$\sigma_W = \sqrt{\frac{2(3)(5) - \frac{1}{2}(2)(3)}{24}} = \sqrt{\frac{30 - 3}{24}} = \sqrt{1.125} = 1.06066$$
$$z = \frac{|0.0 - 1.5| - 0.0}{1.06066} = 1.4142 \implies p = 2 \times (1 - \Phi(1.4142)) = \mathbf{0.157299}$$

**Conclusion:** The reported $p = 0.1573$ was an asymptotic calculation. The **exact permutation two-sided p-value is 0.5000**.

---

## 4. Reconciled and Correctly Labeled Cluster Test Table

| Domain | Intent Cluster Metric | Config A | Config B | Paired Diff ($\Delta$) | Non-Zero Clusters ($n$) | Pos / Neg Split | Test Statistic ($W$) | Asymptotic $p$-value (SciPy) | Exact Permutation $p$-value | Valid Scientific Label |
|---|---|---:|---:|---:|:---:|:---:|---:|---:|---:|---|
| **Retrieval** | Hit@5 Cluster Proportion | 0.1000 | 0.1111 | +0.0111 | 4 | 3 pos, 1 neg | $W = 2.50$ | 0.3173 | **0.6250** | **Exact Permutation: $p = 0.6250$** (Asymp: $p = 0.3173$) |
| **End-to-End**| E2E Success Cluster Proportion| 0.3278 | 0.3389 | +0.0111 | 2 | 2 pos, 0 neg | $W = 0.00$ | 0.1573 | **0.5000** | **Exact Permutation: $p = 0.5000$** (Asymp: $p = 0.1573$) |

Both exact tests fail to reject the null hypothesis by a wide margin ($p \ge 0.50$).
