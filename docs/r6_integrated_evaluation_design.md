# IndicRAG-QA — R6 Integrated Evaluation Design

**Document Version:** 1.0  
**Phase:** R6 — Integrated Evaluation & Regression  
**Task:** Task 1 — Existing Benchmark Audit, Evaluation Design & Test Readiness  
**Date:** 2026-11-19  
**Status:** DESIGN APPROVED  

---

## 1. Objectives & Architectural Principles

Phase R6 establishes an end-to-end, empirical evaluation of IndicRAG-QA following the implementation and verification of:
- **R1:** Structural PDF extraction & table coordinate reconstruction.
- **R2 / R2.1:** Indexed SQLite relationship store (7,714 relationships) and academic calendar reconciliation.
- **R3:** Generic relationship extraction and single-hop relationship-aware retrieval.
- **R4 / R4.1 / R4.1.1:** Bounded multi-hop graph reasoning ($k \le 3$, $|P| \le 12$) with scope and cycle resolution.
- **R5:** Context-aware conversational feedback repair across 8 feedback subtypes.

### Core Evaluation Invariants
1. **Preservation of Baselines:** Frozen benchmark datasets (M3, M6, M9, M10) must never be altered, regenerated, or re-annotated.
2. **Production Invariant:** M10 Production Reranker (`settings.rerank_strategy == "production"`) is the active default; experimental E6b remains disabled.
3. **Statistical Honesty:** Language variants of the same underlying semantic intent must not be counted as independent samples; intent-level grouped evaluations are required.
4. **Provenance & Auditability:** Every evaluation metric must clearly specify its numerator, denominator, evaluation unit, and ground-truth source.
5. **Human vs Machine Transparency:** Benchmark items must be explicitly classified into Auto-Generated, Auto-Validated, Human-Reviewed, or Independently Human-Verified.

---

## 2. Integrated Evaluation Matrix (8 Dimensions)

The evaluation spans 8 orthogonal dimensions covering the complete IndicRAG-QA lifecycle:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 INDICRAG-QA R6 EVALUATION MATRIX                              │
├────────────────────────┬────────────────────────┬────────────────────────────────────────────┤
│ Dimension              │ Target Subsystem       │ Primary Focus                              │
├────────────────────────┼────────────────────────┼────────────────────────────────────────────┤
│ A. Document Ingestion  │ R1 Pipeline & Tables   │ OCR, table cell coordinates, idempotency   │
│ B. Retrieval Quality   │ Engine, FAISS, BM25    │ Hit@k, MRR, nDCG, table cell precision     │
│ C. Multi-Hop Reasoning │ R4 Reasoner & Graph    │ Hop depth ($d \le 3$), cycles, bounds ($|P| \le 12$)│
│ D. Answer Quality      │ Generator & Grounding  │ Entailment, claim verification, citations  │
│ E. Abstention & Bounds │ Evidence Controller    │ Precision on unanswerable/out-of-domain    │
│ F. Multilingual Robust │ Query Processor & Lang │ Cross-lingual parity (EN, HI, hi-Latn, Hing)│
│ G. Conversational Rep. │ R5 Feedback Handler    │ Multi-turn repair across 8 feedback types  │
│ H. Security & Isolation│ Multi-Tenant Isolation │ Cross-user leakage prevention across hops  │
└────────────────────────┴────────────────────────┴────────────────────────────────────────────┘
```

---

## 3. Dimension Specifications & Metric Definitions

### Dimension A: Document Ingestion & Structural Reconstruction
- **Scope:** Validates reliable extraction of text chunks, table headers, table cells, and relationship triples from official PDFs and dynamic user uploads.
- **Metrics:**
  1. **Table Cell Reconstruction Accuracy:**  
     $$\text{Acc}_{\text{cells}} = \frac{\text{Correctly extracted and indexed table cells}}{\text{Ground truth table cells}} \quad (\text{Target: } 21,840 \text{ cells from Academic Calendar})$$
  2. **Page & Provenance Integrity:**  
     $$\text{Rate}_{\text{prov}} = \frac{\text{Passages with valid, verified non-zero page numbers}}{\text{Total indexed passages}} \quad (\text{Target: } 100\%)$$
  3. **Ingestion Idempotency:**  
     Verification that re-ingesting official or user documents does not duplicate records in `documents`, `passages`, or `document_relationships`.
  4. **Dynamic Upload Ingestion:**  
     Ability to ingest arbitrary new PDFs without document-specific or calendar-specific hardcoding.

### Dimension B: Retrieval Performance
- **Scope:** Evaluates candidate selection across hybrid BM25 + FAISS + Cross-Encoder reranking.
- **Evaluation Unit:** Query and Intent level.
- **Metrics:**
  1. **Hit@k ($k \in \{1, 3, 5\}$):**  
     $$\text{Hit@}k = \frac{\sum_{q=1}^Q \mathbb{I}(\text{Top-}k \text{ contains at least one gold passage})}{Q}$$
  2. **Mean Reciprocal Rank (MRR):**  
     $$\text{MRR} = \frac{1}{Q} \sum_{q=1}^Q \frac{1}{\text{rank}_1(\text{first gold passage})}$$
  3. **Normalized Discounted Cumulative Gain (nDCG@5):**  
     Graded relevance assessment across candidate ranks 1 to 5.
  4. **Relationship Expansion Relevance:**  
     Ratio of relationship-expanded passages that are topical and support the query's information need.

### Dimension C: Bounded Multi-Hop Reasoning
- **Scope:** Evaluates the `MultiHopReasoner` across graph traversal depth, cycle detection, scope resolution, and evidence limits.
- **Evaluation Unit:** Multi-hop reasoning traces.
- **Metrics:**
  1. **Traversal Depth Invariant:**  
     $$\text{Max Depth} \le 3 \quad \forall Q \quad (\text{Violation if } d > 3)$$
  2. **Evidence Upper Bound Invariant:**  
     $$|P| \le 12 \quad \forall Q \quad (\text{Violation if } |P| > 12)$$
  3. **Cycle Pruning Rate:**  
     $$\text{Rate}_{\text{no\_cycle}} = \frac{\text{Queries with 0 duplicate passage IDs}}{\text{Total multi-hop queries}} \quad (\text{Target: } 100\%)$$
  4. **Institutional Scope Preservation:**  
     Detection and non-conflation of distinct regulatory scopes (e.g. Clause 30.1 course grading 70% vs Notification 307 exam eligibility 75%).
  5. **Medical Workflow Chain Completeness:**  
     Tracing multi-hop prerequisite chains: Base Rule $\rightarrow$ 10% Exception $\rightarrow$ 2-week continuous illness $\rightarrow$ Medical certificate $\rightarrow$ Coordinator / Dean approval.

### Dimension D: Answer Quality & Claim Grounding
- **Scope:** Evaluates generated answers against evidence passages and reference ground truth.
- **Evaluation Unit:** Atomic claims and full responses.
- **Metrics:**
  1. **Claim Grounding Ratio ($\text{CGR}$):**  
     $$\text{CGR} = \frac{\text{Atomic claims classified as ENTAILED}}{\text{Total atomic factual claims generated}}$$
  2. **Unsupported Claim Rate ($\text{UCR}$):**  
     $$\text{UCR} = \frac{\text{Atomic claims classified as INSUFFICIENT\_SUPPORT}}{\text{Total atomic factual claims generated}}$$
  3. **Contradiction Rate ($\text{CR}$):**  
     $$\text{CR} = \frac{\text{Atomic claims classified as CONTRADICTED}}{\text{Total atomic factual claims generated}} \quad (\text{Target: } 0.0\%)$$
  4. **Citation Page Accuracy:**  
     $$\text{Acc}_{\text{cite}} = \frac{\text{Citations where cited page matches stored passage physical page}}{\text{Total generated citations}} \quad (\text{Target: } 100\%)$$

### Dimension E: Abstention, Uncertainty & Clarification
- **Scope:** Evaluates the Evidence Controller on unanswerable queries, out-of-domain topics, contradictory user premises, and ambiguous cohort questions.
- **Evaluation Unit:** Query response decision.
- **Metrics:**
  1. **Abstention Precision ($\text{Prec}_{\text{abs}}$):**  
     $$\text{Prec}_{\text{abs}} = \frac{\text{True Unanswerable queries where system abstains}}{\text{Total queries where system abstains}}$$
  2. **Abstention Recall ($\text{Rec}_{\text{abs}}$):**  
     $$\text{Rec}_{\text{abs}} = \frac{\text{True Unanswerable queries where system abstains}}{\text{Total True Unanswerable queries in benchmark}} \quad (\text{Target: } \ge 90\% \text{ on M6 Negative})$$
  3. **False Abstention Rate ($\text{FAR}$):**  
     $$\text{FAR} = \frac{\text{Answerable queries incorrectly rejected as UNANSWERABLE}}{\text{Total Answerable queries}} \quad (\text{Target: } \le 10\%)$$
  4. **Cohort Clarification Trigger Rate:**  
     Verification that unanchored attendance queries trigger `status="clarification_required"` when applicable rules diverge across student cohorts.

### Dimension F: Multilingual Robustness
- **Scope:** Evaluates cross-lingual consistency across English (`en`), Devanagari Hindi (`hi`), Romanized Hindi (`hi-Latn`), and Hinglish (`en-hi`).
- **Evaluation Unit:** Intent-level group of 4 language variants ($N=60$ intents, 240 queries).
- **Metrics:**
  1. **Language Identification Accuracy:**  
     Accuracy of language and script detection in `QueryProcessor`.
  2. **Cross-Lingual Retrieval Parity:**  
     Comparison of Hit@5 across the 4 language variants for identical semantic intents.
  3. **Cross-Lingual Answer Consistency:**  
     Semantic equivalence of answers generated across the 4 languages for the same intent.

### Dimension G: Conversational Feedback & Answer Repair
- **Scope:** Evaluates the multi-turn conversational repair engine across all 8 supported feedback subtypes.
- **Evaluation Unit:** Conversational turn pair (Turn $t-1$ Answer $\rightarrow$ Turn $t$ Feedback $\rightarrow$ Repaired Answer).
- **Subtypes Evaluated:**
  1. `GENERAL_DISAGREEMENT`: Unanchored challenge without specific claim.
  2. `FACTUAL_CORRECTION`: User provides correct dates/rules.
  3. `MISSING_EXCEPTION`: User notes an unmentioned relaxation or clause.
  4. `WRONG_COHORT_OR_PROGRAM`: User specifies student admission year / batch.
  5. `SOURCE_DISAGREEMENT`: User challenges authoritative source.
  6. `CITATION_CHALLENGE`: User questions cited page or passage.
  7. `CLARIFICATION_REQUEST`: User asks for re-explanation.
  8. `ANSWER_REEXPLANATION`: User asks for simpler step-by-step breakdown.
- **Metric:** Repair Success Rate ($\text{Rate}_{\text{repair}}$):  
  $$\text{Rate}_{\text{repair}} = \frac{\text{Turns where feedback correctly updates answer / citations without hallucinating}}{\text{Total feedback challenge turns evaluated}}$$

### Dimension H: Security & Multi-Tenant Isolation
- **Scope:** Verifies that user privacy and data separation are enforced at every hop of multi-hop reasoning.
- **Evaluation Unit:** User sessions and tenant identities.
- **Metrics:**
  1. **User Own Upload Retrieval:** User A must successfully retrieve their own uploaded passages.
  2. **Cross-Tenant Leakage Rate:** Zero passages belonging to User B must be retrieved in User A's session:  
     $$\text{Leakage Rate} = \frac{\text{Foreign user passages returned}}{\text{Total passages returned}} = 0.0\%$$
  3. **Anonymous Access Boundary:** Anonymous queries (`user_id = None`) must access 100% official regulations and 0% user uploads.

---

## 4. Evaluation Methodology & Grouping Rules

### 4.1 Statistical Independence & Intent Grouping
In the M9 benchmark ($N=240$), the dataset is constructed from **60 unique semantic intents**, each translated into 4 languages.
- **Mandatory Rule:** Evaluating all 240 queries as independent i.i.d. samples artificially multiplies sample size by 4 and shrinks confidence intervals invalidly.
- **Methodology:**
  - Metrics must be reported **Per Language** ($N=60$ each for EN, HI, hi-Latn, Hinglish).
  - Overall accuracy must be reported with **Intent-Level Clustering**, where an intent is marked fully successful only if all language variants (or a specified quorum) succeed.

### 4.2 Confidence Intervals
- For binomial proportions (Hit@k, Accuracy, Grounding Ratio), 95% confidence intervals must be computed using the **Wilson Score Interval**:
  $$CI_{95\%} = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}} \quad (z = 1.96)$$
- For latency and continuous metrics, report mean, standard deviation, median (p50), and sample size ($N$).

### 4.3 Classification of Benchmark Examples
Every example used in the evaluation report must be assigned to one of four verified categories:
1. **Independently Human-Verified:** Queries and reference answers validated by a verified human subject-matter expert. (None currently in M3, M6, or M9).
2. **Human-Reviewed:** Reviewed by a project contributor but pending independent second-party verification.
3. **Auto-Validated:** Synthetically generated questions that passed automated deterministic validation rules (e.g., regex quote matching, document presence).
4. **Auto-Generated (Provisional):** Machine-translated or synthetically generated queries without manual inspection (e.g. all 240 M9 queries, tagged `PROVISIONAL_NOT_HUMAN_VERIFIED`).

---

## 5. Baselines and Comparison Rules

All R6 evaluation runs will be benchmarked against the historical frozen baselines:
- **Baseline 1 (M4 / M8):** Hybrid BM25 + FAISS without relationship expansion.
- **Baseline 2 (M9):** Cross-lingual retrieval and generation before R1/R2 relationship modeling.
- **Baseline 3 (M10):** Production Reranker baseline snapshot (`m10_baseline_snapshot.json`).
- **Baseline 4 (R4 / R4.1.1):** Bounded multi-hop reasoning baseline (`docs/r4_test_results.json`).

### Comparison Constraints
- Results must be generated in the same runtime environment (Windows CPU, Ollama local inference).
- Cold-start runs must be separated from steady-state warm runs.
- Production reranker configuration must remain fixed across comparisons.
- No benchmark files will be overwritten; all R6 artifacts will be written to new versioned files in `backend/data/experiments/r6/` and `docs/r6_*.md`.
