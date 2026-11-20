# IndicRAG-QA — M6 Comprehensive Evaluation Protocol (Phase 1B Corrected)

**Milestone:** M6 — Evidence Reliability and Answerability  
**Phase:** Phase 1B (Methodological Correction & Implementation Specification)  
**Date:** 2026-11-10  
**Author:** Senior RAG Evaluation Researcher & Evidence Reliability Engineer  
**Evaluation Scope:** Leakage-safe nested evaluation, uncertainty quantification, answerability gating, citation faithfulness, end-to-end multilingual QA  

---

## 1. Experimental Integrity & Protocol Governance

To prevent data leakage, optimistic evaluation bias, and unreplicable threshold claims, this protocol enforces strict methodological constraints:
1. **Zero Test Leakage via Cross-Fitting:** No query is ever evaluated using a calibrator, normalizer, or decision threshold that was fitted using that query.
2. **Honest Statistical Bounds on Small Samples:** Acknowledging that with $N_{\text{unans}} = 20$, each unanswerable query accounts for $5.0\%$ of the class. No claim of "statistically guaranteed $\text{FAR} \le 5\%$" will be made; all rates are accompanied by exact Wilson score $95\%$ confidence intervals.
3. **Six Canonical Evidence States:** Explicit distinction between `SUFFICIENT`, `PARTIAL`, `INSUFFICIENT`, `CONFLICTING`, `MISSING`, and `CLARIFICATION_REQUIRED`.
4. **Independent Verifiers:** Generator models are strictly excluded from verifying their own outputs.

---

## 2. Six Canonical Evidence States and System Behavior

The Evidence Controller evaluates retrieved evidence and emits one of six mutually exclusive states.

```
                          [ Retrieval & Scoring ]
                                    │
                                    ▼
                          Candidates Retrieved?
                          ├── No ───► [ MISSING ]
                          └── Yes
                                    │
                                    ▼
                     Query Temporal / Scope Ambiguous?
                          ├── Yes ──► [ CLARIFICATION_REQUIRED ]
                          └── No
                                    │
                                    ▼
                     Irreconcilable Regulatory Conflict?
                          ├── Yes ──► [ CONFLICTING ]
                          └── No
                                    │
                                    ▼
                         CECI >= Calibrated Threshold?
                          ├── No ───► [ INSUFFICIENT ]
                          └── Yes
                                    │
                                    ▼
                     All Sub-Questions / Clauses Covered?
                          ├── No ───► [ PARTIAL ]
                          └── Yes ──► [ SUFFICIENT ]
```

### 2.1 State Definitions and Expected System Behaviors

| State ID | Semantic Definition | Trigger Conditions | Generator Behavior | User-Facing Disclosure / Response |
|---|---|---|---|---|
| **`SUFFICIENT`** | Retrieved evidence fully and unambiguously supports answering all clauses of the query. | $\Psi(q, D) \ge \theta^*$, all intent keywords/sub-questions covered, no active version conflict. | Grounded generation based solely on retrieved passages. | Emits factual answer with exact citations: `[Source: pid, page X]`. |
| **`PARTIAL`** | Evidence supports some requested sub-questions/clauses, but key parts are missing from the corpus. | $\Psi(q, D) \ge \theta^*$, but sub-question coverage $< 1.0$ (multi-part query). | Answers the supported portions; abstains on missing parts. | Answers supported parts, adding: *"Note: Regulations for [missing aspect] are not specified in the provided documents."* |
| **`INSUFFICIENT`** | Retrieved evidence is off-topic, weak, or does not support a trustworthy answer. | $\Psi(q, D) < \theta^*$, or candidates lack requisite regulatory entities. | Mandatory safe abstention. Zero LLM extrapolation. | Standardized abstention: *"UNANSWERABLE — The available academic regulations do not contain sufficient evidence to answer this question."* |
| **`CONFLICTING`** | Multiple applicable documents assert incompatible rules without temporal resolution. | Contradictory rules detected across coexisting documents (e.g. Clause 30.1 vs Notification 307) and query lacks clarifying year. | Synthesizes comparative summary of both rules without picking one. | *"Notice of Conflicting Rules: Clause 30.1 states X, whereas Notification 307 states Y. Please verify which cohort applies."* |
| **`MISSING`** | Retriever returned zero passages matching query terms or concepts. | $\|D\| = 0$ across BM25 and Dense search. | Immediate abstention without calling generator. | *"MISSING — No relevant documents or clauses were found in the official university corpus."* |
| **`CLARIFICATION_REQUIRED`** | Query is missing essential parameters (academic year, program, cohort) needed to select the correct rule. | Query intent analysis indicates rule varies by cohort/program, but query omits context. | Generates clarification prompt identifying missing variable. | *"Clarification Required: The applicable rule depends on your academic year / program. Please specify your batch."* |

---

## 3. Leakage-Safe Nested Cross-Fitting Evaluation Architecture

To ensure valid evaluation without test-set contamination:

```
Expanded Benchmark Dataset (N=60: 40 Answerable, 20 Unanswerable)
Stratified by (Language, Answerability, Taxonomy Class) into K=5 Folds
══════════════════════════════════════════════════════════════════════════
For fold k in {1, 2, 3, 4, 5}:
  ┌────────────────────────────────────────────────────────┐
  │  Calibration Set: 4 folds combined (N=48)              │
  │  - Fit Platt parameters A, B on calibration data       │
  │  - Fit Logistic CECI weights w on calibration data     │
  │  - Select optimal decision threshold theta_k*          │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │  Test Set: Fold k strictly held out (N=12)             │
  │  - Evaluate CECI using frozen calibrator k             │
  │  - Apply frozen threshold theta_k*                     │
  │  - Record out-of-fold predictions                      │
  └────────────────────────────────────────────────────────┘
══════════════════════════════════════════════════════════════════════════
Aggregate out-of-fold predictions across all 60 queries to compute
unbiased benchmark metrics with Wilson score confidence intervals.
```

### 3.1 Decision Threshold Optimization Formulation

**Defect in Previous Design:** Claimed that $\text{FAR} \le 5\%$ is "statistically guaranteed". On $N_{\text{unans}} = 20$, 1 error yields $5\%$, 2 errors yield $10\%$. A single flip shifts FAR by 5 percentage points. It is statistically impossible to guarantee $\le 5\%$ at standard confidence levels on $N=20$.

**Corrected Threshold Selection Strategy:**
On each calibration set (containing $N_{\text{unans}}^{\text{calib}} = 16$ unanswerable and $N_{\text{ans}}^{\text{calib}} = 32$ answerable instances), we formulate threshold selection using a **Cost-Sensitive Expected Utility Objective**:
$$\theta^* = \arg\max_{\theta \in [0, 1]} \mathcal{U}(\theta) = \text{TP}(\theta) - \lambda \cdot \text{FP}(\theta) - \mu \cdot \text{FN}(\theta)$$
Where:
- $\lambda = 3.0$ (heavy penalty on False Answers / Hallucinations on unanswerables).
- $\mu = 1.0$ (moderate penalty on False Abstentions on answerables).

#### Fallback Protocol When Hard Constraints Cannot Be Met:
If an operator mandates a target $\text{FAR} \le 5\%$:
1. Check if there exists $\theta$ such that $\text{FAR}(\theta) \le 0.05$ on calibration data.
2. If multiple thresholds satisfy this, choose $\theta^* = \arg\max_{\theta: \text{FAR} \le 0.05} \text{Recall}_{\text{ans}}(\theta)$.
3. **If NO threshold achieves $\text{FAR} \le 0.05$ on calibration data** (e.g. if unanswerable queries retrieve high-scoring false matches):
   - Switch automatically to the **Conservative Pareto Threshold**:
     $$\theta^* = \arg\min_{\theta} \text{FAR}(\theta) \quad \text{subject to} \quad \text{Recall}_{\text{ans}}(\theta) \ge 0.70$$
   - Explicitly report the observed empirical FAR and its exact $95\%$ Wilson confidence interval, documenting that the $5\%$ constraint was unachievable under current retrieval embeddings.

---

## 4. Mathematical Metric Definitions & Uncertainty Quantification

### 4.1 Answerability Detection Metrics

Let $N_{\text{ans}} = 40$ and $N_{\text{unans}} = 20$. Let system output be $\hat{y}_i \in \{1 \text{ (Answered)}, 0 \text{ (Abstained)}\}$.

1. **Answerability Precision ($P_{\text{ans}}$):**
   $$P_{\text{ans}} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$
2. **Answerability Recall ($R_{\text{ans}}$):**
   $$R_{\text{ans}} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$
3. **Answerability F1 ($F_{1, \text{ans}}$):**
   $$F_{1, \text{ans}} = \frac{2 \cdot P_{\text{ans}} \cdot R_{\text{ans}}}{P_{\text{ans}} + R_{\text{ans}}}$$
4. **False Answer Rate ($FAR$):**
   $$\text{FAR} = \frac{\text{FP}}{N_{\text{unans}}}$$
5. **False Abstention Rate ($FAR_{\text{abs}}$):**
   $$\text{FAR}_{\text{abs}} = \frac{\text{FN}}{N_{\text{ans}}} = 1 - R_{\text{ans}}$$

### 4.2 Exact Uncertainty Reporting (Wilson Score Interval)

For any observed proportion $\hat{p} = \frac{k}{n}$ (such as FAR on $n=20$ or Answerability Recall on $n=40$), the asymmetric $95\%$ Wilson score confidence interval is reported:
$$w_{\pm} = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1 - \hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
Where $z = 1.95996$ for a two-sided $95\%$ interval.

**Sample Size Sensitivity Table ($n=20$ Unanswerable Queries):**

| Observed Errors ($k$) | Point Estimate ($\text{FAR}$) | 95% Wilson Confidence Interval | Methodological Interpretation |
|---|---|---|---|
| **$0 / 20$** | **$0.0\%$** | $[0.0\%, 16.1\%]$ | Consistent with $\le 5\%$, but upper bound reaches $16.1\%$. |
| **$1 / 20$** | **$5.0\%$** | $[0.88\%, 23.6\%]$ | Point estimate meets $5\%$, but upper bound reaches $23.6\%$. |
| **$2 / 20$** | **$10.0\%$** | $[2.8\%, 30.1\%]$ | Exceeds $5\%$ point target. |
| **$3 / 20$** | **$15.0\%$** | $[5.2\%, 36.0\%]$ | Substantial unanswerability leakage. |

*This proves mathematically why claiming a "guaranteed $\le 5\%$ FAR" on $N=20$ is statistically invalid. All reporting will feature point estimates alongside their 95% Wilson CIs.*

---

## 5. Coverage-Risk Evaluation (Selective Classification)

When the Evidence Controller abstains on low-confidence queries, the system trades Coverage for Accuracy:
- **Coverage ($\mathcal{C}(\theta)$):** Fraction of queries answered:
  $$\mathcal{C}(\theta) = \frac{1}{N} \sum_{i=1}^{N} \mathbb{I}(\Psi(q_i, D) \ge \theta)$$
- **Selective Risk ($\mathcal{R}(\theta)$):** Error rate on answered queries:
  $$\mathcal{R}(\theta) = \frac{\sum_{i=1}^{N} \mathbb{I}(\Psi(q_i, D) \ge \theta) \cdot \text{Loss}(i)}{\sum_{i=1}^{N} \mathbb{I}(\Psi(q_i, D) \ge \theta)}$$
  Where $\text{Loss}(i) = 1.0$ if query $i$ is unanswerable ($\text{FP}$), or if an answerable query yields Token F1 $< 0.50$.
- **Area Under Coverage-Risk Curve (AUCR):** Summarizes selective classification quality across all thresholds $\theta \in [0, 1]$. Lower AUCR indicates superior confidence ranking.

---

## 6. End-to-End QA and Citation Grounding Metrics

On answered queries ($\hat{y}_i = 1$):
1. **Exact Match (EM):** $\mathbb{I}(\text{norm}(\hat{a}) == \text{norm}(a^*))$.
2. **Token F1:** Standard harmonic mean of token overlap between prediction and gold reference.
3. **Claim Support Rate ($S_{\text{claim}}$):** Proportion of atomic claims classified as `ENTAILED` by cited passages.
4. **Citation Precision ($P_{\text{cit}}$):** Proportion of cited passage IDs that are gold evidence passages.
5. **Citation Coverage ($C_{\text{cit}}$):** Proportion of required gold evidence passages that appear in generated citations.
