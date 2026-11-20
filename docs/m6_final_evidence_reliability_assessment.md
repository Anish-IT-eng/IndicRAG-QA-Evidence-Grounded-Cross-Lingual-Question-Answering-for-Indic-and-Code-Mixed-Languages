# IndicRAG-QA — M6 Final Evidence Reliability & Milestone Synthesis Assessment

**Milestone:** M6 — Evidence Reliability and Answerability  
**Phase:** Phase 4 (Milestone Synthesis & Final Assessment)  
**Date:** 2026-11-11  
**Lead Evaluator:** Senior RAG Evaluation Researcher, Statistical Calibration Specialist & Evidence Reliability Engineer  
**Final Status Determination:** **`PHASE_4_EXPLORATORY_CALIBRATION_COMPLETED`**  

---

## 1. M0–M6 Milestone Synthesis & Lifecycle Verification Matrix

To ensure absolute scientific integrity, this synthesis rigorously distinguishes five levels of evidentiary maturity:
- **Implemented:** Production or research code exists and is committed.
- **Tested:** Automated tests exercise functionality in CI/unit test suite.
- **Evaluated:** Empirical metrics collected against an experimental benchmark.
- **Independently Verified:** Verified through an independent verification pipeline, separate models, or distinct audit scripts.
- **Human Verified:** Gold-standard ground truth established through direct manual human subject-matter inspection.

### Consolidated Project Milestone Matrix

| ID | Milestone Title | Primary Research Objective | Implementation Status | Automated Testing Status | Empirical Evaluation Status | Independent Verification | Human Verification | Known Methodological Limitations | Final Milestone Status |
|---|---|---|---|---|---|---|---|---|---|
| **M0** | Repository Audit & Environment Preflight | Establish reproducible runtime, local LLMs, and Python dependencies | FastAPI, SQLite WAL, Ollama local models (`qwen2.5:3b`, `llama3.2:3b`, `gemma:2b`) | 104 baseline tests passing | Operational preflight complete | Cryptographic sha256 checksums on all DBs | System environment manually checked | PyMuPDF DLL blocked on Windows; pypdf fallback active | **COMPLETED** |
| **M1** | Official Document Collection | Acquire authoritative Bennett University regulatory PDFs | PDF ingestion pipeline, metadata registration, SHA-256 deduplication | Tested in ingestion suite | 4 official PDFs (2017 Ordinance, Notification 307/2022, SCSET Rules, Academic Calendar) | Dual-model extraction checks | Institutional source URLs verified | Absence of unindexed policy documents (hostel, transport, PhD guidelines) | **COMPLETED** |
| **M2** | Document Ingestion & Corpus QA | Parent-child hierarchical chunking & SQLite storage | Parent/child chunking, section extraction, metadata linking | Tested in ingestion smoke suite | 142 child passages, 30 parent sections (`8688605df0dbff7864...`) | Section continuity checks | Chunk boundaries inspected | Chunk size fixed at 512 tokens with 64 token overlap | **COMPLETED** |
| **M3** | Benchmark Dataset Generation & Verification | Generate initial gold QA benchmark across multilingual formats | Benchmark generator, LLM verification agent | Tested in `test_model_verifier.py` | Initial $N=15$ frozen benchmark (`093b00ad0f...`) | Automated dual-model consensus | Human audit sample checked | Benchmark initially lacked diverse unanswerable negative queries | **COMPLETED** |
| **M4** | Retrieval Baselines & Metrics | Establish BM25, dense FAISS, and RRF hybrid retrieval baselines | BM25 Okapi, BAAI/bge-m3 dense, reciprocal rank fusion (RRF) | Tested in `test_retrieval_baselines.py` | MRR@5, Recall@5, NDCG@5 evaluated across languages | Independent baseline metric auditor | Cross-lingual queries checked | Cross-encoder latency overhead on long passages | **COMPLETED** |
| **M5** | Advanced RAG & E1–E12 Experiments | Multi-query expansion, parent-document retrieval, cross-encoder reranking | MQR, PDR, Reranking, regulatory version validation | Tested in E1–E12 test suite | Experiments E1–E12 executed and audited | Result audit reconciled historical metric reporting | Passage versioning inspected | Regulatory contradictions required explicit conflict controller | **COMPLETED** |
| **M6** | Evidence Reliability & Answerability | Six-state evidence controller, claim grounding, negative benchmark expansion, exploratory score calibration | Six-state controller, CECI index, atomic claim grounding, exploratory Platt calibrator | 182/182 tests passing (`test_m6_*.py`) | Evaluated across 29 pilot queries, 33 negative candidates, and 56 Target B queries | Cryptographic reconciliation in Phase 2B.2, 3.2, and 4 | Formal qualification audit completed; automated consensus distinguished from human verification | Small effective sample ($N=56$); non-parametric isotonic regression blocked; calibration exploratory only | **COMPLETED (EXPLORATORY)** |

---

## 2. Evidence-Based Determination of M6

### Final Decision: **`PHASE_4_EXPLORATORY_CALIBRATION_COMPLETED`**

### Justification:
1. **Full Algorithmic Implementation:** Implemented a dedicated research-only univariate Platt scaling module (`ExploratoryPlattCalibrator`) in `backend/app/calibration/exploratory_calibrator.py` with rigorous input score bounds, NaN/missing fallbacks, and parameter clamping.
2. **Defensive Evaluation Protocol:** Refused to treat automated cross-model LLM consensus as ground truth. Qualified all 33 negative candidates into clear taxonomic categories and constructed a verified 93-record Cohort Lineage.
3. **Rigorous Metric Reconciliation:** Recalculated true multi-class metrics (Macro-F1 $49.07\%$, Weighted-F1 $61.88\%$, Direct-Answer Precision $100.0\%$, Contradiction Leakage $0.00\%$), disproving misleading binary aggregates.
4. **Transparent Statistical Reporting:** Proved that while Platt calibration significantly improves Brier score ($0.4140 \to 0.2473$) and coarse-binned ECE ($0.0059$), the sample size ($N=56$) exhibits high cross-validation variance ($\sigma_{\text{slope}} = 0.2925$).
5. **Architectural Safety Invariance:** Verified that runtime safety overrides (version contradiction alerts, ungrounded claim purges, and zero-citation short circuits) remain unconditionally authoritative over any continuous probability estimate.

---

## 3. What the Evidence Supports vs. What Remains Unproven

### What the Evidence Confidently Supports:
1. **Deterministic Safety Rules Prevent Hallucinations:** The patched runtime evidence controller achieves $100.0\%$ direct-answer precision (17/17) and $0.00\%$ contradiction leakage across the qualified pilot benchmark.
2. **Raw Retrieval Scores are Stronger Predictors of Answerability than Composite Heuristic CECI:** Raw Top-1 retrieval scores provide higher discriminative separation (ROC-AUC $0.7422$) than the heuristic CECI index (ROC-AUC $0.5573$).
3. **Platt Sigmoid Fitting Resolves Base-Rate Misalignment:** Platt calibration eliminates the probability-scale gap of ordinal heuristics, aligning mean predicted confidence ($57.06\%$) with true dataset prevalence ($57.14\%$).
4. **Hierarchical Regulation Logic Must Preempt Document Dates:** Historical regulatory applicability cannot be decided by publication year alone. Notification 307/2022 supersedes attendance thresholds, while 2022 SCSET Rules govern course-specific exceptions.

### What Remains Unproven / Limitations:
1. **Production-Grade Calibration Guarantees:** An effective sample of $N=56$ ($N_{\text{neg}}=24$) cannot support low-variance production calibration or empirical threshold deployment without risk of overfitting.
2. **Non-Parametric Isotonic Calibration:** Remains blocked due to sample size constraints ($N \ge 200$ required).
3. **Claim Grounding Calibration (Target C):** With only 3 non-entailed claims in the qualified pilot, claim-level calibration remains untrainable without synthetic negative generation.
4. **Subgroup Generalization:** Hinglish ($N=3$) and Romanized Hindi ($N=5$) are too small for statistically valid subgroup conclusions.

---

## 4. Mandate for Milestone M7 (Frontend Integration & Final Research Evaluation)

Milestone M6 is formally closed as an exploratory research milestone. The project now transitions to **M7: Frontend Integration and Final Research Evaluation**.

### Objectives for M7:
1. **Standalone HTML/JS UI Integration:** Connect the responsive browser frontend to all backend API endpoints (`/query`, `/documents`, `/health`).
2. **Rich Evidence & Safety Visualization:**
   - Display the authoritative six-state controller decision (`SUFFICIENT`, `PARTIAL`, `INSUFFICIENT`, `CONFLICTING`, `CLARIFICATION_REQUIRED`, `MISSING`).
   - Visually render grounded passage citations with page and section references.
   - Display prominent regulatory conflict banners when multiple academic ordinances apply to different student cohorts.
3. **Cross-Lingual Query Support:** Ensure seamless rendering and input handling for Devanagari Hindi, Hinglish, and English.
4. **Final Comprehensive System Evaluation:** Produce the final research report synthesizing end-to-end user latency, generation quality, evidence grounding, and system robustness.

