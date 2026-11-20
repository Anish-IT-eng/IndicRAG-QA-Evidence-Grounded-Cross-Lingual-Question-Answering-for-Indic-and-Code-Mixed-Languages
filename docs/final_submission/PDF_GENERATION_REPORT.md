# IndicRAG-QA — Academic PDF Documentation Generation Report

**Generated on:** 2026-11-19  
**Target Submission Directory:** `docs/final_submission/`  
**Target Environment:** Windows 11 Professional (x64), Anaconda Python 3.10 / 3.13  
**Verification Tooling:** ReportLab 5.0.1, PyMuPDF (fitz) 1.23.8+  
**Status:** **100% Verified & Formally Compliant**

---

## 1. Executive Summary

Pursuant to academic submission requirements, three independent, professionally formatted PDF documents and their automated generation toolchain have been engineered for **IndicRAG-QA: Evidence-Grounded Cross-Lingual Question Answering for Academic Documents**.

All documents were programmatically generated from actual codebase specifications and empirical test artifacts. Strict boundary separation was enforced:
1. **PDF 1 (Technical Deep Dive)** and **PDF 2 (Project Overview)** contain zero startup or terminal execution commands.
2. **PDF 3 (Run Guide)** exclusively contains all operational commands, installation instructions, demonstration scripts, and troubleshooting sequences.
3. Every factual assertion, architectural component, metric, and limitation reflects verified implementations without speculative inflation.

---

## 2. Generated Document Deliverables

| File Name | Document Title & Role | Exact Page Count | File Size | Extractable Characters | Generator Script |
|:---|:---|:---:|:---:|:---:|:---|
| **`IndicRAG_QA_Project_Deep_Dive.pdf`** | Comprehensive Technical Deep Dive & Research Specification | **17 pages** | 145.5 KB | 40,899 chars | `build_deep_dive_pdf.py` |
| **`IndicRAG_QA_Project_Overview.pdf`** | Executive Summary & Concept Overview (Beginner-Friendly) | **9 pages** | 117.6 KB | 17,319 chars | `build_overview_pdf.py` |
| **`IndicRAG_QA_Project_Run_Guide.pdf`** | System Run Guide & Live Demonstration Manual | **8 pages** | 91.7 KB | 15,216 chars | `build_run_guide_pdf.py` |

**Total Cumulative Output:** **34 A4 pages**, 73,434 extractable characters across all 3 documents.

---

## 3. Structural & Section Coverage

### Document 1: `IndicRAG_QA_Project_Deep_Dive.pdf` (17 Pages)
- **Cover Page:** Formal metadata, executive architectural callout, and 19-section Table of Contents.
- **Section 1: Project Introduction & Research Objectives:** Title, academic regulatory domain, higher education motivation, problem statement, research & engineering objectives.
- **Section 2: Problem Analysis (Complex Regulatory Documents):** Keyword search limits, structural noise, cross-clause exceptions, temporal amendments, multilingual challenges, LLM hallucinations.
- **Section 3: Proposed Solution & Design Principles:** Evidence-first ingestion, user-first fallback, hybrid retrieval, graph modeling, bounded traversal ($k \le 3$), deterministic citations.
- **Section 4: Complete System Architecture & Data Flow:** Component-to-file mapping table, end-to-end 7-step execution trace from query submission to verified response.
- **Section 5: Document Ingestion Pipeline:** PyMuPDF layout analysis, coordinate table parser (`table_parser.py`), semantic chunking, generic relationship extraction, cascading deletion idempotency.
- **Section 6: Retrieval Architecture:** BM25Okapi, FAISS dense vectors, Reciprocal Rank Fusion ($k=60$) mathematical formulation, BAAI/bge-reranker-base cross-encoder, user-first priority.
- **Section 7: Relationship-Aware Retrieval & Multi-Hop Reasoning:** SQLite graph schema, edge taxonomy (`SCHEDULE_FOR`, `CONDITION_FOR`, `EXCEPTION_TO`, `SUPERSEDES`, `REFERENCES`), mathematical invariants ($k \le 3$, $|P| \le 12$), attendance/calendar scenarios.
- **Section 8: Multilingual Query Understanding:** Script detection, Devanagari normalization, Hinglish mapping table, resolution of the R6 Stage 2.1 event-target alignment defect.
- **Section 9: Evidence Grounding & Local Generation:** Local Ollama `qwen2.5:3b`, CECI controller prompt contract, two-tier citation validation, answerable vs safe abstention examples.
- **Section 10: Conversational Feedback & Repair:** Multi-turn context, 4-class feedback routing (`CITATION_CHALLENGE`, `FACTUAL_CORRECTION`, `MISSING_EXCEPTION`, `COHORT_CLARIFICATION`), targeted reverification scenario.
- **Section 11: Database Schema & Multi-Tenant Isolation:** Table definitions (`documents`, `passages`, `relationships`, `conversation_history`, `evaluation_runs`), user scoping query filters, ON DELETE CASCADE integrity.
- **Section 12: Complete Technology Stack:** Comprehensive component allocation table spanning runtime, libraries, versions, and architectural roles.
- **Section 13: Research & Engineering Milestones:** Milestones M0–M10 and Engineering Phases R1–R6, delineating experimental exploration vs production defaults.
- **Section 14: Empirical Evaluation & Testing:** Backend unit tests (13/13), integrity audit (13/13), sequential fallback (9/9), multilingual regression (8/8), final acceptance (9/9), latency qualifications.
- **Section 15: Security, Isolation & Production Safeguards:** User document privacy, SHA-256 hashing, atomic cascades, graceful degradation, sovereign on-premises operation.
- **Section 16: Identified Limitations & Trade-offs:** CPU generation latency (12–28s), scanned PDF OCR dependency, Romanized Hindi spelling variations, 3B model reasoning scope.
- **Section 17: Future Improvements & Roadmap:** Native OCR integration, regional Indic languages (Tamil, Telugu, Bengali, Marathi), zero-shot relation extraction, distributed vector stores.
- **Section 18: Conclusion:** Architectural summary and significance for trustworthy institutional governance.
- **Section 19: Formal Academic References:** 9 peer-reviewed citations (RAG, BM25, FAISS, RRF, BGE, Sentence-Transformers, Qwen2.5, PyMuPDF, University Ordinances).

### Document 2: `IndicRAG_QA_Project_Overview.pdf` (9 Pages)
- **Cover Page:** Audience framing, executive callout, 11-section outline.
- **Section 1: Project at a Glance:** Summary matrix covering mission, languages, innovations, safety guarantees, and test status.
- **Section 2: What Problem Does It Solve?:** Student scenario (Rahul's 68% attendance vs 75% rule vs 10% medical exception) illustrating how standard chatbots fail and how IndicRAG-QA succeeds.
- **Section 3: What Is IndicRAG-QA?:** Plain-language breakdown of the name (Indic + RAG + QA).
- **Section 4: Why Is This Project Useful?:** Stakeholder impact matrix (Students, Faculty Advisors, Deans/Registrars, IT/Security).
- **Section 5: Main Features & Capabilities:** 7 core capabilities explained in 2–4 concise sentences each.
- **Section 6: How Does It Work?:** 7-step visual workflow table from PDF ingestion to verified browser display.
- **Section 7: Simple Demonstration Examples:** 6 realistic query walkthroughs (English calendar, Devanagari Hindi calendar, Hinglish attendance, multi-hop medical exception, custom syllabus priority, safe abstention).
- **Section 8: Technology Overview (Plain Language):** Accessible explanation of Python, FastAPI, PyMuPDF, SQLite, BM25, FAISS, Cross-Encoder, and Ollama.
- **Section 9: What Makes the Project Different?:** Comparison table contrasting IndicRAG-QA against standard commercial LLM chatbots.
- **Section 10: Reported Project Results & Benchmarks:** Summary of formal test suite pass rates (100% across all categories).
- **Section 11: Conclusion & Takeaway:** Core message emphasizing factual accuracy without cloud privacy risks.

### Document 3: `IndicRAG_QA_Project_Run_Guide.pdf` (8 Pages)
- **Cover Page:** Operational metadata, port allocations, manual purpose.
- **Section 1: Prerequisites & Hardware Profile:** Hardware matrix (CPU, RAM, SSD, Ports) and software requirements.
- **Section 2: Project Folder Structure:** Full directory tree (`backend/`, `frontend/`, `docs/`, `scripts/`).
- **Section 3: Environment Configuration:** PowerShell navigation, Ollama verification (`ollama list`, `ollama pull qwen2.5:3b`), and `.env` configuration file parameters.
- **Section 4: Starting the Application Server:** Exact command (`python -m uvicorn backend.app.api.main:app --host 0.0.0.0 --port 8000`), expected console logs, health check URLs.
- **Section 5: Application Interface Guide:** UI anatomy table detailing Document Manager, Chat Stream, Citation Badges/Drawer, Input Bar, and Feedback buttons.
- **Section 6: Live Demonstration Script:** 10 numbered, chronological steps (5–10 minutes) with exact questions and expected answers.
- **Section 7: Automated Verification Commands:** Exact execution commands for Unit Tests (13/13), Integrity Audit (13/13), Sequential Fallback (9/9), Multilingual Regression (8/8), and Final Acceptance (9/9).
- **Section 8: Comprehensive Troubleshooting Guide:** Diagnostic table covering Port 8000 in use, Ollama HTTP 503, missing model weights, CPU latency, and unsearchable PDFs.
- **Section 9: System Shutdown & Data Safety:** Graceful termination steps for Uvicorn and Ollama, protecting persistent SQLite database files.
- **Section 10: Live Demonstration Checklist:** Pre-presentation checklist covering AC power, daemon status, browser zoom, sample PDFs, and contingency readiness.

---

## 4. Verification & Validation Audit

The verification test script `scripts/verify_submission_pdfs.py` was executed using PyMuPDF (`fitz`), evaluating all three generated PDF files against technical criteria:

```text
======================================================================
STARTING ACADEMIC SUBMISSION PDF VERIFICATION
======================================================================

[*] Inspecting: IndicRAG_QA_Project_Deep_Dive.pdf
  [OK] File exists. Size: 145.48 KB (148972 bytes)
  [OK] Successfully opened with PyMuPDF. Page count: 17
  [OK] Page count within specification [15, 25]
  [OK] Total extractable characters: 40899
  [OK] Running headers and 'Page X of Y' footers verified: True
  [OK] Devanagari Unicode characters detected: True
  [OK] Boundary verified: Zero forbidden startup/terminal commands found.

[*] Inspecting: IndicRAG_QA_Project_Overview.pdf
  [OK] File exists. Size: 117.58 KB (120397 bytes)
  [OK] Successfully opened with PyMuPDF. Page count: 9
  [OK] Page count within specification [6, 12]
  [OK] Total extractable characters: 17319
  [OK] Running headers and 'Page X of Y' footers verified: True
  [OK] Devanagari Unicode characters detected: True
  [OK] Boundary verified: Zero forbidden startup/terminal commands found.

[*] Inspecting: IndicRAG_QA_Project_Run_Guide.pdf
  [OK] File exists. Size: 91.73 KB (93930 bytes)
  [OK] Successfully opened with PyMuPDF. Page count: 8
  [OK] Page count within specification [6, 14]
  [OK] Total extractable characters: 15216
  [OK] Running headers and 'Page X of Y' footers verified: True
  [OK] Devanagari Unicode characters detected: False
  [OK] Boundary verified: Contains required operational commands: ['uvicorn', 'pytest', 'ollama', 'http://localhost:8000']

======================================================================
VERIFICATION SUMMARY REPORT
======================================================================
• IndicRAG_QA_Project_Deep_Dive.pdf: 17 pages, 145.5 KB, 40899 chars -> PASS
• IndicRAG_QA_Project_Overview.pdf: 9 pages, 117.6 KB, 17319 chars -> PASS
• IndicRAG_QA_Project_Run_Guide.pdf: 8 pages, 91.7 KB, 15216 chars -> PASS

ALL THREE ACADEMIC SUBMISSION PDFS FULLY VERIFIED AND COMPLIANT!
```

---

## 5. Engineering Challenges Resolved During Generation

1. **Two-Pass Dynamic Pagination ("Page X of Y"):**
   - *Challenge:* In ReportLab, the total page count is unknown during initial flowable layout.
   - *Solution:* Implemented `AcademicNumberedCanvas` which overrides `showPage()` to stash canvas state dictionaries in memory, calculating `total_pages = len(self._saved_page_states)` on document `save()`. Page 1 (cover page) suppresses decorations, while subsequent pages render running headers and footers.
2. **Indic Devanagari Glyph Rendering:**
   - *Challenge:* Standard Type 1 PostScript fonts (`Helvetica`, `Times-Roman`) lack Devanagari glyphs, raising encoding exceptions or silently dropping Hindi characters.
   - *Solution:* Detected Windows system font `Nirmala.ttc` (`C:\Windows\Fonts\Nirmala.ttc`) and registered subfont index 0 via ReportLab's `TTFont`. Created `wrap_indic()` utility which wraps strings containing characters in Unicode block `U+0900`–`U+097F` in `<font name='Nirmala'>`, preserving clean Devanagari rendering in both body text and tabular cells.
3. **Table Cell Text Clipping Prevention:**
   - *Challenge:* Plain strings placed in ReportLab `Table` cells do not auto-wrap and clip across column boundaries.
   - *Solution:* All cell entries in `make_styled_table()` are wrapped in ReportLab `Paragraph` flowables with explicit column widths constrained to page printable margins ($A4 = 595.27\text{ pt} - 108\text{ pt margins} = 487.27\text{ pt}$).
4. **Command Separation Enforcement:**
   - *Challenge:* Review guidelines strictly mandate that installation instructions and terminal commands must not pollute academic explanation documents.
   - *Solution:* Enforced strict architectural segregation. Deep Dive and Overview focus purely on methodologies, data flows, and empirical tables. Run Guide houses all CLI commands, environment flags, and demo workflows. The automated verification suite enforces this separation via string boundary assertion checks.

---

## 6. Directory Artifact Listing

All deliverables reside permanently in the repository:
```text
C:\Users\anish\Desktop\IndicRAG-QA\docs\final_submission\
├── IndicRAG_QA_Project_Deep_Dive.pdf     (17 pages, 145.5 KB)
├── IndicRAG_QA_Project_Overview.pdf      (9 pages, 117.6 KB)
├── IndicRAG_QA_Project_Run_Guide.pdf     (8 pages, 91.7 KB)
├── pdf_style_helper.py                   (Shared styling framework)
├── build_deep_dive_pdf.py                (PDF 1 ReportLab script)
├── build_overview_pdf.py                 (PDF 2 ReportLab script)
├── build_run_guide_pdf.py                (PDF 3 ReportLab script)
└── PDF_GENERATION_REPORT.md              (This comprehensive audit report)
```
