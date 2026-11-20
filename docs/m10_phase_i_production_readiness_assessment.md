# M10 Phase I — Production Promotion Readiness Assessment

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** I — Production Promotion Readiness & Final Deployment Decision  
**Date:** November 18, 2026  
**Document Type:** Formal Production Readiness Assessment  
**Current Operational Status:** Evaluation & Decision Phase (Audit Only)  
**Production Runtime Default:** Invariant as `"production"` in [backend/app/retrieval/engine.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L395)  

---

## 1. Executive Summary & Assessment Mandate

This report delivers an independent, evidence-based production-readiness assessment of the experimental **E6b Adaptive Bi-Encoder Routing** strategy (`adaptive_e6b`), comparing it against the existing production baseline **Config A (`E1_PROD_MSMARCO_D10`)**.

The evaluation synthesizes empirical findings across Milestones M9 and M10 (Phases E through H), drawing from the verified evidence inventory registered in [m10_phase_i_evidence_inventory.json](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_i_evidence_inventory.json).

### Primary Readiness Verdict:
While E6b demonstrates undeniable technical promise—recovering Hindi Devanagari Hit@5 by $+100\%$, increasing MRR by $+220\%$, unlocking 2 verified regulatory answers, maintaining $100\%$ claim support precision, and reducing Devanagari retrieval latency by $90.8\%$ without Latin-script regressions—**E6b is NOT YET READY for unconditional production promotion**.

**Core Blockers:**
1. **Statistical Power Limitation:** The evaluation on $N=45$ answerable intent groups yields an exact paired two-sided binomial p-value of $p = 0.6250$ (power $= 65.37\%$). The observed improvements are exploratory pilot findings, not confirmatory evidence.
2. **Downstream Threshold Conservatism:** Of the 4 Devanagari retrieval hits achieved by E6b (`M9-Q002`, `M9-Q010`, `M9-Q014`, `M9-Q030`), 3 (`M9-Q010`, `M9-Q014`, `M9-Q030`) were falsely rejected by the Evidence Controller due to cross-script CECI score depression, resulting in unnecessary abstentions. Along with `M9-Q058` (which achieved an answer via expanded context) and `M9-Q002` (which produced a structured regulatory disclosure), this yielded an end-to-end Devanagari answer/disclosure rate of only $4.44\%$ ($2/45$). (Note: `M9-Q018` was a Config A-only retrieval hit, also resulting in an unnecessary abstention).
3. **Operational Integration Gaps:** E6b is implemented solely as an internal parameter in `engine.py`. It is not configurable via `backend/app/core/config.py`, not exposed in FastAPI `QueryRequest` schemas, not accessible via the frontend UI, and lacks production observability tags.

**Recommendation:** **`RETAIN_AS_EXPERIMENTAL`** in the codebase. Maintain the runtime default as `"production"` and defer production promotion review pending the fully powered Milestone M11 confirmatory benchmark ($N=230$ intent groups).

---

## 2. Dimension A: Retrieval Quality Evaluation

Retrieval performance was evaluated across the 180 answerable queries of the frozen M9 benchmark ($45$ intents $\times$ $4$ languages), comparing Config A and Config B:

### 2.1 Granular Retrieval Metrics Table ($N=180$ Answerable Queries)

| Language Formulation | Configuration | Sample Size | Hit@1 | Hit@3 | Hit@5 (Count) | MRR | nDCG@5 | Retrieval Latency (Mean) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **English (`en`)** | Config A (Prod) | 45 | 0.0889 | 0.1111 | 0.1111 (5/45) | 0.1000 | 0.0839 | 1,097.10 ms |
| | Config B (E6b) | 45 | 0.0889 | 0.1111 | 0.1111 (5/45) | 0.1000 | 0.0839 | 1,097.10 ms |
| | *Delta* | *0* | *0.0000* | *0.0000* | *0 (0.0%)* | *0.0000* | *0.0000* | *0.00 ms* |
| **Hindi Devanagari (`hi`)** | Config A (Prod) | 45 | 0.0222 | 0.0222 | 0.0444 (2/45) | 0.0278 | 0.0195 | 1,097.10 ms |
| | Config B (E6b) | 45 | **0.0889** | **0.0889** | **0.0889 (4/45)** | **0.0889** | **0.0717** | **62.88 ms** |
| | *Delta* | *0* | *+0.0667* | *+0.0667* | *+2 (+100.0%)* | *+0.0611* | *+0.0522* | *-1,034.22 ms (-94.3%)* |
| **Romanized Hindi (`hi-Latn`)** | Config A (Prod) | 45 | 0.1333 | 0.1333 | 0.1333 (6/45) | 0.1333 | 0.1161 | 1,097.10 ms |
| | Config B (E6b) | 45 | 0.1333 | 0.1333 | 0.1333 (6/45) | 0.1333 | 0.1161 | 1,097.10 ms |
| | *Delta* | *0* | *0.0000* | *0.0000* | *0 (0.0%)* | *0.0000* | *0.0000* | *0.00 ms* |
| **Hinglish (`en-hi`)** | Config A (Prod) | 45 | 0.1111 | 0.1111 | 0.1111 (5/45) | 0.1111 | 0.0939 | 1,097.10 ms |
| | Config B (E6b) | 45 | 0.1111 | 0.1111 | 0.1111 (5/45) | 0.1111 | 0.0939 | 1,097.10 ms |
| | *Delta* | *0* | *0.0000* | *0.0000* | *0 (0.0%)* | *0.0000* | *0.0000* | *0.00 ms* |
| **Overall Answerable** | Config A (Prod) | 180 | 0.0889 | 0.0944 | 0.1000 (18/180) | 0.0931 | 0.0784 | 1,097.10 ms |
| | Config B (E6b) | 180 | **0.1056** | **0.1111** | **0.1111 (20/180)** | **0.1083** | **0.0914** | **849.87 ms** |
| | *Delta* | *0* | *+0.0167* | *+0.0167* | *+2 (+11.1%)* | *+0.0152* | *+0.0130* | *-247.23 ms (-22.5%)* |

### 2.2 Retrieval Assessment Finding:
- **Devanagari Recovery:** E6b successfully eliminates the catastrophic MS-MARCO score penalty on Devanagari Hindi, recovering Hit@5 from $2/45$ to $4/45$ ($+100\%$) and MRR from $0.0278$ to $0.0889$ ($+220\%$). However, under paired binomial testing ($b=3, c=1, n_D=4$), this improvement is **not statistically significant** ($p = 0.6250 > 0.05$).
- **Latin-Script Preservation:** Across all 135 Latin-script queries (`en`, `hi-Latn`, `en-hi`), E6b preserves production retrieval rankings bit-for-bit ($b=0, c=0$ observed regressions in the evaluated sample). Note that while zero sample regressions were observed, this does not constitute a formal statistical demonstration of non-inferiority, which would require a pre-specified non-inferiority margin and a dedicated power calculation.
- **Absolute Magnitude:** While relative gains are large ($+100\%$), the absolute Devanagari Hit@5 remains low ($8.89\%$, $4/45$), leaving $41/45$ answerable queries unretrieved due to dense bi-encoder vocabulary limitations. The aspirational goal of $\ge 50\%$ Hit@5 represents a **provisional M11 engineering target**, rather than a validated production acceptance criterion.

---

## 3. Dimension B: Statistical Evidence & Power Assessment

### 3.1 Unit of Analysis & Paired Inference
- **Independent Statistical Unit:** Semantic intent group ($N=45$ answerable; $N=60$ total).
- **Exact Paired McNemar / Binomial Test (Devanagari Hit@5, $N=45$):**
  - Discordant pairs: $b = 3$ (E6b wins: `M9-Q002`, `Q010`, `Q030`), $c = 1$ (Prod wins: `M9-Q018`). Total $n_D = 4$.
  - Exact two-sided binomial p-value: **$p = 0.6250 > 0.05$**.
- **Exact Paired McNemar / Binomial Test (Devanagari E2E Success, $N=45$):**
  - Discordant pairs: $b = 2$ (`M9-Q002`, `M9-Q058`), $c = 0$. Total $n_D = 2$.
  - Exact two-sided binomial p-value: **$p = 0.5000 > 0.05$**.
- **Cluster-Aware Permutation Wilcoxon Test ($N=45$ clusters):**
  - Non-zero clusters ($n=4$): Intents 1, 3, 5, 8.
  - Test statistic $W = 2.50$, exact permutation p-value: **$p = 0.6250$**.

### 3.2 Power Analysis & Confirmatory Benchmark Sizing
- **Post-Hoc Pilot Power:** At $n_D = 23$ discordant pairs ($p_1 = 0.75, \alpha = 0.05$), the exact two-sided power is **$65.37\%$**. Exact two-sided power $\ge 80\%$ requires at least $n_D = 30$ discordant pairs ($c_{\text{crit}} = 21, \alpha = 0.0428, \text{Power} = 80.34\%$).
- **Unconditional Sample Size Requirement (Milestone M11):** Treating discordant pair count as a random binomial variable ($D \sim \text{Binomial}(N, p_d = 0.15)$), unconditional power reaches **$80.20\%$ at $N = 225$** and **$81.22\%$ at $N = 230$** independent intent groups.
- **Statistical Verdict:** The current sample size of $N=45$ is **underpowered for a confirmatory production decision**. Observed improvements must be classified as exploratory pilot observations.

---

## 4. Dimension C: End-to-End Answer Quality

End-to-end execution was audited across all 240 benchmark queries (180 answerable, 60 unanswerable):

### 4.1 Complete Mutually Exclusive Outcome Partition Table

| Outcome Dimension | Config A (Production) | Config B (Adaptive E6b) | Delta | Classification |
|---|---:|---:|---:|---|
| **Answerable Direct Answers (`answered`)** | 52 / 180 (28.89%) | 53 / 180 (29.44%) | +1 | Success |
| **Answerable Regulatory Disclosures** | 7 / 180 (3.89%) | 8 / 180 (4.44%) | +1 | Success (`M9-Q002`) |
| **Combined Regulatory Success** | **59 / 180 (32.78%)** | **61 / 180 (33.89%)** | **+2** | **Success** |
| — English (`en`) | 28 / 45 (62.22%) | 28 / 45 (62.22%) | 0 | Preserved |
| — Hindi Devanagari (`hi`) | 0 / 45 (0.00%) | **2 / 45 (4.44%)** | **+2** | **Recovered** |
| — Romanized Hindi (`hi-Latn`) | 14 / 45 (31.11%) | 14 / 45 (31.11%) | 0 | Preserved |
| — Hinglish (`en-hi`) | 17 / 45 (37.78%) | 17 / 45 (37.78%) | 0 | Preserved |
| **Clean Unnecessary Abstentions (`unanswerable`)** | 119 / 180 (66.11%) | 117 / 180 (65.00%) | -2 | Failure |
| **Pipeline Execution Errors (`error`)** | 2 / 180 (1.11%) | 2 / 180 (1.11%) | 0 | Failure (`Q123`, `Q124`) |
| **Unanswerable Correct Abstentions** | **58 / 60 (96.67%)** | **58 / 60 (96.67%)** | **0** | **Safety Preserved** |
| **Unanswerable Incorrect Answers** | 2 / 60 (3.33%) | 2 / 60 (3.33%) | 0 | Failure (`Q201`, `Q229`) |

### 4.2 Answer Quality Verdict:
E6b successfully unlocks 2 verified Devanagari answers (`M9-Q002` structured disclosure and `M9-Q058` direct answer) while preserving Latin performance and maintaining a $96.67\%$ unanswerable safety rate. However, the absolute recovery rate ($4.44\%$, $2/45$) reflects persistent Evidence Controller false abstentions: 3 of E6b's 4 retrieval hits (`M9-Q010`, `M9-Q014`, `M9-Q030`) were rejected by uncalibrated CECI thresholds, while `M9-Q018` was a Config A-only retrieval hit that also ended in an unnecessary abstention.

---

## 5. Dimension D: Evidence Grounding & Citation Reliability

All 85 atomic claims and 57 citations generated by Config B across its 39 answering queries were audited:

### 5.1 Verification Summary Table

| Verification Gate | Config A (Production) | Config B (Adaptive E6b) | Production Benchmark Standard | Pass/Fail |
|---|---:|---:|---:|:---:|
| **Claim Support Precision** | 100.0% (82/82) | **100.0% (85/85)** | $\ge 98.0\%$ | **PASS** |
| **Unsupported Claim Rate** | 0.0% (0/82) | **0.0% (0/85)** | $\le 2.0\%$ | **PASS** |
| **Rule-of-Three 95% CI Upper Bound** | $\le 3.66\%$ | $\mathbf{\le 3.53\%}$ | $\le 5.0\%$ | **PASS** |
| **Citation UUID Validity** | 100.0% (54/54) | **100.0% (57/57)** | $100.0\%$ | **PASS** |
| **Corpus Passage Existence** | 100.0% (54/54) | **100.0% (57/57)** | $100.0\%$ | **PASS** |
| **Authoritative Page Accuracy** | 98.15% (53/54) | **98.25% (56/57)** | $\ge 95.0\%$ | **PASS** |
| **Semantic Claim-to-Citation Support** | 100.0% (54/54) | **100.0% (57/57)** | $\ge 95.0\%$ | **PASS** |

### 5.2 Grounding Verdict:
E6b satisfies all institutional evidence grounding and citation integrity standards. The bi-encoder bypass introduces zero hallucination or citation corruption.

---

## 6. Dimension E: Performance & Resource Constraints

### 6.1 Controlled Retrieval Benchmarking (Phase E Profiling)
- **Config A Overall Retrieval Mean:** $1,097.10\text{ ms}$ (p95: $1,477.08\text{ ms}$).
- **Config B Overall Retrieval Mean:** $849.87\text{ ms}$ (p95: $1,337.49\text{ ms}$).
- **Hindi Devanagari Retrieval Speedup:** From $1,051.81\text{ ms}$ to **$62.88\text{ ms}$ (a $94.0\%$ reduction)**.

### 6.2 Cold CPU End-to-End Execution (Phase F/H Records)
- **Retrieval Mean:** Config A $= 2,805.54\text{ ms}$; Config B $= 2,372.50\text{ ms}$ (Hindi Devanagari drops from $1,907.62\text{ ms}$ to **$175.46\text{ ms}$, a $90.8\%$ reduction**).
- **Controller Mean:** $1.50\text{ ms}$ (Config A) / $1.25\text{ ms}$ (Config B).
- **Generation Latency (Invoked on CPU, $N=117/119$):** Mean $= 89,995.25\text{ ms}$ / $88,532.03\text{ ms}$ (~88.5s).
- **Amortized Generation Latency ($N=240$):** Mean $= 43,872.76\text{ ms}$ / $43,897.19\text{ ms}$.
- **Total Pipeline Latency:** Config A $= 46,694.32\text{ ms}$; Config B $= 46,270.94\text{ ms}$.
- **Memory & Resource Profile:**
  - *Model-Loading Overhead:* Zero additional neural model weights or parameters loaded into RAM/VRAM beyond the pre-existing bi-encoder and cross-encoder models already initialized by production.
  - *Temporary Score Storage:* Negligible transient memory allocated for in-process Python dictionaries and float score sorting during candidate routing.
  - *Total Process Memory:* Peak process RSS during evaluation remained invariant at $\approx 1,180\text{ MB}$ (base process) and $\approx 2,192\text{ MB}$ (during PyTorch tensor evaluation across both configurations), remaining well within standard 8 GB system thresholds.

### 6.3 Performance Verdict:
E6b delivers a massive $90.8\%$ retrieval latency reduction in Devanagari Hindi with zero additional model-loading overhead and an invariant process memory profile. However, cold CPU generation latency remains high (~88.5s), highlighting that production responsiveness depends on Evidence Controller compute gating.

---

## 7. Dimension F: Operational Integration Assessment

Inspection of the codebase reveals several critical operational integration gaps:

| Component | Current State | Required for Production Promotion | Status |
|---|---|---|:---:|
| **Retrieval Engine (`engine.py`)** | Implemented at line 449 via `if rerank_strategy == "adaptive_e6b":` | Internal engine routing logic | **Implemented** |
| **Engine Default (`engine.py` L395)** | `rerank_strategy: str = "production"` | Default must remain safe production | **Verified Invariant** |
| **Settings Configuration (`config.py`)** | Missing `DEFAULT_RERANK_STRATEGY` environment variable setting | Must allow devops configuration without code mutation | **GAP** |
| **FastAPI API Schema (`schemas.py`)** | `QueryRequest` lacks `rerank_strategy` field | API clients cannot specify or toggle routing | **GAP** |
| **Frontend UI (`index.html`)** | Only exposes boolean `use_reranker` toggle | Users/admins cannot select adaptive routing in UI | **GAP** |
| **Observability & Logging** | Generic query logs; no tag recording whether dense bypass was triggered | Operational telemetry must log routing decisions | **GAP** |
| **Unit & Regression Tests** | `test_retrieval_baselines.py` covers adaptive routing (260/260 pass) | Full regression test suite passing | **PASS** |

### 7.1 Operational Integration Verdict:
E6b is currently an **internal experimental branch within `engine.py`**. It lacks the API contract, configuration settings, and telemetry required for production deployment.

---

## 8. Evaluation Against the Production Decision Framework

| Criterion # | Production Readiness Requirement | Evaluation Status | Supporting Evidence |
|---|---|:---:|---|
| **1** | Retrieval quality is adequately demonstrated | **PARTIAL** | $+100\%$ Hit@5 and $+220\%$ MRR in Devanagari, but absolute recall remains low ($8.89\%$). |
| **2** | No unacceptable language-specific regression | **PASS** | Zero observed regressions across 135 Latin queries in sample ($b=0, c=0$; non-inferiority not formally proven). |
| **3** | End-to-end answer quality is reliable | **PARTIAL** | Unlocks 2 verified answers (`M9-Q002`, `M9-Q058`), but 3 retrieval hits (`M9-Q010`, `M9-Q014`, `M9-Q030`) falsely abstained in Evidence Controller. |
| **4** | Evidence grounding and citations validated | **PASS** | $100\%$ claim precision across 85 audited claims, $0$ unsupported claims, $98.25\%$ page accuracy. |
| **5** | Abstention behavior is safe | **PASS** | $96.67\%$ correct abstention on unanswerable queries. |
| **6** | Latency and resource requirements acceptable | **PASS** | $90.8\%$ retrieval speedup on Devanagari; zero added model weights; process RSS invariant. |
| **7** | API and frontend integration operationally safe | **FAIL** | Not exposed in `QueryRequest` schema, `config.py`, or `index.html`. |
| **8** | Regression test coverage adequate | **PASS** | All 260 regression tests pass with 0 failures. |
| **9** | Rollback mechanism available | **PASS** | Production default invariant; rollback is instantaneous via `rerank_strategy="production"`. |
| **10** | Evaluation evidence sufficiently representative | **FAIL** | $N=45$ answerable intents is underpowered ($p=0.6250$, power $65.37\%$). Requires $N=230$. |

---

## 9. Assessment Conclusion

Because Criteria 7 (Operational Integration) and 10 (Confirmatory Benchmark Power) have not been satisfied, **promoting E6b to production at this time would violate institutional deployment standards**.

However, because Criteria 2, 4, 5, 6, 8, and 9 pass decisively, **rejecting E6b would be counter-productive**. E6b represents the strongest technical candidate developed in the project and must be preserved as an experimental alternative for confirmatory evaluation in Milestone M11.
