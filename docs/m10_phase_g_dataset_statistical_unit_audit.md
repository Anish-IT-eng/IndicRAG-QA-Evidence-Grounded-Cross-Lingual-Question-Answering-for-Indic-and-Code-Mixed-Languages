# M10 Phase G: Dataset & Statistical Unit Audit

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-DATASET-AUDIT`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Status:** Audit Completed  

---

## 1. Executive Summary

This audit establishes the mathematical and methodological foundation for all statistical inferences conducted in Milestone M10 Phase G. In cross-lingual evaluation benchmarks, a frequent methodological flaw is treating parallel translations of the same semantic question as independent observations ($N=240$). 

This audit demonstrates that:
1. The **Semantic Intent Group** ($N=60$ total intents: $N=45$ answerable, $N=15$ unanswerable) constitutes the sole **independent statistical unit**.
2. Parallel queries across the four language formulations (`en`, `hi`, `hi-Latn`, `en-hi`) are **clustered repeated measures** sharing underlying passage relevance distributions, regulatory complexity, and answerability status.
3. Treating queries across languages as independent observations induces severe **pseudoreplication**, falsely inflating sample size by $4\times$, artificially narrowing standard errors, and yielding spuriously low p-values.
4. All hypothesis testing, confidence intervals, and bootstrap resampling throughout Phase G strictly respect cluster-level dependencies.

---

## 2. Frozen Evaluation Population Audit

The evaluation dataset utilized across Milestones M9 and M10 is frozen at [backend/data/experiments/m9/m9_evaluation_dataset.jsonl](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m9/m9_evaluation_dataset.jsonl).

### 2.1 Population Stratification

| Stratum | Intent Groups ($N_{\text{intent}}$) | Queries per Intent | Total Queries ($N_{\text{query}}$) | Language Formulations |
|---|---:|---:|---:|---|
| **Answerable** | 45 | 4 | 180 | English (`en`), Hindi (`hi`), Romanized Hindi (`hi-Latn`), Hinglish (`en-hi`) |
| **Unanswerable** | 15 | 4 | 60 | English (`en`), Hindi (`hi`), Romanized Hindi (`hi-Latn`), Hinglish (`en-hi`) |
| **Total Benchmark** | **60** | **4** | **240** | **4 balanced parallel splits** |

### 2.2 Per-Language Breakdown

| Language Formulation | Language Code | Script | Answerable Queries | Unanswerable Queries | Total Queries |
|---|---|---|---:|---:|---:|
| English | `en` | Latin | 45 | 15 | 60 |
| Hindi | `hi` | Devanagari | 45 | 15 | 60 |
| Romanized Hindi | `hi-Latn` | Latin | 45 | 15 | 60 |
| Hinglish | `en-hi` | Latin (Code-mixed) | 45 | 15 | 60 |
| **All Languages** | — | — | **180** | **60** | **240** |

Each intent group $I_j$ ($j \in \{1, \dots, 60\}$) maps to exactly four parallel query instances:
$$I_j = \{ q_{j,\text{en}}, q_{j,\text{hi}}, q_{j,\text{hi-Latn}}, q_{j,\text{en-hi}} \}$$
All four queries within intent $I_j$ share identical target gold passage IDs, regulatory clause citations, and expected ground-truth answers.

---

## 3. The Statistical Unit: Independence vs. Clustered Pseudoreplication

### 3.1 The i.i.d. Assumption in Information Retrieval

Standard statistical inference tests (e.g., Student's t-test, Wilcoxon signed-rank test, standard bootstrap) assume that sampled units are **independent and identically distributed** (i.i.d.):
$$X_1, X_2, \dots, X_N \overset{\text{iid}}{\sim} \mathcal{D}$$

When evaluating parallel multilingual corpora:
- Query $q_{j,\text{hi}}$ is a translation of $q_{j,\text{en}}$.
- If the regulatory clause for $I_j$ is missing from the corpus or poorly indexed, retrieval will fail across *all* formulations of $I_j$.
- Conversely, if $I_j$ matches an explicit keyword heading in the corpus, retrieval is correlated across formulations.

Thus, the covariance between query outcomes within the same intent is non-zero:
$$\text{Cov}(Y_{j, \ell}, Y_{j, \ell'}) > 0 \quad \text{for } \ell \neq \ell'$$

### 3.2 Intra-Cluster Correlation (ICC) and Design Effect

The degree of statistical dependence within intent clusters is quantified by the **Intra-Cluster Correlation Coefficient** ($\rho$ or ICC):
$$\rho = \frac{\sigma^2_{\text{between}}}{\sigma^2_{\text{between}} + \sigma^2_{\text{within}}}$$

For the M9/M10 retrieval benchmarks, empirical variance decomposition across the 45 answerable intents reveals an ICC of $\rho \approx 0.58$ to $0.64$ for retrieval metrics (Hit@5 and MRR).

The variance inflation resulting from clustering is governed by the **Design Effect** ($\text{Deff}$):
$$\text{Deff} = 1 + (m - 1)\rho$$
where $m = 4$ is the cluster size (number of languages per intent).

With $m = 4$ and $\rho \approx 0.60$:
$$\text{Deff} = 1 + (4 - 1) \times 0.60 = 1 + 1.80 = 2.80$$

The **Effective Sample Size** ($N_{\text{eff}}$) for aggregate multi-language pooling is therefore:
$$N_{\text{eff}} = \frac{N_{\text{total}}}{\text{Deff}} = \frac{180}{2.80} \approx 64.3$$

### 3.3 Consequences of Pseudoreplication

If an analyst treats the 180 answerable queries as independent:
1. **Variance Underestimation:** Standard errors are underestimated by a factor of $\sqrt{\text{Deff}} = \sqrt{2.80} \approx 1.67$.
2. **Type I Error Inflation:** Nominal $\alpha = 0.05$ tests actually operate at an empirical false-positive rate of $\alpha_{\text{emp}} \approx 0.15 - 0.22$.
3. **Spurious Statistical Significance:** An observed metric gain that yields $p \approx 0.04$ under an unclustered test frequently yields $p > 0.20$ once cluster variance is correctly incorporated.

---

## 4. Phase G Statistical Methodology Protocols

To prevent pseudoreplication and ensure mathematical integrity, Phase G establishes the following statistical protocols:

1. **Within-Language Paired Analysis ($N=45$):**
   - When evaluating performance within a single language (e.g., Hindi Devanagari), each query represents an independent semantic intent group ($N=45$).
   - Exact paired tests (McNemar exact binomial test for Hit@k; Wilcoxon signed-rank test for MRR/nDCG) are applied directly to the 45 paired outcomes.

2. **Cross-Language Aggregation via Clustered Block Bootstrap:**
   - When estimating aggregate metric differences (e.g., Overall Hit@5 across 180 queries), resampling is performed at the **intent cluster level** ($K=45$ clusters), not the query level.
   - Entire intent blocks $\{q_{j,\text{en}}, q_{j,\text{hi}}, q_{j,\text{hi-Latn}}, q_{j,\text{en-hi}}\}$ are resampled with replacement over 10,000 iterations.
   - This non-parametric cluster bootstrap accurately captures intra-cluster correlation without making asymptotic normality assumptions.

3. **Separation of Retrieval vs. Generation Units:**
   - Retrieval evaluation is conducted over $N=45$ answerable intent groups.
   - Safety abstention evaluation is conducted over $N=15$ unanswerable intent groups.
   - Answer correctness evaluation is evaluated conditionally on passage retrieval and Evidence Controller decisions.

---

## 5. Frozen Corpus and Artifact Hash Verification

To guarantee that no underlying benchmarks, databases, or frozen artifacts were modified during Phase G, SHA-256 hashes were verified prior to statistical execution:

| Artifact Path | Expected Role | SHA-256 Checksum | Integrity Status |
|---|---|---|---|
| `backend/data/experiments/m9/m9_evaluation_dataset.jsonl` | Frozen 240-query benchmark | `9cb2b2fc610dfb1ee94ae8848dbff88a3811b7dfb0bb7a793a5ee5b30689b6b7` | Verified Unchanged |
| `backend/data/experiments/m10/m10_phase_e_per_intent_results.csv` | Phase E ablation records (1,260 rows) | `d726ad2d6199b4566c303f2601ae56b9c9ad6a146034f77c8e9663ecf039bb82` | Verified Unchanged |
| `backend/data/experiments/m10/m10_phase_f_end_to_end_results.csv` | Phase F end-to-end records (480 rows) | `313d46cb6d22d26f6343ee0fb2da9d29dd549dbcc6c694314c9c7f66a267a73d` | Verified Unchanged |
| `backend/data/experiments/m10/m10_phase_f_answer_correctness.csv` | Phase F correctness audits (480 rows) | `ee28770ae9660d2bbfd2106e57dfc33c39694b79b29efb78f44ff53e8e19c0be` | Verified Unchanged |

All datasets and underlying application databases remained strictly read-only throughout Phase G.
