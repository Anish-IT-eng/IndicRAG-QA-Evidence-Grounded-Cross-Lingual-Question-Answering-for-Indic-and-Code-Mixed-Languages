"""
Import human-reviewed QA candidates from CSV back into the database.

After manually setting review_status to 'approved' or 'rejected' in the
exported CSV, run this script to persist the decisions.

Usage:
    python scripts/import_reviewed_dataset.py --file candidates_20261110_123456.csv
    python scripts/import_reviewed_dataset.py --file candidates_20261110_123456.csv --dry-run

SAFETY:
  - Only updates review_status and reviewer_notes fields.
  - Never marks a row as approved unless the CSV explicitly says 'approved'.
  - Logs every update — no silent changes.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

try:
    import pyarrow.dataset as _pds
    if not hasattr(_pds, "ParquetFragmentScanOptions"):
        _pds.ParquetFragmentScanOptions = type("ParquetFragmentScanOptions", (), {})
except ImportError:
    pass

from app.core.database import init_db, get_db
from app.core.logging_config import setup_logging, logger
from app.models.schemas import ReviewStatus


VALID_STATUSES = {s.value for s in ReviewStatus}


def main():
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Import human-reviewed QA decisions into the database."
    )
    parser.add_argument(
        "--file", required=True,
        help="CSV filename (in backend/data/dataset/) or absolute path."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without writing to DB."
    )
    args = parser.parse_args()

    csv_path = Path(args.file)
    if not csv_path.is_absolute():
        csv_path = REPO_ROOT / "backend" / "data" / "dataset" / args.file
    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_path}")
        sys.exit(1)

    init_db()

    approved = rejected = requires_revision = skipped_pending = skipped_invalid = updated = corrected = 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"\nProcessing {len(rows)} rows from {csv_path.name}")

    for row in rows:
        qid = row.get("question_id", "").strip()
        if not qid:
            skipped_invalid += 1
            continue

        # Check REVIEWER_APPROVE column first, fallback to review_status
        decision_raw = (row.get("REVIEWER_APPROVE") or "").strip().lower()
        status_raw = (row.get("review_status") or "").strip().lower()
        notes = (row.get("REVIEWER_NOTES") or row.get("reviewer_notes") or "").strip()
        correction = (row.get("REVIEWER_CORRECTION") or "").strip()

        final_status = None
        if decision_raw:
            if decision_raw in ("yes", "approved"):
                final_status = ReviewStatus.APPROVED.value
            elif decision_raw in ("no", "rejected"):
                final_status = ReviewStatus.REJECTED.value
            elif decision_raw in ("revise", "requires_revision"):
                final_status = ReviewStatus.REQUIRES_REVISION.value
            else:
                print(f"  SKIP (invalid REVIEWER_APPROVE '{decision_raw}'): {qid}")
                skipped_invalid += 1
                continue
        elif status_raw:
            if status_raw == ReviewStatus.PENDING.value:
                skipped_pending += 1
                continue
            elif status_raw in VALID_STATUSES:
                final_status = status_raw
            else:
                print(f"  SKIP (invalid status '{status_raw}'): {qid}")
                skipped_invalid += 1
                continue
        else:
            skipped_pending += 1
            continue

        if final_status == ReviewStatus.APPROVED.value:
            approved += 1
        elif final_status == ReviewStatus.REJECTED.value:
            rejected += 1
        elif final_status == ReviewStatus.REQUIRES_REVISION.value:
            requires_revision += 1

        if correction:
            corrected += 1

        print(f"  {final_status.upper():18s}: {qid[:36]}  notes={notes[:40] or '(none)'}{' [CORRECTION]' if correction else ''}")

        if not args.dry_run:
            with get_db() as c:
                if correction:
                    c.execute(
                        "UPDATE qa_instances SET review_status=?, reviewer_notes=?, "
                        "reference_answer=?, updated_at=datetime('now') WHERE question_id=?",
                        (final_status, notes, correction, qid)
                    )
                else:
                    c.execute(
                        "UPDATE qa_instances SET review_status=?, reviewer_notes=?, "
                        "updated_at=datetime('now') WHERE question_id=?",
                        (final_status, notes, qid)
                    )
            updated += 1

    print(f"\nSummary:")
    print(f"  Approved:          {approved}")
    print(f"  Rejected:          {rejected}")
    print(f"  Requires Revision: {requires_revision}")
    print(f"  With Correction:   {corrected}")
    print(f"  Skipped (pending): {skipped_pending}")
    print(f"  Skipped (invalid): {skipped_invalid}")
    if args.dry_run:
        print(f"  [DRY RUN] No changes written.")
    else:
        print(f"  DB rows updated:   {updated}")


if __name__ == "__main__":
    main()

