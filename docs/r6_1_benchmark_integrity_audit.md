# IndicRAG-QA — R6.1 Complete Benchmark Integrity Audit

**Audit Date:** 2026-11-19  
**Auditor Role:** Evaluation Auditor & Data Integrity Engineer  
**Milestone:** R6 Task 1.1 Benchmark Integrity and Runtime Readiness Correction  
**Determination:** **ALL_FROZEN_BENCHMARKS_CRYPTOGRAPHICALLY_VERIFIED**  

---

## 1. Executive Summary & Chain of Custody

In R6 Task 1, an initial benchmark inventory was compiled. However, a rigorous distinction was required between:
1. Artifacts whose cryptographic SHA-256 hashes are **directly verified against independent historical baselines** recorded in prior milestone manifests (M8.1, M8.6, M8.7, M8.8, M9, and M10);
2. Artifacts that have **recorded hashes without an independent baseline comparison** (such as milestone snapshot checkpoints or dynamic test outputs);
3. **Frozen artifacts without established baseline hashes** (such as historical intermediate CSV experiment dumps).

This audit independently computes the SHA-256 hash of every benchmark and result artifact directly from disk and compares it against frozen historical manifests (`m10_baseline_snapshot.json`, `m10_phase_f_baseline_snapshot.json`, `m9_integrity_manifest.json`, `m8_8_integrity_manifest.json`, `m8_6_integrity_manifest.json`, and `m8_1_integrity_manifest.json`).

**Key Result:** 100% of frozen benchmark datasets (M3, M6, M6 Negative, M9, and M9 answers) match their historical baseline hashes with zero drift, zero byte alteration, and intact provenance.

---

## 2. Artifact Integrity Matrix Across All Tiers

### Tier 1: Directly Hash-Verified Artifacts Against Trusted Historical Baselines

| Artifact Name | Milestone | Exact File Path | Actual SHA-256 | Expected Baseline SHA-256 | Source Baseline Reference | Frozen Status | Match Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M3 Final Dataset** ($N=15$) | M3 | `backend/data/dataset/final_verified_dataset.csv` | `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` | `093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520` | `m10_baseline_snapshot.json` / `m8_1` / `m8_6` / `m8_7` / `m8_8` / `m9` | FROZEN | **VERIFIED MATCH** |
| **M6 Expanded Benchmark** ($N=60$) | M6 | `backend/data/dataset/m6_expanded_benchmark_n60.csv` | `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` | `a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae` | `m10_baseline_snapshot.json` / `m8_1` / `m8_6` / `m8_7` / `m8_8` / `m9` | FROZEN | **VERIFIED MATCH** |
| **M6 Benchmark Qualification Ledger** ($N=60$) | M6 | `backend/data/dataset/m6_benchmark_qualification.csv` | `db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13` | `db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13` | `m10_baseline_snapshot.json` / `m8_1` / `m8_6` / `m8_7` / `m8_8` / `m9` | FROZEN | **VERIFIED MATCH** |
| **M6 Phase 3 Negative Benchmark** ($N=33$) | M6 | `backend/data/experiments/m6/m6_phase3_1_negative_benchmark_audit.csv` | `be02da59b85d2895b8c60f52266540c27e39c4e8fb39810b1152cf74ea69b05c` | `be02da59b85d2895b8c60f52266540c27e39c4e8fb39810b1152cf74ea69b05c` | `m10_baseline_snapshot.json` / `m8_8` / `m9` | FROZEN | **VERIFIED MATCH** |
| **M6 Phase 3 Candidates Pool** ($N=60$) | M6 | `backend/data/dataset/m6_phase3_negative_candidates.csv` | `492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa` | `492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa` | `m8_1_integrity_manifest.json` / `m8_6` / `m8_7` | FROZEN | **VERIFIED MATCH** |
| **M9 Multilingual Evaluation Dataset** ($N=240$) | M9 | `backend/data/experiments/m9/m9_evaluation_dataset.jsonl` | `f1829bdcad4512b6481005a944ab65da6dbd2858de5cc83a4a289d15bd506c2f` | `f1829bdcad4512b6481005a944ab65da6dbd2858de5cc83a4a289d15bd506c2f` | `m10_phase_f_baseline_snapshot.json` / `m9_integrity_manifest.json` | FROZEN | **VERIFIED MATCH** |
| **M9 Answer Generation Results Baseline** ($N=240$) | M9 | `backend/data/experiments/m9/answer_generation_results.csv` | `8dd71a906d704a9e2dfce55dee3d977555f6e59d5deb7a20eef8fc3ce0b13943` | `8dd71a906d704a9e2dfce55dee3d977555f6e59d5deb7a20eef8fc3ce0b13943` | `m10_phase_f_baseline_snapshot.json` (`m9_answers_csv_sha256`) | FROZEN | **VERIFIED MATCH** |
| **Pre-Refresh Official FAISS Index** | M8/M10 | `backend/data/backups/m8_pre_refresh_20261116_095304/indexes/official/faiss.index` | `19e57ba4d910eb911ff6300d196c222b3bdd3735b878352f6f504311f7c10d2c` | `19e57ba4d910eb911ff6300d196c222b3bdd3735b878352f6f504311f7c10d2c` | `m10_phase_f_baseline_snapshot.json` (`faiss_index_sha256`) | FROZEN | **VERIFIED MATCH** |

---

### Tier 2: Artifacts with Recorded Hashes but No Independent Baseline Comparison

These artifacts have their current SHA-256 hashes recorded in the system manifest, but either serve as self-referencing snapshot checkpoints or represent dynamic regression outputs produced during R1–R5 verification suites:

| Artifact Name | Milestone / Phase | Exact File Path | Actual SHA-256 | Role / Classification Notes | Frozen Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **M10 Baseline Snapshot** | M10 Phase A | `backend/data/experiments/m10/m10_baseline_snapshot.json` | `06370db7b83ed53c5beb18b1a0a4f9b7877a5c46e83b8e5c47586bccea2fd693` | Self-referencing milestone snapshot checkpoint recording M3, M6, and database state | FROZEN CHECKPOINT |
| **M10 Phase F Baseline Snapshot** | M10 Phase F | `backend/data/experiments/m10/m10_phase_f_baseline_snapshot.json` | `ece587035b7e22c4755c8dcbbab091f8255e78c293f917d9960eb969f8fce24b` | Self-referencing milestone snapshot checkpoint recording M9 dataset and answer hashes | FROZEN CHECKPOINT |
| **R4 Comprehensive Test Results** | R4.1.1 | `docs/r4_test_results.json` | `364ab44b00f4f084461f9ae7b86cd1910aaace0ad3d838af5ae996dfd1d3b198` | Test suite output from `scripts/test_r4_comprehensive.py` (14/14 passed) | VERSIONED OUTPUT |
| **R4.1 Multilingual Audit** | R4.1 | `docs/r4_1_multilingual_audit.json` | `da50986309daca1fdcf7d0bcbc13fc87df2dddf921e99799408a047664d964bc` | Quality audit execution trace across 4 linguistic query variants | VERSIONED OUTPUT |
| **R2.1 Regression Test Results** | R2.1 | `docs/r2_1_regression_test_results.json` | `97a78044061c08a71e8be5de3574c4ffce0063e76a7b8874dedbcd66429c53c8` | Calendar reconciliation test trace verifying official exam dates | VERSIONED OUTPUT |
| **R3 Test Results** | R3 | `docs/r3_test_results.json` | `c8309769ab5000fbe139bdde6da5a7aa2324eeed806c12096152542f3be35b78` | Generic relationship-aware retrieval test results (15/15 passed) | VERSIONED OUTPUT |

---

### Tier 3: Frozen Artifacts without Established Baseline Hash

These artifacts represent historical intermediate experiment logs produced during earlier development phases (M4 and M8) that were preserved as frozen reference records but were not ledgered into an external manifest:

| Artifact Name | Milestone | Exact File Path | Actual SHA-256 | Description | Frozen Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **M4 BM25 Results** | M4 | `backend/data/experiments/m4_bm25_results.csv` | `1bcfaaf5dbbe1b4ec3c2ea662ff827e7f671c667a42bbca4fe80fefaf4668b31` | BM25 retrieval baseline scores | FROZEN HISTORICAL |
| **M4 Dense Results** | M4 | `backend/data/experiments/m4_dense_results.csv` | `2e05df8421b8ff120140228d447d2ce893b80b2a752252a537f59d04bc5ca7db` | FAISS dense retrieval baseline scores | FROZEN HISTORICAL |
| **M4 Hybrid Results** | M4 | `backend/data/experiments/m4_hybrid_results.csv` | `a90c102a281e4bda00881f1ec76e038c92a2a7aa61a073f1d9a5b3a4a7536d71` | Hybrid RRF retrieval baseline scores | FROZEN HISTORICAL |
| **M8.6 Claim Evidence Matrix** | M8.6 | `backend/data/experiments/m8/m8_6_claim_evidence_matrix.csv` | `b3d4f572aa34d7fa8f6f70932dc9622c366ffba75bf14a1a3666fcf9b0ce3950` | Controller claim-evidence alignment trace | FROZEN HISTORICAL |
| **M8.8 Clause Relationship Matrix** | M8.8 | `backend/data/experiments/m8/m8_8_clause_relationship_matrix.csv` | `8ee98939626359e99cce89fa7a26887569b917d52b95c07b6bfb10292fe97dc1` | Regulatory clause relationship cross-check | FROZEN HISTORICAL |

---

## 3. Database and Corpus Evolution Reconciliation

An audit of `indicrag.db` and the active FAISS index reveals an intentional and fully documented divergence from M10:

1. **Database (`backend/data/db/indicrag.db`):**
   - **M10 Baseline Hash:** `2ec61aae957c51eb9703e5322461e044b8432e1b752a9a6e8e2b154bd68121d3` (Size: ~1.95 MB, 253 child passages, 53 parent passages, 0 relationships).
   - **Current Database Hash:** `38ee352fd51628c397708d1c4370644f594877638070250d815ed52be83396e3` (Size: 17.25 MB).
   - **Reconciliation:** Between M10 and R6, Phases R1, R2, R2.1, R3, R4, and R5 created and populated:
     - The `document_relationships` table (7,714 valid relationship edges).
     - The `extracted_tables` and `table_cells` tables (structured calendar and ordinance data).
     - The `conversation_sessions` and `conversation_turns` tables (R5 conversational state).
   - The original M10 pre-refresh database was safely backed up at `backend/data/backups/m8_pre_refresh_20261116_095304/indicrag.db` and intermediate phase backups (`indicrag.db.bak_r1`, `indicrag.db.bak_r2`, `indicrag.db.bak_r5`) are intact.

2. **FAISS Index (`backend/data/indexes/official/faiss.index`):**
   - **M10 Baseline Hash:** `19e57ba4d910eb911ff6300d196c222b3bdd3735b878352f6f504311f7c10d2c`.
   - **Archival Verification:** `backend/data/backups/m8_pre_refresh_20261116_095304/indexes/official/faiss.index` has the exact SHA-256 `19e57ba4...` (**VERIFIED MATCH**).
   - **Current Active Index:** `19be1f540cc23c5458f91ff55240db86ad34a4452ea35dcce0c4a0cd329ab2f4` (430 KB) contains the updated embeddings corresponding to the verified 7 official documents.

---

## 4. Benchmark Qualification Integrity

The qualification status across the benchmarks is verified as follows:

1. **M3 Benchmark ($N=15$):**
   - 13 Answerable, 2 Unanswerable.
   - Gold citations and reference answers verified against BU-First-Ordinance-2016 and Academic Rules.
   - Status: `AUTOMATED_VALIDATION_PENDING_HUMAN` (Frozen).

2. **M6 Benchmark ($N=60$):**
   - 40 Answerable, 20 Unanswerable.
   - Complete ledger in `m6_benchmark_qualification.csv`.
   - Primary taxonomies: direct, numerical, conditional, temporal, multi_part.
   - Status: `AUTOMATED_VALIDATION_PENDING_HUMAN` (Frozen).

3. **M6 Phase 3 Negative Benchmark ($N=33$):**
   - 33 strictly Unanswerable queries.
   - Covers absence of regulation, historical conflict, out-of-scope policies.
   - Status: `AUTOMATED_VALIDATION_PENDING_HUMAN` (Frozen).

4. **M9 Multilingual Evaluation Dataset ($N=240$):**
   - 60 distinct intents $\times$ 4 language variants (`en`, `hi`, `hi-Latn`, `en-hi`).
   - 180 Answerable (45 intents $\times$ 4), 60 Unanswerable (15 intents $\times$ 4).
   - Status: `PROVISIONAL_NOT_HUMAN_VERIFIED` (Frozen).

---

## 5. Audit Conclusion

All benchmark datasets intended for R6 evaluation are cryptographically intact, match historical baselines, and are free of corruption or post-hoc modifications.

Evaluation scripts in R6 must operate strictly in **READ-ONLY** mode against these datasets.
