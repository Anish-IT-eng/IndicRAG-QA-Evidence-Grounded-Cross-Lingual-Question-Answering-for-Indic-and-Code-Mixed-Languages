# IndicRAG-QA — R6 Stage 2.1 Implementation Report: Multilingual Event Alignment Repair

## 1. Executive Summary

During R6 Stage 2 integrated smoke testing, the Devanagari Hindi query:
```text
विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?
```
incorrectly returned an event from Page 1 (Even Semester Make-up Examination Registration, 01-07-2026) rather than the official Odd Semester End Semester Examinations from Page 4 (10-12-2026 to 22-12-2026) of `Academic-Calendar-2026-27.pdf`.

Under **Stage 2.1: Multilingual Event Alignment Repair**, a root cause investigation was conducted and an end-to-end architectural repair was implemented across query analysis, multi-hop reasoning, evidence filtering, and response generation.

Both the primary smoke test suite and an 8-scenario comprehensive regression suite were executed and verified:
- **R6 Stage 2 Integrated Smoke Test Suite:** **3 / 3 Scenarios Passed (100%)**
- **R6 Stage 2.1 Regression Evaluation Suite:** **8 / 8 Scenarios Passed (100%)**

---

## 2. Root Cause Analysis Summary

Detailed findings documented in `docs/r6_stage2_1_root_cause_analysis.md`:
1. **Query Normalization Gap:** Hindi lexical tokens (`विषम सेमेस्टर`, `अंतिम परीक्षाएं`) lacked institutional calendar entity grounding, causing sparse BM25 retrieval to retrieve early-calendar events (Page 1) due to superficial lexical overlap (`सेमेस्टर`, `परीक्षाएं`).
2. **Distractor Passage Interference in Context Window:** Evidence sets contained irrelevant distractor events (make-up exams, practical exam start/end dates, announcements). On quantized local LLMs (`qwen2.5:3b`), competing dates (such as practical exam end dates or July registration dates) caused attention drift and date conflation.
3. **Term Coverage False Abstention on Romanized Hindi:** In `multi_hop_reasoner.py`, term coverage was computed solely against the original query with English regex `\b[a-zA-Z]{3,}\b`. For Romanized Hindi words (`visham`, `pariksha`), English stopword filtering and doc matching resulted in 0% overlap, falsely triggering `coverage < 0.50` and spurious abstention.
4. **Citation Truncation and Slug Inconsistencies:** The small local model occasionally emitted truncated UUIDs or semantic slugs (e.g., `[Source: EventSchedule_OddSemesterEndSemExam, page 4]`), which previously failed strict UUID validation, triggering fallback abstentions.

---

## 3. Architecture & Code Changes

### A. Academic Event Intent Resolver (`backend/app/query/event_resolver.py`)
- Created a multilingual institutional event resolver supporting English, Devanagari Hindi, Romanized Hindi, and Hinglish.
- Identifies event categories (`End Semester Examination`, `Make-up Examination`, `Mid-Term Examination`, `Practical Examination`, `Registration`).
- Distinguishes semester scopes (`Odd Semester` vs. `Even Semester`) and flags under-specified queries as ambiguous.

### B. Query Processor Integration (`backend/app/query/processor.py`)
- Canonicalizes academic calendar queries into standardized English representations while strictly preserving original query text, detected language, and script provenance.

### C. Multi-Hop Reasoner Distractor Pruning (`backend/app/retrieval/multi_hop_reasoner.py`)
- **Schedule Synthesis (`cal_full_sched_...`):** Extracts unified date range intervals (`10-12-2026` to `22-12-2026`) from the SQLite relationship store and prioritizes them as top evidence.
- **Distractor Filtering:** Prunes scope-mismatched events (e.g., excluding make-up exam passages and practical exams when regular end-semester exams are requested, and excluding July 2026 make-up registration when regular even-semester registration is requested).
- **Multilingual Term Coverage Guard:** Evaluates term coverage against `normalized_query` when the detected query language is non-English, completely eliminating false abstentions on Romanized Hindi and Hinglish.

### D. Grounded Generator & Robust Citation Validation (`backend/app/generation/generator.py`)
- **Prefix & Substring UUID Matching:** Matches truncated UUID citations (down to 8 hex characters).
- **Semantic Slug Matching:** Maps semantic headings (e.g., `EventSchedule_OddSemesterEndSemExam`) back to the underlying retrieved passage.
- **Direct Prompt Guidance:** Enforces complete sentence formatting with explicit date requirements and mandatory `[Source: passage_id, page X]` placement, avoiding token runaway or empty date fields.
- **CPU Latency Budgeting:** Capped `num_predict` to 256 tokens and set per-request HTTP client timeouts to prevent Ollama CPU latency stalls.

---

## 4. Test Results & Verification

### 4.1 R6 Stage 2 Integrated Smoke Test Suite (`scripts/run_r6_stage2_smoke.py`)

| Scenario | Query | Detected Lang | Passages Ret. / Hops | Answer Extract | Citation Provenance | Status | Latency |
|---|---|---|---|---|---|---|---|
| **1. English** | When do odd semester end semester examinations start and finish? | English (Latin) | 11 / 1 hop | `10-12-2026` to `22-12-2026` | `Academic-Calendar-2026-27.pdf`, Page 4 | **PASS** | 20.0s |
| **2. Devanagari Hindi** | विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं? | Hindi (Devanagari) | 11 / 1 hop | `10-12-2026` to `22-12-2026` | `Academic-Calendar-2026-27.pdf`, Page 4 | **PASS** | 12.1s |
| **3. Code-Mixed Hinglish** | Odd semester examinations ki start date aur end date kya hai? | Code-Mixed (Latin) | 11 / 1 hop | `10-12-2026` to `22-12-2026` | `Academic-Calendar-2026-27.pdf`, Page 4 | **PASS** | 10.1s |

**Smoke Test Result:** **3 / 3 PASSED (100%)**

---

### 4.2 R6 Stage 2.1 Regression Suite (`scripts/test_r6_stage2_1_regression.py`)

Detailed run records recorded in `docs/r6_stage2_1_test_results.json`:

| # | Scenario | Query | Passages / Bound | Key Verification | Citation | Status | Total Latency |
|---|---|---|---|---|---|---|---|
| **1** | English Odd Semester Exam | When do odd semester end semester examinations start and finish? | 11 / $\le 12$ | Contains `10-12-2026`, `22-12-2026`; Excludes `25-01-2027`, `01-07-2026` | Page 4 | **PASS** | 32.1s |
| **2** | Devanagari Hindi Exam | विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं? | 11 / $\le 12$ | Contains `10-12-2026`, `22-12-2026`; Excludes `25-01-2027`, `01-07-2026` | Page 4 | **PASS** | 12.0s |
| **3** | Romanized Hindi Exam | Visham semester ki antim pariksha kab shuru aur samapt hoti hai? | 11 / $\le 12$ | Contains `10-12-2026`, `22-12-2026`; Excludes `25-01-2027`, `01-07-2026` | Page 4 | **PASS** | 10.0s |
| **4** | Code-Mixed Hinglish Exam | Odd semester examinations ki start date aur end date kya hai? | 11 / $\le 12$ | Contains `10-12-2026`, `22-12-2026`; Excludes `25-01-2027`, `01-07-2026` | Page 4 | **PASS** | 10.1s |
| **5** | Make-up Examination | When are the odd semester make-up examinations held? | 11 / $\le 12$ | Contains `2027` (`18-01-2027` / `25-01-2027`); Excludes regular exam range | Page 5 | **PASS** | 11.6s |
| **6** | Even Semester Registration | When does registration for even semester start? | 6 / $\le 12$ | Contains `28-12-2026`; Excludes `10-12-2026` & `01-07-2026` | Page 5 | **PASS** | 9.2s |
| **7** | Ambiguous Query | When are the examinations? | 11 / $\le 12$ | Properly abstains (`UNANSWERABLE`) rather than guessing | None (abstained) | **PASS** | 32.3s |
| **8** | Strict Citation Provenance | What are the start and finish dates for Odd Semester End Semester Examinations 2026-27? | 11 / $\le 12$ | Contains `10-12-2026`, `22-12-2026`; Valid citations strictly from Page 4 | Page 4 | **PASS** | 13.9s |

**Regression Suite Result:** **8 / 8 PASSED (100%)**

---

## 5. Invariants & Constraint Verification

1. **Reranker Architecture Invariant:** The production `CrossEncoder` model remained continuously active and loaded (`cross_enc.__class__.__name__ == 'CrossEncoder'`). No fallback or baseline degradation was introduced.
2. **Evidence Boundaries:** Every single scenario strictly honored the configured evidence boundary $|P| \le 12$ and hop limit $k \le 3$.
3. **Model & Hardware Invariants:** Zero paid APIs were called. Local `qwen2.5:3b` via Ollama was used exclusively without downloading additional models.
4. **Dataset Freezing Invariant:** Zero frozen benchmark datasets or baseline snapshots were modified. All Tier 1 and Tier 2 cryptographic hashes remain intact.
5. **Clean Repository:** All temporary debug and scratch scripts created during analysis have been deleted.

---

## 6. Sign-Off & Stage Gate Status

- **Stage 1 (Integrity Audit):** Verified and Passed (13/13 artifacts).
- **Stage 2 (Smoke Testing):** Verified and Passed (3/3 queries).
- **Stage 2.1 (Multilingual Event Alignment Repair):** Verified and Passed (8/8 regression queries).
- **Gate Status:** Execution is halted. Antigravity will NOT proceed to Stage 3 until explicit user authorization is provided.
