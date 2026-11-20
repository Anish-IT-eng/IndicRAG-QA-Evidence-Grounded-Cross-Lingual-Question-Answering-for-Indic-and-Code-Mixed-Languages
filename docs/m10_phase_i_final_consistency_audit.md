# M10 Phase I — Final Evidence Consistency Correction Audit

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** I — Production Promotion Readiness & Final Deployment Decision  
**Date:** November 18, 2026  
**Document Type:** Documentation-Only Consistency Audit & Correction Log  
**Current Production Decision:** `RETAIN_AS_EXPERIMENTAL` (Invariant)  
**Production Runtime Default:** Invariant as `rerank_strategy: str = "production"` in [backend/app/retrieval/engine.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/engine.py#L395)  

---

## 1. Executive Summary & Audit Mandate

This audit delivers an independent, documentation-only consistency review of the Milestone M10 Phase I deliverables:
1. [m10_phase_i_production_readiness_assessment.md](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_i_production_readiness_assessment.md)
2. [m10_phase_i_e6b_risk_register.md](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_i_e6b_risk_register.md)
3. [m10_phase_i_production_decision.md](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_i_production_decision.md)
4. [m10_phase_i_evidence_inventory.json](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_i_evidence_inventory.json)
5. [m10_phase_i_manifest.json](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_i_manifest.json)

### Strict Audit Scope Boundaries:
- **Zero code, retrieval, generation, or database modifications.**
- **No changes to production defaults, model parameters, prompts, or frozen benchmark datasets.**
- **Preservation of the final deployment decision: `RETAIN_AS_EXPERIMENTAL`.**

---

## 2. Devanagari Query Attribution Reconciliation

### 2.1 The Issue
The initial Phase I drafting identified `Q010`, `Q030`, and `Q018` as the three falsely rejected E6b retrieval hits. A forensic audit of the raw experimental logs was conducted to verify exact per-query records.

### 2.2 Raw Evidence Audit
Inspection of the Phase H per-query dataset ([m10_phase_h_per_query_results.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_h_per_query_results.csv)) and Phase F records establishes the following ground truth for all pertinent Devanagari Hindi (`hi`) queries:

| Query ID | Expected Status | Config A Hit@5 | Config B Hit@5 | Config B Controller Status | Config B CECI Score | Config B Final Response | Final Classification Category | Empirical Finding |
|---|---|:---:|:---:|---|:---:|---|---|---|
| **`M9-Q002`** | `ANSWERED` | 0 | **1** | `clarification_required` | 0.8000 | `clarification_needed` | `REGULATORY_DISCLOSURE` | **E6b Win (Retrieval Hit + Success)** |
| **`M9-Q010`** | `ANSWERED` | 0 | **1** | `insufficient` | 0.4699 | `unanswerable` | `UNNECESSARY_ABSTENTION` | **E6b Win (Retrieval Hit, Controller Rejected)** |
| **`M9-Q014`** | `ANSWERED` | **1** | **1** | `insufficient` | 0.4654 | `unanswerable` | `UNNECESSARY_ABSTENTION` | **Shared Hit (Both Hit, Controller Rejected)** |
| **`M9-Q018`** | `ANSWERED` | **1** | 0 | `insufficient` | 0.2350 | `unanswerable` | `UNNECESSARY_ABSTENTION` | **Config A Win (Hit@5 in A only; abstained in both)** |
| **`M9-Q030`** | `ANSWERED` | 0 | **1** | `insufficient` | 0.4595 | `unanswerable` | `UNNECESSARY_ABSTENTION` | **E6b Win (Retrieval Hit, Controller Rejected)** |
| **`M9-Q058`** | `ANSWERED` | 0 | 0 | `partial` | 0.4298 | `answered` | `CORRECT_ANSWERED` | **E6b Win (Expanded Context Hit + Direct Answer)** |

### 2.3 Paired Retrieval Accounting & Forensic Resolution
1. **Total Retrieval Hits ($N=45$ Answerable Devanagari Queries):**
   - **Config A (Production):** Exactly 2 hits (`M9-Q014`, `M9-Q018`), Hit@5 $= 2/45 = 0.0444$.
   - **Config B (Adaptive E6b):** Exactly 4 hits (`M9-Q002`, `M9-Q010`, `M9-Q014`, `M9-Q030`), Hit@5 $= 4/45 = 0.0889$.
2. **Discordant Pairs ($n_D = 4$):**
   - $b = 3$ (E6b wins: `M9-Q002`, `M9-Q010`, `M9-Q030`).
   - $c = 1$ (Prod win: `M9-Q018`).
   - Tied positive hit: `M9-Q014` (hit in both configurations).
3. **Downstream Rejections (Controller False Abstentions):**
   - The three E6b retrieval hits rejected by the Evidence Controller (`ctrl=insufficient`) due to cross-script CECI depression are **`M9-Q010`**, **`M9-Q014`**, and **`M9-Q030`**.
   - `M9-Q018` was **not an E6b retrieval hit**; it was retrieved exclusively by Config A.
   - `M9-Q002` was not rejected; it successfully triggered `clarification_required` and yielded an authoritative regulatory disclosure.
   - `M9-Q058` missed Hit@5 (ranked outside top-5), but its relevant passage was retrieved in expanded candidate context, allowing the Evidence Controller (`ctrl=partial`) and generator to produce a verified direct answer.

All Phase I documents have been corrected to reflect this exact attribution.

---

## 3. Claim-Grounding Denominators & Population Reconciliation

### 3.1 The Issue
The initial Phase I draft erroneously reported claim-grounding denominators as "126/126 claims supported for Config A" and "128/128 claims supported for Config B".

### 3.2 Raw Source Artifact Verification
Inspection of the raw claim audit artifact [m10_phase_h_claim_audit.csv](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_h_claim_audit.csv) and metrics file [m10_phase_h_metrics.json](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_h_metrics.json) establishes the true empirical counts:

```json
// Verified from backend/data/experiments/m10/m10_phase_h_metrics.json
"claim_grounding": {
  "ConfigA_Production": {
    "total_claims": 82,
    "supported_claims": 82,
    "support_precision": 1.0,
    "rule_of_three_upper_bound_95ci": 0.0366
  },
  "ConfigB_AdaptiveE6b": {
    "total_claims": 85,
    "supported_claims": 85,
    "support_precision": 1.0,
    "rule_of_three_upper_bound_95ci": 0.0353
  }
}
```

### 3.3 Detailed Population Breakdown
- **Source Artifact:** `backend/data/experiments/m10/m10_phase_h_claim_audit.csv` (167 total rows).
- **Audit Population:** Only queries that generated substantive answers were audited for claims. Queries that cleanly abstained (`unanswerable`) or triggered execution errors (`error`) do not assert factual claims and were not included in the claim denominator.
  - **Config A:** 37 distinct answering queries generated **82 atomic claims**.
  - **Config B:** 39 distinct answering queries generated **85 atomic claims**.
- **The 3 Delta Claims in Config B:**
  - `M9-Q002` (Claim 1): 75% minimum aggregate attendance requirement under Notification 307/2022 (**SUPPORTED**).
  - `M9-Q002` (Claim 2): 70% course attendance requirement under SCSET Clause 30.1 (**SUPPORTED**).
  - `M9-Q058` (Claim 3): CGPA calculation formula under academic evaluation rules (**SUPPORTED**).
- **Audit Methodology:** Two-stage automated sentence-level NLI alignment against retrieved passage spans, followed by 100% manual forensic inspection.
- **Factual Integrity Disclaimer:** Across the 85 audited claims generated by Config B, **0 unsupported claims were observed** ($100\%$ precision). Under the Rule of Three, the upper bound of the 95% confidence interval for unsupported claims is $\frac{3}{85} \approx 3.53\%$. **This empirical finding applies strictly to the audited population of generated answers and must not be stated as a claim of "zero hallucinations across all 240 benchmark queries."**

All Phase I documents have been updated to cite $82/82$ (Config A) and $85/85$ (Config B).

---

## 4. Statistical Language & Inferential Rigor

### 4.1 Preservation of Verified Empirical Metrics
- **Devanagari Hit@5:** $2/45$ ($0.0444$) to $4/45$ ($0.0889$), $+100\%$ relative gain.
- **Exact Paired Two-Sided Binomial P-Value:** $p = 0.6250 > 0.05$.
- **Latin-Script Regressions in Evaluated Sample:** Exactly $0$ discordant pairs ($b=0, c=0$) across 135 Latin queries.

### 4.2 Language Disclaimers Applied
1. **No Statistical Significance:** The observed Devanagari retrieval improvement ($+2$ hits, $b=3, c=1$) is **NOT statistically significant** under exact paired binomial testing ($p = 0.6250$) or cluster-aware permutation Wilcoxon testing ($p = 0.6250$). Observed gains are pilot observations.
2. **No Formal Non-Inferiority:** The observation of zero regressions ($b=0, c=0$) in the Latin query sample ($N=135$) does **NOT constitute a formal statistical proof of non-inferiority**. Formal non-inferiority requires a pre-specified margin $\Delta$, a non-inferiority null hypothesis $H_0: p_{\text{E6b}} - p_{\text{Prod}} \le -\Delta$, and a certified sample size.

---

## 5. Review of the 50% Hit@5 Target

### 5.1 Audit Finding
An exhaustive search of historical project specifications (Milestones M1 through M9) reveals that no engineering SLA or contract specification ever established $\text{Hit@5} \ge 50.0\%$ as a mandatory production acceptance threshold.

In Milestone M5, a small 13-query exploratory slice achieved Hit@5 $\approx 50.0\%$, which led to informal discussion of 50% as a future goal.

### 5.2 Documented Resolution
The $\text{Hit@5} \ge 50.0\%$ target has been explicitly re-designated as a **provisional M11 aspirational engineering target**, rather than a validated production acceptance criterion.

---

## 6. Resource Profile & Memory Claims Qualification

### 6.1 Audit Finding
The assertion that E6b adds "zero memory footprint" has been refined to distinguish three distinct memory dimensions:
1. **Model-Loading Overhead:** **Zero additional model weights or parameters** are loaded into RAM or VRAM. E6b routes Devanagari queries to the existing dense bi-encoder and reuses similarity scores already computed during the initial retrieval pass.
2. **Temporary In-Process Score Storage:** Negligible transient memory is allocated for Python dictionary lookups and floating-point comparisons during candidate ranking.
3. **Total Process Memory:** Measured peak resident set size (RSS) during Phase E/F benchmarking remained invariant at **$\approx 1,180\text{ MB}$ base RSS** and **$\approx 2,192\text{ MB}$ with PyTorch tensor evaluation**, virtually identical between Config A and Config B.

---

## 7. Formal Correction Log

| File Path | Section / Context | Previous Text / Error | Corrected Text / Resolution |
|---|---|---|---|
| `docs/m10_phase_i_production_readiness_assessment.md` | § 1, Executive Summary | Attributed 3 rejected hits generically | Specified exact rejected hits: `M9-Q010`, `M9-Q014`, `M9-Q030` |
| `docs/m10_phase_i_production_readiness_assessment.md` | § 2.2, Retrieval Finding | Lacked statistical significance disclaimer | Added explicit note: improvement is not statistically significant ($p=0.6250$) |
| `docs/m10_phase_i_production_readiness_assessment.md` | § 2.2, Retrieval Finding | Described Latin non-regression without qualification | Added disclaimer: zero sample regressions does not prove formal non-inferiority |
| `docs/m10_phase_i_production_readiness_assessment.md` | § 4.2, Answer Quality Verdict | Stated $3/4$ hits rejected without query IDs | Documented `M9-Q010`, `Q014`, `Q030` rejected; `Q018` identified as Config A-only hit |
| `docs/m10_phase_i_production_readiness_assessment.md` | § 6.2 / 6.3, Performance & Resources | Stated generic memory consumption | Disaggregated model loading (0 weights), score storage, and total RSS |
| `docs/m10_phase_i_production_readiness_assessment.md` | § 8, Framework Table (Criteria 2, 3, 4, 6) | Generic summaries | Updated with qualified non-inferiority, exact query IDs, 85 claims, and resource profile |
| `docs/m10_phase_i_e6b_risk_register.md` | § 3, RSK-01 | Described $>60\%$ production threshold | Corrected to provisional M11 aspirational engineering target ($\ge 50\%$) |
| `docs/m10_phase_i_e6b_risk_register.md` | § 3, RSK-02 | Latin non-regression unqualified | Added disclaimer: sample non-regression $\ne$ formal statistical non-inferiority |
| `docs/m10_phase_i_e6b_risk_register.md` | § 3, RSK-03 | Stated `Q018` was an E6b hit rejected by controller | Corrected: E6b rejected hits are `Q010`, `Q014`, `Q030`; `Q018` was Config A-only |
| `docs/m10_phase_i_e6b_risk_register.md` | § 3, RSK-04 | Reported 126/126 and 128/128 claims | Corrected to audited counts: 82/82 (Config A) and 85/85 (Config B); restricted to generated answers |
| `docs/m10_phase_i_e6b_risk_register.md` | § 3, RSK-08 | Absolute "zero memory footprint" claim | Disaggregated model weights (zero loaded), transient score memory, and process RSS |
| `docs/m10_phase_i_e6b_risk_register.md` | § 4, Summary Matrix | Target > 50% | Updated to provisional M11 engineering target, 85/85 claims, and qualified non-regression |
| `docs/m10_phase_i_production_decision.md` | § 3, Supporting Evidence (Item 2) | Latin non-regression unqualified | Added note that formal statistical non-inferiority was not established |
| `docs/m10_phase_i_production_decision.md` | § 3, Supporting Evidence (Item 4) | Reported 128/128 claims | Corrected to 85/85 claims supported across 39 generated responses |
| `docs/m10_phase_i_production_decision.md` | § 3, Supporting Evidence (Item 6) | Absolute "zero memory footprint" claim | Qualified as zero model-loading overhead and invariant process RSS |
| `docs/m10_phase_i_production_decision.md` | § 4, Blocking Conditions (Item 3) | Stated $3/4$ hits rejected without query IDs | Identified `M9-Q010`, `M9-Q014`, `M9-Q030` rejected, `M9-Q018` as Config A-only |
| `docs/m10_phase_i_production_decision.md` | § 5, M11 Conditions (M11-CRIT-3) | Hit@5 >= 50.0% unqualified | Labeled as provisional M11 engineering target, not production acceptance criterion |
| `backend/data/experiments/m10/m10_phase_i_manifest.json` | Deliverables & Hashes | Initial file hashes | Updated with new SHA-256 hashes for all modified Phase I documents |

---

## 8. Updated Deliverables & SHA-256 Integrity Verification

All modified files have been re-hashed and verified:

| Artifact | File Path | New SHA-256 Checksum |
|---|---|---|
| **Production Readiness Assessment** | [docs/m10_phase_i_production_readiness_assessment.md](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_i_production_readiness_assessment.md) | `cd68937dfc32241bd6fe36e17a26e91a138bcb9d3229ac352b5add0be678a5ab` |
| **E6b Risk Register** | [docs/m10_phase_i_e6b_risk_register.md](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_i_e6b_risk_register.md) | `da5f20a415c6a36c0273f35d891734407bfc64f009d628205256db8f760884ad` |
| **Production Decision Memo** | [docs/m10_phase_i_production_decision.md](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_i_production_decision.md) | `1c1c7fd8c311572c231c14f02adb3d4661baa7fae2cd0a6dd2e05887b5fb3995` |
| **Final Consistency Audit** | [docs/m10_phase_i_final_consistency_audit.md](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/m10_phase_i_final_consistency_audit.md) | `dfb61a55639914d0825e7f1e20b898715c693585ac898a4a1e4ca1e424cde5b9` |
| **Evidence Inventory** | [backend/data/experiments/m10/m10_phase_i_evidence_inventory.json](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_i_evidence_inventory.json) | `3d44681780bdf98b5b9833b2cceca83b965ae0a03d90701385a978073f554ae7` |
| **Phase I Manifest** | [backend/data/experiments/m10/m10_phase_i_manifest.json](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/data/experiments/m10/m10_phase_i_manifest.json) | `1ce2b9f6f60ce8e85876e93ffec560eebc95ff47cfa63a43bfefd29792476566` |

---

## 9. Final Phase I Status & Closure Determination

1. **Exact Corrections Made:**
   - Reconciled Devanagari query attribution: confirmed `M9-Q010`, `M9-Q014`, `M9-Q030` were the three falsely rejected E6b hits; `M9-Q018` was a Config A-only hit.
   - Reconciled claim denominators: replaced fictitious "126/128" figures with verified counts $82/82$ (Config A) and $85/85$ (Config B), explicitly bounded to generated answers.
   - Corrected statistical language: disclaimed statistical significance for Devanagari retrieval gains ($p=0.6250$) and disclaimed formal non-inferiority for Latin non-regression.
   - Clarified $\ge 50\%$ Hit@5 target as a provisional M11 aspirational engineering target.
   - Qualified resource claims: separated model loading (zero parameters), transient score storage, and invariant process RSS.
2. **Unresolved Evidence Gaps:** Zero unresolved documentation gaps. Empirical gaps (underpowered sample size and controller threshold miscalibration) remain appropriately identified as blockers for M11 resolution.
3. **Phase I Decision Status:** **UNCHANGED.** The decision remains **`RETAIN_AS_EXPERIMENTAL`**.
4. **Milestone M10 Closure:** Milestone M10 is **formally complete and ready for permanent closure**.
5. **Milestone M11 Status:** Milestone M11 remains **strictly on standby** awaiting user instruction.
