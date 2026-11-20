"""
Official document ingestion runner.

Reads verified entries from source_registry.py and ingests each into the pipeline.
Only ingests entries with verified=True unless --force-unverified is given.

Usage:
  python scripts/ingest_official.py --dry-run      # preview without changes
  python scripts/ingest_official.py                # ingest all verified entries
  python scripts/ingest_official.py --force        # re-ingest even if hash matches
  python scripts/ingest_official.py --file bennett_btech_regulations_2023.pdf

Safety:
  - Skips files not present in data/official/
  - Skips entries with verified=False (unless --force-unverified)
  - Never downloads from URLs — all files must be placed locally
  - SHA-256 deduplication prevents re-processing unchanged files
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import logger, setup_logging
from app.ingestion.pipeline import ingest_pdf
from app.ingestion.source_registry import OFFICIAL_SOURCES, SourceEntry
from app.models.schemas import DocumentSource, DocumentVersionInfo


def ingest_entry(entry: SourceEntry, official_dir: Path, force: bool, dry_run: bool) -> str:
    """
    Ingest a single registry entry.
    Returns: 'ok' | 'skipped_missing' | 'skipped_unverified' | 'skipped_unchanged' | 'error'
    """
    path = official_dir / entry.filename

    if not path.exists():
        logger.warning("File not found — skipping: %s", path)
        return "skipped_missing"

    if not entry.verified:
        logger.warning(
            "Entry '%s' has verified=False — skipping. "
            "Set verified=True in source_registry.py after manual review.",
            entry.filename,
        )
        return "skipped_unverified"

    version_info = DocumentVersionInfo(
        effective_date=entry.effective_date,
        academic_year=entry.academic_year,
        program_applicability=entry.program_applicability or [],
        superseded_by=entry.superseded_by,
        supersedes=entry.supersedes,
        is_current=entry.is_current,
        notes=entry.notes,
    )

    if dry_run:
        print(f"  [DRY RUN] Would ingest: {entry.filename}")
        print(f"            title:          {entry.title}")
        print(f"            academic_year:  {entry.academic_year}")
        print(f"            effective_date: {entry.effective_date}")
        print(f"            is_current:     {entry.is_current}")
        print(f"            source_url:     {entry.source_url}")
        return "dry_run"

    try:
        doc = ingest_pdf(
            pdf_path=path,
            source_type=DocumentSource.OFFICIAL,
            source_url=entry.source_url,
            title=entry.title,
            description=entry.description,
            version_info=version_info,
            force=force,
        )
        status = doc.ingestion_status.value
        logger.info(
            "Ingested %s — status=%s, pages=%s, id=%s",
            entry.filename, status, doc.page_count, doc.document_id,
        )
        return status
    except Exception as exc:
        logger.exception("Ingestion error for %s: %s", entry.filename, exc)
        return "error"


def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Ingest verified official Bennett University documents."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview ingestion without making changes.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-ingest even if the file hash has not changed.",
    )
    parser.add_argument(
        "--force-unverified", action="store_true",
        help="Ingest entries with verified=False. NOT RECOMMENDED.",
    )
    parser.add_argument(
        "--file", metavar="FILENAME",
        help="Ingest only the entry with this filename.",
    )
    args = parser.parse_args()

    official_dir = REPO_ROOT / "backend" / "data" / "official"

    if not args.dry_run:
        init_db()

    entries = OFFICIAL_SOURCES
    if args.file:
        entries = [e for e in entries if e.filename == args.file]
        if not entries:
            print(f"ERROR: No entry in source_registry.py for filename='{args.file}'.")
            sys.exit(1)

    if not args.force_unverified:
        unverified = [e for e in entries if not e.verified]
        if unverified:
            print(
                f"\nSkipping {len(unverified)} unverified entries "
                f"(use --force-unverified to override):"
            )
            for e in unverified:
                print(f"  ⚠  {e.filename}  — {e.notes[:80]}")
        entries = [e for e in entries if e.verified]

    if not entries:
        print(
            "\nNo verified entries to ingest.\n"
            "Add and verify documents in source_registry.py first.\n"
            "See: python scripts/discover_sources.py\n"
        )
        sys.exit(0)

    print(f"\nIngesting {len(entries)} entries from {official_dir}\n")
    results: dict[str, int] = {}
    for entry in entries:
        print(f"  → {entry.filename}")
        status = ingest_entry(entry, official_dir, args.force, args.dry_run)
        results[status] = results.get(status, 0) + 1

    print(f"\nResults: {results}")

    if results.get("error", 0) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
