# IndicRAG-QA — R6 Stage 1: Benchmark Integrity Audit Results

**Execution Timestamp:** 2026-11-19T13:14:48+05:30  
**Executing Command:** `python scripts/audit_existing_benchmarks.py`  
**Auditor Role:** Evaluation Auditor & Data Integrity Engineer  
**Stage Status:** **PASSED — ALL_HASHES_MATCH_VERIFIED**  

---

## 1. Executive Summary

Stage 1 execution performed direct cryptographic SHA-256 hash checks on all 13 configured benchmark datasets, qualification ledgers, milestone baselines, and regression verification logs. 

- **Total Configured Artifacts:** 13
- **Accessible & Present Files:** 13
- **Missing or Inaccessible Files:** 0
- **Cryptographic Hash Matches:** 13 (100.0%)
- **Cryptographic Hash Mismatches:** 0 (0.0%)
- **Integrity Determination:** **STAGE_1_PASSED**

---

## 2. Granular Artifact Verification Table

| Artifact Identifier | Classification Tier | File Path | Expected SHA-256 Baseline | Computed Actual SHA-256 | Match Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **M3 Final Dataset** ($N=15$) | Tier 1 (Directly Verified) | `backend/data/dataset/final_verified_dataset.csv` | `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` | `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` | **MATCH** |
| **M6 Expanded Benchmark** ($N=60$) | Tier 1 (Directly Verified) | `backend/data/dataset/m6_expanded_benchmark_n60.csv` | `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` | `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` | **MATCH** |
| **M6 Benchmark Qualification Ledger** | Tier 1 (Directly Verified) | `backend/data/dataset/m6_benchmark_qualification.csv` | `db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13` | `db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13` | **MATCH** |
| **M6 Phase 3 Negative Benchmark** ($N=33$) | Tier 1 (Directly Verified) | `backend/data/experiments/m6/m6_phase3_1_negative_benchmark_audit.csv` | `be02da59b85d2895b8c60f52266540c27e39c4e8fb39810b1152cf74ea69b05c` | `be02da59b85d2895b8c60f52266540c27e39c4e8fb39810b1152cf74ea69b05c` | **MATCH** |
| **M6 Phase 3 Negative Candidates Pool** | Tier 1 (Directly Verified) | `backend/data/dataset/m6_phase3_negative_candidates.csv` | `492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa` | `492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa` | **MATCH** |
| **M9 Evaluation Dataset** ($N=240$) | Tier 1 (Directly Verified) | `backend/data/experiments/m9/m9_evaluation_dataset.jsonl` | `f1829bdcad4512b6481005a944ab65da6dbd2858de5cc83a4a289d15bd506c2f` | `f1829bdcad4512b6481005a944ab65da6dbd2858de5cc83a4a289d15bd506c2f` | **MATCH** |
| **M9 Answer Generation Results Baseline** | Tier 1 (Directly Verified) | `backend/data/experiments/m9/answer_generation_results.csv` | `8dd71a906d704a9e2dfce55dee3d977555f6e59d5deb7a20eef8fc3ce0b13943` | `8dd71a906d704a9e2dfce55dee3d977555f6e59d5deb7a20eef8fc3ce0b13943` | **MATCH** |
| **M10 Baseline Snapshot** | Tier 2 (Snapshot Checkpoint) | `backend/data/experiments/m10/m10_baseline_snapshot.json` | `06370db7b83ed53c5beb18b1a0a4f9b7877a5c46e83b8e5c47586bccea2fd693` | `06370db7b83ed53c5beb18b1a0a4f9b7877a5c46e83b8e5c47586bccea2fd693` | **MATCH** |
| **M10 Phase F Baseline Snapshot** | Tier 2 (Snapshot Checkpoint) | `backend/data/experiments/m10/m10_phase_f_baseline_snapshot.json` | `ece587035b7e22c4755c8dcbbab091f8255e78c293f917d9960eb969f8fce24b` | `ece587035b7e22c4755c8dcbbab091f8255e78c293f917d9960eb969f8fce24b` | **MATCH** |
| **R4 Comprehensive Test Results** | Tier 2 (Dynamic Test Trace) | `docs/r4_test_results.json` | `364ab44b00f4f084461f9ae7b86cd1910aaace0ad3d838af5ae996dfd1d3b198` | `364ab44b00f4f084461f9ae7b86cd1910aaace0ad3d838af5ae996dfd1d3b198` | **MATCH** |
| **R4.1 Multilingual Audit** | Tier 2 (Dynamic Test Trace) | `docs/r4_1_multilingual_audit.json` | `da50986309daca1fdcf7d0bcbc13fc87df2dddf921e99799408a047664d964bc` | `da50986309daca1fdcf7d0bcbc13fc87df2dddf921e99799408a047664d964bc` | **MATCH** |
| **R2.1 Regression Test Results** | Tier 2 (Dynamic Test Trace) | `docs/r2_1_regression_test_results.json` | `97a78044061c08a71e8be5de3574c4ffce0063e76a7b8874dedbcd66429c53c8` | `97a78044061c08a71e8be5de3574c4ffce0063e76a7b8874dedbcd66429c53c8` | **MATCH** |
| **R3 Test Results** | Tier 2 (Dynamic Test Trace) | `docs/r3_test_results.json` | `c8309769ab5000fbe139bdde6da5a7aa2324eeed806c12096152542f3be35b78` | `c8309769ab5000fbe139bdde6da5a7aa2324eeed806c12096152542f3be35b78` | **MATCH** |

---

## 3. Manifest Synchronization Status

The manifest file `docs/r6_dataset_integrity_manifest.json` was updated during execution. It records:
- File paths, sizes, record counts, and schema columns.
- Cryptographic SHA-256 hashes matching baseline ledgers.
- Frozen status annotations for M3–M10 benchmarks.

Zero anomalies, corruption, or missing data were observed.

---

## 4. Stage 1 Sign-Off

Stage 1 verification is completely satisfied with zero warnings or errors. Authorization criteria to proceed to Stage 2 are satisfied.
