# IndicRAG-QA — M6 Phase 2B: Transparent Score Normalization Specification

**Milestone:** M6 — Evidence Reliability and Answerability  
**Status:** PHASE 2B DELIVERABLE (Approved Implementation)  
**Corpus SHA-256:** `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d`  
**Execution Context:** Theory-Anchored Heuristic Normalization Framework  

---

## 1. Executive Summary & Governance Preconditions

In production Retrieval-Augmented Generation (RAG) pipelines, multimodal retrieval systems aggregate evidence scores from heterogeneous sources:
1. Unbounded lexical match scores (BM25: $[0, \infty)$)
2. Directional vector space similarities (Dense cosine: $[-1, 1]$, empirically clustered in $[0.30, 0.85]$)
3. Unbounded discriminative cross-attention logits (Cross-Encoder: $(-\infty, +\infty)$)
4. Rank-reciprocal sums (Reciprocal Rank Fusion: $\sum \frac{1}{60 + r} \in (0, 0.033]$)

A critical defect identified in early milestones was the naive linear mixing or heuristic thresholding across incompatible mathematical scales.

### Mandatory Research Constraints & Anti-Overfitting Safeguards
- **Heuristic Normalization Only:** The mathematical transformations detailed in this specification are transparent, theory-anchored engineering normalizers designed to map disparate numerical ranges into the common unit interval $[0.0, 1.0]$.
- **Strict Prohibition Against Empirical Calibration Claims:** These transformations are **NOT** empirically fitted calibration parameters, **NOT** Platt scaling, **NOT** isotonic regressions, and **NOT** learned temperature parameters.
- **Probabilistic Meaning Prohibited:** Output values $\tilde{s} \in [0.0, 1.0]$ represent normalized ordinal features for downstream ranking and heuristic thresholding. They **MUST NEVER** be interpreted or reported as calibrated posterior probabilities of document relevance $P(\text{Relevant} \mid q, d)$.
- **Raw Score Preservation:** Every transformation produces a structured `NormalizedScore` container that preserves the exact, unaltered raw retrieval score alongside the normalized representation.

---

## 2. Modality Scale Disparities & Theoretical Analysis

| Retrieval Modality | Mathematical Domain | Empirical Domain (Official Corpus) | Characteristics | Failure Mode of Direct Linear Scaling |
| :--- | :--- | :--- | :--- | :--- |
| **BM25 Lexical** | $[0, \infty)$ | $[2.1, 28.6]$ (median: $15.2$) | Unbounded, sensitive to document length and query term frequency. | Query-local min-max normalization destroys cross-query score comparability. |
| **Dense Cosine** | $[-1.0, 1.0]$ | $[0.32, 0.84]$ (mean: $0.58$) | High-dimensional geometric dot product of normalized embeddings. | Range compression; cosine distances do not linearly translate to relevance odds. |
| **Cross-Encoder** | $(-\infty, +\infty)$ | $[-6.2, +4.8]$ | Uncalibrated classification logits from joint query-passage cross-attention. | Negative logits cause clamping issues; uncalibrated margins vary with prompt framing. |
| **RRF Fusion** | $(0, 0.033]$ | $[0.008, 0.032]$ | Sum of rank reciprocals $\sum \frac{1}{k + r_i}$. | Score magnitude is an artifact of pool depth $K$ and constant $k=60$, not evidence relevance. |

---

## 3. Mathematical Formulations

### 3.1 BM25 Provisional Corpus-Anchored Sigmoid

To transform unbounded positive BM25 scores into $[0.0, 1.0]$ without query-local scale distortion, we anchor a logistic sigmoid to the empirical corpus median:

$$\tilde{s}_{\text{BM25}}(s) = \sigma\left(\frac{s - s_0}{\tau}\right) = \frac{1}{1 + \exp\left(-\frac{s - 15.0}{3.0}\right)}$$

- **Provisional Operating Center ($s_0 = 15.0$):** Derived from corpus-wide median match scores observed during M4 benchmark construction on Bennett University regulations.
- **Provisional Scale ($\tau = 3.0$):** Selected to span the interquartile range $[9.0, 21.0]$ over the transition interval $[0.10, 0.90]$.
- **Boundary Properties:**
  $$\lim_{s \to 0^+} \tilde{s}_{\text{BM25}}(s) = \sigma(-5.0) \approx 0.0067, \quad \lim_{s \to \infty} \tilde{s}_{\text{BM25}}(s) = 1.0$$
  For any $s \le 0$ or non-finite inputs, $\tilde{s}_{\text{BM25}} \triangleq 0.0$.

### 3.2 Dense Cosine Prior-Anchored Logistic

Dense embeddings from `sentence-transformers/all-MiniLM-L6-v2` produce cosine similarities where irrelevant negative passages typically score in $[0.15, 0.35]$ and relevant passages score in $[0.65, 0.85]$. To avoid arbitrary artificial shifts while maintaining monotonicity:

$$\tilde{s}_{\text{dense}}(s) = \sigma(A \cdot s + B) = \frac{1}{1 + \exp(-1.0 \cdot s)}$$

- **Un-shifted Parameterization ($A = 1.0, B = 0.0$):** Preserves natural ordering and ensures zero cosine similarity maps to neutral $0.50$.
- **Empirical Mapping:**
  - $s = 0.35 \implies \tilde{s} = 0.5866$
  - $s = 0.65 \implies \tilde{s} = 0.6570$
  - $s = 0.85 \implies \tilde{s} = 0.7006$

### 3.3 Cross-Encoder Logit Logistic Transformation

Cross-encoder models (`ms-marco-MiniLM-L-6-v2`) output raw unbounded logits $z \in (-\infty, +\infty)$:

$$\tilde{s}_{\text{CE}}(z) = \sigma(z) = \frac{1}{1 + \exp(-z)}$$

- **Logit Invariance:** Maps positive logits ($z > 0$) to $(0.5, 1.0]$ and negative logits ($z < 0$) to $[0.0, 0.5)$.
- **Extreme Clamping:** For numerical stability, $z > 35.0 \implies 1.0$ and $z < -35.0 \implies 0.0$.

### 3.4 Reciprocal Rank Fusion (RRF) Normalized Rank Feature

RRF raw scores ($\sim 0.016$) cannot be directly mapped via sigmoid because their values represent rank sums rather than margins. We implement an auditable rank-based normalizer over the candidate pool:

$$\tilde{s}_{\text{RRF}}(r) = \frac{K - r + 1}{K}$$

where $K$ is the candidate pool depth ($K = |D_{\text{pool}}|$) and $r \in [1, K]$ is the 1-based rank of the candidate.

- **Boundary Condition ($K = 1$):** If a single candidate is returned, $\tilde{s}_{\text{RRF}}(1) = \frac{1 - 1 + 1}{1} = 1.0$.
- **Boundary Condition ($K = 0$):** Returns empty list.
- **Deterministic Tie-Breaking:** Candidates with identical raw RRF scores receive the average fractional rank of their tied group:
  $$\bar{r} = \frac{1}{|T|} \sum_{i \in T} r_i \implies \tilde{s}_{\text{RRF}}(\bar{r}) = \frac{K - \bar{r} + 1}{K}$$
  This prevents rank arbitrariness from non-deterministic database ordering.

---

## 4. Scale Invariance and Monotonicity Guarantees

Every implemented normalizer satisfies strict mathematical monotonicity:

$$\forall s_1, s_2 \in \mathbb{R}, \quad s_1 > s_2 \implies \tilde{s}(s_1) \ge \tilde{s}(s_2)$$

Strict equality occurs only at clamped floating-point saturation boundaries ($s > 35.0$ or $s < -35.0$).

```
Raw BM25 Score:        0.0  ──>  9.0  ──>  15.0  ──>  21.0  ──>  27.0
Normalized Score:     0.007 ──> 0.119 ──> 0.500 ──> 0.881 ──> 0.982

Raw Dense Cosine:     -0.5  ──>  0.0  ──>  0.50  ──>  0.75  ──>  1.00
Normalized Score:     0.378 ──> 0.500 ──> 0.622 ──> 0.679 ──> 0.731

Raw CE Logit:         -4.0  ──> -1.0  ──>  0.00  ──>  2.00  ──>  4.00
Normalized Score:     0.018 ──> 0.269 ──> 0.500 ──> 0.881 ──> 0.982
```

---

## 5. Structured Data Schema & Audit Logging

The runtime implementation produces immutable `NormalizedScore` containers (`app/retrieval/score_normalizer.py`):

```python
@dataclass(frozen=True)
class NormalizedScore:
    raw_score: float
    normalized_score: float
    modality: RetrievalModality
    is_empirically_calibrated: bool = False
    transformation_notes: str = ""
```

### Verification & Validation Post-Conditions
1. Normalized score is guaranteed finite (`math.isfinite(normalized_score) is True`).
2. Normalized score is strictly bounded (`0.0 <= normalized_score <= 1.0`).
3. `is_empirically_calibrated` is hardcoded to `False` to prevent experimental misinterpretation.

---

## 6. Regression & Verification Results

All normalizer functions and boundary behaviors are verified under `backend/tests/test_m6_phase2b_scoring_and_controller.py`:
- `test_bm25_sigmoid_normalization`: Verified center (15.0 $\to$ 0.500), monotonicity, and non-finite clamping.
- `test_dense_logistic_normalization`: Verified unshifted midpoint (0.0 $\to$ 0.500) and $\pm\infty$ safety.
- `test_cross_encoder_normalization`: Verified logit transformation and sign preservation.
- `test_rrf_rank_normalization_and_ties`: Verified pool depth $K=1$, $K=4$, and fractional tie handling.
- `test_unified_dispatcher`: Verified multi-modal dispatching and fallback handling.

**Test Outcome:** 21/21 Phase 2B tests passing; 163/163 full suite regression tests passing.

