"""
M3 — Dataset Generation Script (Pilot)

Generates candidate QA instances from actual extracted corpus passages
using the local Ollama LLM. All instances are marked PENDING — they must
be human-reviewed before any experiments use them.

Usage:
    python scripts/generate_candidates.py --doc "Academic-Rules-for-SCSET_UG.pdf" --n 3 --max-passages 15
    python scripts/generate_candidates.py --doc "Academic-Calendar-2026-27.pdf" --n 2 --max-passages 11
    python scripts/generate_candidates.py --dry-run   # check Ollama connectivity without generating

Output:
    backend/data/dataset/candidates_<timestamp>.csv
    backend/data/dataset/candidates_<timestamp>_meta.json
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

# Pyarrow shim (must come before sentence_transformers / datasets import)
try:
    import pyarrow.dataset as _pds
    if not hasattr(_pds, "ParquetFragmentScanOptions"):
        _pds.ParquetFragmentScanOptions = type("ParquetFragmentScanOptions", (), {})
except ImportError:
    pass

from app.core.config import settings
from app.core.database import init_db, get_db
from app.core.logging_config import setup_logging, logger
from app.evaluation.dataset import generate_candidate_questions, save_qa_instance


def get_passages_for_doc(filename: str, max_passages: int) -> list[dict]:
    """Fetch child passages for a named document."""
    with get_db() as c:
        doc = c.execute(
            "SELECT document_id, title, academic_year FROM documents WHERE filename = ?",
            (filename,)
        ).fetchone()
        if not doc:
            print(f"ERROR: Document '{filename}' not found in DB.")
            sys.exit(1)

        rows = c.execute(
            "SELECT passage_id, text, page_number, section, heading, chunk_index "
            "FROM passages WHERE document_id = ? AND is_parent = 0 "
            "ORDER BY chunk_index LIMIT ?",
            (doc["document_id"], max_passages),
        ).fetchall()
        return [
            {
                "passage_id": r["passage_id"],
                "text": r["text"],
                "page_number": r["page_number"],
                "section": r["section"],
                "heading": r["heading"],
                "document_id": doc["document_id"],
                "document_title": doc["title"],
                "academic_year": doc["academic_year"],
            }
            for r in rows
        ]


async def check_ollama() -> bool:
    """Check Ollama is reachable and the model exists."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", [])]
            if settings.ollama_model not in models:
                print(f"WARNING: model '{settings.ollama_model}' not in ollama list: {models}")
                print("         Run: ollama pull gemma:2b")
                return False
            print(f"[OK] Ollama running. Model '{settings.ollama_model}' available.")
            return True
    except Exception as exc:
        print(f"ERROR: Ollama not reachable at {settings.ollama_base_url}: {exc}")
        return False


async def main_async(args):
    setup_logging()
    init_db()

    # Connectivity check
    ok = await check_ollama()
    if args.dry_run:
        print("[DRY RUN] Would generate candidates from corpus passages. Exiting.")
        return
    if not ok:
        print("Cannot generate candidates — fix Ollama first.")
        sys.exit(1)

    # Collect passages
    passages = get_passages_for_doc(args.doc, args.max_passages)
    print(f"\nDocument: {args.doc}")
    print(f"Passages to process: {len(passages)}")
    print(f"Questions per passage: {args.n}")
    print(f"Estimated total candidates: {len(passages) * args.n}\n")

    all_instances = []
    total_ok = 0
    total_fail = 0

    for i, passage in enumerate(passages, 1):
        text_preview = passage["text"][:80].replace("\n", " ")
        print(f"[{i}/{len(passages)}] p{passage['page_number']}: {text_preview}...")

        try:
            instances = await generate_candidate_questions(
                passage_text=passage["text"],
                document_id=passage["document_id"],
                passage_id=passage["passage_id"],
                page_number=passage["page_number"],
                section=passage["section"],
                source_document_id=passage["document_id"],
                n_questions=args.n,
                languages=["en", "hi-Latn", "hi-en"],
            )
            if instances:
                for inst in instances:
                    save_qa_instance(inst)
                    all_instances.append(inst)
                print(f"  Generated {len(instances)} candidates.")
                total_ok += len(instances)
            else:
                print("  LLM returned 0 parseable candidates.")
                total_fail += 1
        except Exception as exc:
            print(f"  ERROR: {exc}")
            total_fail += 1

    # Export CSV
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = settings.dataset_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"candidates_{ts}.csv"
    meta_path = out_dir / f"candidates_{ts}_meta.json"

    fieldnames = [
        "question_id", "original_question", "query_language", "query_script",
        "question_type", "answerability", "reference_answer",
        "gold_evidence_quotes", "gold_passage_ids", "source_document_id",
        "page_number", "section", "effective_date", "academic_year",
        "program_applicability", "review_status", "reviewer_notes",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for inst in all_instances:
            row = {
                "question_id": inst.question_id,
                "original_question": inst.original_question,
                "query_language": inst.query_language.value,
                "query_script": inst.query_script.value,
                "question_type": inst.question_type.value,
                "answerability": inst.answerability.value,
                "reference_answer": inst.reference_answer or "",
                "gold_evidence_quotes": json.dumps(inst.gold_evidence_quotes),
                "gold_passage_ids": json.dumps(inst.gold_passage_ids),
                "source_document_id": inst.source_document_id or "",
                "page_number": inst.page_number or "",
                "section": inst.section or "",
                "effective_date": inst.effective_date or "",
                "academic_year": args.doc,  # document filename as proxy
                "program_applicability": json.dumps(inst.program_applicability or []),
                "review_status": inst.review_status.value,
                "reviewer_notes": inst.reviewer_notes or "",
            }
            writer.writerow(row)

    # Metadata
    meta = {
        "generated_at": ts,
        "source_document": args.doc,
        "passages_processed": len(passages),
        "questions_per_passage": args.n,
        "total_candidates": total_ok,
        "generation_failures": total_fail,
        "model": settings.ollama_model,
        "review_status": "ALL PENDING — must be human-reviewed before use in experiments",
        "csv_path": str(csv_path),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Generated: {total_ok} candidates, {total_fail} failures")
    print(f"CSV:  {csv_path}")
    print(f"Meta: {meta_path}")
    print(f"\nNEXT STEP: Open the CSV and manually review each row.")
    print(f"Set review_status to 'approved' or 'rejected' in each row,")
    print(f"then run: python scripts/import_reviewed_dataset.py --file {csv_path.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate candidate QA instances from corpus passages (M3 pilot)."
    )
    parser.add_argument(
        "--doc", default="Academic-Rules-for-SCSET_UG.pdf",
        help="Filename (in data/official) to generate from."
    )
    parser.add_argument(
        "--n", type=int, default=3,
        help="Questions per passage (default: 3)."
    )
    parser.add_argument(
        "--max-passages", type=int, default=15,
        help="Max passages to process (default: 15)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Check connectivity without generating."
    )
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()

