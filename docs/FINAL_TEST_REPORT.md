# IndicRAG-QA — Final Test & Verification Report

## 1. Executive Summary

This report documents the verification, regression testing, and end-to-end acceptance testing of the integrated **IndicRAG-QA** system.

All test suites were executed against the full system with the real `qwen2.5:3b` Ollama model and production CrossEncoder reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`).

---

## 2. Test Suites and Granular Results

### 2.1 Backend Unit & Integration Tests (`backend/tests/test_api.py`)
- **Total Tests:** 13
- **Passed:** 13 (100%)
- **Failed:** 0
- **Scope Covered:**
  - `GET /health` API status and passage statistics
  - Root `/` frontend serving and static asset delivery
  - `POST /uploads` PDF ingestion and validation
  - `GET /documents/{document_id}/status` ingestion health tracking
  - `DELETE /documents/{document_id}` cascading deletion and tenant authorization enforcement
  - `POST /query` standard execution, multi-part, cross-lingual normalization, and error handling
  - `POST /feedback` turn repair and feedback classification

### 2.2 Sequential Fallback Engine Tests (`backend/tests/test_sequential_retrieval_fallback.py`)
- **Total Scenarios:** 9
- **Passed:** 9 (100%)
- **Failed:** 0
- **Scenarios Covered:**
  - Scenario 1: User Upload Sufficiency (Stage 1 bypasses official corpus)
  - Scenario 2: User Upload Insufficiency (triggers automatic Stage 2 fallback)
  - Scenario 3: Missing User Uploads (immediate Stage 2 fallback)
  - Scenario 4: Final Institutional Abstention (safe UNANSWERABLE when both stores lack evidence)
  - Scenario 5: Multi-Tenant Data Segregation (User B cannot retrieve User A's uploads)
  - Scenario 6: Combined Multi-Condition Disclosure (both user and official rules cited)
  - Scenario 7: Out-of-Corpus Query Abstention (institutional safety check)
  - Scenario 8: Clarification on Ambiguous Calendar Inquiries
  - Scenario 9: Multi-Hop Regulatory Reasoning Integration

### 2.3 R6 Stage 2.1 Multilingual Regression Suite (`scripts/test_r6_stage2_1_regression.py`)
- **Total Scenarios:** 8
- **Passed:** 8 (100%)
- **Failed:** 0
- **Scenarios Covered:**
  - Query 1: English Calendar Exam Dates (Page 4 End Exams: 10-12-2026 to 22-12-2026)
  - Query 2: Devanagari Hindi Exam Dates (विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?)
  - Query 3: Romanized Hindi Exam Dates (Visham semester ki antim pariksha...)
  - Query 4: Code-Mixed Hinglish Exam Dates (Odd semester examinations ki start date aur end date...)
  - Query 5: Even Semester Registration (Negative test: verifies 28-12-2026 selected, not regular exam dates)
  - Query 6: Ambiguous Query (Prompts for clarification when semester/exam type is unspecified)
  - Query 7: Bounded Hop Depth Invariant ($k \le 3$)
  - Query 8: Strict Evidence Item Invariant ($|P| \le 12$)

### 2.4 End-to-End Acceptance Suite (`scripts/run_final_e2e_acceptance.py`)
- **Total Tests:** 9 (Tests A through I)
- **Status:** PASS
- **Test Matrix:**
  - **Test A: Application Startup, Health Check & Frontend Serving** — Verified `/health` and root `/` serving single-page application.
  - **Test B: User Document Ingestion, Indexing & Upload-Grounded QA** — Verified PDF upload, indexing, and Stage 1 user-document grounding.
  - **Test C: Official Regulatory Document Retrieval & Citation Grounding** — Verified Stage 2 official fallback, 75% attendance rule retrieval, and citation extraction.
  - **Test D: Multilingual Questions** — Verified English, Devanagari Hindi, Romanized Hindi, Hinglish, and Even Semester Registration event selection.
  - **Test E: Insufficient Evidence & Abstention** — Verified safe institutional abstention on out-of-scope drone policy query.
  - **Test F: Multi-Hop Reasoning** — Verified attendance relaxation rules connecting Clause 30.1(v) conditions (10% relaxation, two weeks continuous illness).
  - **Test G: Conversational Feedback & Repair** — Verified feedback classification and turn repair from conversational history.
  - **Test H: Multi-Tenant Security & Cascading Deletion** — Verified tenant isolation (Bob blocked from querying/deleting Alice's doc) and cascading removal.
  - **Test I: Regression Benchmark & Invariant Status** — Verified previous benchmark integrity and regression invariants.

---

## 3. Invariant Verification Summary

| Invariant | Target Boundary | Observed System Behavior | Verdict |
|:---|:---:|:---:|:---:|
| **Max Traversal Depth ($k$)** | $k \le 3$ hops | Traversal strictly terminates at hop 3 | **VERIFIED** |
| **Max Evidence Budget ($|P|$)** | $|P| \le 12$ passages | Reasoner evidence set capped at 12 passages | **VERIFIED** |
| **Tenant Isolation** | Total segregation | Unauthorized cross-tenant queries return 0 citations; deletion returns 403 | **VERIFIED** |
| **Citation Grounding** | 100% cited facts | All factual claims cite filename, page, and clause | **VERIFIED** |
| **Hallucination Prevention** | Zero out-of-corpus fabrication | Unanswerable queries reliably return institutional abstention | **VERIFIED** |
