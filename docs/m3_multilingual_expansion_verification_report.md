# M3 Independent Model Verification Report

**Generated:** 2026-11-10 16:42:34
**Total Candidates Evaluated:** 21

**Verifier A:** `qwen2.5:3b`
**Verifier B:** `llama3.2:3b`

## 1. Validation Status Breakdown

| Status | Count | Percentage | Definition |
|---|---|---|---|
| `auto_validated` | **0** | 0.0% | Passed all deterministic checks + dual independent model agreement |
| `auto_rejected` | **14** | 66.7% | Clear fabricated/unmatched quotes, placeholders, or dual rejection |
| `needs_review` | **7** | 33.3% | Model disagreement, ambiguity, warnings, or missing passages |
| `human_verified` | **0** | 0.0% | Human review confirmed (never assigned by automated system) |

## 2. Independent Verifier Agreement Matrix

| Category | Count |
|---|---|
| Both Agree: ACCEPT | 0 |
| Both Agree: REJECT | 4 |
| Both Agree: UNCERTAIN | 0 |
| Verifier Disagreement | 8 |
| Skipped LLM (deterministic reject) | 9 |

## 3. Distribution by Tagged Query Language

| Language | Count | Percentage |
|---|---|---|
| `hi-en` | 11 | 52.4% |
| `hi` | 10 | 47.6% |

## 4. Failure Categories Summary

| Failure Category | Count | Description |
|---|---|---|
| `FABRICATED_OR_UNMATCHED_QUOTE` | 9 | Flagged during verification |
| `VERIFIER_DISAGREEMENT` | 7 | Flagged during verification |
| `DUAL_VERIFIER_REJECTION` | 4 | Flagged during verification |
| `GARBLED_OR_NONSENSE_TEXT` | 1 | Flagged during verification |
| `VERIFIER_UNCERTAINTY` | 1 | Flagged during verification |
