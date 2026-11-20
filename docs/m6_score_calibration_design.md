# IndicRAG-QA — M6 Score Calibration and Decision Gating Specification (Phase 1B Corrected)

**Milestone:** M6 — Evidence Reliability and Answerability  
**Phase:** Phase 1B (Methodological Correction & Implementation Specification)  
**Date:** 2026-11-10  
**Author:** Senior RAG Evaluation Researcher & Evidence Reliability Engineer  
**Status:** Methodological Baseline Specification (No runtime modification prior to Phase 2 approval)  
**Corpus SHA-256:** `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d`  
**Frozen Benchmark SHA-256:** `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` ($N=15$)  

---

## 1. Executive Summary & Audit of Methodological Defects

In the preliminary Phase 1 design, several methodological errors were identified that violated sound experimental RAG design:
1. **Flawed Score Normalization:** Query-local min-max scaling was proposed for BM25. In practice, local min-max scaling forces the top retrieved candidate of ANY query—even an irrelevant out-of-domain query where all passages have near-zero relevance—to scale to $1.0$. This destroys cross-query score comparability and renders global thresholding mathematically impossible.
2. **Arbitrary Empirical Bounds:** Dense cosine similarity was arbitrarily clamped between $0.20$ and $0.80$ without empirical justification or parameter fitting.
3. **Mischaracterized Platt Calibration:** A static, fixed-temperature logistic sigmoid ($\tau = 1.8, \mu = 0.0$) was improperly labeled as "Platt calibration". True Platt scaling requires fitting parametric parameters $A$ and $B$ via maximum likelihood on a held-out calibration set.
4. **Uncalibrated Probability Claims:** The composite score $\Phi$ was referred to as a "probability", despite being a heuristic linear sum with arbitrary weights and unbounded additive offsets ($v_{\text{align}} \in [-0.2, +0.1]$) that violated the $[0.0, 1.0]$ probability axioms.
5. **RRF Channel Asymmetry Ignored:** Theoretical maximum calculation assumed equal weights ($1.0/1.0$), ignoring the actual default configuration (`bm25_weight = 0.4, dense_weight = 0.6`). Furthermore, RRF was treated as a cardinal relevance score rather than an ordinal rank aggregation metric.

This document provides mathematically rigorous, empirically verifiable corrections for all scoring transformations, composite confidence estimation, and parameter estimation workflows.

---

## 2. Corrected Score Normalization Transformations

To ensure cross-query comparability and preserve low-quality pool detection, **all raw retrieval scores must be preserved verbatim in data structures**. Calibrated representations are maintained as secondary attributes alongside raw scores.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Retrieved Candidate Pool                        │
│   (Raw Scores Preserved: s_bm25 in [0, inf), s_dense in [-1, 1],       │
│    s_rrf in [0, S_max], s_cross_encoder in (-inf, +inf))               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   BM25 Scoring   │      │  Dense Cosine    │      │  Cross-Encoder   │
│  Corpus-level    │      │  Empirical Platt │      │  Fitted Platt    │
│  Sigmoid Mapping │      │  Calibration     │      │  Logistic Sigmoid│
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

### 2.1 Lexical BM25 Transformation

**Defect in Previous Design:** Query-local min-max normalization $\frac{s - \min(S)}{\max(S) - \min(S)}$ assigns $1.0$ to the top document even if the top document has a raw BM25 score of $0.8$ on an unanswerable query.

**Corrected Formulation:**
Raw BM25 scores are unbounded $[0, +\infty)$. To transform raw BM25 scores into a cross-query comparable confidence index $s_{\text{cal}}^{\text{BM25}} \in [0.0, 1.0]$ without losing low-quality pool detection, we employ a corpus-anchored sigmoid mapping fitted to the empirical calibration split:
$$s_{\text{cal}, i}^{\text{BM25}} = \frac{1}{1 + \exp\left(-\beta_{\text{bm25}} \cdot (s_i^{\text{BM25}} - \mu_{\text{bm25}})\right)}$$

Where:
- $\mu_{\text{bm25}}$ is the empirical median BM25 score of gold passage hits on the calibration split (estimated prior: $\approx 10.5$).
- $\beta_{\text{bm25}}$ is the scale factor fitted via maximum likelihood on calibration binary relevance labels ($y \in \{0, 1\}$).
- **Behavior on Low-Quality Pools:** If a query retrieves passages with raw BM25 scores near zero (e.g., $s \le 2.0$), $s_{\text{cal}}^{\text{BM25}} \to \frac{1}{1 + e^{10.5 \beta}} \approx 0.001$, correctly reflecting near-zero lexical confidence across the entire candidate list.

### 2.2 Dense Cosine Transformation

**Defect in Previous Design:** Setting arbitrary hard clamps $\gamma_{\min} = 0.20$ and $\gamma_{\max} = 0.80$ without fitting on empirical data.

**Corrected Formulation:**
The retrieval backend uses FAISS `IndexFlatIP` with unit-normalized embeddings, guaranteeing raw scores are exact cosine similarities:
$$s_{\cos} = \mathbf{q}^T \mathbf{d} \in [-1.0, 1.0]$$

To convert raw cosine similarity to an empirically calibrated relevance probability, we use univariate logistic calibration (Platt scaling):
$$P(\text{Relevant} \mid s_{\cos}) = \frac{1}{1 + \exp\left(A_{\text{dense}} \cdot s_{\cos} + B_{\text{dense}}\right)}$$
Parameters $A_{\text{dense}}$ and $B_{\text{dense}}$ are fitted on calibration split query-passage pairs by minimizing binary cross-entropy loss:
$$\min_{A, B} -\sum_{k} \left[ y_k \log \sigma(A s_k + B) + (1 - y_k) \log(1 - \sigma(A s_k + B)) \right]$$
- **Low-Quality Pool Behavior:** When an out-of-domain query is embedded (e.g. general knowledge or hostel fees), cosine similarity to academic regulation passages typically drops to $s_{\cos} \le 0.30$. Under fitted logistic parameters ($A < 0$), $P(\text{Relevant} \mid s_{\cos}) \to 0.05$, correctly flagging the pool as ungrounded.

### 2.3 Hybrid Reciprocal Rank Fusion (RRF) Formulation

**Defect in Previous Design:** Treating RRF as a cardinal probability and ignoring runtime channel weights (`0.4/0.6`).

**Verified Runtime Reality:**
In `backend/app/retrieval/engine.py` (lines 225–248):
$$S_{\text{RRF}}(d) = \sum_{m \in \{\text{BM25}, \text{Dense}\}} \frac{w_m}{k + r_m(d)}$$
Where default configuration settings are:
- $k = 60$ (`settings.rrf_k`)
- $w_{\text{bm25}} = 0.4$, $w_{\text{dense}} = 0.6$ (`settings.bm25_weight`, `settings.dense_weight`)

**Theoretical Maximum:**
The theoretical maximum RRF score occurs if and only if a candidate is ranked #1 in both the BM25 pool ($r_{\text{bm25}} = 1$) and the Dense pool ($r_{\text{dense}} = 1$):
$$S_{\max}^{\text{RRF}} = \frac{w_{\text{bm25}}}{k + 1} + \frac{w_{\text{dense}}}{k + 1} = \frac{0.4}{61} + \frac{0.6}{61} = \frac{1.0}{61} \approx \mathbf{0.016393}$$
*(Note: If equal weights $1.0 / 1.0$ are used, $S_{\max}^{\text{RRF}} = \frac{2.0}{61} \approx \mathbf{0.032787}$).*

**Methodological Interpretation:**
RRF is an **ordinal rank fusion algorithm**, not a cardinal confidence estimator. The ratio:
$$s_{\text{rank\_index}}^{\text{RRF}} = \frac{S_{\text{RRF}}(d)}{S_{\max}^{\text{RRF}}} \in [0.0, 1.0]$$
measures **relative consensus rank**, NOT probability of truth. If a candidate appears at rank 1 in Dense but is absent from BM25 top-100, its normalized rank index is:
$$\frac{0.6 / 61}{1.0 / 61} = 0.60$$
This index indicates strong dense rank agreement, but cannot be treated as a probability without calibration.

### 2.4 Cross-Encoder Logit Transformation

**Defect in Previous Design:** Claiming fixed temperature scaling $\sigma(z / 1.8)$ was "Platt scaling".

**Corrected Formulation:**
The cross-encoder (`ms-marco-MiniLM-L-6-v2`) computes real-valued logits $z \in (-\infty, +\infty)$. True Platt scaling fits parameters $A_{\text{ce}}$ and $B_{\text{ce}}$ on held-out validation query-passage pairs:
$$P(\text{Relevant} \mid z) = \frac{1}{1 + \exp\left(A_{\text{ce}} \cdot z + B_{\text{ce}}\right)}$$
Parameters are fitted via maximum likelihood with regularized logistic loss:
$$\mathcal{L}(A, B) = -\sum_{i=1}^{M} \left[ y_i \log \hat{p}_i + (1 - y_i) \log(1 - \hat{p}_i) \right]$$
Where $\hat{p}_i = \sigma(A z_i + B)$. To prevent over-fitting on small calibration sets, $A$ and $B$ are initialized at $A = -1.0, B = 0.0$ and regularized with an $L_2$ penalty.
- **Low-Quality Pool Behavior:** When cross-encoder evaluates irrelevant text pairs, it produces strongly negative logits ($z \le -5.0$). Under Platt scaling, $P(\text{Relevant} \mid z \le -5.0) \le 0.007$, ensuring immediate rejection.

---

## 3. Redesigned Composite Evidence Confidence Index (CECI)

Rather than falsely claiming that an ad-hoc linear sum is a "probability", we define the **Composite Evidence Confidence Index (CECI)** $\Psi(q, D) \in [0.0, 1.0]$. 

### 3.1 Strict Feature Definitions and Bounded Domains

Let candidate pool $D = [d_1, d_2, \dots, d_K]$ be sorted descending by top ranker score. We extract a 5-dimensional feature vector $\mathbf{x} = [x_1, x_2, x_3, x_4, x_5]^T$:

| Feature | Notation | Range | Definition | Fallback / Missing Data Handling |
|---|---|---|---|---|
| **Top Calibrated Score** | $x_1 = s_{\text{cal}}(d_1)$ | $[0.0, 1.0]$ | Calibrated relevance score of highest-ranked candidate (from Cross-Encoder if enabled, else Dense Platt). | $0.0$ if candidate pool is empty. |
| **Rank Separation Margin** | $x_2 = \Delta s_{1,2}$ | $[0.0, 1.0]$ | $s_{\text{cal}}(d_1) - s_{\text{cal}}(d_2)$. Quantifies distinctiveness of best candidate over closest competitor. | If pool size $K=1$, default $x_2 = s_{\text{cal}}(d_1)$ (no competing candidate). |
| **Multi-Channel Consensus** | $x_3 = c_{\text{consensus}}$ | $[0.0, 1.0]$ | Degree of overlap between BM25 and Dense top-$K$ sets: $\frac{\|D_{\text{BM25}}^{K} \cap D_{\text{Dense}}^{K}\|}{\min(\|D_{\text{BM25}}^{K}\|, \|D_{\text{Dense}}^{K}\|)}$. | $0.5$ (neutral) if single-retriever mode is executed. |
| **Intent Keyword Coverage** | $x_4 = \text{cov}_{\text{intent}}$ | $[0.0, 1.0]$ | Fraction of query intent keywords present in $d_1$: $\frac{\|\mathcal{K}_q \cap \text{Tokens}(d_1)\|}{\max(1, \|\mathcal{K}_q\|)}$. | $1.0$ if query analysis identifies zero intent keywords ($|\mathcal{K}_q| = 0$). |
| **Regulatory Version Fit** | $x_5 = v_{\text{fit}}$ | $[0.0, 1.0]$ | Degree of temporal and jurisdictional compatibility between query constraints and passage metadata. | $0.5$ (neutral) if query has no temporal qualifiers. |

#### Explicit Definition of Regulatory Version Fit ($x_5$):
$$x_5 = \begin{cases}
1.0 & \text{Query year matches passage year explicitly (e.g. '2026-27' in query and calendar).} \\
1.0 & \text{Query has no year and passage is verified current regulation (e.g. Notification 307).} \\
0.5 & \text{Query has no year, passage is general SCSET UG rule without active competing notification.} \\
0.1 & \text{Query asks for current rule, but passage is historical (2017 Ordinance) with an active superseding rule.} \\
0.0 & \text{Direct year mismatch (e.g. query asks for 2026-27, passage is from 2017).}
\end{cases}$$

### 3.2 Mathematical Formulation of CECI

To guarantee strict compliance with $[0.0, 1.0]$ boundaries without clipping artifacts, CECI is formulated as a **convex combination**:
$$\Psi(q, D) = \sum_{j=1}^{5} w_j \cdot x_j \quad \text{where} \quad w_j \ge 0 \quad \text{and} \quad \sum_{j=1}^{5} w_j = 1.0$$

#### Why Each Feature is Essential:
1. **$x_1$ (Top Score):** Fundamental measure of semantic relevance. Without high $x_1$, candidate is irrelevant.
2. **$x_2$ (Margin):** Guards against ambiguous query drift. High $x_1$ with $x_2 \approx 0$ indicates ambiguous competing passages; high $x_1$ with high $x_2$ indicates unambiguous evidence.
3. **$x_3$ (Consensus):** Guards against modality-specific failure (e.g. BM25 keyword stuffing or dense vector semantic hallucination).
4. **$x_4$ (Intent Coverage):** Ensures regulatory entities (e.g., "supplementary", "makeup", "condonation") are explicitly grounded in the passage text, not inferred out of context.
5. **$x_5$ (Version Fit):** Directly addresses the Bennett University regulatory landscape where Ordinance 2017 and Notification 307 coexist.

### 3.3 Comparative Baseline Architectures

In Phase 2, CECI will be evaluated against four explicit reference baselines:
1. **Baseline 1 (Dense Cosine Alone):** $\Psi_1 = s_{\cos}(d_1)$.
2. **Baseline 2 (Cross-Encoder Alone):** $\Psi_2 = \sigma(z_1)$.
3. **Baseline 3 (RRF Rank Ratio Alone):** $\Psi_3 = \frac{S_{\text{RRF}}(d_1)}{S_{\max}^{\text{RRF}}}$.
4. **Baseline 4 (Equal-Weight CECI Heuristic):** $\Psi_4 = \sum_{j=1}^5 0.20 \cdot x_j$.
5. **Model 5 (Fitted Logistic CECI):** $\Psi_5 = \sigma(\mathbf{w}^T \mathbf{x} + b)$, where weights $\mathbf{w}$ are fitted via cross-validated logistic regression.

---

## 4. Parameter Estimation Workflow

All normalizers and confidence estimators must be fitted exclusively on training splits:

```
┌────────────────────────────────────────────────────────┐
│             Training / Calibration Split               │
│               (48 instances across 4 folds)            │
└───────────────────────────┬────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌────────────────────────┐      ┌────────────────────────┐
│  Fit Platt Parameters  │      │  Fit Logistic Weights  │
│  A_dense, B_dense      │      │  w_1 ... w_5, b        │
│  A_ce, B_ce            │      │  via L2-regularized    │
│  via Newton-Raphson    │      │  logistic regression   │
└────────────────────────┘      └────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│        Frozen Fitted Model for Test Evaluation         │
└────────────────────────────────────────────────────────┘
```

Weights and parameters will **never** be hardcoded or tuned against evaluation test folds.
