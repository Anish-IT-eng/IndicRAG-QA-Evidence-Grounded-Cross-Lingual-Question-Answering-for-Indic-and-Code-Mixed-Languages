# Official Document Acquisition Checklist

**Before ingesting ANY document into IndicRAG-QA, complete every item in this checklist.**

---

## Per-Document Checklist

### Step 1 — Find the document
- [ ] Navigated to the official Bennett University website or SCSET page
- [ ] Located the document through an official navigation path (not a search engine result)
- [ ] Confirmed the URL is under `bennett.edu.in` or an authenticated university portal

**Entry points to try:**
- https://www.bennett.edu.in/ → Academics → Regulations
- https://www.bennett.edu.in/departments/scset/ → Downloads or Resources
- https://www.bennett.edu.in/academics/
- Bennett University ERP portal (login required): https://erp.bennett.edu.in/

---

### Step 2 — Verify the document
- [ ] The document has a cover page or header showing its official title
- [ ] The document contains an effective date or academic year (e.g., "2023-24")
- [ ] The document contains the issuing authority (e.g., "Office of the Registrar", "SCSET")
- [ ] Checked whether a newer version exists (look for version number, date, or "supersedes" language)
- [ ] If an older version: noted what it is superseded by (or confirmed it is not superseded)

---

### Step 3 — Download and place
- [ ] Downloaded the PDF using a browser (not a script)
- [ ] Saved the exact URL where you found it (for the `source_url` field)
- [ ] Named the file descriptively: `bennett_btech_regulations_YYYY.pdf`
- [ ] Placed the file in `backend/data/official/`
- [ ] Confirmed the file opens correctly and is not corrupt

---

### Step 4 — Update source_registry.py
- [ ] Added a `SourceEntry` to `OFFICIAL_SOURCES` in `backend/app/ingestion/source_registry.py`
- [ ] Set `filename` to the exact filename saved in Step 3
- [ ] Set `title` to the official document title (from the cover page)
- [ ] Set `source_url` to the exact download URL (even if it may change — record what was used)
- [ ] Set `effective_date` in `YYYY-MM-DD` format (from document)
- [ ] Set `academic_year` (e.g., `"2023-24"`)
- [ ] Set `program_applicability` (e.g., `["B.Tech"]`)
- [ ] Set `is_current=True` ONLY if confirmed this is the current version
- [ ] Set `is_current=False` if known to be superseded; set `superseded_by` to newer filename
- [ ] Set `is_current=None` if currency is unknown
- [ ] Set `verified=True` after completing this entire checklist
- [ ] Set `notes` with any caveats (e.g., "Applies to students admitted 2023 onwards")

---

### Step 5 — Verify ingestion readiness
- [ ] Run: `python scripts/verify_corpus.py --strict`
- [ ] All registered PDFs have matching files
- [ ] No unexpected files in `data/official/`
- [ ] No unverified entries blocking ingestion

---

### Step 6 — Test ingestion
- [ ] Run: `python scripts/ingest_official.py --dry-run`
- [ ] Review the dry-run output for correct title, academic_year, effective_date
- [ ] Run: `python scripts/ingest_official.py`
- [ ] Confirm `ingestion_status=completed` in the output
- [ ] Query the API: `GET http://localhost:8000/documents` — document appears in list
- [ ] Spot-check passages: `GET http://localhost:8000/documents/{id}/passages`
  - Verify page_number matches the actual PDF page
  - Verify section text is correctly extracted

---

## Honesty Rules

**NEVER:**
- Set `verified=True` without personally reading the document
- Set `is_current=True` without checking for newer versions
- Guess an `effective_date` if it is not stated in the document — use `None` and note it
- Claim a passage cites a rule if the passage does not contain that rule
- Add a source URL that you did not use to obtain the document

**WHEN IN DOUBT:**
- Set `is_current=None` (system will warn at query time)
- Set `verified=False` (document will not be ingested until reviewed)
- Add a detailed `notes` field explaining the uncertainty

---

## Target Documents (unverified — research targets only)

The following types of documents are relevant. The exact titles and URLs must be verified by a human before use.

| Type | What to search for | Priority |
|------|-------------------|---------|
| B.Tech Academic Regulations | Main handbook covering attendance, exams, grading, progression | Critical |
| SCSET Program Guidelines | SCSET-specific rules or supplements | High |
| Examination Rules | Separate exam conduct/malpractice/re-exam rules | High |
| Academic Calendar | Semester dates, exam windows, holidays | Medium |
| Grading Policy | Standalone grading/SGPA/CGPA policy | Medium |
| Attendance Rules | Separate attendance condonation notices | Medium |

**Target corpus size for Milestone 1:** 3–5 verified documents.  
**Minimum viable:** 1 verified document (B.Tech Academic Regulations, current year).

---

_Document last updated: 2026-11-02_

