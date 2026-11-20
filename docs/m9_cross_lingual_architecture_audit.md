# Milestone M9: Cross-Lingual Architecture Audit & Component Inspection

**Milestone Identifier:** M9 (Phase A)  
**Role:** Senior Multilingual NLP Architect, RAG Systems Engineer & Research Evaluation Auditor  
**Audit Timestamp:** 2026-11-16T19:10:00+05:30  
**Repository:** `C:\Users\anish\Desktop\IndicRAG-QA`  

---

## 1. Executive Summary

This architecture audit provides a rigorous, line-by-line inspection of IndicRAG-QA's cross-lingual, code-mixed, and multilingual question-answering subsystem as implemented in Milestone M8.8. 

The primary research objective of Milestone M9 is to determine whether IndicRAG-QA can retrieve relevant evidence and generate accurate, grounded, and appropriately cited answers across four query language varieties:
1. **English (EN)**
2. **Hindi in Devanagari script (HI-Deva)**
3. **Romanized Hindi (HI-Latn)**
4. **Hindi-English Code-Mixed / Hinglish (EN-HI Code-Mixed)**

Rather than assuming multilingual capability from non-English query acceptance, this audit examines the actual executed code paths, identifies architectural gaps, and documents operational limits before constructing the evaluation benchmark.

---

## 2. Implemented Architecture & Data Flow

The following sequence diagram details the end-to-end processing pipeline from incoming raw query to final grounded response:

```
[User Query: EN / HI-Deva / HI-Latn / Hinglish]
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          1. Query Preprocessing & Identification        │
│          (backend/app/query/processor.py)               │
├─────────────────────────────────────────────────────────┤
│ • Unicode NFC Normalization                             │
│ • Script Detection (_has_devanagari, _latin_ratio)     │
│ • Language Identification:                              │
│     - Devanagari -> HINDI (QueryScript.DEVANAGARI)      │
│     - Devanagari + Latin (>15%) -> CODE_MIXED (MIXED)   │
│     - Latin + Hinglish Keyword Ratio (>=25%) -> CM      │
│     - Latin + Hinglish Keyword Ratio (>=10%) -> ROM_HI  │
│     - langdetect fallback -> EN / ROM_HI                │
│ • Code-Mixed Lexical Normalization (normalize_code_mix) │
│ • Temporal, Cohort, Programme & Condition Extraction    │
│ • Optional LLM Translation (translate_query_to_english) │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│          2. Adaptive Query Routing                      │
│          (backend/app/retrieval/router.py)              │
├─────────────────────────────────────────────────────────┤
│ • Evaluates language, script, complexity, exact anchors │
│ • Strategies:                                           │
│     - Devanagari + Translation -> TRANSLATION_ASSISTED │
│     - Devanagari (no translation) -> CROSS_LINGUAL_MQR  │
│     - High Complexity / Multi-part -> CROSS_LINGUAL_MQR │
│     - English + Exact Anchors -> BM25_LEXICAL           │
│     - Romanized Hindi (no anchors) -> DENSE_SEMANTIC    │
│     - Default -> HYBRID_RRF                             │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│          3. Multi-Engine Retrieval & Indexing           │
│          (backend/app/retrieval/engine.py)              │
├─────────────────────────────────────────────────────────┤
│ • Dense Semantic Search:                                │
│     - Model: paraphrase-multilingual-MiniLM-L12-v2     │
│     - FAISS IndexFlatL2 (dim 384, 253 vectors)          │
│ • Lexical Search:                                       │
│     - BM25Okapi over tokenized English corpus           │
│ • Fusion & Ranking:                                     │
│     - Reciprocal Rank Fusion (RRF, k=60)                │
│     - Parent Document Retrieval (PDR expansion)         │
│     - Cross-Encoder Reranker: ms-marco-MiniLM-L-6-v2    │
│     - Version Validation (Temporal/Cohort Anchoring)    │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│          4. Regulatory-Aware Evidence Controller        │
│          (backend/app/retrieval/evidence_controller.py) │
├─────────────────────────────────────────────────────────┤
│ • Condition Matching & Partition Isolation              │
│ • Temporal & Cohort Applicability Filtering             │
│ • Consensus Checking & False-Conflict Suppression       │
│ • Claim Grounding & CECI Reliability Scoring            │
│ • Decision: SUFFICIENT / CLARIFICATION / INSUFFICIENT   │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│          5. Evidence-Grounded Answer Generation         │
│          (backend/app/generation/generator.py)          │
├─────────────────────────────────────────────────────────┤
│ • Language Instruction Injection:                       │
│     - EN: "Answer in English."                          │
│     - HI: "कृपया उत्तर हिंदी में दें।"                 │
│     - ROM_HI: "Answer in simple Romanized Hindi."       │
│     - CODE_MIXED: "Answer in Hinglish."                 │
│ • Inference: Local Ollama (gemma:2b / qwen2.5:3b)       │
│ • Citation Parsing & Page-Verification Engine           │
│ • Post-Generation NLI Claim Verification & Abstention   │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Component Status & Classification Matrix

Each architectural component is audited across five technical categories:
1. **Existing Working Components**
2. **Missing Components**
3. **Implemented but Unintegrated Components**
4. **Components with Known Limitations**
5. **Components Requiring No Modification**

| Subsystem | Component | Status | Implementation Details | Audit Notes & Findings |
| :--- | :--- | :--- | :--- | :--- |
| **Language ID** | Heuristic Script Classifier | **Working** | `_has_devanagari()`, `_latin_ratio()` | High reliability on pure Devanagari or mixed Unicode ranges. |
| **Language ID** | Hinglish Keyword Heuristic | **Working** | `_HINGLISH_PATTERNS` regex | 24 core stopwords (`kya`, `hai`, `kitna`, etc.). Effective on common conversational syntax. |
| **Language ID** | `langdetect` Integration | **Working** | Deterministic seed (`seed=42`) | Used as fallback for English and Latin-script Hindi detection. |
| **Language ID** | Neural IndicLID / FastText | **Missing** | Not implemented | The system does NOT run a trained IndicLID neural classifier; relies purely on regex + `langdetect`. |
| **Preprocessing** | NFC Normalizer | **No Mod Needed** | `unicodedata.normalize("NFC")` | Clean, robust standard Unicode normalization. |
| **Preprocessing** | Code-Mixed Normalizer | **Working** | `normalize_code_mixed()` | Expands abbreviations (`exam` -> `examination`, `sem` -> `semester`). |
| **Preprocessing** | Hindi Transliteration | **Implemented / Unintegrated** | Field `romanized_query` in `QueryAnalysis` | `processor.py` line 504 leaves `romanized_query=None` as a placeholder. No active transliteration library (e.g. Indic-Xlit / AI4Bharat) is loaded. |
| **Translation** | LLM Query Translation | **Working / Conditional** | `translate_query_to_english()` | Uses local Ollama `qwen2.5:3b` with zero-shot translation prompt. Only invoked if `enable_translation=True`. |
| **Retrieval Router** | Adaptive Decision Tree | **Working** | `AdaptiveRouter.route()` in `router.py` | Routes Devanagari to `cross_lingual_mqr`, Romanized Hindi to `dense_semantic`, English with exact anchors to `bm25_lexical`. |
| **Retrieval Engine** | Multilingual Dense Retrieval | **No Mod Needed** | `paraphrase-multilingual-MiniLM-L12-v2` | Native 384-dim multilingual embedding model covers 50+ languages including English and Hindi. |
| **Retrieval Engine** | Lexical BM25 Search | **Known Limitation** | `BM25Okapi` | Standard whitespace/word tokenization over English corpus. Zero lexical overlap when queried in Devanagari unless translated or transliterated. |
| **Retrieval Engine** | Reciprocal Rank Fusion | **No Mod Needed** | `_rrf_fuse(k=60)` | Fuses dense and lexical candidate lists. |
| **Retrieval Engine** | Cross-Encoder Reranker | **Known Limitation** | `cross-encoder/ms-marco-MiniLM-L-6-v2` | English-trained cross-encoder. May miscalculate semantic relevance when given Devanagari queries against English passages. |
| **Retrieval Engine** | PDR Parent Expansion | **No Mod Needed** | `expand_to_parents()` | Successfully attaches parent context while preserving child citations. |
| **Controller** | Evidence Controller | **No Mod Needed** | `EvidenceController` (M8.5/M8.8) | Multi-condition isolation, temporal anchoring, false-conflict suppression, CECI scoring. |
| **Generator** | Citation Parser & Validator | **No Mod Needed** | `_extract_citations_from_text()` | Full regex support for `[Source: <uuid>, page X]`, case insensitivity, `page_verified` tracking. |
| **Generator** | Answer Language Steering | **Known Limitation** | `_LANG_INSTRUCTIONS` prompt injection | Prompt instructs `gemma:2b` to reply in Hindi or Hinglish, but 2B parameter models exhibit high variance in code-mixed fluency. |

---

## 4. In-Depth Technical Limitations & Failure Hypotheses

### 4.1 Language Identification (LID) Bottlenecks
- **Short Query Risk:** Short Hinglish queries (e.g., *"75% attendance rule kya hai?"*) contain only 2 Hinglish words (`kya`, `hai`) out of 6 tokens (ratio $0.33 \ge 0.25$), correctly classifying as `CODE_MIXED`. However, queries like *"75% attendance rule bataye"* fail the 24-word keyword list and trigger `langdetect`, which frequently misclassifies short Romanized Hindi as English or other European languages.
- **Transliteration Absence:** Because `romanized_query` remains `None`, BM25 cannot match Romanized Hindi tokens against the English corpus passages. All retrieval burden falls on dense multilingual vector representations.

### 4.2 Cross-Encoder Cross-Lingual Degradation
- The active reranker is `cross-encoder/ms-marco-MiniLM-L-6-v2`. MS MARCO is an English-only passage ranking corpus.
- When query $q$ is in Devanagari (e.g. `उपस्थिति नियम`) and passage $p$ is in English (`The minimum attendance criteria is 70%...`), the cross-encoder attention layers have not been fine-tuned on cross-lingual translation pairs. It may assign disproportionately low reranking scores to relevant English passages, potentially ranking them below irrelevant passages containing random subword overlaps.

### 4.3 Generation and Script Consistency
- While `paraphrase-multilingual-MiniLM-L12-v2` successfully bridges cross-lingual vector spaces for retrieval, the generator model (`gemma:2b`) must synthesize the final answer.
- Asking a 2B parameter model to answer in Devanagari Hindi based solely on English evidence passages requires joint translation and factual summarization. If the model defaults to English or hallucinates transliterated vocabulary, `answer_language_consistency` will penalize it.

---

## 5. Architectural Verdict for Milestone M9

1. **No Destructive Rewrites:** The current architecture contains a fully operational multilingual retrieval backbone (`paraphrase-multilingual-MiniLM-L12-v2` + FAISS + RRF) and a verified Evidence Controller. We do not rewrite or replace working components.
2. **Evaluation Focus:** The evaluation must quantitatively benchmark:
   - Language/script detection accuracy across all four variants.
   - The effect of query normalization and abbreviation expansion.
   - Dense vs. BM25 vs. Hybrid cross-lingual performance.
   - The impact of translation-assisted routing.
   - End-to-end answer correctness, citation validity, and language policy compliance.
