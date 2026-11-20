# M10 Phase I — Production Promotion Decision

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** I — Production Promotion Readiness & Final Deployment Decision  
**Date:** November 18, 2026  
**Document Type:** Formal Executive Production Decision Memo  
**Current Operational Status:** Audit & Decision Phase (Complete)  
**Production Runtime Invariant:** Invariant default `rerank_strategy = "production"` in [backend/app/retrieval/engine.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L395)  

---

## 1. Formal Decision Determination

### **DECISION: RETAIN_AS_EXPERIMENTAL**

The experimental **E6b Adaptive Bi-Encoder Routing** strategy (`adaptive_e6b`) is **RETAINED AS AN EXPERIMENTAL ALTERNATIVE** in the IndicRAG-QA codebase. 

**Production promotion is DEFERRED pending confirmatory evaluation in Milestone M11.**

The active production default in [backend/app/retrieval/engine.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L395) remains unchanged:
```python
# Line 395 of backend/app/retrieval/engine.py
rerank_strategy: str = "production",
```

---

## 2. Decision Rationale & Executive Summary

The mandate of Milestone M10 was to investigate the catastrophic retrieval drop observed on Hindi Devanagari queries under MS-MARCO cross-encoder reranking, evaluate recovery strategies, and assess whether the candidate strategy (`adaptive_e6b`) is ready for production deployment.

Over Phases E through H, E6b was subjected to rigorous empirical evaluation across retrieval effectiveness, statistical significance, end-to-end generation quality, citation faithfulness, and computational efficiency.

The empirical evaluation reveals that while E6b succeeds as a **highly effective algorithmic recovery technique**, it fails to satisfy **production readiness standards** across four mandatory dimensions:
1. **Statistical Power Gap:** The pilot benchmark ($N=45$ answerable intent groups) is severely underpowered (power = $65.37\%$, paired binomial $p = 0.6250$). Observed gains are exploratory and cannot serve as the statistical foundation for production promotion.
2. **Low Absolute Devanagari Recall:** While E6b doubles Devanagari Hit@5 from $4.44\%$ to $8.89\%$, $91.11\%$ ($41/45$) of answerable Devanagari queries still experience complete retrieval failure due to dense bi-encoder vocabulary limitations.
3. **Downstream Controller Rejection:** Out of 4 Devanagari retrieval hits delivered by E6b, 3 were rejected by the uncalibrated Evidence Controller due to cross-script CECI score compression, resulting in an end-to-end success rate of only $4.44\%$ ($2/45$).
4. **Operational Integration Deficit:** E6b exists only as an internal routing branch in `engine.py`. It is absent from `backend/app/core/config.py`, cannot be configured via environment variables, lacks API request overrides, and has no production telemetry.

Retaining E6b as an experimental alternative preserves its algorithmic breakthroughs for ongoing research while safeguarding the stability, predictability, and governance standards of the production system.

---

## 3. Strongest Supporting Evidence (Why E6b is Retained)

The M10 audit established conclusive empirical evidence supporting E6b's technical validity:

1. **Elimination of the Devanagari Reranking Penalty:**
   - Devanagari Hit@5 doubled from $2/45$ ($4.44\%$) to $4/45$ ($8.89\%$, $+100\%$).
   - Devanagari MRR increased from $0.0278$ to $0.0889$ ($+220\%$).
   - Devanagari nDCG@5 increased from $0.0195$ to $0.0717$ ($+268\%$).
2. **Zero Observed Latin-Script Regressions:**
   - Across all 135 Latin-script answerable queries (English, Romanized Hindi, Hinglish), E6b demonstrated **zero discordant pairs** ($b = 0, c = 0$ in the evaluation sample). Hit rates, MRR, nDCG@5, and ranking order were bit-for-bit identical to production. (Note: While no sample regressions were observed, formal statistical non-inferiority was not established).
3. **Dramatic Devanagari Retrieval Speedup:**
   - By eliminating the cross-encoder inference pass on Devanagari queries and reusing BGE-M3 dense similarity scores, Devanagari retrieval latency dropped from **1,097.10 ms to 62.88 ms (-94.3%)**, saving over 1 second per query.
4. **Flawless Claim & Citation Precision:**
   - Evaluated across generated responses containing substantive claims, Config B achieved **$100\%$ claim support precision** ($85/85$ claims supported across 39 generated responses) and **$100\%$ citation precision** ($57/57$ valid citations mapped to authoritative corpus anchors; Config A achieved $82/82$ supported claims across 37 generated responses).
   - Config B successfully unlocked the first fully grounded Devanagari answer in system history (`M9-Q058`), citing `acad_eval_2024#grading_scale` with 100% claim support.
5. **Robust Regulatory Safety & Version Conflict Detection:**
   - Config B maintained identical safety on unanswerable queries ($58/60$ correct abstentions, $96.67\%$).
   - For ambiguous multi-version query `M9-Q002`, E6b retrieved the conflicting academic year regulations, enabling the pipeline to issue a deterministic `CLARIFICATION_REQUIRED` disclosure rather than a hallucinated policy.
6. **Zero Model-Loading Overhead & Invariant Process Memory:**
   - Dense score reuse loads zero additional neural network models or parameters into RAM/VRAM beyond pre-existing models, maintaining total process memory invariant at $\approx 1,180\text{ MB}$ base RSS.

---

## 4. Strongest Counter-Evidence & Blocking Conditions (Why Promotion is Rejected)

The following four deficiencies formally block production promotion:

1. **Failure of Statistical Significance & Confirmatory Power:**
   - The observed Devanagari retrieval delta consists of only 4 discordant pairs ($b=3, c=1$), resulting in an exact two-sided binomial p-value of **$p = 0.6250$** (not statistically significant).
   - The post-hoc statistical power of the $N=45$ benchmark is only **$65.37\%$**. 
   - A production promotion cannot be authorized on pilot findings that do not reach statistical significance ($p < 0.05$) with certified $\ge 80\%$ power.
2. **Insufficient Absolute Retrieval Recall:**
   - Although relative retrieval gains are high ($+100\%$), the absolute Devanagari Hit@5 is only **$8.89\%$ ($4/45$)**.
   - Over $90\%$ of Devanagari queries fail retrieval because dense bi-encoders struggle with domain-specific Indic academic terminology without transliteration or hybrid BM25 expansion.
3. **Downstream Pipeline Bottleneck (Evidence Controller Rejection):**
   - End-to-end evaluation demonstrated that retrieval recovery does not equate to user-facing recovery.
   - The Evidence Controller rejected $75\%$ ($3/4$) of E6b's retrieved Devanagari passages (`M9-Q010`, `M9-Q014`, `M9-Q030`) due to cross-script CECI score compression, resulting in unnecessary abstentions. Along with `M9-Q002` (disclosure) and `M9-Q058` (direct answer via expanded context), this yielded an end-to-end Devanagari success rate of only **$4.44\%$ ($2/45$)**. (Note: `M9-Q018` was a Config A-only retrieval hit).
4. **Lack of Production Architecture & Observability:**
   - E6b is hardcoded inside an internal routing conditional in `engine.py`.
   - It cannot be toggled via environment variables, has no fallback hooks, is missing from the FastAPI application schema, and emits no operational Prometheus/logging metrics.

---

## 5. Explicit Conditions Required for Milestone M11 Promotion Review

Before E6b (or its successor) can be reconsidered for production promotion in Milestone M11, the following five criteria must be satisfied:

```
[M11-CRIT-1] Confirmatory Sample Size:
             Benchmark expanded to N = 225 - 230 independent semantic intent groups
             (900 - 920 total queries across 4 languages) to achieve >= 80% unconditional
             two-sided power under realistic discordance assumptions (p_d = 0.15, p_1 = 0.75).

[M11-CRIT-2] Evidence Controller Calibration:
             Implement script-calibrated or normalized CECI relevance thresholds in the
             Evidence Controller so retrieved Devanagari passages are not falsely rejected.

[M11-CRIT-3] Absolute Devanagari Recall Enhancement:
             Incorporate hybrid dense-sparse indexing, transliteration query expansion, or
             multilingual cross-encoders to achieve a provisional M11 engineering target of
             Devanagari Hit@5 >= 50.0% (not a validated production acceptance criterion).

[M11-CRIT-4] Production Operationalization & Telemetry:
             Expose RETRIEVAL_RERANK_STRATEGY in backend/app/core/config.py, support per-request
             overrides in FastAPI schemas, and emit structured metrics for routing decisions.

[M11-CRIT-5] Rigorous Non-Regression Guarantee:
             Demonstrate zero statistically significant degradation on English, Romanized Hindi,
             and Hinglish retrieval benchmarks under paired testing.
```

---

## 6. Milestone M10 Formal Closure & Final Determination

Milestone M10 is officially closed with the following final audit determination:

### **Milestone Status: M10_PHASE_I_VERIFIED_RETAIN_AS_EXPERIMENTAL**

- **Production Codebase Status:** Intact, unchanged, and verified.
- **Production Default:** [backend/app/retrieval/engine.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L395) confirmed as `rerank_strategy: str = "production"`.
- **Regression Suite:** 260/260 tests passing with zero failures.
- **Evidence Integrity:** All 17 core M10 artifacts cataloged and SHA-256 hashed in [m10_phase_i_evidence_inventory.json](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_i_evidence_inventory.json).
- **Next Step:** Milestone M11 planning and confirmatory benchmark expansion will be initiated upon user instruction.
