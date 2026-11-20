# IndicRAG-QA — M7 Frontend Integration Technical Report

**Document Title:** Frontend Implementation, API Contract Synchronization, and User Experience Verification  
**Milestone:** M7 — Frontend Integration and Final Research Evaluation  
**Phase:** Phase 1 (Frontend Integration & Evidence Transparency)  
**Date:** 2026-11-11  
**Author:** Senior Full-Stack RAG Engineer & Evidence Reliability Specialist  

---

## 1. Integration Overview

Milestone M7 Phase 1 successfully unifies the verified IndicRAG-QA backend with an accessible, high-performance HTML5/JavaScript frontend located at `frontend/index.html`.

The UI implements a transparent evidentiary paradigm: rather than presenting generated answers as unquestionable truths, the interface surfaces backend evidence sufficiency, regulatory version conflicts, and missing information directly to the user.

---

## 2. Component Verification

### A. Query Interface (`#tab-query`)
- **Multilingual Support:** Seamlessly accepts English, Devanagari Hindi, Hinglish, and Romanized Hindi.
- **Corpus Selection Chips:** Toggles between `Official Regulations` (`official`) and `User Uploads` (`upload`), maintaining strict document isolation.
- **Pipeline Controls:** Configurable toggles for Cross-Encoder Reranking, Parent-Document Retrieval (PDR), and Diagnostic Traces.
- **Example Chips:** Provides pre-formulated cross-lingual queries covering attendance, grading, dean condonation, and examination rules.

### B. Evidentiary Presentation Layer
- **Status Pills:** Dynamically styled badges reflecting `answered`, `unanswerable`, `conflicting_versions`, and `clarification_needed`.
- **Evidence State Banners:**
  - `SUFFICIENT`: Clean answer card with citation breakdown.
  - `PARTIAL`: Prominent notice indicating that only a subset of query requirements could be substantiated.
  - `INSUFFICIENT`: Safe abstention notice explaining corpus coverage limitations.
  - `MISSING`: Out-of-corpus warning for policies absent from indexed undergraduate regulations.
  - `CONFLICTING`: Prominent amber discrepancy card detailing competing regulatory instruments.
  - `CLARIFICATION_REQUIRED`: Interactive cohort prompt enabling users to refine queries with one click.

### C. Citation & In-Situ Passage Modal
- Every citation displays the source document, page number, section heading, and quote excerpt.
- Clicking any citation opens the **Passage Inspector Drawer** (`#passage-modal`), showing the complete stored passage from the backend database for full provenance verification.

### D. Document Registry & User Uploads
- **Registry (`#tab-docs`):** Interactively fetches and renders indexed documents with page counts, academic years, and ingestion timestamps.
- **Uploads (`#tab-upload`):** Drag-and-drop PDF upload zone connecting to `POST /uploads`, enforcing document isolation.

---

## 3. Regression & Unit Testing Certification

The integration was verified by a dedicated test module (`backend/tests/test_m7_frontend_api_integration.py`):
- **15 Tests Implemented:** Covering English, Hindi, Hinglish, Romanized Hindi, citation structure, abstention handling, partial evidence, conflicting versions, clarification requests, upload isolation, error states, and Unicode preservation.
- **15/15 Tests Passing:** Verified in automated test runner (`pytest`).
- **Full Suite Regression:** All 197 tests pass across 13 test modules with 0 failures.

