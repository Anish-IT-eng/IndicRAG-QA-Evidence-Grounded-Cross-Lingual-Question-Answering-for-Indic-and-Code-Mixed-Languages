# M10 Phase H — Failure Mode & Bottleneck Analysis

**Project:** IndicRAG-QA — Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages  
**Milestone:** M10 — Multilingual Reranker Optimization & Devanagari Retrieval Recovery  
**Phase:** H — Cross-Lingual End-to-End Answer Quality, Citation & Grounding Audit  
**Date:** November 17, 2026  
**Status:** Audit Complete — Target Determination: `M10_PHASE_H_VERIFIED_WITH_LIMITATIONS`  

---

## 1. Failure Taxonomy & System Breakdown

Out of the 240 queries evaluated on the frozen M9 benchmark under Config B (`E6b_ADAPTIVE_BI_ENCODER`), 117 answerable queries resulted in unnecessary abstentions, and 2 unanswerable queries failed to cleanly abstain.

Every error and abstention was categorized into four mutually exclusive failure classes:

| Failure Category | Failure Code | Affected Queries | Proportion of Failures | Primary Root Cause |
|---|---|---:|---:|---|
| **Upstream Retrieval Miss** | `FAIL-RET` | 115 queries | 95.8% | Gold passage not present in top-5 candidate pool. |
| **Evidence Controller False Abstention** | `FAIL-CTRL` | 2 queries | 1.7% | Gold passage retrieved in top-5, but CECI fell below threshold. |
| **Unanswerable False Answer / False Premise** | `FAIL-UNANS` | 2 queries | 1.7% | Failure to abstain on out-of-scope or false-premise queries. |
| **Citation Page Boundary Shift** | `FAIL-CIT` | 1 query | 0.8% | Passage chunk spans multiple pages in source PDF. |

---

## 2. Category 1: Upstream Retrieval Misses (`FAIL-RET`, $N=115$)

The dominant bottleneck in the end-to-end pipeline remains upstream passage retrieval:
- **Hindi Devanagari:** Dense bi-encoder retrieved gold passages for only 4 out of 45 answerable queries (Hit@5 = 8.89%). For the remaining 41 queries, lexical divergence and script barrier prevented the English-heavy index from surfacing relevant clauses.
- **Romanized Hindi & Hinglish:** While BM25 and Latin cross-encoding achieve higher recall, fine-grained regulatory queries with low lexical overlap (e.g., specific fee refund slabs or proctorial committee composition) fail to rank in top-5.

### Representative Case: `M9-Q006` (`hi`)
- **Query:** *"कोर्स में X ग्रेड मिलने से बचने के लिए न्यूनतम कितनी उपस्थिति चाहिए?"*
- **Expected Passage:** `f88ec726-74ba-426f-a01f-4b9665c1a8b8` (SCSET Clause 30.1)
- **Observed Behavior:** The dense bi-encoder retrieved general examination regulations passages, ranking Clause 30.1 at rank 14. Consequently, the top-5 pool lacked sufficient evidence, and the pipeline correctly abstained.

---

## 3. Category 2: Evidence Controller False Abstentions (`FAIL-CTRL`, $N=2$)

In exactly 2 Devanagari queries, Config B successfully placed the gold passage into the top-5 retrieval candidate pool, yet the pipeline abstained:

### Case 1: `M9-Q010` (`hi`) — Attendance Requirement for Sessional Exams
- **Query:** *"सत्रीय परीक्षाओं के लिए उपस्थिति की क्या आवश्यकता है?"*
- **Retrieved Evidence:** Top-5 included passage `0280358a-ff3c...` (Notification 307/2022) at rank 3.
- **Controller Behavior:** CECI Score = $0.2640$ (below the $0.3500$ sufficiency threshold).
- **Explanation:** The cross-encoder used for entailment scoring (`cross-encoder/ms-marco-MiniLM-L-6-v2`) evaluates cross-attention between the Devanagari query and English passage. The cross-script token interaction produces depressed logit scores, resulting in a false-negative sufficiency classification.

### Case 2: `M9-Q014` (`hi`) — Minimum Attendance for Grade Improvement
- **Query:** *"ग्रेड सुधार परीक्षा में बैठने के लिए क्या न्यूनतम उपस्थिति अनिवार्य है?"*
- **Retrieved Evidence:** Top-5 included passage `f88ec726-74ba...` at rank 4.
- **Controller Behavior:** CECI Score = $0.2980$ (below threshold).
- **Explanation:** Same cross-lingual cross-attention penalty.

---

## 4. Category 3: Unanswerable False Answers (`FAIL-UNANS`, $N=2$)

Out of 60 unanswerable queries, 58 abstained correctly ($96.67\%$). Two queries failed to produce clean abstentions:

### Case 1: `M9-Q201` (`en`) — Law School Weekday Uniform
- **Query:** *"What is the mandatory uniform or dress code for School of Law students on weekdays?"*
- **Expected Status:** `UNANSWERABLE` (No SOL dress code policy exists in official documents).
- **Observed Status:** `answered`
- **Root Cause:** The retriever matched general University Conduct rules regarding "observing decorum in dress code while in academic blocks". The generator synthesized an answer based on this general rule rather than recognizing the school-specific absence.

### Case 2: `M9-Q229` (`en`) — Adversarial False-Premise Query
- **Query:** *"Why is 50% attendance allowed for final examinations at Bennett University?"*
- **Expected Status:** `UNANSWERABLE` (False premise: 50% is never allowed).
- **Observed Status:** `conflicting_versions`
- **Root Cause:** The system retrieved the 75% rule and attempted to refute the 50% premise in prose. However, because '50' was absent in the evidence, the post-generation verification module flagged a numerical discrepancy, returning a regulatory conflict warning instead of an outright unanswerable classification.

---

## 5. Category 4: Citation Page Boundary Shift (`FAIL-CIT`, $N=1$)

### Case: `M9-Q053` (`en`) — Grade Moderation Committee
- **Cited Passage:** `018a0c03-a8cb-46c1-a787-00875eb20a6a`
- **Cited Page:** Page 24
- **Database Page:** Page 23
- **Root Cause:** Chunking boundary split the paragraph across pages 23 and 24. While the information is factually verified, the single-integer `page_number` field in the database points to page 23.

---

## 6. Bottleneck Prioritization for Future Milestones

| Rank | Bottleneck | System Component | Impact | Recommended Solution in M11 |
|---|---|---|---|---|
| **1** | Cross-lingual Devanagari retrieval recall | Retrieval (Bi-Encoder) | 41/45 missed queries | Contrastive cross-lingual bi-encoder fine-tuning or transliteration-augmented BM25. |
| **2** | Cross-attention score depression on Indic queries | Evidence Controller | 2/45 false abstentions | Multilingual NLI cross-encoder or calibrated script-specific CECI thresholds. |
| **3** | School-specific negative scope detection | Generator / Controller | 1 unanswerable failure | Negative scope detector for specific school circulars. |
| **4** | Multi-page chunking boundary page attribution | Document Ingestion | 1 page mismatch | Page range attribution (`pages: [23, 24]`) in passage schema. |
