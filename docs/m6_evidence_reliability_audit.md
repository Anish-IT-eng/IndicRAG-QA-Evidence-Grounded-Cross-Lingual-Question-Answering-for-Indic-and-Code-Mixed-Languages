# IndicRAG-QA — M6 Phase 1: Evidence Reliability and Retrieval Score Audit

**Milestone:** M6 — Evidence Reliability and Answerability  
**Phase:** Phase 1 (Audit and Expansion Design)  
**Date:** 2026-11-10  
**Author:** Senior RAG Research Engineer & Multilingual Evaluation Specialist  
**Corpus State:** 142 child passages, 30 parent passages (172 SQLite rows in `backend/data/db/indicrag.db`)  
**Corpus SHA-256:** `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d`  
**Frozen M3 Benchmark SHA-256:** `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` ($N=15$)  

---

## 1. Executive Summary

Milestone 6 addresses the core challenge of **evidence-grounded trustworthiness**: determining whether retrieved context contains sufficient, valid, and uncontradicted evidence to answer a user's question, or whether the system must abstain.

In Milestone 5 (Experiment E10), an architectural defect in evidence score gating was identified: the Evidence Controller evaluated retrieval candidates using a static minimum score threshold (`settings.evidence_min_score = 0.35`), but received uncalibrated Reciprocal Rank Fusion (RRF) scores ($\le 0.033$). Consequently, all 15 benchmark queries evaluated to `INSUFFICIENT`, forcing false abstentions across all answerable queries. Furthermore, the frozen M3 benchmark contains only $N=2$ unanswerable queries, which is statistically inadequate for calibrating any reliable decision boundary.

This audit provides a comprehensive investigation of:
1. The mathematical score distributions across BM25, Dense FAISS, Hybrid RRF, and Cross-Encoder reranking.
2. The root-cause mechanics of the E10 score-scale defect.
3. The five canonical states and lifecycle transitions of the Evidence Controller (`backend/app/retrieval/evidence_controller.py`).
4. The citation extraction and claim validation workflows in generation and evaluation.
5. The requirements for an expanded benchmark ($N=60$) and calibrated multi-feature confidence estimator.

---

## 2. Retrieval Score Distribution Analysis

The current retrieval pipeline integrates four distinct scoring algorithms across its retrieval and ranking stages. Each produces scores on fundamentally different numerical scales, with distinct probabilistic and statistical interpretations.

### 2.1 Comparative Score Properties

| Retrieval Method | Implementation / Model | Mathematical Range | Empirical Benchmark Range | Value Meaning | Invariance / Scale Properties |
|---|---|---|---|---|---|
| **Lexical (BM25)** | `rank_bm25.BM25Okapi` | $[0, +\infty)$ | $2.14$ to $28.65$ | Inverse document frequency weighted term match | Unbounded; increases with query length and rare token overlap |
| **Dense Embeddings** | `paraphrase-multilingual-MiniLM-L12-v2` via FAISS FlatIP | $[-1.0, 1.0]$ (Cosine Sim) | $0.22$ to $0.78$ | Cosine of angle between L2-normalized vectors | Bounded; non-negative in practice for semantic text |
| **Hybrid RRF** | Reciprocal Rank Fusion ($k=60$) | $[0, 0.0328]$ | $0.0078$ to $0.0328$ | Sum of rank reciprocals: $\sum \frac{w_m}{k + r_m}$ | Strictly rank-dependent; completely blind to absolute semantic match |
| **Cross-Encoder Reranker** | `cross-encoder/ms-marco-MiniLM-L-6-v2` | $(-\infty, +\infty)$ (Logits) | $-6.84$ to $+5.92$ | Unnormalized log-odds of passage answering query | Unbounded real line; requires logistic/sigmoid transformation |

### 2.2 Mathematical Score Formulation

1. **BM25 Okapi:**
   $$\text{score}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
   Because term frequencies and IDFs accumulate additively over query terms, a multi-word query with several rare terms easily exceeds scores of $20.0$, whereas a short single-term query may peak at $3.5$, despite both being perfectly relevant.

2. **Dense Inner Product (Cosine Similarity):**
   $$\text{sim}(\mathbf{q}, \mathbf{d}) = \frac{\mathbf{q} \cdot \mathbf{d}}{\|\mathbf{q}\|_2 \|\mathbf{d}\|_2} = \tilde{\mathbf{q}} \cdot \tilde{\mathbf{d}}$$
   Because vectors are L2-normalized prior to insertion in FAISS `IndexFlatIP`, the inner product equals cosine similarity. Relevant passages typically fall in the range $[0.50, 0.85]$, while irrelevant passages hover around $[0.15, 0.35]$.

3. **Reciprocal Rank Fusion (RRF):**
   $$S_{\text{RRF}}(d) = \sum_{m \in \{\text{BM25}, \text{Dense}\}} \frac{w_m}{k + r_m(d)}$$
   Under the project configuration ($k=60$, $w_{\text{bm25}}=0.4$, $w_{\text{dense}}=0.6$ or equal weights $1.0/1.0$):
   - Under $0.4 / 0.6$: Theoretical maximum (Rank 1 in both lists) is $\frac{0.4}{60+1} + \frac{0.6}{60+1} = \frac{1.0}{61} \approx \mathbf{0.01639}$.
   - Under $1.0 / 1.0$: Theoretical maximum is $\frac{1.0}{61} + \frac{1.0}{61} = \frac{2.0}{61} \approx \mathbf{0.03279}$.
   - Rank 10 in a single list yields $\frac{0.6}{60+10} \approx \mathbf{0.00857}$.

4. **Cross-Encoder Logits:**
   $$z = f_{\text{transformer}}([\text{CLS}] \circ \text{query} \circ [\text{SEP}] \circ \text{passage} \circ [\text{SEP}])$$
   The raw score $z$ is a linear logit representing $\log \frac{P(\text{relevant})}{1 - P(\text{relevant})}$. A score of $z=0$ represents an even $50\%$ probability, $z=+4.0$ represents $P \approx 98.2\%$, and $z=-4.0$ represents $P \approx 1.8\%$.

---

## 3. Root Cause Investigation of the E10 Defect

### 3.1 Defect Mechanics in `backend/app/retrieval/evidence_controller.py`

In `EvidenceController.__init__`:
```python
def __init__(
    self,
    min_score: float = settings.evidence_min_score,  # default 0.35
    sufficient_count: int = settings.evidence_sufficient_count,  # default 1
    max_retries: int = settings.max_retrieval_retries,  # default 2
):
    self.min_score = min_score
    self.sufficient_count = sufficient_count
    self.max_retries = max_retries
```

In `EvidenceController.evaluate()`:
```python
# Filter by minimum score
above_threshold = [p for p in valid if p.score >= self.min_score]

if len(above_threshold) == 0:
    return EvidenceDecision(
        status=EvidenceStatus.INSUFFICIENT,
        valid_passages=valid,
        coverage_score=0.0,
        explanation=f"Retrieval scores below evidence threshold ({self.min_score:.2f}). Insufficient evidence to answer.",
        retry_recommended=attempt < self.max_retries,
    )
```

### 3.2 Failure in `scripts/run_m5_experiments.py` (E10)

In `run_e10()`:
```python
retrieved = hybrid_retrieval(inst.question, top_k=5, lang=inst.language)
# Passages returned with raw RRF scores:
# p.score in [0.008, 0.032]
decision = controller.evaluate(retrieved_result)
```

Because every retrieved passage had $p.\text{score} \le 0.0328$, the condition $p.\text{score} \ge 0.35$ was mathematically impossible to satisfy. 
Consequently:
- `above_threshold` was empty for **100% of benchmark queries** (15 / 15).
- Every query received `EvidenceStatus.INSUFFICIENT`.
- While unanswerable queries (`b0a1c010`, `b0a1c011`) were correctly marked `INSUFFICIENT` by accident of scale failure, all 13 answerable queries were also marked `INSUFFICIENT`.
- If generator abstention was enforced strictly, the system would exhibit a **False Abstention Rate of 100%** (13 / 13).

### 3.3 Methodological Conclusion
Static thresholding (`0.35`) is valid **only** when applied to a calibrated score metric (e.g., Cosine Similarity or Sigmoid Cross-Encoder probability). Applying a fixed $0.35$ threshold to uncalibrated RRF scores or raw Cross-Encoder logits is a fatal pipeline error.

---

## 4. Evidence Controller State Machine Audit

The Evidence Controller implements a 5-state decision model. Below is the authoritative specification of state triggers, semantics, and downstream generator contracts.

```
                         [ Retrieval Result ]
                                  │
                                  ▼
                        Passage List Empty?
                        ├── Yes ──► [ MISSING ] ──────► Abstain (Out of corpus)
                        └── No
                                  │
                                  ▼
                     Conflicting Versions Present?
                        ├── Yes ──► [ CONFLICTING ] ──► Disclose both / Ask batch
                        └── No
                                  │
                                  ▼
                   Top Score >= Calibrated Threshold?
                        ├── No ───► [ INSUFFICIENT ] ─► Retry or Abstain
                        └── Yes
                                  │
                                  ▼
                     Multi-Part Query Coverage < 0.6?
                        ├── Yes ──► [ PARTIAL ] ──────► Answer with caveats
                        └── No
                                  │
                                  ▼
                    Valid Count >= sufficient_count?
                        ├── Yes ──► [ SUFFICIENT ] ───► Proceed to Grounded Answer
                        └── No ───► [ INSUFFICIENT ] ─► Abstain
```

### 4.1 Canonical State Definitions

| State | Semantic Meaning | Retried? | Generator Action | Citation Requirement |
|---|---|---|---|---|
| **`SUFFICIENT`** | Retrieved passages fully answer all aspects of the query with high confidence. | No | Generates direct grounded answer. | Mandatory exact citation `[Source: pid, page X]`. |
| **`PARTIAL`** | Evidence answers some clauses/sub-questions, but key aspects are missing. | Optional | Generates answer for covered parts, explicitly noting missing elements. | Cites valid passages; flags unverified parts. |
| **`INSUFFICIENT`** | Candidates exist but relevance scores fall below minimum confidence threshold. | Yes (up to max retries) | Returns standardized abstention response. | No citations generated. |
| **`CONFLICTING`** | Multiple document versions apply (e.g. 2017 Ordinance vs 2022 Notification). | No | Synthesizes comparative answer highlighting rules per cohort/year. | Cites both versions with respective effective dates. |
| **`MISSING`** | Zero passages returned by retriever (query completely disjoint from corpus). | Yes (fallback query) | Returns standardized abstention response. | No citations generated. |

### 4.2 Version Conflict Logic

Currently, `_split_passages()` checks:
```python
for p in passages:
    if p.version_info.superseded_by:
        conflicting.append(p)
    elif p.is_valid_for_query is False:
        conflicting.append(p)
    else:
        valid.append(p)
```
- **Audit Finding:** In M5 E8, `validate_versions()` unilaterally marked 2017 Ordinance passages as `is_valid_for_query = False` even when no academic year was specified in the query.
- **Remediation for M6:** Passages should only be classified into `conflicting` when:
  1. Passages from distinct documents make contradictory assertions on the same regulatory topic (e.g., Clause 30.1 stating 70% vs Notification 307 stating 75%).
  2. The query does not specify which document/year governs.
  3. When the query explicitly requests a specific year, the applicable passage is `valid` and the other is demoted.

---

## 5. Citation Validation and Claim Support Audit

### 5.1 Generator Citation Extraction (`backend/app/generation/generator.py`)

The generator parses citations via regex pattern:
```python
pattern = re.compile(r"\[Source:\s*([\w-]+)(?:,\s*page\s*(\d+))?\]")
```
Validation rules enforced:
1. **Passage ID Existence:** The parsed `passage_id` must exist in `passage_map` (the set of passages actually passed to the LLM).
2. **Deduplication:** Repeated citations for the same passage are collapsed.
3. **Invalid Rejection:** Any citation citing a hallucinated ID or an ID outside the retrieved context is discarded with a warning:
   ```python
   logger.warning("Citation references unknown passage_id: %s", pid)
   ```

### 5.2 Critical Defect: Hardcoded Claim Support

In `generator.py` line 151:
```python
citations.append(Citation(
    document_id=p.document_id,
    filename=document_filenames.get(p.document_id, "unknown"),
    page=p.page_number or page,
    passage_id=pid,
    quote=p.text[:300],
    section=p.section,
    heading=p.heading,
    version_info=DocumentVersionInfo(...),
    claim_supported=True,  # <--- DEFECT: HARDCODED TO TRUE
))
```
- **Audit Finding:** `claim_supported` is currently hardcoded to `True` for any citation whose `passage_id` exists in the retrieved set.
- **Consequence:** If the LLM generates a hallucinated statement (e.g., *"Attendance requirement is 50%"*) and tags it with a valid passage ID that actually says *"Attendance requirement is 75%"*, the current pipeline classifies the claim as **fully supported**!
- **M6 Requirement:** Implement sentence-level claim-evidence entailment verification or n-gram overlap check before declaring a claim supported.

---

## 6. Current Abstention Baseline Limitations

The frozen M3 benchmark (`final_verified_dataset.csv`) contains:
- Total instances: $N = 15$
- Answerable instances: $N = 13$ (86.7%)
- Unanswerable instances: $N = 2$ (13.3%)
  - `b0a1c010`: PhD dissertation thesis fee (Out-of-scope; SCSET UG covers undergraduate only).
  - `b0a1c011`: Hostel mess fee refund (Out-of-scope; hostel policies are outside academic regulations).

### Methodological Vulnerabilities:
1. **Zero Degrees of Freedom for Threshold Optimization:** Two negative examples allow only three possible false alarm states ($0\%, 50\%, 100\%$). It is statistically invalid to compute an ROC curve, Precision-Recall curve, or optimal F1 threshold on $N=2$.
2. **Narrow Unanswerability Typology:** Both existing queries belong to a single category: *completely absent out-of-domain topics*. The benchmark lacks:
   - Queries with missing temporal qualifiers (AY indeterminate).
   - Queries with contradictory constraints.
   - Queries asking for non-existent clauses within existing topics (e.g. attendance waiver for startup founders).
   - Ambiguous student cohort queries.
3. **Language Imbalance in Unanswerables:** The two unanswerable queries cover only English (`en`) and Devanagari Hindi (`hi`). Hinglish (`hi-en`) and Romanized Hindi (`hi-Latn`) have zero unanswerable queries.

---

## 7. Audit Recommendations for M6

1. **Implement Calibrated Score Normalization:** Standardize all retrieval scores to a bounded probability scale $[0.0, 1.0]$ before passing them to the Evidence Controller.
2. **Multi-Feature Confidence Formulation:** Augment the decision boundary beyond a single top score to include margin-to-second ($\Delta s = s_1 - s_2$), cross-channel consensus (BM25 + Dense agreement), and intent keyword coverage.
3. **Expand Benchmark to $N=60$:** Add 45 new instances (27 answerable, 18 unanswerable), balancing all 4 language modalities and comprehensive query categories while preserving the original 15 instances frozen.
4. **Implement True Claim Support Checking:** Replace hardcoded `claim_supported=True` with token overlap and semantic entailment checking against cited passage text.
5. **Calibrate Strictly on Train/Val Splits:** Ensure no score threshold is tuned on test evaluations.

