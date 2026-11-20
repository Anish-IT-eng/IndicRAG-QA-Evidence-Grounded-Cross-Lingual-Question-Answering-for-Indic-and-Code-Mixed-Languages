# IndicRAG-QA — Milestone M8: Retrieval Index Validation Report

**Role:** Senior Retrieval and Search Engine Specialist  
**Milestone:** M8 — Corpus Document Refresh  
**Date:** 2026-11-16  
**Status:** Complete  

---

## 1. Index Architecture & Configuration

The official retrieval pipeline uses a dual hybrid search architecture combined via Reciprocal Rank Fusion (RRF):

```
                       User Query
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
     BM25 Lexical Search        Dense Vector Search
     (BM25Okapi, 253 units)     (FAISS FlatIP, dim 384)
             │                           │
             └─────────────┬─────────────┘
                           ▼
                 Reciprocal Rank Fusion
                      (RRF k=60)
                           │
                           ▼
               Version Validation & PDR
              (Parent Document Expansion)
```

---

## 2. Quantitative Verification

| Index Parameter | Value | Verification Status |
| :--- | :--- | :--- |
| **Index Directory** | `backend/data/indexes/official/` | Verified on disk |
| **Passage Storage** | `meta.pkl` (253 passages, texts & metadata) | Verified |
| **FAISS Index File** | `faiss.index` | Verified |
| **Vector Total (`ntotal`)** | 253 | Matches exactly total child passages |
| **Embedding Dimension (`d`)** | 384 | Matches MiniLM-L12-v2 spec |
| **Embedding Normalization** | L2 normalized (Cosine similarity via IP) | Verified |
| **BM25 Corpus Size** | 253 documents | Verified |

---

## 3. Retrieval Sanity & Regression Smoke Tests

The index was tested with automated queries across both historical and new regulatory provisions:

```
Test Query 1: "What is the minimum attendance requirement?"
  -> Hit 1: SEAS 2017 Clause 30 (70% attendance) [Historical]
  -> Hit 2: Notification 307/2022 (75% attendance) [Current]
  -> Outcome: Both versions retrieved, allowing conflict disclosure.

Test Query 2: "What are the penalties for unfair means during examinations?"
  -> Hit 1: SEAS 2017 Section V (General UFM)
  -> Hit 2: UFM Guidelines 2024 (Specific penalty schedule)
  -> Outcome: High-confidence retrieval of authoritative penalties.

Test Query 3: "What is the role of the Proctorial Committee in student discipline?"
  -> Hit 1: Students' Discipline Rules 2024 Page 4
  -> Hit 2: Students' Discipline Rules 2024 Page 5
  -> Outcome: Grounded extraction of Proctorial inquiry powers.

Test Query 4: "What are the requirements for the award of a B.Tech degree in the First Ordinances?"
  -> Hit 1: First Ordinances Page 16 (Ordinance 4C)
  -> Hit 2: SEAS 2017 Section III
  -> Outcome: Grounded statutory degree criteria.
```

---

## 4. Index Rollback and Versioning Safety

Before index rebuilding, a timestamped backup of the database and index files was created:
- **Backup Path:** `backend/data/backups/m8_pre_refresh_20261116_095304/`
- Contains: `indicrag.db`, `indexes/official/faiss.index`, `indexes/official/meta.pkl`.

