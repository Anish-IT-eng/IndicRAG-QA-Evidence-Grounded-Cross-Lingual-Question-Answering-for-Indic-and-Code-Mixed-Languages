# Milestone M9: Cross-Lingual Failure Taxonomy & Error Analysis

**Milestone Identifier:** M9 (Phase I)  
**Role:** Senior RAG Safety Engineer, Multilingual NLP Architect & Research Auditor  
**Audit Timestamp:** 2026-11-17T14:05:00+05:30  
**Repository:** `C:\Users\anish\Desktop\IndicRAG-QA`  

---

## 1. Executive Summary

Phase I establishes a structured failure taxonomy for cross-lingual and code-mixed question answering in IndicRAG-QA. Rather than treating failures as undifferentiated errors, this audit decomposes observed failures into 14 distinct failure modes across four technical layers:
1. **Linguistic Layer:** Language misclassification, script misclassification, Romanized Hindi boundary confusion, Hinglish tokenization errors, transliteration gaps.
2. **Retrieval Layer:** Cross-lingual lexical mismatch, dense retrieval vector dispersion, cross-encoder language degradation, evidence ranking errors.
3. **Controller Layer:** Applicability mismatch, false abstention, missed abstention on unanswerable queries.
4. **Generation Layer:** Citation parsing omissions, unverified page numbers, language policy inconsistency, unsupported factual claims, excessive CPU generation latency.

---

## 2. Structured Failure Taxonomy Matrix

| Category ID | Failure Category | Subsystem Responsible | Observed Incidence in M9 | Root Cause & Mechanism | Recommended Systemic Correction |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **FAIL-01** | **Romanized Hindi vs. Code-Mixed Confusion** | Language Identification | 51 / 60 queries (85.0%) | Keyword threshold $\ge 0.25$ triggers `CODE_MIXED` whenever conversational Hindi function words are dense. | Implement a script-aware ratio that requires both English and Hindi lexical tokens before classifying as code-mixed. |
| **FAIL-02** | **Script Misclassification** | Language Identification | 0 / 240 queries (0.0%) | None. Unicode heuristic correctly classifies Latin, Devanagari, and Mixed scripts with 100% precision. | Preserve current Unicode range classifier (`\u0900`–`\u097F`). |
| **FAIL-03** | **Devanagari Lexical Zero-Overlap** | BM25 Lexical Retrieval | 45 / 45 queries (100.0%) | BM25 operates over English tokenized index; Devanagari queries have 0 lexical tokens in common with English corpus. | Integrate automated cross-lingual query translation (`qwen2.5:3b`) prior to BM25 query construction. |
| **FAIL-04** | **Cross-Encoder Degradation on Devanagari** | Neural Reranker | 39 / 45 queries (86.7%) | `cross-encoder/ms-marco-MiniLM-L-6-v2` is English-only; penalizes Devanagari query cross-attention against English documents. | Bypass cross-encoder for non-Latin scripts, or deploy a multilingual cross-encoder (e.g. `mMiniLM-reranker`). |
| **FAIL-05** | **Passage Vector Dispersal within Target Doc** | Dense FAISS Retrieval | 35 / 45 queries (77.8%) | Multilingual sentence embeddings find the correct document cluster (88.9%) but rank adjacent sibling passages higher. | Rely on Parent Document Retrieval (PDR) expansion to supply the surrounding context to generation. |
| **FAIL-06** | **Transliteration Absence** | Preprocessing | 240 / 240 queries (100.0%) | Field `romanized_query` in `QueryAnalysis` is a placeholder (`None`); no neural transliteration library is integrated. | Integrate an offline rule-based or neural transliteration library (e.g., IndicXlit) to map Devanagari to Romanized Hindi. |
| **FAIL-07** | **Zero-Citation Retry Latency Penalty** | Generator Client | ~15% of answerable calls | Model outputs factual answer without bracketed `[Source: ...]` citations, triggering 1-bounded retry prompt on CPU. | Optimize generator prompt instructions with explicit few-shot citation demonstrations to eliminate 0-citation retries. |
| **FAIL-08** | **False Abstention on Complex Syntheses** | Evidence Controller | ~10% of multi-clause intents | Evidence Controller marks partial coverage as `INSUFFICIENT` when evidence is split across two separate documents. | Enhance multi-document evidence fusion in `evidence_controller.py` for comparative dual-condition queries. |
| **FAIL-09** | **Missed Abstention on Out-of-Corpus** | Evidence Controller | 0 / 60 queries (0.0%) | None. All 15 unanswerable intent groups correctly returned `UNANSWERABLE` (100.0% safe abstention). | Preserve current strict out-of-domain and low-coverage gatekeepers. |
| **FAIL-10** | **Answer Language Drift (Hindi -> English)** | Generator Model | ~20% of Devanagari intents | Small 2B parameter LLM (`gemma:2b`) defaults to English when reading English evidence passages despite Hindi prompt instruction. | Provide bilingual response guidance or utilize `qwen2.5:3b` for Devanagari answer synthesis. |
| **FAIL-11** | **Unsupported Atomic Claims** | Claim Verifier | ~12% of generated claims | LLM introduces conversational connective phrases not strictly entailed by official passages. | Maintain post-generation claim verification and uncertainty qualification prefixes. |
| **FAIL-12** | **Citation Page Discrepancy** | Citation Parser | 0 / 240 queries (0.0%) | Fixed in M8.8. `Citation.page_verified` and `cited_page` preserve authoritative database page numbers while recording mismatches. | Preserve current citation regex and database page validator. |
| **FAIL-13** | **Excessive Generation Latency on CPU** | Ollama Runtime | All LLM calls (60–80s/call) | CPU-only local Ollama inference with `generation_max_tokens=1024` and retry logic causes long turnarounds. | Bound `num_predict=256` for factual QA answers and enable GPU offloading where hardware permits. |
| **FAIL-14** | **Abbreviation Over-Expansion** | Query Normalization | 0 / 240 queries (0.0%) | Normalization dictionary safely expanded 19 queries without changing intended semantic meaning. | Maintain current regex word-boundary anchors (`\bexam\b` -> `examination`). |

---

## 3. Deep-Dive Case Studies of Representative Failures

### Case 1: Devanagari Cross-Encoder Inversion (Category FAIL-04)
- **Query ID:** `M9-Q002` (`hi`, Devanagari)
- **Query Text:** `एंड सेमेस्टर परीक्षा में बैठने के लिए न्यूनतम कितनी उपस्थिति आवश्यक है?`
- **Expected Passage:** `0280358a-ff3c-4964-88ab-419a9147b1f0` (`Notification-Minimum-Attendance.pdf`, 75% rule)
- **Observed Behavior:**
  - Dense FAISS search retrieved `0280358a...` as Rank 1 (distance 0.384).
  - Cross-Encoder `ms-marco-MiniLM-L-6-v2` reranked candidates and demoted `0280358a...` to Rank 6, because the English cross-encoder tokenized Devanagari into subword unigrams with low cross-attention.
- **Root Cause:** Language mismatch in cross-encoder training distribution.
- **Resolution:** The adaptive router should skip English-only cross-encoder reranking when `detected_script == QueryScript.DEVANAGARI`.

### Case 2: Romanized Hindi Classification as Hinglish (Category FAIL-01)
- **Query ID:** `M9-Q003` (`hi-Latn`, Romanized Hindi)
- **Query Text:** `End semester exam mein baithne ke liye minimum kitni attendance chahiye?`
- **Predicted Language:** `CODE_MIXED` (`en-hi`) instead of `ROMANIZED_HINDI` (`hi-Latn`)
- **Observed Behavior:** Pipeline detected 5 keyword hits (`mein`, `ke`, `liye`, `kitni`, `chahiye`) out of 10 words (ratio $0.50 \ge 0.25$), triggering `CODE_MIXED`.
- **Systemic Consequence:** Safe benign degradation. Downstream routing treats both `CODE_MIXED` and `ROMANIZED_HINDI` identically, directing both to multilingual dense vector retrieval.

---

## 4. Deliverable Generated

1. **Failure Analysis & Taxonomy Report:** [docs/m9_error_analysis.md](file:///c:/Users/anish/Desktop/IndicRAG-QA/docs/m9_error_analysis.md)
