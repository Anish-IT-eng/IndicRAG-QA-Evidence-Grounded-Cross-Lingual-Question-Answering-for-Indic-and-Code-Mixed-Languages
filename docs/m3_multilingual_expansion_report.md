# M3 Independent Model Verification Report

**Generated:** 2026-11-10 16:02:56
**Total Candidates Evaluated:** 14

**Verifier A:** `qwen2.5:3b`
**Verifier B:** `llama3.2:3b`

## 1. Validation Status Breakdown

| Status | Count | Percentage | Definition |
|---|---|---|---|
| `auto_validated` | **0** | 0.0% | Passed all deterministic checks + dual independent model agreement |
| `auto_rejected` | **10** | 71.4% | Clear fabricated/unmatched quotes, placeholders, or dual rejection |
| `needs_review` | **4** | 28.6% | Model disagreement, ambiguity, warnings, or missing passages |
| `human_verified` | **0** | 0.0% | Human review confirmed (never assigned by automated system) |

## 2. Independent Verifier Agreement Matrix

| Category | Count |
|---|---|
| Both Agree: ACCEPT | 0 |
| Both Agree: REJECT | 0 |
| Both Agree: UNCERTAIN | 5 |
| Verifier Disagreement | 0 |
| Skipped LLM (deterministic reject) | 9 |

## 3. Distribution by Tagged Query Language

| Language | Count | Percentage |
|---|---|---|
| `hi` | 7 | 50.0% |
| `hi-en` | 7 | 50.0% |

## 4. Failure Categories Summary

| Failure Category | Count | Description |
|---|---|---|
| `FABRICATED_OR_UNMATCHED_QUOTE` | 9 | Flagged during verification |
| `VERIFIER_UNCERTAINTY` | 4 | Flagged during verification |
| `GARBLED_OR_NONSENSE_TEXT` | 1 | Flagged during verification |
