"""
Corpus verification script.

Checks the official/ directory against source_registry.py:
  - Every registered entry should have a file present.
  - Every file present should be registered.
  - Files that are registered but not verified are flagged.
  - Files are SHA-256 hashed and compared against the database if already ingested.

Run:
  python scripts/verify_corpus.py          # full check
  python scripts/verify_corpus.py --strict # exit 1 if any unverified or missing
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

# Ensure Unicode output works on Windows (cmd/PowerShell use cp1252 by default)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Allow running from project root without installing the package
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.ingestion.source_registry import OFFICIAL_SOURCES, SourceEntry


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def main(strict: bool = False) -> int:
    official_dir = REPO_ROOT / "backend" / "data" / "official"
    official_dir.mkdir(parents=True, exist_ok=True)

    actual_files = {f.name: f for f in official_dir.glob("*.pdf")}
    registered   = {e.filename: e for e in OFFICIAL_SOURCES}

    issues: list[str] = []
    warnings: list[str] = []
    ok: list[str] = []

    print("\n" + "=" * 70)
    print("  IndicRAG-QA — Official Corpus Verification")
    print("=" * 70)

    # 1. Registered entries without a file
    for name, entry in registered.items():
        if name not in actual_files:
            issues.append(
                f"MISSING FILE: '{name}' is registered in source_registry.py "
                f"but not present in data/official/"
            )

    # 2. Files present but not registered
    for name in actual_files:
        if name not in registered:
            warnings.append(
                f"UNREGISTERED: '{name}' exists in data/official/ "
                f"but has no entry in source_registry.py"
            )

    # 3. For each file that is both registered AND present:
    for name in set(registered) & set(actual_files):
        entry = registered[name]
        path  = actual_files[name]
        size_kb = path.stat().st_size // 1024
        digest = sha256(path)

        if not entry.verified:
            warnings.append(
                f"NOT VERIFIED: '{name}' is present but verified=False in source_registry.py"
            )
        if entry.is_current is None:
            warnings.append(
                f"UNKNOWN CURRENCY: '{name}' has is_current=None — "
                "confirm whether this is the latest version"
            )
        if not entry.effective_date:
            warnings.append(
                f"NO EFFECTIVE DATE: '{name}' has no effective_date — "
                "check document cover/footer"
            )
        if not entry.source_url:
            warnings.append(
                f"NO SOURCE URL: '{name}' has no source_url — "
                "record where you downloaded it (audit trail)"
            )
        if not entry.academic_year:
            warnings.append(
                f"NO ACADEMIC YEAR: '{name}' has no academic_year"
            )

        # Check against DB if available
        db_hash = _get_db_hash(name)
        if db_hash and db_hash != digest:
            issues.append(
                f"HASH MISMATCH: '{name}' SHA-256 has changed since ingestion. "
                f"Re-ingest with --force or restore the original file."
            )
        elif db_hash and db_hash == digest:
            ok.append(f"HASH OK: '{name}' matches ingested record ({size_kb} KB)")
        else:
            ok.append(f"PRESENT, NOT YET INGESTED: '{name}' ({size_kb} KB)  sha256={digest[:16]}...")

    # Summary
    print(f"\nOfficial corpus directory: {official_dir}")
    print(f"  Registered entries: {len(registered)}")
    print(f"  PDF files found:    {len(actual_files)}\n")

    if not actual_files:
        print("  [CORPUS IS EMPTY]\n"
              "  No PDFs in data/official/.\n"
              "  Run: python scripts/discover_sources.py  to see where to find them.\n")

    if ok:
        print("OK:")
        for line in ok:
            print(f"  [OK]  {line}")

    if warnings:
        print("\nWARNINGS:")
        for line in warnings:
            print(f"  [!]   {line}")

    if issues:
        print("\nERRORS:")
        for line in issues:
            print(f"  [X]   {line}")

    print()
    if issues:
        print("Result: FAILED - resolve the errors above before ingesting.")
        return 1
    elif warnings and strict:
        print("Result: FAILED (--strict) - resolve warnings before ingesting.")
        return 1
    elif warnings:
        print("Result: WARNINGS - review before ingesting, not blocking.")
        return 0
    else:
        print("Result: OK - all registered documents present and verified.")
        return 0


def _get_db_hash(filename: str) -> str | None:
    """Look up the stored hash for this filename from the SQLite DB, if available."""
    try:
        import sqlite3
        db_path = REPO_ROOT / "backend" / "data" / "db" / "indicrag.db"
        if not db_path.exists():
            return None
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT file_hash FROM documents WHERE filename = ? "
            "AND ingestion_status = 'completed' ORDER BY created_at DESC LIMIT 1",
            (filename,),
        ).fetchone()
        conn.close()
        return row["file_hash"] if row else None
    except Exception:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify official corpus integrity.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 on warnings, not just errors.")
    args = parser.parse_args()
    sys.exit(main(strict=args.strict))
