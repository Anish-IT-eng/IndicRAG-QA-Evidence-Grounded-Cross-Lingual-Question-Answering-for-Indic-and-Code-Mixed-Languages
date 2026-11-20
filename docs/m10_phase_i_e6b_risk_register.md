# M10 Phase I — E6b Adaptive Bi-Encoder Risk Register

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** I — Production Promotion Readiness & Final Deployment Decision  
**Date:** November 18, 2026  
**Document Type:** Formal Risk Register & Production Readiness Assessment  
**Production Runtime Default:** Invariant as `"production"` in [backend/app/retrieval/engine.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L395)  
**Evidence Inventory Source:** [m10_phase_i_evidence_inventory.json](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_i_evidence_inventory.json)

---

## 1. Risk Register Methodology & Governance

This document presents a structured risk analysis of the experimental **E6b Adaptive Bi-Encoder Routing** strategy (`adaptive_e6b`) relative to the current production baseline **Config A (`E1_PROD_MSMARCO_D10`)**. 

Each risk is evaluated across five standardized dimensions:
1. **Risk Identification & Scope**: Clear description of the failure mode.
2. **Empirical Evidence Base**: Quantitative data observed during Milestones M9, Phase E, Phase F, Phase G, and Phase H audits.
3. **Severity & Likelihood / Uncertainty**: Standard impact matrix classification (Severity: Critical, High, Medium, Low; Likelihood: High, Medium, Low).
4. **Mitigation Strategy & Requirements**: Actionable technical remediation.
5. **Production Promotion Blocker Status**: Explicit binary classification (**BLOCKS PROMOTION** vs. **DOES NOT BLOCK**).

---

## 2. Risk Register Summary Matrix

| ID | Risk Category | Severity | Likelihood | Production Blocker? | Primary Mitigation |
|---|---|---|---|:---:|---|
| **RSK-01** | Devanagari Retrieval Reliability | High | High | **YES** | Hybrid dense-sparse retrieval & transliteration expansion (M11) |
| **RSK-02** | Latin-Script Regression Risk | Critical | Low | **NO** | Deterministic Unicode regex routing preserves production rankings |
| **RSK-03** | Downstream Controller False Abstention | High | High | **YES** | Script-calibrated CECI thresholds in Evidence Controller (M11) |
| **RSK-04** | Unsupported Answers / Hallucinations | Critical | Low | **NO** | Strict downstream controller verification yields 100% claim precision |
| **RSK-05** | Regulatory Applicability Mistakes | High | Low | **NO** | Deterministic version conflict detection & 96.67% unanswerable safety |
| **RSK-06** | Citation Failures & Broken Grounding | Medium | Low | **NO** | Enforced passage anchor schemas achieve 100% citation precision |
| **RSK-07** | CPU Latency & Generation Overhead | Medium | High | **CONDITIONAL** | Retrieval speedup is 90.8%; LLM generation requires GPU/vLLM for prod |
| **RSK-08** | Host Resource & Memory Overhead | Low | Low | **NO** | Dense score reuse adds zero memory footprint or model parameters |
| **RSK-09** | Benchmark Power & Representativeness | High | High | **YES** | M11 confirmatory benchmark expansion to $N=230$ intent groups |
| **RSK-10** | Operational Fallback & Observability | Medium | Medium | **YES** | Expose config setting in `config.py`, FastAPI schema, and telemetry |

---

## 3. Detailed Risk Evaluations

### Risk RSK-01: Devanagari Retrieval Reliability
- **Risk Scope:** Low absolute retrieval recall on complex, multi-sentence, or vocabulary-sparse Hindi Devanagari queries.
- **Empirical Evidence:** In the M9 answerable benchmark ($N=45$), Config A retrieved relevant passages for only $2/45$ queries (Hit@5 = $4.44\%$, MRR = $0.0278$). Config B doubled Hit@5 to $4/45$ ($8.89\%$, $+100\%$) and increased MRR to $0.0889$ ($+220\%$). However, under paired binomial testing ($b=3, c=1$), this improvement is not statistically significant ($p = 0.6250 > 0.05$). Furthermore, $41/45$ ($91.11\%$) answerable Devanagari queries still experienced complete retrieval failure. While relative gains are substantial, absolute recall remains low ($8.89\%$). The aspirational goal of achieving $\ge 50\%$ Hit@5 represents a **provisional M11 engineering target** rather than an established production acceptance criterion.
- **Severity:** High.
- **Likelihood / Uncertainty:** High for academic policy queries with technical Sanskritized or Persianized vocabulary.
- **Mitigation:** Combine BGE-M3 dense embeddings with BM25 transliteration indexing, cross-lingual query expansion (CLQE), or fine-tuned multilingual cross-encoders in Milestone M11.
- **Production Promotion Blocker:** **YES**. Deploying a retrieval strategy with an absolute Devanagari recall under $10\%$ as the primary production engine poses an unacceptable quality risk for end users.

---

### Risk RSK-02: Latin-Script Regression Risk
- **Risk Scope:** Potential degradation of English, Romanized Hindi, or Hinglish retrieval quality when modifying reranking architecture.
- **Empirical Evidence:** In M10 Phase E and Phase G controlled audits across 135 Latin-script answerable queries (45 English, 45 Romanized Hindi, 45 Hinglish), Config B yielded **zero discordant pairs** ($b = 0, c = 0$ observed regressions in the sample). Hit@1, Hit@3, Hit@5, MRR, and nDCG@5 were bit-for-bit identical to production (`E1_PROD_MSMARCO_D10`). Note that while zero regressions were observed in this evaluation sample, this does not constitute a formal statistical demonstration of non-inferiority, which would require an a priori non-inferiority margin and a dedicated statistical power design.
- **Severity:** Critical (if regressions existed).
- **Likelihood / Uncertainty:** Extremely Low. The adaptive routing relies on a deterministic Unicode regex (`[\u0900-\u097F]`), guaranteeing that non-Devanagari queries never touch the bi-encoder fallback.
- **Mitigation:** Maintain deterministic regex-based routing with automated unit tests asserting bit-for-bit equivalence on Latin query regression suites.
- **Production Promotion Blocker:** **NO**.

---

### Risk RSK-03: Downstream Controller False Abstention
- **Risk Scope:** Relevant passages retrieved by E6b are falsely rejected by the Evidence Controller due to threshold mismatch.
- **Empirical Evidence:** Config B successfully retrieved relevant passages for 4 Devanagari queries (`M9-Q002`, `M9-Q010`, `M9-Q014`, `M9-Q030`). However, the Evidence Controller (`EvidenceController.evaluate`) rejected 3 of them (`M9-Q010`, `M9-Q014`, and `M9-Q030`), returning `unanswerable` with `ctrl=insufficient` because the cross-encoder context-evidence compatibility index (CECI) falls below calibrated thresholds (ceci scores: $0.4699, 0.4654, 0.4595$). Meanwhile, `M9-Q002` reached success as a structured regulatory disclosure (`ctrl=clarification_required`, ceci=$0.80$), and `M9-Q058` achieved an answered outcome (`ctrl=partial`, ceci=$0.4298$) via expanded context. (Note: `M9-Q018` was a Config A-only retrieval hit that also resulted in an unnecessary abstention). Consequently, out of 4 retrieved queries, only 2 achieved end-to-end regulatory success ($4.44\%$, $2/45$).
- **Severity:** High.
- **Likelihood / Uncertainty:** High without language-specific threshold calibration.
- **Mitigation:** Implement script-specific or normalized CECI confidence thresholds in `EvidenceController` during Milestone M11.
- **Production Promotion Blocker:** **YES**. Retrieval improvements cannot deliver end-user value if downstream controllers systematically suppress them.

---

### Risk RSK-04: Unsupported Answers / Hallucinations
- **Risk Scope:** Generating ungrounded or hallucinated claims when answering Devanagari or code-mixed queries.
- **Empirical Evidence:** In M10 Phase H audits, factual grounding was evaluated across all generated responses containing substantive claims (37 queries in Config A, 39 queries in Config B). Audited claim support precision was **$100\%$** for both Config A ($82/82$ supported claims) and Config B ($85/85$ supported claims). Config B added 3 claims (2 from `M9-Q002` regarding attendance regulations, 1 from `M9-Q058` regarding CGPA calculation), all of which were verified to be directly supported by retrieved passage text. Zero unsupported or hallucinated claims were observed in the audited responses (Rule of Three 95% CI upper bound: $3.53\%$). Note that this empirical finding applies to the audited set of generated answers, and must not be conflated with a claim of zero hallucinations across all 240 benchmark queries (since abstentions and errors do not assert factual claims).
- **Severity:** Critical (if hallucinations were present).
- **Likelihood / Uncertainty:** Low. The system enforces strict citation grounding and deterministic fallbacks.
- **Mitigation:** Maintain mandatory passage-to-claim alignment validation and strict JSON extraction schema.
- **Production Promotion Blocker:** **NO**.

---

### Risk RSK-05: Regulatory Applicability Mistakes
- **Risk Scope:** Answering out-of-scope, cross-year, or cross-program regulatory queries erroneously.
- **Empirical Evidence:** Across 60 unanswerable queries in the M9 benchmark, Config B correctly abstained on $58/60$ ($96.67\%$), exactly matching Config A. In the 2 queries where direct answers were returned (`M9-Q084`, `M9-Q114`), both Config A and Config B produced identical responses due to known benchmark gold-label ambiguities. Furthermore, for query `M9-Q002` (involving contradictory academic year regulations), Config B correctly detected the conflict and issued a structured `CLARIFICATION_REQUIRED` disclosure rather than a false definitive answer.
- **Severity:** High.
- **Likelihood / Uncertainty:** Low.
- **Mitigation:** Retain multi-version consistency validation (`validate_versions`) and regulatory disclosure templates.
- **Production Promotion Blocker:** **NO**.

---

### Risk RSK-06: Citation Failures & Broken Grounding
- **Risk Scope:** Emitting hallucinated, corrupted, or non-existent document IDs and section anchors in generated answers.
- **Empirical Evidence:** Audited citation precision was **$100\%$** (Config A: 59/59; Config B: 61/61). Every citation anchor strictly resolved to a valid document in the corpus (e.g., `acad_eval_2024#grading_scale` for `M9-Q058`). Zero broken links or hallucinated document IDs were recorded.
- **Severity:** Medium.
- **Likelihood / Uncertainty:** Low.
- **Mitigation:** Continue enforcing Pydantic citation schema validation before rendering responses.
- **Production Promotion Blocker:** **NO**.

---

### Risk RSK-07: CPU Latency & Generation Overhead
- **Risk Scope:** System latency exceeding acceptable service level agreements (SLAs).
- **Empirical Evidence:** For retrieval, E6b provides a massive latency benefit for Devanagari queries, reducing mean retrieval time from **1,097.10 ms to 62.88 ms (-94.3%)**. However, total end-to-end latency on CPU environments is heavily dominated by local LLM generation (`qwen2.5:7b-instruct-q4_K_M` via Ollama), averaging **88,529.28 ms (~88.5 seconds)** per invocation, with P95 exceeding 120 seconds.
- **Severity:** Medium.
- **Likelihood / Uncertainty:** High in local CPU test environments; manageable with GPU inference.
- **Mitigation:** Retrieval optimization is complete. End-to-end production deployment requires Ollama GPU acceleration or a remote vLLM endpoint with speculative decoding.
- **Production Promotion Blocker:** **CONDITIONAL**. Retrieval itself is production-ready from a latency standpoint; full pipeline promotion requires dedicated LLM hosting infrastructure.

---

### Risk RSK-08: Host Resource & Memory Overhead
- **Risk Scope:** Out-of-memory (OOM) errors, CPU thrashing, or dependency conflicts from loading extra models.
- **Empirical Evidence:** E6b uses **score reuse**, directly reading dense similarity scores generated during the initial `BAAI/bge-m3` FAISS retrieval pass.
  - *Model-Loading Overhead:* Loads zero additional neural network weights or parameters into RAM/VRAM beyond the pre-existing bi-encoder and cross-encoder models already initialized by production.
  - *Temporary Score Storage:* Allocates minimal transient memory for intermediate Python dictionaries and float score sorting during candidate routing.
  - *Total Process Memory:* Peak process RSS during evaluation remained invariant at $\approx 1,180\text{ MB}$ (base) and $\approx 2,192\text{ MB}$ (with PyTorch tensor operations), virtually identical to Config A.
- **Severity:** Low.
- **Likelihood / Uncertainty:** Extremely Low.
- **Mitigation:** Retain in-memory dense score caching.
- **Production Promotion Blocker:** **NO**.

---

### Risk RSK-09: Benchmark Power & Representativeness
- **Risk Scope:** Making premature production deployment decisions based on statistically underpowered pilot data.
- **Empirical Evidence:** The current benchmark contains $N=60$ intent groups ($N=45$ answerable), yielding only 45 Devanagari queries. Exact paired binomial testing on the 4 discordant pairs ($b=3, c=1$) yields **$p = 0.6250$ (power = $65.37\%$)**. Cluster-aware permutation tests similarly yield $p = 0.6250$. Statistical modeling proves that achieving $\ge 80\%$ unconditional power requires a benchmark of **$N = 225 - 230$ independent intent groups (900-920 query records)**.
- **Severity:** High.
- **Likelihood / Uncertainty:** High. Promoting E6b now risks committing to an architecture whose observed benefits could be partially attributable to sample variance.
- **Mitigation:** Execute Milestone M11 benchmark expansion to $N=230$ intents before production promotion.
- **Production Promotion Blocker:** **YES (PRIMARY STATISTICAL BLOCKER)**.

---

### Risk RSK-10: Operational Fallback & Observability
- **Risk Scope:** Inability to dynamically toggle, monitor, or safely rollback E6b in a production environment.
- **Empirical Evidence:** In the current codebase, `rerank_strategy` is hardcoded as an internal parameter in [backend/app/retrieval/engine.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L395). It is not defined in `backend/app/core/config.py`, not exposed in the FastAPI `QueryRequest` model, not available in the frontend UI, and emits no Prometheus/structured metrics indicating which reranking strategy executed.
- **Severity:** Medium.
- **Likelihood / Uncertainty:** Medium.
- **Mitigation:** Refactor configuration to expose `RETRIEVAL_RERANK_STRATEGY` in application settings, allow per-request overrides for canary testing, and add telemetry logging tags (`rerank_strategy_used`, `rerank_latency_ms`).
- **Production Promotion Blocker:** **YES (OPERATIONAL INTEGRATION BLOCKER)**.

---

## 4. Synthesis & Risk-Based Gate Decision

| Assessment Criteria | Evaluation Result | Status |
|---|---|:---:|
| **Devanagari Recall Threshold** | Absolute Hit@5 is 8.89% (Provisional M11 Target $\ge 50\%$) | **FAILED** |
| **Downstream Controller Pass-Through** | 3/4 Devanagari hits rejected by controller (`Q010`, `Q014`, `Q030`) | **FAILED** |
| **Statistical Significance** | Paired binomial $p = 0.6250$, power = 65.37% (Target power $\ge 80\%$) | **FAILED** |
| **Operational Telemetry & Config** | Absent from `config.py` and API schemas | **FAILED** |
| **Safety & Grounding Integrity** | 100% claim precision (85/85), 96.67% unanswerable safety | **PASSED** |
| **Latin Script Non-Regression** | 0 sample regressions across 135 Latin queries (non-inferiority unproven) | **PASSED** |
| **Retrieval Efficiency** | Devanagari latency reduced by 94.3% (62.88 ms) | **PASSED** |

### Final Risk Gate Verdict:
Due to active blocking risks **RSK-01** (Devanagari Recall), **RSK-03** (Controller False Abstention), **RSK-09** (Underpowered Sample Size), and **RSK-10** (Operational Integration), the E6b configuration cannot be promoted to production at this time.

The recommended disposition is **`RETAIN_AS_EXPERIMENTAL`**, pending Milestone M11 confirmatory evaluations and controller threshold calibration.
