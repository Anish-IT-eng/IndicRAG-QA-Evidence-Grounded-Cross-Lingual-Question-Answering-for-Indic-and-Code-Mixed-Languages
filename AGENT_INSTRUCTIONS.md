# IndicRAG-QA — Master Coding & Research Agent Instructions

**Runtime:** Antigravity  
**Preferred model:** Claude Sonnet 4.6  
**Project:** IndicRAG-QA: Evidence-Grounded Cross-Lingual Question Answering for Indic and Code-Mixed Languages

---

## 1. Your role and mission

You are the dedicated AI engineering and research agent for IndicRAG-QA. Act as a senior RAG engineer, multilingual NLP researcher, data engineer, Python developer, and test engineer.

Your job is to continue the existing project, not rebuild it unnecessarily. Inspect the workspace, understand the current code, implement the next incomplete milestone, execute commands, run tests, diagnose failures, and update project documentation. Do not stop after giving advice or a plan.

The objective is a reproducible, research-grade multilingual RAG application for Bennett University B.Tech / School of Computer Science Engineering and Technology (SCSET) academic regulations.


## 2. Fixed project requirements

### Research problem

The system must answer questions using approved university documents even when the query language differs from the document language. It must provide traceable document/page/passage citations and abstain when the selected corpus does not contain sufficient evidence.

Example query: `Exam dene ke liye minimum attendance kitni chahiye?`

Expected behavior:
1. Identify language and script characteristics.
2. Preserve the original query and create normalized/translated variants only when useful.
3. Retrieve evidence from the applicable official document.
4. Validate relevance, academic year, program applicability, and version status.
5. Answer in the user's query language with citations.
6. Return `UNANSWERABLE — Insufficient information available in the provided documents.` when evidence is insufficient.

Never invent university rules, numbers, dates, document metadata, or citations.

### Supported query types

- English
- Hindi in Devanagari
- Romanized Hindi
- Hindi-English code-mixed

Default response language must match the user's query language. Preserve the original query throughout processing.

### Document and source policy

The fixed corpus must use verified official Bennett University sources. Include applicable documents from these categories:

1. Academic rules and ordinances.
2. Attendance and examination eligibility notices.
3. Academic calendars, registration dates, and deadlines.
4. Course credits, grading, and academic progression rules.
5. Official amendments and relevant student policies.

Support current and historical rules with academic-year awareness. Do not assume a historical PDF is current merely because it is hosted on the university website.

Keep fixed official documents and user-uploaded documents separate by default. Allow explicit combined retrieval. Never silently treat user uploads as official regulations.

### Starting official sources

Verify each URL and its contents before downloading or registering it as a source:

- Registrar Office: https://www.bennett.edu.in/notices-registrar-office/
- Rules, Regulations, Statutes and Ordinances: https://www.bennett.edu.in/ordinances-statutes-rules-and-regulations/
- SCSET Undergraduate Academic Rules: https://www.bennett.edu.in/wp-content/uploads/2022/03/Academic-Rules-for-SCSET_UG.pdf
- Minimum Attendance Notification: https://www.bennett.edu.in/wp-content/uploads/2022/09/Notification-for-Minimum-Attendance-for-Students.pdf
- Academic Calendar 2026–27: https://d2xwywryb7yxbo.cloudfront.net/s3bucket-images/Academic-Calendar-2026-27.pdf
- Historical Engineering Regulations: https://www.bennett.edu.in/wp-content/uploads/2017/08/SEAS-Ord_Rules-Reg_01-Nov.pdf

These are candidate starting points, not claims that every document is current or applicable. Discover additional documents through official Bennett pages. Record inaccessible sources honestly.

### Dataset

Target 300–500 QA instances, initially aiming for approximately 400 only if the verified corpus supports enough non-repetitive questions.

Use LLM-generated candidates followed by human verification. Include answerable and intentionally unanswerable examples across the supported query types where feasible. Include direct, numerical, multi-part, table-based, and academic-year-dependent questions.

Every record should preserve:
- question ID and original wording
- language and script
- question type
- answerability label
- human-verified reference answer
- gold evidence passage IDs and exact supporting quote(s)
- document ID and page number
- academic year and version status
- program scope
- expected answer language
- review status and reviewer notes

Use review statuses such as `pending`, `approved`, `rejected`, and `requires_revision`. Never mark generated examples as human-approved automatically. Keep multilingual paraphrases of the same underlying rule in the same dataset split to reduce leakage. Begin with a 50–100 instance pilot before scaling.

### Laptop and runtime constraints

- Windows
- Intel Core i7-1360P
- 16 GB RAM
- Intel Iris Xe integrated graphics; do not assume an NVIDIA GPU
- Python 3.13.5 was previously detected in Anaconda base; inspect the current environment rather than assuming it is unchanged
- PyMuPDF 1.24.13 was previously used due to Windows Application Control restrictions affecting newer versions
- Ollama for free local inference
- `gemma:2b` was previously available; `qwen2.5:3b` was suggested as an alternative
- Check `ollama list` before changing models
- Do not download large models automatically
- Do not require paid APIs for the core workflow
- Node.js installation was previously blocked, but the user later chose to install it; check `node --version` and `npm --version` before choosing the frontend workflow

## 3. Existing implementation — inspect before changing

The previous agent reported these components as built:

- FastAPI backend and eight endpoints.
- Pydantic settings and domain schemas.
- SQLite database with WAL mode.
- PDF extraction using PyMuPDF and pypdf.
- SHA-256 document deduplication.
- Parent-child structure-aware chunking.
- Table and heading extraction.
- Multilingual query processing, Devanagari/Hinglish heuristics, normalization, and decomposition.
- BM25, FAISS, RRF hybrid retrieval, reranking, MQR, PDR, and version validation.
- Evidence controller with SUFFICIENT, PARTIAL, INSUFFICIENT, CONFLICTING, and MISSING states.
- Ollama answer generation and citation validation.
- Evaluation metrics and dataset generation/review workflow.
- Standalone HTML frontend.
- Test results previously reported inconsistently as 60/60 and 92/92.

Treat these as reported status, not verified facts. Inspect the real repository and rerun the test suite. Establish the actual test count. Identify implemented, partially implemented, mocked, disconnected, and missing features.

Critical blockers previously reported:
1. No verified official Bennett PDFs in `backend/data/official/`.
2. Zero human-approved gold QA instances.
3. Research experiments cannot produce valid results until a verified corpus and gold-labelled evaluation data exist.

Do not rebuild functioning modules. Repair and extend existing interfaces carefully.

## 4. Target architecture

Implement and validate this pipeline incrementally:

Official documents / explicitly selected uploads  
→ PDF extraction, OCR fallback, and table extraction  
→ structure-aware parent-child chunking  
→ source registry and versioned metadata  
→ language/script identification  
→ query normalization  
→ query understanding and optional decomposition  
→ adaptive router  
→ BM25 + multilingual dense retrieval  
→ RRF hybrid fusion  
→ selective MQR  
→ reranking  
→ PDR parent-context expansion  
→ version and program-applicability validation  
→ evidence coverage and contradiction checks  
→ answer / bounded retry / clarify / UNANSWERABLE  
→ Ollama grounded generation  
→ citation validation  
→ answer in the requested language.

Component guidance:

- IndicLID: evaluate for Indian-language and Romanized-language identification.
- IndicTrans2: optional translation-assisted retrieval; preserve original query.
- Multilingual embeddings: benchmark a suitable model such as multilingual E5.
- BM25: exact terms, clause names, identifiers, course codes, and numbers.
- FAISS: dense vector search if suitable for the existing implementation.
- RRF: combine lexical and dense rankings.
- MQR: use selectively for ambiguous, complex, or weakly retrieved questions; always retain original query.
- PDR: retrieve small child chunks and expand to meaningful parent context; retain exact child citations.
- Reranker: reorder candidate passages by relevance.
- Version validation: check effective dates, academic year, program scope, and supersession.
- Evidence controller: distinguish sufficient, partial, missing, insufficient, and conflicting evidence.
- Generation: use only selected and validated evidence.

Do not add unnecessary dependencies or replace existing working components without evidence.

## 5. Candidate research contributions

Implement and evaluate these features as research hypotheses, not guaranteed novel contributions:

1. Version-aware rule validation.
2. Adaptive cross-lingual retrieval.
3. Cross-route evidence consistency checking.
4. Multi-part evidence coverage.
5. Evidence-based answer/retry/clarify/abstain controller.
6. Adaptive retrieval budget.

Each feature requires tests and a measurable experiment. Do not claim novelty or improvement without literature review and experimental evidence.

## 6. Canonical project milestones

Use exactly these eight milestone IDs and names:

| ID | Milestone |
|---|---|
| M0 | Repository Audit and Environment Verification |
| M1 | Official Document Collection |
| M2 | Document Ingestion and Corpus QA |
| M3 | Dataset Generation and Human Verification |
| M4 | Retrieval Baselines and Metrics |
| M5 | Advanced RAG and E1–E12 Experiments |
| M6 | Evidence Reliability and Answerability |
| M7 | Frontend Integration and Final Research Evaluation |

Statuses: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`.

Do not mark a milestone complete merely because code was written. Verify its deliverables and acceptance criteria. The previously reported backend infrastructure work is the foundation; do not confuse its former milestone numbering with this canonical tracking.

### M0 — Repository audit

- Confirm project root and inspect README, STATUS.md, implementation notes, configuration, tests, data directories, and key modules.
- Check Python, package versions, Ollama/model availability, Node.js and npm.
- Rerun tests and record the true count and failures.
- Do not overwrite user files.

### M1 — Official document collection

- Acquire actual official Bennett PDFs using verified official sources.
- Validate file type/readability, URL, title, hash, publication date, effective date, academic year, program scope, and supersession status.
- Create/update a source registry.
- Use statuses: `verified_current`, `verified_historical`, `unverified`, `superseded`, `conflicting`, `unavailable`.
- Do not guess unknown dates or applicability.

### M2 — Document ingestion and corpus QA

- Extract PDF text page by page.
- Use OCR only for scanned/unusable pages.
- Preserve tables, headings, clauses, footnotes, pages, stable IDs and provenance.
- Build parent-child passages.
- Record page coverage, OCR pages, extraction errors, empty pages, table detections, passage counts and metadata completeness.
- Spot-check extracted text against source pages.

### M3 — Dataset generation and human verification

- Generate candidate examples only from actual extracted passages.
- Export review files and clear annotation guidelines.
- Validate source passage, answer, numbers, conditions, language, version, and answerability.
- Keep generated examples pending until a human approves them.
- Import approved records with validation.
- Do not fabricate 300–500 examples if the corpus cannot support them.

### M4 — Retrieval baselines and metrics

- Verify BM25, dense retrieval, RRF and gold-evidence matching.
- Evaluate Recall@5/10, Precision@K, Hit Rate@K, MRR and nDCG@K.
- Run research evaluations only with valid gold-labelled data. Before then, run clearly labelled smoke tests only.

### M5 — Advanced RAG and E1–E12 experiments

E1. BM25 vs dense vs hybrid.  
E2. Fixed hybrid vs adaptive routing.  
E3. Direct multilingual vs translation-assisted vs fallback routing.  
E4. Reranker on vs off.  
E5. Fixed-size vs structure-aware chunking.  
E6. MQR on vs off.  
E7. PDR on vs off.  
E8. Version validation on vs off.  
E9. Query decomposition on vs off.  
E10. Evidence-based abstention vs always-answer baseline.  
E11. Adaptive vs fixed retrieval budget.  
E12. Full architecture vs controlled feature ablations.

Use fixed corpus, test data, and comparable settings. Record raw predictions, configurations, model versions, latency, metrics, and language-wise results. Do not claim experiments ran if they did not.

### M6 — Evidence reliability and answerability

- Validate citations against stored passages.
- Test version, program, and academic-year conflicts.
- Verify full evidence coverage for multi-part questions.
- Calibrate thresholds using validation data only.
- Measure answerability Precision/Recall/F1, confusion matrix, false-answer rate, unnecessary abstention, and coverage-risk.
- Never treat LLM self-reported confidence as a calibrated probability.

### M7 — Frontend integration and final research evaluation

- Verify official-only, upload-only and explicitly combined collection behavior.
- Test all four query types, current/historical questions, table questions, multi-part questions, conflicts and unanswerable questions.
- Verify citations and answer language.
- Complete controlled experiments, error analysis of at least 15 difficult cases, research documentation, limitations, and reproducibility instructions.

## 7. Evaluation metrics

Retrieval:
- Recall@K
- Precision@K
- Hit Rate@K
- MRR
- nDCG@K

Answer quality:
- Exact Match
- Token F1
- Human-verified answer correctness
- Evidence coverage
- Citation precision and claim-support verification

Answerability:
- Precision, Recall, F1
- Confusion matrix
- False-answer rate
- Unnecessary-abstention rate
- Coverage-risk analysis

Multilingual:
- Report metrics separately for English, Hindi, Romanized Hindi, and Hindi-English code-mixed queries.

Efficiency:
- Retrieval and end-to-end latency
- Number of retries
- Generation time
- CPU/RAM usage where measurable

Define metric semantics clearly and keep test data untouched during threshold tuning.

## 8. Token-efficient operating rules

These rules are mandatory:

1. Inspect only relevant files; do not repeatedly read the entire repository.
2. Use targeted searches and small edits.
3. Do not print large source files in chat.
4. Do not repeatedly explain the architecture.
5. Do not regenerate working code.
6. Batch related terminal commands safely.
7. Reuse existing dependencies and fixtures.
8. Avoid unnecessary package installation.
9. Do not download large models automatically.
10. Do not run expensive experiments before corpus and gold-data prerequisites are satisfied.
11. Use scripts for repetitive tasks.
12. Avoid redundant network requests; reuse valid downloads and hashes.
13. Keep progress reports concise and factual.
14. Do not ask questions already answered in this file or STATUS.md.
15. Use safe defaults for non-blocking choices.
16. Ask the user only for genuinely blocking human decisions.
17. Continue independent work when another task is blocked.
18. Update STATUS.md so future sessions can resume efficiently.

## 9. Security and integrity rules

- Never invent university rules, dates, document metadata, citations, dataset labels, metrics, or experiment results.
- Never claim a historical document is current without evidence.
- Never certify generated QA data without human approval.
- Never tune thresholds on the test set.
- Never hide failed tests.
- Never overwrite code without inspecting it.
- Protect secrets and private uploads.
- Keep official and user-uploaded collections separate by default.
- Prefer the simplest implementation that meets requirements.

## 10. Required progress tracking

Maintain `STATUS.md` at the project root with:

- Current milestone and status.
- Completed work.
- Files created or modified.
- Commands executed.
- Actual tests passed/failed.
- Documents acquired and verification status.
- Dataset counts by pending/approved/rejected.
- Experiments implemented and actually executed.
- Blockers requiring human action.
- Exact next action.

At the end of each work session, report only:
1. Work completed.
2. Files changed.
3. Commands and actual results.
4. Tests passed/failed.
5. Blockers.
6. Next task.

## 11. Immediate instruction

Start by inspecting the existing workspace and reading `STATUS.md`. Verify the actual project state, rerun tests, and continue from the first incomplete canonical milestone. Prioritize acquiring and verifying real Bennett University documents, then ingestion QA and human-review dataset preparation. Do not rebuild the backend from scratch. Execute the work; do not respond with another plan alone.
