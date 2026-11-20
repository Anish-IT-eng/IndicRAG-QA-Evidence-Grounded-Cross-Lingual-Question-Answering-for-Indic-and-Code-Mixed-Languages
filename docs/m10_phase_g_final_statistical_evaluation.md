# M10 Phase G: Final Statistical Evaluation & Research Significance Audit

**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** G — Comprehensive Statistical Evaluation & Research Significance Audit  
**Document ID:** `DOC-M10-PHASE-G-FINAL-REPORT`  
**Repository:** [IndicRAG-QA](file:///C:/Users/anish/Desktop/IndicRAG-QA)  
**Date:** 2026-11-17  
**Status:** Audit Completed  
**Final Determination:** `M10_PHASE_G_VERIFIED_WITH_LIMITATIONS`  

---

## 1. Executive Summary & Audit Determination

Milestone M10 Phase G conducted an independent, mathematically rigorous statistical evaluation of the experimental findings reported across M10 Phase E (retrieval ablation) and Phase F (end-to-end answer evaluation). The primary focus was candidate `E6b_ADAPTIVE_BI_ENCODER` versus the production baseline `ConfigA_Production` (`E1_PROD_MSMARCO_D10`).

### Final Determination: `M10_PHASE_G_VERIFIED_WITH_LIMITATIONS`

This determination reflects four verified realities:
1. **Verified Empirical Recovery:** Candidate E6b demonstrably improves Devanagari Hindi retrieval (Hit@5: $0.0444 \to 0.0889$, +100%; MRR: $0.0278 \to 0.0889$, +220%; Latency: $1,097\text{ ms} \to 850\text{ ms}$, -22.5%) and enables end-to-end answer generation ($0/45 \to 2/45$).
2. **Verified Non-Significance Under Rigorous Testing:** The observed improvement yields an exact two-sided McNemar $p = 0.6250$ (on $b=1, c=3$ discordant pairs). Because $N=45$ is severely underpowered for sparse discordant pairs, the gain cannot be confirmed as statistically significant ($\alpha = 0.05$).
3. **Verified Invariance & Safety:** Candidate E6b causes strictly zero regression on English, Romanized Hindi, and Hinglish queries ($p = 1.0000$). Abstention fidelity on unanswerable queries is perfectly preserved (96.7%), and the Unsupported Answer Rate remains 0.0% (95% upper bound $\le 4.91\%$).
4. **Deferred Production Integration:** In strict adherence to experimental integrity rules, Candidate E6b remains an experimental configuration. Production default behavior is preserved, and production promotion is deferred to Phase I.

---

## 2. Answers to Core Research Questions

### Question 1: What is the true independent statistical unit in cross-lingual retrieval evaluation?
**Finding:** The **Semantic Intent Group** ($N=60$ total: 45 answerable, 15 unanswerable) is the sole independent statistical unit. The four language formulations (`en`, `hi`, `hi-Latn`, `en-hi`) are clustered repeated measures sharing underlying passage relevance and regulatory complexity. Treating the 180 answerable queries as independent induces severe pseudoreplication ($\text{Deff} \approx 2.80$), underestimating variance by $1.67\times$ and producing false significance. Detailed in [m10_phase_g_dataset_statistical_unit_audit.md](file:///C:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_g_dataset_statistical_unit_audit.md).

### Question 2: Did Candidate E6b achieve statistically significant retrieval improvement in Devanagari Hindi?
**Finding:** **No.** While the empirical effect size is substantial ($\text{OR} = 3.00$, Cohen's $g = 0.250$, $+100\%$ relative gain in Hit@5), the exact paired McNemar binomial test yields $p = 0.6250$, and the Wilcoxon signed-rank test for MRR yields $p = 0.2579$. The 95% bootstrap confidence interval for Hit@5 difference spans zero: $[-0.0444, +0.1333]$. The improvement is an **exploratory pilot finding**, not a confirmatory result. Detailed in [m10_phase_g_retrieval_statistical_analysis.md](file:///C:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_g_retrieval_statistical_analysis.md).

### Question 3: What is the mathematical origin of the reported $p = 0.0455$, and is it valid?
**Finding:** The $p = 0.0455$ reported in earlier Phase E documentation was derived from an **uncorrected asymptotic Chi-Square formula** assuming a synthetic $0:4$ cell split ($\chi^2 = 4^2/4 = 4.0$). It is **invalid** on two grounds:
1. On sparse cell counts ($n_D = 4$), asymptotic continuous Chi-Square distributions fail; the exact discrete binomial distribution yields $p = 0.1250$ for a $0:4$ split.
2. The actual empirical data contained a regression (`M9-Q018`, where Config A succeeded and Config B failed), resulting in an empirical cell split of $b=1, c=3$, for which the exact two-sided $p$-value is **0.6250**.

### Question 4: Did Candidate E6b preserve performance across English, Romanized Hindi, and Hinglish?
**Finding:** **Yes, strictly.** Across all 135 answerable queries in Latin scripts, there were zero discordant pairs ($b=0, c=0$). Hit@1, Hit@5, MRR, and nDCG@5 were mathematically identical ($p = 1.0000$), confirming that adaptive routing does not disrupt non-Devanagari execution paths.

### Question 5: Did the retrieval gains translate into end-to-end answer correctness?
**Finding:** **Partially.** Candidate E6b recovered 2 verified end-to-end answers in Devanagari Hindi (`M9-Q014` and `M9-Q030`), increasing Devanagari answerable success from $0/45$ (0.0%) to $2/45$ (4.4%). However, for two other intents where passages were retrieved in Top-5 (`M9-Q002` and `M9-Q010`), the downstream Evidence Controller rejected the evidence due to conservative cross-lingual entailment scoring, resulting in abstention.

### Question 6: Did Candidate E6b compromise safe abstention on unanswerable queries?
**Finding:** **No.** On the 60 unanswerable queries (15 per language), both configurations achieved identical $58/60$ (96.7%) correct abstentions ($p = 1.0000$). No false-positive answers or hallucinations were generated on unanswerable queries. Detailed in [m10_phase_g_end_to_end_statistical_analysis.md](file:///C:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_g_end_to_end_statistical_analysis.md).

### Question 7: What is the empirical and theoretical upper bound on hallucination/unsupported answers?
**Finding:** The observed Unsupported Answer Rate was **0.0%** ($0/61$). Applying the Rule of Three for zero observed events ($3/N$), the 95% upper confidence bound on the true population hallucination rate is **4.91%**.

### Question 8: Can any performance claims survive family-wise multiplicity adjustment?
**Finding:** **No.** Across the family of 25 evaluated hypotheses, zero tests met raw significance ($\alpha = 0.05$). Under both Holm-Bonferroni FWER control and Benjamini-Hochberg FDR control, all adjusted p-values equal $1.0000$. All findings remain exploratory. Detailed in [m10_phase_g_multiple_comparison_analysis.md](file:///C:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_g_multiple_comparison_analysis.md).

### Question 9: Is Candidate E6b recommended for immediate production deployment?
**Finding:** **No.** While Candidate E6b is an exceptionally promising candidate with strong empirical gains (+100% Hit@5, -22.5% latency) and zero observed safety regressions, production deployment requires confirmatory verification on a properly powered sample ($N \ge 150$ intents). Candidate E6b remains available via parameter dispatch (`rerank_strategy="adaptive_e6b"`), but runtime defaults remain `"production"`. Final production approval is deferred to Phase I.

---

## 3. Comprehensive Summary of Experimental Deliverables

| Deliverable # | Relative Path | Purpose | Status |
|---|---|---|:---:|
| 1 | [docs/m10_phase_g_dataset_statistical_unit_audit.md](file:///C:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_g_dataset_statistical_unit_audit.md) | Statistical unit audit and design effect derivation | Complete |
| 2 | [docs/m10_phase_g_retrieval_statistical_analysis.md](file:///C:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_g_retrieval_statistical_analysis.md) | Paired retrieval analysis across languages | Complete |
| 3 | [docs/m10_phase_g_end_to_end_statistical_analysis.md](file:///C:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_g_end_to_end_statistical_analysis.md) | End-to-end answer quality and abstention safety | Complete |
| 4 | [docs/m10_phase_g_confidence_intervals_and_effect_sizes.md](file:///C:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_g_confidence_intervals_and_effect_sizes.md) | Wilson intervals, Cohen's g, and bootstrap distributions | Complete |
| 5 | [docs/m10_phase_g_multiple_comparison_analysis.md](file:///C:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_g_multiple_comparison_analysis.md) | Multiplicity adjustments (Holm-Bonferroni & BH FDR) | Complete |
| 6 | [docs/m10_phase_g_power_and_sample_size_analysis.md](file:///C:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_g_power_and_sample_size_analysis.md) | Post-hoc power analysis and M11 sample planning | Complete |
| 7 | [docs/m10_phase_g_final_statistical_evaluation.md](file:///C:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_g_final_statistical_evaluation.md) | Milestone synthesis and final determination | Complete |
| 8 | [backend/data/experiments/m10/m10_phase_g_statistical_results.csv](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_g_statistical_results.csv) | Full statistical test results across 30 metric-language pairs | Complete |
| 9 | [backend/data/experiments/m10/m10_phase_g_paired_contingency_tables.csv](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_g_paired_contingency_tables.csv) | 2x2 contingency tables for McNemar tests | Complete |
| 10 | [backend/data/experiments/m10/m10_phase_g_confidence_intervals.csv](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_g_confidence_intervals.csv) | Wilson score and Rule-of-Three confidence intervals | Complete |
| 11 | [backend/data/experiments/m10/m10_phase_g_bootstrap_results.csv](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_g_bootstrap_results.csv) | Clustered block bootstrap resampling distributions | Complete |
| 12 | [backend/data/experiments/m10/m10_phase_g_multiple_testing_results.csv](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_g_multiple_testing_results.csv) | Family of 25 hypotheses with Holm & BH corrections | Complete |
| 13 | [backend/data/experiments/m10/m10_phase_g_integrity_manifest.json](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_g_integrity_manifest.json) | Cryptographic SHA-256 integrity manifest | Complete |
| 14 | [backend/experiments/m10/phase_g_statistical_analysis.py](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/experiments/m10/phase_g_statistical_analysis.py) | Fully reproducible Python analysis script | Complete |
| 15 | [backend/data/experiments/m10/m10_phase_g_execution.log](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_g_execution.log) | Script execution log and environment metadata | Complete |

---

## 4. Architectural Status & Sign-off

- **Baseline Code Base:** [backend/app/retrieval/engine.py](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py) preserves `"production"` as default.
- **Unit Test Coverage:** All 260 unit tests pass with zero regressions.
- **Data Integrity:** Frozen benchmark hashes verified unchanged.
- **Milestone Determination:** `M10_PHASE_G_VERIFIED_WITH_LIMITATIONS`.
