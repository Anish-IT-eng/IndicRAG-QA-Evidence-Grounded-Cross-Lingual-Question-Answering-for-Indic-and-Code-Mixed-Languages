# IndicRAG-QA — Phase R4.1.1: Evidence-Boundary and Benchmark Reporting Clarification

**Status:** `R4_1_1_VERIFIED`  
**Execution Date:** 2026-11-19  
**Scope:** Investigation of Evidence Limit Inconsistency, Total Evidence Invariant Enforcement, and Rigorous Latency Distribution Clarification  
**Benchmark Invariant:** All frozen milestone artifacts (M3–M10) preserved without modification  
**Production Retrieval Invariant:** M10 Production Reranker (`rerank_strategy: str = "production"`) preserved as active default  

---

## 1. Executive Summary

Phase R4.1.1 provides a targeted investigation and resolution for the remaining evidence-count discrepancy identified in the R4.1 audit and provides full mathematical transparency for the benchmark latency measurements.

1. **Evidence Boundary Resolved:** The apparent violation where Test 1 reported $|P| = 13$ against a configured limit of `max_evidence_items = 12` was traced to Step 3b (`Special Calendar Multi-Hop Schedule Linking`), where a canonical schedule passage was prepended at index 0 after the Step 3 BFS loop had already populated 12 passages. An unconditional tail-clamping invariant was added to `MultiHopReasoner.reason()`, strictly enforcing $|P| \le 12$ across all queries.
2. **Latency Statistics Clarified:** The raw benchmark timing samples from `scripts/benchmark_r4_performance.py` were audited. The reported mean (6,736 ms) and standard deviation (4,431 ms) included the initial cold-start model-loading run (14,658 ms). When evaluated separately, the **steady-state warm retrieval latency ($N=4$) is $4,755.64 \pm 175.75\text{ ms}$**, and multi-hop graph BFS reasoning is **$104.53 \pm 8.39\text{ ms}$** (~2.15% overhead). The mathematical degeneracy of $p95$ on small sample sizes ($N=5$) is formally documented.
3. **Verification:** All 14 checks in `scripts/test_r4_comprehensive.py` pass cleanly with strict adherence to `|P| <= 12`.

---

## 2. Investigation of the Evidence Limit

### 2.1 The Observed Inconsistency
In the Phase R4.1 audit report, Test 1 reported:
- `max_evidence_items = 12`
- `|P| = 13` passages retrieved

### 2.2 Trace Analysis & Item Categorization
Inspection of `backend/app/retrieval/multi_hop_reasoner.py` and diagnostic execution of Test 1 revealed the exact 13 items returned:

| Index | Passage ID | Retrieval Method | Category | Page | Document | Score |
| :---: | :--- | :--- | :--- | :---: | :--- | :---: |
| 1 | `cal_full_sched_0c174816` | `multi_hop_calendar_schedule` | **Special Calendar Schedule (Step 3b)** | 4 | `Academic-Calendar-2026-27.pdf` | 0.980 |
| 2 | `9b7c06be-aac0-4401-82a7-4...` | `hybrid` | **Initial Seed Passage (Step 1)** | 4 | `Academic-Calendar-2026-27.pdf` | 7.705 |
| 3 | `1ef0ccfc-0e11-4406-a880-a...` | `hybrid` | **Initial Seed Passage (Step 1)** | 4 | `Academic-Calendar-2026-27.pdf` | 7.480 |
| 4 | `18df7c3d-8ae4-4297-9e6a-8...` | `hybrid` | **Initial Seed Passage (Step 1)** | 5 | `Academic-Calendar-2026-27.pdf` | 7.473 |
| 5 | `d8178353-051f-4126-8882-0...` | `hybrid` | **Initial Seed Passage (Step 1)** | 5 | `Academic-Calendar-2026-27.pdf` | 7.340 |
| 6 | `4947b921-5b6f-4636-b78b-d...` | `hybrid` | **Initial Seed Passage (Step 1)** | 4 | `Academic-Calendar-2026-27.pdf` | 7.208 |
| 7 | `mhop_syn_rel_d7b86b6374ac` | `multi_hop_1` | **Coordinate Table Cell (Step 3)** | 4 | `Academic-Calendar-2026-27.pdf` | 0.425 |
| 8 | `mhop_syn_rel_7e34f9b99b7f` | `multi_hop_1` | **Coordinate Table Cell (Step 3)** | 4 | `Academic-Calendar-2026-27.pdf` | 0.425 |
| 9 | `mhop_syn_rel_5ff9c5f7f835` | `multi_hop_1` | **Coordinate Table Cell (Step 3)** | 4 | `Academic-Calendar-2026-27.pdf` | 0.425 |
| 10 | `mhop_syn_rel_69b153d3eb98` | `multi_hop_1` | **Coordinate Table Cell (Step 3)** | 4 | `Academic-Calendar-2026-27.pdf` | 0.425 |
| 11 | `mhop_syn_rel_e70fe9d959c5` | `multi_hop_1` | **Coordinate Table Cell (Step 3)** | 4 | `Academic-Calendar-2026-27.pdf` | 0.425 |
| 12 | `mhop_syn_rel_2bfe8aa561ad` | `multi_hop_1` | **Coordinate Table Cell (Step 3)** | 4 | `Academic-Calendar-2026-27.pdf` | 0.425 |
| 13 | `mhop_syn_rel_3edfd00e0532` | `multi_hop_1` | **Coordinate Table Cell (Step 3)** | 4 | `Academic-Calendar-2026-27.pdf` | 0.425 |

### 2.3 Category Breakdown
- **Initial Seed Passages (Step 1):** 5 passages
- **Coordinate-Level Table Cells (Step 3):** 7 synthetic passages
- **Canonical Calendar Schedule Linking (Step 3b):** 1 passage
- **Relationship-Expanded Text Passages:** 0 passages
- **Duplicates or Overlapping Records:** 0 (all 13 passage IDs are distinct)
- **Total:** $5 + 7 + 1 = 13$ items

### 2.4 Root Cause
1. In Step 1, hybrid retrieval populated `all_passages` with $k = 5$ seed passages.
2. In Step 3, the BFS traversal while loop executed with the guard `while current_hop <= self.max_hops and len(all_passages) < self.max_evidence_items:`. Inside the relationship loop, `if len(all_passages) >= self.max_evidence_items: break` correctly halted expansion when `len(all_passages)` reached 12 ($5 \text{ seed} + 7 \text{ table cells}$).
3. In Step 3b, the calendar schedule linker executed `all_passages.insert(0, rp_cal)` unconditionally. Because Step 3b did not trim `all_passages` back to `max_evidence_items`, the list expanded to $12 + 1 = 13$.

---

## 3. Actual Boundary Definition & Implementation Fix

### 3.1 Formal Boundary Invariant
The parameter `max_evidence_items = 12` represents the **strict upper bound on the total evidence passages** delivered by `MultiHopReasoner` to the Evidence Controller and Generator, preventing context overflow in local LLMs:

$$\forall Q, \quad |\text{ev\_set.all\_passages}| \le \text{max\_evidence\_items} \quad (\text{default } 12)$$

### 3.2 Implementation Corrections
Two targeted corrections were applied to `backend/app/retrieval/multi_hop_reasoner.py`:

1. **Step 3b Tail-Clamping:**
   ```python
   all_passages.insert(0, rp_cal)
   if len(all_passages) > self.max_evidence_items:
       all_passages = all_passages[:self.max_evidence_items]
   ```
   When the canonical schedule passage is inserted at index 0 (score 0.980), the lowest-scoring trailing expansion (score 0.425) is dropped.

2. **Terminal Invariant Guard:**
   Immediately prior to returning `MultiHopEvidenceSet`:
   ```python
   if len(all_passages) > self.max_evidence_items:
       all_passages = all_passages[:self.max_evidence_items]
   ```

3. **Query Intent Disambiguation:**
   Refined `is_calendar_query` to prevent false positive triggers on general attendance queries (e.g., questions mentioning `"examination eligibility"` without date intent):
   ```python
   is_calendar_query = (
       any(w in q_lower for w in ["calendar", "schedule", "when"])
       or ("date" in q_lower and ("exam" in q_lower or "semester" in q_lower))
   )
   ```

### 3.3 Regression Test Verification
In `scripts/test_r4_comprehensive.py`, Test 1 now explicitly asserts the evidence boundary:
```python
within_boundary = len(ev_set.all_passages) <= reasoner.max_evidence_items
t1_pass = has_start and has_end and has_page and has_event_name and within_boundary
```
- **Test 1 Result:** `passages_retrieved: 12`, `boundary_enforced: true`, `status: PASS`.
- **Test 2 Result:** `evidence_passages: 12`, `status: PASS`.
- **Test 10 Result:** `verified_count: 12`, `status: PASS`.

---

## 4. Latency Statistics Clarification

### 4.1 Raw Timing Samples
The exact raw execution times from the benchmark task (`scripts/benchmark_r4_performance.py`, run on Windows CPU with `ms-marco-MiniLM-L-6-v2` / `bge-reranker-large`) are:

| Run Number | Run Type | Retrieval Latency ($T_{\text{ret}}$) | Graph Reasoning Latency ($T_{\text{reason}}$) | Total Pipeline Latency ($T_{\text{total}}$) |
| :---: | :---: | :---: | :---: | :---: |
| **Run 1** | **Cold Start** | **14,658.85 ms** | **114.60 ms** | **14,773.47 ms** |
| **Run 2** | Warm | 4,942.23 ms | 103.17 ms | 5,045.41 ms |
| **Run 3** | Warm | 4,733.57 ms | 100.16 ms | 4,833.73 ms |
| **Run 4** | Warm | 4,531.66 ms | 98.13 ms | 4,629.80 ms |
| **Run 5** | Warm | 4,815.08 ms | 116.66 ms | 4,931.75 ms |

### 4.2 Sample Count & Cold-Start Impact
- **Total Samples Executed:** 5
- **Cold-Start Samples:** 1 (Run 1)
- **Warm Samples:** 4 (Runs 2, 3, 4, 5)

**Did the previously reported mean and standard deviation include the cold run?**  
**YES.** The previous report computed `statistics.mean()` across all 5 runs:
$$\text{Mean} = \frac{14,658.85 + 4,942.23 + 4,733.57 + 4,531.66 + 4,815.08}{5} = 6,736.28\text{ ms}$$
Including Run 1 (cold start) inflated the reported mean by $+1,980.64\text{ ms}$ and caused an artificial standard deviation of $4,431.36\text{ ms}$.

### 4.3 Rigorous Statistical Breakdown

When evaluated correctly by separating cold-start from steady-state warm runs:

| Statistical Metric | Steady-State Warm ($N=4$, Runs 2–5) | Combined Set ($N=5$, Runs 1–5) | Cold Start (Run 1) |
| :--- | :---: | :---: | :---: |
| **Retrieval Mean** | **4,755.64 ms** | 6,736.28 ms | 14,658.85 ms |
| **Retrieval Std Dev** | **175.75 ms (3.7% variance)** | 4,431.36 ms | — |
| **Retrieval Min / Max** | 4,531.66 ms / 4,942.23 ms | 4,531.66 ms / 14,658.85 ms | 14,658.85 ms |
| **Reasoning Mean** | **104.53 ms** | 106.54 ms | 114.60 ms |
| **Reasoning Std Dev** | **8.39 ms** | 8.52 ms | — |
| **Reasoning Min / Max** | 98.13 ms / 116.66 ms | 98.13 ms / 116.66 ms | 114.60 ms |
| **Total Pipeline Mean** | **4,860.17 ms** | 6,842.83 ms | 14,773.47 ms |
| **Reasoning Overhead Ratio** | **2.15%** | **1.56%** | **0.78%** |

### 4.4 Mathematical Validity of p95 on Small Sample Sizes
- **Exact Sample Set for p50 (Median):** For $N=5$, sorted sample index 2 (4,815.08 ms). For warm $N=4$, average of indices 1 and 2 (4,774.33 ms).
- **Exact Sample Set for p95:** Calculated via `int(0.95 * len(s)) = int(0.95 * 5) = 4` (index 4, the maximum element: 14,658.85 ms).
- **Statistical Validity:** **A 95th percentile ($p95$) is NOT statistically meaningful with $N=5$ (or $N=4$).** At $N=5$, $p95$ degenerates mathematically to the sample maximum. A statistically robust estimate of $p95$ requires at least $N \ge 20$ samples (and ideally $N \ge 100$). Reporting $p95 = 14,658.85\text{ ms}$ merely identifies the single cold-start maximum, not a steady-state tail quantile.

---

## 5. Preservation & Non-Regression Checklist

- [x] **R1, R2, R2.1, R3, R4, R5 Intact:** 21,840 table cells, 7,714 relationships, and conversational answer repair verified.
- [x] **M10 Production Reranker Default:** `settings.rerank_strategy == "production"` active across all runs.
- [x] **Frozen Milestones Untouched:** No modifications made to M3–M10 benchmark artifacts.
- [x] **Evidence Limits Preserved:** Limit not artificially expanded; strict $k \le 12$ bound enforced.
- [x] **Zero Hardcoding:** No document filenames or specific dates hardcoded in generic traversal routines.
- [x] **Tenant Isolation:** Enforced and verified across all queries.

---

## 6. Deliverables Index

1. **Evidence Boundary Clarification Report:** [docs/r4_1_1_evidence_boundary_clarification.md](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/r4_1_1_evidence_boundary_clarification.md)
2. **Updated Audit Document:** [docs/r4_1_final_consistency_audit.md](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/r4_1_final_consistency_audit.md)
3. **Updated Test Results JSON:** [docs/r4_test_results.json](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/r4_test_results.json)
4. **Updated Comprehensive Test Suite:** [scripts/test_r4_comprehensive.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/scripts/test_r4_comprehensive.py)
5. **Multi-Hop Reasoner Core:** [backend/app/retrieval/multi_hop_reasoner.py](file:///c:/Users/anish/Desktop/IndicRAG-QA/backend/app/retrieval/multi_hop_reasoner.py)

---

## 7. Final Sign-off

Phase R4.1.1 closes all outstanding evidence-boundary and statistical reporting ambiguities.

**Final Status:** **`R4_1_1_VERIFIED`**  
Execution is complete. Phase R6 will not be initiated.
