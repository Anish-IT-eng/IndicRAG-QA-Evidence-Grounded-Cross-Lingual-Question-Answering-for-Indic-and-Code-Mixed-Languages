# M10 Phase H — Documentation Correction Log

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** H — Cross-Lingual End-to-End Answer Quality, Citation & Grounding Audit  
**Date:** November 18, 2026  
**Document Type:** Formal Audit Correction Log  
**Current Determination:** `M10_PHASE_H_VERIFIED_WITH_LIMITATIONS`  

---

## 1. Summary of Identified Numerical Discrepancies & Resolutions

During the Phase H final consistency audit, five specific documentation discrepancies were identified between historical baseline reports, intermediate summaries, and the underlying repository records:

| # | Discrepancy Description | Erroneous / Ambiguous Notation | Audited Ground Truth | Resolution / Document Corrected |
|---|---|---|---|---|
| **1** | **Answerable Outcome Summation** | $59 + 119 = 178 \ne 180$ (Config A)<br>$61 + 117 = 178 \ne 180$ (Config B) | 2 answerable queries (`M9-Q123`, `M9-Q124`) failed due to pipeline generation errors (`'error'`), separate from clean abstentions (`'unanswerable'`). | Explicitly established 4-way mutually exclusive outcome partition: Success ($59 / 61$), Clean Abstention ($119 / 117$), Pipeline Error ($2 / 2$). Sum $= 180$. |
| **2** | **Phase G vs Phase H Retrieval Metrics** | Phase H text cited historical M9 snapshot: English Hit@5 $= 0.1333$, Hinglish Hit@5 $= 0.1333$, Config A Overall $= 0.1111$, Config B Overall $= 0.1222$. | Phase E rerun and Phase G records: English Hit@5 $= 0.1111$ ($5/45$), Hinglish Hit@5 $= 0.1111$ ($5/45$), Config A Overall $= 0.1000$ ($18/180$), Config B Overall $= 0.1111$ ($20/180$). | Reconciled historical M9 vs Phase E rerun discrepancy. Standardized all Phase H documents to Phase E/G audited ground truth ($0.1000$ and $0.1111$). |
| **3** | **Devanagari False Abstention Count** | Earlier text claimed $4 \text{ hits} - 2 \text{ successes} = 2 \text{ false abstentions}$. | Of the 4 benchmark PID hits (`Q002`, `Q010`, `Q014`, `Q030`), **3** falsely abstained (`Q010`, `Q014`, `Q030`). The 2nd success (`Q058`) retrieved an unannotated authentic clause (`f6d95cc5...`, Page 15). | Documented exact 5-class partition of the 45 Hindi answerable queries: 1 benchmark hit success, 3 benchmark hit false abstentions, 1 unannotated hit success, 40 retrieval misses. |
| **4** | **Latency Benchmark Labeling** | Warm/GPU profile timing (Retrieval $= 1,097.1\text{ ms}$, Total $= 1,842.3\text{ ms}$) was presented without distinguishing cold CPU end-to-end execution. | Raw execution records in `m10_phase_h_per_query_results.csv` record cold CPU execution: Config A mean retrieval $= 2,805.5\text{ ms}$, CPU generation $= 43,872.8\text{ ms}$, total $= 46,694.3\text{ ms}$. | Explicitly labeled both timing benchmarks: (A) Controlled Retrieval Latency (Phase E profiling), and (B) Cold CPU End-to-End Latency (Phase F/H execution records). |
| **5** | **Claim Audit Scope & Adjudication** | Prose suggested global 100% claim grounding across the entire corpus. | The audited claim population consists of 85 atomic claims across the 39 answering queries in Config B (and 82 in Config A). Abstaining queries produced no claims to audit. | Bound all grounding metrics strictly to the audited population: 85 claims across 39 answering queries ($100.0\%$ support precision). Stated absence of human review on abstained queries. |

---

## 2. Itemized Correction Entries

### Entry CORR-01: Outcome Partition Summation
- **Affected Files:** `docs/m10_phase_h_answer_quality_report.md`, `docs/m10_phase_h_final_reconciliation.md`.
- **Nature of Defect:** Arithmetic omission of the 2 pipeline execution errors from high-level summary tables.
- **Root Cause:** In M9, queries `M9-Q123` (`hi-Latn`) and `M9-Q124` (`en-hi`) on campus alcohol/drug regulations failed during local Ollama generation with a JSON parsing error, receiving status `error`. In downstream aggregation, they were classified as unsuccessful answerable queries, but separate from clean `unanswerable` abstentions.
- **Correction:** Both categories are now explicitly tabulated:
  - Config A: 52 Direct Answers + 7 Regulatory Disclosures + 119 Clean Abstentions + 2 Execution Errors $= 180$.
  - Config B: 53 Direct Answers + 8 Regulatory Disclosures + 117 Clean Abstentions + 2 Execution Errors $= 180$.

### Entry CORR-02: Retrieval Metric Standardization (Phase G Alignment)
- **Affected Files:** `docs/m10_phase_h_statistical_analysis.md`, `docs/m10_phase_h_answer_quality_report.md`.
- **Nature of Defect:** Reversion to historical M9 baseline retrieval numbers ($0.1333$ for English and Hinglish) instead of the Phase E / Phase G audited rerun numbers ($0.1111$).
- **Root Cause:** In the initial M9 run, English Hit@5 was 6/45 ($0.1333$, including `M9-Q029`) and Hinglish Hit@5 was 6/45 ($0.1333$, including `M9-Q028`). In the Phase E controlled depth-10 evaluation, `M9-Q028` and `M9-Q029` ranked at rank 6 (just below the top-5 cutoff), resulting in 5/45 ($0.1111$).
- **Correction:** All retrieval tables updated to reflect the audited Phase E/G/H records:
  - English Hit@5: $5/45 = 0.1111$
  - Hindi Config A Hit@5: $2/45 = 0.0444$; Config B Hit@5: $4/45 = 0.0889$
  - Romanized Hindi Hit@5: $6/45 = 0.1333$
  - Hinglish Hit@5: $5/45 = 0.1111$
  - Overall Config A Hit@5: $18/180 = 0.1000$
  - Overall Config B Hit@5: $20/180 = 0.1111$

### Entry CORR-03: Devanagari Hindi Trace Disaggregation
- **Affected Files:** `docs/m10_phase_h_failure_analysis.md`, `docs/m10_phase_h_final_reconciliation.md`.
- **Nature of Defect:** Claim that "2 false abstentions occurred out of 4 retrieval hits".
- **Root Cause:** Automated comparison between Hit@5 count (4) and answer count (2) assumed that both answered queries (`M9-Q002` and `M9-Q058`) were among the 4 Hit@5 queries. Detailed tracing revealed that `M9-Q058` retrieved an authentic unannotated clause (`f6d95cc5...`, Page 15) rather than the single annotated benchmark passage (`6fc987b9...`, Page 13), scoring automated Hit@5 $= 0$.
- **Correction:** Documented the exact distribution:
  - Benchmark Hit & Success: 1 query (`M9-Q002`)
  - Benchmark Hit & False Abstention: 3 queries (`M9-Q010`, `M9-Q014`, `M9-Q030`)
  - Unannotated Hit & Success: 1 query (`M9-Q058`)
  - Benchmark Miss & Abstention: 40 queries
  - Total: 45 queries.

### Entry CORR-04: Dual Latency Classification
- **Affected Files:** `docs/m10_phase_h_e2e_evaluation_protocol.md`, `docs/m10_phase_h_final_reconciliation.md`.
- **Nature of Defect:** Lack of distinction between controlled retrieval benchmarking and cold end-to-end CPU generation latency.
- **Correction:** Both measurements are now formally reported under distinct headings:
  - *Benchmark A (Controlled Retrieval Latency):* Config A Mean $= 1,097.1\text{ ms}$; Config B Mean $= 849.9\text{ ms}$ (Hindi $= 98.4\text{ ms}$).
  - *Benchmark B (Cold End-to-End Execution Latency):* Config A Mean $= 46,694.3\text{ ms}$ (Retrieval $= 2,805.5\text{ ms}$, CPU Generation $= 43,872.8\text{ ms}$); Config B Mean $= 46,270.9\text{ ms}$ (Retrieval $= 2,372.5\text{ ms}$, CPU Generation $= 43,897.2\text{ ms}$).

---

## 3. Preservation & Sign-off

No application code, retrieval engines, models, prompts, database entries, or raw experiment CSVs were altered. All corrections are documentation reconciliations that enhance transparency and reproducibility.
