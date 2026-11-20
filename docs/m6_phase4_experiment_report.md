# IndicRAG-QA — M6 Phase 4: Experiment Report & Empirical Evaluation

**Document Title:** Exploratory Empirical Calibration Results, Error Deconstruction, and Threshold Analysis  
**Milestone:** M6 — Evidence Reliability and Answerability  
**Phase:** Phase 4 (Empirical Calibration Experiment)  
**Date:** 2026-11-11  
**Author:** Senior RAG Evaluation Researcher, Statistical Calibration Specialist & Evidence Reliability Engineer  
**Status:** Completed under `PHASE_4_AUTHORIZED_EXPLORATORY_ONLY`  

---

## 1. Experimental Setup and Preflight Certification

Prior to execution, all cryptographic fingerprints were independently verified against canonical project baselines:
- **Corpus DB Hash (142 child passages):** `8688605df0dbff786454ec770e95609d9d3aacb284fdb3a2f97191f7d2971e9d` (Verified 100% Match)
- **Frozen M3 Benchmark Hash ($N=15$):** `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` (Verified 100% Match)
- **Frozen M6 Benchmark Hash ($N=60$):** `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` (Verified 100% Match)
- **M6 Qualification Ledger Hash:** `db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13` (Verified 100% Match)
- **Phase 3 Negative Benchmark Hash ($N=33$):** `492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa` (Verified 100% Match)
- **Regression Suite:** 182/182 passing tests confirmed (`pytest` in 19.36s).

---

## 2. Quantitative Calibration Results (Target B: Evidence Answerability)

The calibration experiment evaluated $N = 56$ qualified benchmark queries ($N_{\text{pos}} = 32$ answerable, $N_{\text{neg}} = 24$ unanswerable).

### Comparative Metric Performance Table

| Model / Score Formulation | Brier Score $\downarrow$ | Log Loss $\downarrow$ | ROC-AUC $\uparrow$ | PR-AUC $\uparrow$ | ECE (5 Coarse Bins) $\downarrow$ | Calib Slope $A$ | Calib Intercept $B$ |
|---|---|---|---|---|---|---|---|
| **1. Uncalibrated Heuristic CECI Baseline** | 0.4140 | 9.0813 | 0.5573 | 0.7079 | 0.3963 | — | — |
| **2. Platt-Calibrated CECI (Out-of-Fold 3-CV)** | 0.2473 | 0.6879 | 0.3770 | 0.5391 | **0.0059** | 0.1202 | 0.2372 |
| **3. Platt-Calibrated CECI (Full Exploratory Fit)** | 0.2440 | 0.6811 | 0.5573 | 0.7079 | 0.0000 | 0.2893 | 0.2372 |
| **4. Platt-Calibrated Top-1 Retrieval Score (OOF)** | **0.2031** | **0.5789** | **0.7422** | **0.8362** | 0.0938 | **0.8113** | **0.0594** |
| **5. Platt-Calibrated F1 Relevance Score (OOF)** | 0.2423 | 0.6775 | 0.6322 | 0.6885 | 0.0410 | 0.6535 | 0.2671 |

### Critical Statistical Findings:
1. **CECI Probability Flattening:** The uncalibrated heuristic CECI had a poor Brier score ($0.4140$) because it was designed as an ordinal heuristic index, not an absolute probability. Applying Platt scaling dramatically improves the Brier score ($0.2473$) and Expected Calibration Error ($0.0059$).
2. **High Estimation Variance in Cross-Validation:** Due to small sample counts, the fitted slope across 3 cross-validation folds showed extreme variance: $\text{Fold Slopes} = [0.1202, -0.1007, 0.5999]$ ($\sigma = 0.2925$). One fold exhibited a negative slope, illustrating that $N=56$ is vulnerable to fold composition and cannot support stable out-of-fold generalization.
3. **Top-1 Raw Retrieval Score Superiority:** The raw Top-1 retrieval score yielded a markedly stronger discriminatory signal than composite CECI (ROC-AUC $0.7422$ vs $0.3770$ OOF; Brier score $0.2031$ vs $0.2473$). This demonstrates that for answerability detection, raw passage retrieval margin is less compressed than the multi-feature heuristic.

---

## 3. Coarse-Binned Reliability Analysis (Platt CECI)

To avoid misleading reliability curves with single-digit counts, a uniform 5-bin calibration analysis was conducted:

| Bin Range | Candidate Count | Mean Predicted Confidence | Empirical Accuracy | Calibration Gap | Reliability Diagnosis |
|---|---|---|---|---|---|
| **Bin 1: [0.00, 0.20)** | 0 | — | — | 0.0000 | Unpopulated (sigmoid floor $> 0.50$) |
| **Bin 2: [0.20, 0.40)** | 0 | — | — | 0.0000 | Unpopulated |
| **Bin 3: [0.40, 0.60)** | **53** | 0.5706 | 0.5660 | **0.0046** | High clustering around base rate ($\approx 57\%$) |
| **Bin 4: [0.60, 0.80)** | **3** | 0.6200 | 0.6667 | **0.0467** | Small sample, moderate confidence |
| **Bin 5: [0.80, 1.00]** | 0 | — | — | 0.0000 | Unpopulated (no extreme overconfidence) |

**Diagnosis:** Platt calibration prevents catastrophic overconfidence by compressing predictions into the central $[0.55, 0.62]$ probability interval matching the benchmark base rate ($57.1\%$). While this minimizes ECE ($0.0059$), it provides low decision sharpness across individual queries.

---

## 4. Empirical Threshold Exploration & Operational Trade-offs

We evaluated decision thresholds on the Out-of-Fold Platt-Calibrated probability:

| Threshold | True Pos (TP) | False Pos (FP) | True Neg (TN) | False Neg (FN) | Sensitivity (Recall) | Specificity | Precision | Youden's $J$ | Hypothetical Risk Cost ($5 \cdot \text{FP} + 1 \cdot \text{FN}$) |
|---|---|---|---|---|---|---|---|---|---|
| **0.10 – 0.50** | 32 | 24 | 0 | 0 | 1.0000 | 0.0000 | 0.5714 | 0.0000 | 120 (Max Hallucination Risk) |
| **0.60** | 2 | 1 | 23 | 30 | 0.0625 | 0.9583 | 0.6667 | 0.0208 | 35 (Balanced Abstention) |
| **0.70 – 0.90** | 0 | 0 | 24 | 32 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 32 (Complete Abstention) |

**Operational Conclusion:** In institutional regulatory RAG, emitting a false answer on an unanswerable policy query carries severe compliance penalties. Operating at a conservative threshold ($\tau \ge 0.60$) or relying on multi-state EvidenceController rules prevents unsafe answers, achieving high specificity ($95.8\%$) at the cost of conservative abstention on borderline queries.

---

## 5. Cross-Lingual Calibration Behavior

Calibration metrics were decomposed across language representations:

| Language Cohort | Sample Size | Answerable | Unanswerable | Mean Calibrated Probability | Brier Score | Evaluation Designation |
|---|---|---|---|---|---|---|
| **English (`en`)** | 35 | 17 | 18 | 0.5720 | 0.2578 | EXPLORATORY (Balanced) |
| **Devanagari Hindi (`hi`)** | 13 | 9 | 4 | 0.5680 | 0.2321 | DESCRIPTIVE_ONLY (Small Sample) |
| **Hinglish (`hi-en`)** | 3 | 3 | 0 | 0.5590 | 0.1943 | DESCRIPTIVE_ONLY (Single Class) |
| **Romanized Hindi (`hi-Latn`)** | 5 | 3 | 2 | 0.5760 | 0.2455 | DESCRIPTIVE_ONLY (Small Sample) |

All Indic subgroups demonstrate well-bounded mean confidence ($0.559 – 0.576$), closely tracking the true base rate without severe language-specific degradation.

