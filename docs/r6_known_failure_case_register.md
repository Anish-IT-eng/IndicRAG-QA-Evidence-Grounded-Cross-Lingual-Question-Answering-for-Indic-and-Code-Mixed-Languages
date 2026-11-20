# IndicRAG-QA — R6 Known Failure Case Register

**Document Version:** 1.0  
**Phase:** R6 — Integrated Evaluation & Regression  
**Task:** Task 1 — Existing Benchmark Audit, Evaluation Design & Test Readiness  
**Date:** 2026-11-19  
**Status:** COMPLETE & REGISTERED  

---

## 1. Executive Summary

This register provides a centralized, classified catalog of all known failure modes, edge cases, model vulnerabilities, and historical architectural defects identified across Milestones M3–M10 and Phases R1–R5.

In accordance with R6 integrity guidelines:
- Known failure cases must **never be silently removed** or filtered out of evaluation datasets.
- Each failure mode is assigned an architectural subsystem classification, an impact assessment, an observed manifestation, and an R6 evaluation test case.

---

## 2. Master Failure Case Catalog

| Failure ID | Pipeline Stage | Failure Description | Root Cause / Manifestation | Impact Severity | R6 Evaluation Scenario |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **FAIL-01** | **Generation** | **Devanagari Retrieval Success with Downstream Generation Hallucination** | Multi-hop evidence retrieves correct calendar schedule in Passage 0, but local LLM attends to Passage 1 coordinate row (Make-up Exam in July) due to terminology mismatch in translated prompt. | High | Multilingual Dimension (Intent 1) |
| **FAIL-02** | **Controller / Generation** | **Romanized Hindi (Hinglish) Conservative Abstention** | Query transliteration induces low token overlap with formal regulation text, causing LLM to emit `UNANSWERABLE` despite valid evidence in context. | Medium | Multilingual Dimension (M9 hi-Latn) |
| **FAIL-03** | **Infrastructure / Latency** | **Local CPU Ollama Generation Timeout** | On Windows CPU with high token load, local quantized LLM inference occasionally exceeds HTTP timeout (30s) on long English prompts, returning empty text. | High | Latency & Reliability Dimension |
| **FAIL-04** | **Language Identification** | **Weak Romanized Hindi (hi-Latn) Classification** | Short Romanized Hindi queries containing English loanwords (e.g. *"odd semester exam kab start hoga"*) are misclassified as pure English or generic code-mixed. | Medium | Query Processing Dimension (M9) |
| **FAIL-05** | **Retrieval** | **Low M9 Hit@5 and MRR on Complex Indic Queries** | Pure vector or lexical retrieval struggles with morphological inflection in Hindi without multilingual reranking or script normalization. | High | Retrieval Dimension (M9 Benchmark) |
| **FAIL-06** | **Reasoning / Applicability** | **Incorrect Historical or Cohort Selection** | Unanchored attendance queries return rules without distinguishing whether student is governed by SEAS 2017 Ordinance vs Notification 307/2022. | High | Multi-Hop & Clarification Dimension |
| **FAIL-07** | **Citation / Evidence Selection**| **Incorrect Citation or Page Selection** | Generator cites the document or passage ID of an intermediate reasoning hop instead of the primary rule source page (e.g. citing Page 1 header instead of Page 4 event row). | Medium | Answer & Citation Dimension |
| **FAIL-08** | **Reasoning / Disambiguation**| **Calendar Regular vs Make-up Examination Confusion** | Conflating regular End Semester Examinations (10-12-2026 to 22-12-2026) with Make-up Examinations (18-01-2027) due to lexical similarity. | Critical | Multi-Hop Reasoning (Scenario 1) |
| **FAIL-09** | **Reasoning / Scope** | **Attendance Course Grading vs Exam Eligibility Confusion** | Conflating Clause 30.1 70% per-course attendance (X grade) with Notification 307 75% aggregate attendance (exam debarment). | Critical | Multi-Hop Reasoning (Scenario 2) |
| **FAIL-10** | **Relationship Extraction** | **Relationship-Expansion Graph Noise** | Expanding high-degree nodes (e.g. generic clause headers or document titles) floods the frontier with irrelevant subclauses, crowding out specific rules. | Medium | Traversal & Evidence Boundary |
| **FAIL-11** | **Controller / Abstention** | **False Abstention on Answerable Specific Questions** | Overly aggressive CECI or coverage thresholds ($\tau_{\text{suff}} = 0.65$) rejecting valid answers when queries use non-standard phrasing. | High | Abstention Dimension (FAR Metric) |
| **FAIL-12** | **Controller / Abstention** | **Failure to Abstain on Non-Existent Entities** | Generic university stopwords in queries (e.g. *"university"*, *"students"*) inflating keyword coverage and bypassing abstention on non-existent university policies. | Critical | Abstention Dimension (Test 7) |
| **FAIL-13** | **Conversational Feedback** | **Loss of Preceding Conversation Context during Repair** | Disagreement turn fails to retrieve preceding assistant answer or cited document IDs, falling back to a fresh ungrounded search. | High | Conversational Dimension (R5) |
| **FAIL-14** | **Security / Multi-Tenant** | **Cross-Tenant Document Leakage during BFS Expansion** | Graph frontier expanding relationships from a shared entity into another user's private document due to un-scoped joins. | Critical | Security Dimension (Test 9) |

---

## 3. Deep-Dive Analysis of Primary Failure Modes

### FAIL-01: Devanagari Hindi Downstream Generation Misalignment
- **Pipeline Stage:** Generation / Cross-Lingual Prompting
- **Mechanism:** In Phase R4.1 multilingual evaluation, the Devanagari Hindi query:  
  `"विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?"`  
  successfully retrieved the target schedule passage from Page 4 in `ev_set.all_passages`. However, when passed to the local LLM (`qwen2.5:7b-instruct` / `llama3.1:8b`), the model overlooked Passage 0 and extracted the make-up examination row from Passage 1:  
  `"[Source: passage_id=mhop_syn_rel_e5246064a51c, page 1] Registration for Even Semester Make-up Examination-Start Date is on 01-07-2026."`
- **Root Cause:** Devanagari query prompting creates cross-lingual semantic distraction when synthetic English coordinate table cells are interleaved with formal passages.
- **R6 Evaluation Action:** Benchmark prompt framing and passage ordering in Stage 7 of R6 execution plan.

### FAIL-02: Romanized Hindi (Hinglish) Conservative Abstention
- **Pipeline Stage:** Evidence Controller / Prompting
- **Mechanism:** In Phase R4.1, the query:  
  `"Odd semester end semester exams kab start aur finish hote hain?"`  
  retrieved 13 valid passages including the exact schedule. However, the LLM outputted:  
  `"UNANSWERABLE — Insufficient information available in the provided documents."`
- **Root Cause:** In Hinglish queries, system prompt rule 3 (*"If the evidence does not contain enough information, say: UNANSWERABLE"*) is triggered when the language instruction demands Hinglish response while evidence is English, causing the model to conservatively treat language disparity as evidence absence.
- **R6 Evaluation Action:** Measure false abstention rate ($\text{FAR}$) specifically partitioned by query language.

### FAIL-03: Local Ollama CPU Generation Timeout
- **Pipeline Stage:** Infrastructure & Runtime Reliability
- **Mechanism:** Local Ollama inference on Windows CPU occasionally requires 25–35 seconds for long system prompts with 12 evidence passages. If `httpx.Timeout` or Ollama server socket hangs, the client receives empty text or an error.
- **R6 Evaluation Action:** Implement robust retry and explicit latency capture distinguishing inference timeout from architectural failure.

### FAIL-04 & FAIL-05: M9 Multilingual Retrieval & Routing Degradation
- **Pipeline Stage:** Language Identification & Retrieval
- **Mechanism:** In Milestone M9, Romanized Hindi retrieval achieved Hit@5 of only 0.6167 and MRR of 0.4048 compared to English Hit@5 of 0.9667 and MRR of 0.9417.
- **Root Cause:** Out-of-vocabulary transliterated words fail in BM25 token matching, and English-centric embedding models (`bge-large-en`) fail to align romanized Hindi phonetics with English semantic concepts without query normalization.
- **R6 Evaluation Action:** Measure the exact Delta in M9 Hit@5 between baseline M9 (without relationship expansion) and R6 (with relationship expansion).

### FAIL-08: Calendar Regular vs Make-up Exam Conflation
- **Pipeline Stage:** Multi-Hop Disambiguation
- **Mechanism:** In Milestone M2.1/R2.1, calendar queries asking for "End Semester Examination" frequently returned the start date of Make-up Examinations (`18-01-2027`) or Mid-Term Examinations (`12-10-2026`).
- **Root Cause:** Both events share identical table column headers (`Date`, `Day`, `Type`, `Event`). Without coordinate-aware table extraction and row-level grouping, retrieval models match the word "Examination" to any nearby date.
- **R6 Evaluation Action:** Dedicated verification in Stage 5 multi-hop evaluation.

### FAIL-09: Attendance Course Grading (70%) vs Exam Eligibility (75%)
- **Pipeline Stage:** Scope Compatibility & Contradiction Resolution
- **Mechanism:** Queries asking for "minimum attendance" return conflicting figures without explaining that 70% applies to course passing/grading under the 2017 Ordinance, while 75% applies to exam hall entry under Notification 307/2022.
- **Root Cause:** Both rules are authentic official regulations of Bennett University but govern distinct administrative procedures.
- **R6 Evaluation Action:** Verify that the system assigns `EvidenceStatus.MULTI_CONDITION_DISCLOSURE` and generates dual-policy explanations.

---

## 4. Failure Mode Tracking Matrix for R6

During execution of Phase R6, every query failure must be cross-referenced against this register using the `FAIL-XX` identifier:

```
[Query Execution] -> [Failure Detected] -> [Map to FAIL-01..14] -> [Log in r6_failure_log.csv]
```

Any new, previously unrecorded failure observed during R6 must be documented in a dedicated section with full error traces and input query reproduction scripts.
