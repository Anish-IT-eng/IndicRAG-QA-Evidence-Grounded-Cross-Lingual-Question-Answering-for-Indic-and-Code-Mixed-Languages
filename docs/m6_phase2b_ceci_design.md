# IndicRAG-QA — M6 Phase 2B: Composite Evidence Confidence Index (CECI) Design

**Milestone:** M6 — Evidence Reliability and Answerability  
**Status:** PHASE 2B DELIVERABLE (Approved Implementation)  
**Corpus SHA-256:** `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d`  
**Execution Context:** Theory-Anchored Heuristic Evidence Scoring  

---

## 1. Executive Summary & Design Principles

The **Composite Evidence Confidence Index (CECI)**, denoted $\Psi \in [0.0, 1.0]$, is a transparent, multi-dimensional evidence evaluation metric designed to measure the factual groundedness and regulatory reliability of retrieved context before response generation.

### Mandatory Research Principles
1. **Strict Convex Combination:** $\Psi = \sum_{i=1}^5 w_i f_i$, where $\forall i, w_i \ge 0$, $\sum_{i=1}^5 w_i = 1.0$, and $\forall i, f_i \in [0.0, 1.0]$.
2. **Deterministic Precedence Hierarchy:** Cross-Encoder (if available) > RRF (if hybrid) > Dense > BM25.
3. **Same-Scale Margin Constraint:** The score margin $f_2$ must be calculated strictly between items measured on the identical scale. It is mathematically invalid to subtract a BM25 score from a cross-encoder score.
4. **Conservative Missing-Feature Fallbacks:** When context is missing (e.g. single modality executed, keyword-less query), features must default to neutral or conservative values ($0.50$), **NEVER** optimistic perfect scores ($1.00$). If zero passages are retrieved, all features evaluate strictly to $0.00$.
5. **No Probabilistic Claims:** $\Psi$ is a heuristic ordinal confidence index, **NOT** an empirical probability of correctness.

---

## 2. Mathematical Formulation & Weight Distribution

$$\Psi = w_1 f_1 + w_2 f_2 + w_3 f_3 + w_4 f_4 + w_5 f_5$$

| Weight | Feature Name | Description | Rationalized Heuristic Weight |
| :--- | :--- | :--- | :--- |
| **$w_1$** | Top-1 Normalized Relevance ($f_1$) | Peak confidence of the best retrieved passage | **$0.35$** |
| **$w_2$** | Same-Scale Score Margin ($f_2$) | Distinction between top-1 and top-2 candidates | **$0.15$** |
| **$w_3$** | Modality Consensus ($f_3$) | Agreement between lexical (BM25) and semantic (Dense) pools | **$0.15$** |
| **$w_4$** | Intent Keyword Coverage ($f_4$) | Proportion of query keywords found in retrieved evidence | **$0.15$** |
| **$w_5$** | Regulatory Version Fit ($f_5$) | Document validity, currency, and lack of superseded tags | **$0.20$** |
| **Total** | **Convex Sum** | $\sum_{i=1}^5 w_i = 0.35 + 0.15 + 0.15 + 0.15 + 0.20$ | **$1.00$** |

---

## 3. Detailed Feature Definitions

### 3.1 Feature 1: Top-1 Normalized Relevance ($f_1$)

Measures the normalized retrieval score of the top-ranked passage $p_{(1)}$ following strict deterministic modality precedence:

1. **Precedence Tier 1 (Cross-Encoder):** If cross-encoder rerank scores exist on $p_{(1)}$:
   $$f_1 = \tilde{s}_{\text{CE}}(\text{logit}_{(1)}) = \sigma(\text{logit}_{(1)})$$
2. **Precedence Tier 2 (RRF Rank):** If hybrid RRF fusion was executed:
   $$f_1 = \tilde{s}_{\text{RRF}}(1) = 1.0$$
3. **Precedence Tier 3 (Dense Cosine):** If dense retrieval was executed:
   $$f_1 = \tilde{s}_{\text{dense}}(s_{(1)}^{\text{dense}}) = \sigma(1.0 \cdot s_{(1)}^{\text{dense}})$$
4. **Precedence Tier 4 (BM25 Lexical):**
   $$f_1 = \tilde{s}_{\text{BM25}}(s_{(1)}^{\text{BM25}}) = \sigma\left(\frac{s_{(1)}^{\text{BM25}} - 15.0}{3.0}\right)$$

### 3.2 Feature 2: Top-1 vs. Top-2 Same-Scale Margin ($f_2$)

A large margin between the top-ranked passage and the runner-up indicates unambiguous evidence retrieval, whereas a zero or near-zero margin indicates competing or ambiguous candidate passages:

$$f_2 = \text{clip}\left(\tilde{s}_{(1)}^{\text{mod}} - \tilde{s}_{(2)}^{\text{mod}}, 0.0, 1.0\right)$$

- **Strict Scale Consistency:** Both $\tilde{s}_{(1)}$ and $\tilde{s}_{(2)}$ MUST be evaluated on the identical modality (e.g., both cross-encoder logits, or both BM25 scores).
- **Single-Candidate Fallback:** If only a single passage is retrieved ($K=1$), runner-up score does not exist. To avoid either penalizing single authoritative passages or assuming infinite separation, $f_2 \triangleq 0.50$ (neutral conservative fallback).

### 3.3 Feature 3: Modality Retrieval Consensus ($f_3$)

Evaluates whether independent lexical and semantic retrieval retrieval pipelines agree on the relevant evidence context:

$$f_3 = J(D_{\text{BM25}}, D_{\text{Dense}}) = \frac{|D_{\text{BM25}} \cap D_{\text{Dense}}|}{|D_{\text{BM25}} \cup D_{\text{Dense}}|}$$

- When full candidate ID pools are provided, $f_3$ computes the exact Jaccard similarity.
- **Conservative Fallback:** If only a single modality was executed or candidate pools are unavailable, $f_3 \triangleq 0.50$ (neutral conservative fallback).

### 3.4 Feature 4: Intent Keyword Evidence Coverage ($f_4$)

Calculates the proportion of extracted query intent keywords present in the retrieved evidence text:

$$f_4 = \frac{|\{k \in K_{\text{query}} \mid k \in \text{Text}(D_{\text{valid}})\}|}{|K_{\text{query}}|}$$

- **Mandatory Correction (Non-Optimistic Fallback):** If the query has no intent keywords ($|K_{\text{query}}| = 0$) or query analysis was unpopulated, $f_4 \triangleq 0.50$ (neutral conservative fallback). **NEVER** return optimistic $1.00$.
- If passages are empty, $f_4 \triangleq 0.00$.

### 3.5 Feature 5: Regulatory Version and Applicability Fit ($f_5$)

Encodes university regulatory governance directly into the evidence confidence metric:

$$f_5 = \begin{cases}
1.0 & \text{if document is verified current, non-superseded, and matches cohort} \\
0.5 & \text{if applicability is unconfirmed or general university policy} \\
0.0 & \text{if document is explicitly superseded, conflicting, or debarred}
\end{cases}$$

---

## 4. Conservative Fallback Matrix

| Missing Condition | Affected Feature | Implemented Fallback | Justification |
| :--- | :--- | :--- | :--- |
| Zero retrieved passages ($|D|=0$) | All ($f_1 \dots f_5$) | **$0.00$** | Absolute absence of evidence requires zero confidence. |
| Single candidate pool ($K=1$) | $f_2$ (Margin) | **$0.50$** | Cannot compute margin; neutral middle ground avoids penalizing valid single-clause rules. |
| Single modality executed | $f_3$ (Consensus) | **$0.50$** | Cannot evaluate cross-modal agreement; neutral middle ground. |
| Keyword-less query ($|K_{\text{query}}|=0$) | $f_4$ (Coverage) | **$0.50$** | Keyword absence does not prove complete evidence coverage. |
| Unconfirmed document version | $f_5$ (Regulatory) | **$0.50$** | Document is active but lack of explicit timestamp requires conservative neutrality. |

---

## 5. Architectural Integration

The CECI estimator is implemented in `app/retrieval/ceci.py` and produces auditable `CECIResult` objects:

```python
@dataclass
class CECIResult:
    ceci_heuristic_score: float
    features: Dict[str, float]
    weights: Dict[str, float]
    primary_modality: str
    relevance_source_precedence: str
    is_calibrated_probability: bool = False
    notes: str = ""
```

The resulting `ceci_heuristic_score` is directly fed into the six-state `EvidenceController` for thresholding against:
- $\tau_{\text{sufficient}} = 0.65$
- $\tau_{\text{insufficient}} = 0.35$

