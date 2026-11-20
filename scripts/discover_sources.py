"""
Official Bennett University document discovery tool.

PURPOSE
-------
This script ONLY helps you locate and verify official sources.
It does NOT download PDFs automatically.

Automatic download of university documents is disabled because:
  1. Bennett University does not publish a stable machine-readable document index.
  2. URLs change without notice between academic years.
  3. Provenance must be manually confirmed before ingestion.
  4. Ingesting an unverified or superseded document would corrupt the corpus.

WORKFLOW
--------
1. Run:  python scripts/discover_sources.py
   This prints a checklist of known public entry points and
   the fields you must fill in source_registry.py for each document.

2. Open each URL in a browser.
3. Locate the official PDF.
4. Download it manually and save to:  backend/data/official/<filename>
5. Fill in OFFICIAL_SOURCES in source_registry.py with:
     - exact filename you saved
     - source_url  (URL where you found it — for audit trail)
     - effective_date (from the document cover page or footer)
     - academic_year (e.g. "2023-24")
     - is_current  (True only if you've confirmed it is the latest version)
     - verified = True  (only after you've read the document and confirmed it)
6. Run:  python scripts/verify_corpus.py
   This will hash-check files and warn about metadata gaps.

KNOWN PUBLIC ENTRY POINTS (as of October 2026 — verify before using)
---------------------------------------------------------------------
These are starting points only. Always navigate to the official page and
confirm the document date before downloading.

  1. Bennett University main website:
       https://www.bennett.edu.in/

  2. SCSET (School of Computer Science Engineering and Technology) page:
       https://www.bennett.edu.in/departments/scset/

  3. Bennett University Examination / Academics section:
       Search for "Academic Regulations", "B.Tech Handbook",
       "Examination Rules", "Grading Policy" on the university portal.

  4. Bennett University student portal (login required):
       https://erp.bennett.edu.in/  (or the current ERP URL)
       Documents are sometimes accessible only after login.

  5. NAAC / NIRF disclosures (may contain regulations as appendices):
       https://www.bennett.edu.in/accreditation/

WHAT TO LOOK FOR
----------------
Look for PDFs titled (or similar to):
  - "Academic Regulations"
  - "B.Tech Ordinances"
  - "B.Tech Student Handbook [Year]"
  - "Examination and Assessment Policy"
  - "Attendance Rules"
  - "Grading Scheme"
  - "SCSET Academic Guidelines"

VERIFICATION CHECKLIST FOR EACH DOCUMENT
-----------------------------------------
Before setting verified=True in source_registry.py:
  [ ] Document title matches official university letterhead or portal name
  [ ] Document contains an effective date or academic year on its cover/footer
  [ ] Document has not been superseded (check for "supersedes" or "replaces" language)
  [ ] Page numbers are preserved correctly after ingestion (spot-check 3 pages)
  [ ] SHA-256 hash recorded in source_registry.py matches the downloaded file
  [ ] Source URL is the direct PDF link (not a search result page)

EXAMPLE source_registry.py entry (fill this in yourself):

    SourceEntry(
        filename="bennett_btech_regulations_2023.pdf",   # exact saved filename
        title="Bennett University B.Tech Academic Regulations 2023-24",
        description="Academic regulations governing B.Tech programs. Covers "
                    "attendance (≥75%), examination, grading, promotion.",
        source_url="https://www.bennett.edu.in/path/to/document.pdf",
        effective_date="2023-07-01",    # from document header
        academic_year="2023-24",
        program_applicability=["B.Tech"],
        is_current=True,               # only True if you've confirmed no newer version
        verified=True,                 # only True after manual review
        notes="Downloaded from official SCSET page. Covers all B.Tech branches."
    ),

INTEGRITY NOTES
---------------
- NEVER mark verified=True without personally reading the document.
- NEVER set is_current=True without checking the university portal for newer versions.
- If in doubt, set is_current=None (unknown) — the system will warn at query time.
- The file SHA-256 is recorded at ingest time; re-run verify_corpus.py to confirm
  the file has not changed since ingestion.
"""

import sys
from pathlib import Path

DISCOVERY_GUIDE = [
    {
        "label": "Bennett University Main Website",
        "url": "https://www.bennett.edu.in/",
        "what_to_find": "Navigate to Academics -> Regulations or SCSET -> Downloads",
    },
    {
        "label": "SCSET Department Page",
        "url": "https://www.bennett.edu.in/departments/scset/",
        "what_to_find": "Look for 'Student Handbook', 'Academic Regulations', 'B.Tech Program Guide'",
    },
    {
        "label": "Bennett University Examination / Academics",
        "url": "https://www.bennett.edu.in/academics/",
        "what_to_find": "Examination policy, grading scheme, attendance rules",
    },
    {
        "label": "NAAC / NIRF Disclosures",
        "url": "https://www.bennett.edu.in/accreditation/",
        "what_to_find": "Appendices may include academic regulations",
    },
]

REQUIRED_FIELDS = [
    "filename       — exact filename you saved in data/official/",
    "title          — official document title from cover page",
    "source_url     — the exact URL where you downloaded the PDF",
    "effective_date — YYYY-MM-DD from document cover/footer",
    "academic_year  — e.g. '2023-24'",
    "is_current     — True only if you confirmed it is the latest version",
    "verified       — True only after you have read and confirmed the document",
    "notes          — any scope caveats (e.g. 'only applies to 2023 batch onwards')",
]


def main():
    # Ensure stdout can handle Unicode on Windows (e.g. cmd.exe uses cp1252)
    import sys, io
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    elif sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("\n" + "=" * 70)
    print("  IndicRAG-QA — Official Document Discovery Guide")
    print("=" * 70)
    print("\nThis tool DOES NOT download documents automatically.")
    print("You must manually locate, verify, and download each PDF.\n")

    official_dir = Path(__file__).parent.parent / "backend" / "data" / "official"
    existing = list(official_dir.glob("*.pdf"))
    print(f"Current official corpus ({official_dir}):")
    if existing:
        for f in existing:
            size_kb = f.stat().st_size // 1024
            print(f"  ✓  {f.name}  ({size_kb} KB)")
    else:
        print("  [EMPTY — no PDFs found]")

    print("\n" + "-" * 70)
    print("Known public entry points to check:")
    for entry in DISCOVERY_GUIDE:
        print(f"\n  [{entry['label']}]")
        print(f"  URL: {entry['url']}")
        print(f"  Find: {entry['what_to_find']}")

    print("\n" + "-" * 70)
    print("Required source_registry.py fields for each document you download:")
    for field in REQUIRED_FIELDS:
        print(f"  • {field}")

    print("\n" + "-" * 70)
    print("After downloading, run:")
    print("  python scripts/verify_corpus.py")
    print("  python scripts/ingest_official.py --dry-run")
    print("  python scripts/ingest_official.py")
    print()


if __name__ == "__main__":
    main()
