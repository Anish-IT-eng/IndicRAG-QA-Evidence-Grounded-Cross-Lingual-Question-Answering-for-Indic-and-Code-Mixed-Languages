"""
E5 Fixed-Window Chunking Index Builder.

Builds an independent fixed-window retrieval index to compare against
the structure-aware parent-child corpus for experiment E5.

DOES NOT overwrite the official structure-aware index.
Saves to backend/data/indexes/fixed_window/ (faiss.index + meta.pkl).
"""
from __future__ import annotations

import json
import os
import pickle
import sqlite3
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.logging_config import logger
from app.ingestion.pdf_extractor import extract_pages
from app.retrieval.engine import RetrieverIndex

FIXED_INDEX_NAME = "fixed_window"
FIXED_INDEX_DIR = settings.indexes_dir / FIXED_INDEX_NAME
FIXED_INDEX_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE_WORDS = 300
OVERLAP_WORDS = 50

OFFICIAL_DOCS = [
    ("Academic-Rules-for-SCSET_UG.pdf", "b787fd22-eb2f-42ed-9ef7-ef098e5ff8b6"),
    ("Notification-Minimum-Attendance.pdf", "40c366dd-41b2-49f6-b5e4-492a8b5bbe8a"),
    ("Academic-Calendar-2026-27.pdf", "0c174816-3d23-4e47-aef4-8b8579b801d6"),
    ("SEAS-Ordinance-Rules-Regulations-2017.pdf", "b6f9aad0-7a87-432a-bc91-38fe8eaec817"),
]

def build_fixed_window_index() -> Dict[str, Any]:
    print("=" * 80)
    print("E5 — Building Fixed-Window Chunking Comparison Index")
    print("=" * 80)
    print(f"Target index directory: {FIXED_INDEX_DIR}")
    print(f"Fixed Window Params: Chunk Size = {CHUNK_SIZE_WORDS} words, Overlap = {OVERLAP_WORDS} words")

    all_passage_ids: List[str] = []
    all_texts: List[str] = []
    all_metas: List[Dict[str, Any]] = []

    doc_stats = []

    for filename, doc_id in OFFICIAL_DOCS:
        pdf_path = settings.official_docs_dir / filename
        if not pdf_path.exists():
            raise FileNotFoundError(f"Missing official document: {pdf_path}")

        pages = extract_pages(pdf_path)
        print(f"Processing {filename}: {len(pages)} pages extracted.")

        doc_chunks = 0
        for page in pages:
            words = page.text.strip().split()
            if not words:
                continue

            # Fixed stride chunking over page words
            start = 0
            while start < len(words):
                end = min(start + CHUNK_SIZE_WORDS, len(words))
                chunk_words = words[start:end]
                chunk_text = " ".join(chunk_words)

                if len(chunk_text.strip()) >= 30:
                    pid = str(uuid.uuid4())
                    meta = {
                        "document_id": doc_id,
                        "filename": filename,
                        "page_number": page.page_number,
                        "source_type": "official",
                        "chunk_index": doc_chunks,
                        "chunking_strategy": "fixed_window",
                        "word_count": len(chunk_words),
                        "text": chunk_text,
                    }
                    all_passage_ids.append(pid)
                    all_texts.append(chunk_text)
                    all_metas.append(meta)
                    doc_chunks += 1

                if end >= len(words):
                    break
                start += (CHUNK_SIZE_WORDS - OVERLAP_WORDS)

        doc_stats.append({
            "filename": filename,
            "document_id": doc_id,
            "page_count": len(pages),
            "fixed_chunks_count": doc_chunks,
        })
        print(f"  -> Generated {doc_chunks} fixed-window chunks.")

    print(f"\nTotal fixed-window passages generated: {len(all_passage_ids)}")

    # Build the RetrieverIndex in backend/data/indexes/fixed_window
    idx = RetrieverIndex(FIXED_INDEX_NAME)
    idx.add_passages(all_passage_ids, all_texts, all_metas)
    idx.build()

    manifest = {
        "index_name": FIXED_INDEX_NAME,
        "index_dir": str(FIXED_INDEX_DIR),
        "chunking_strategy": "fixed_window",
        "chunk_size_words": CHUNK_SIZE_WORDS,
        "overlap_words": OVERLAP_WORDS,
        "total_passages": len(all_passage_ids),
        "documents": doc_stats,
    }

    manifest_path = backend_dir / "data" / "experiments" / "m5" / "e5_fixed_window_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest written to: {manifest_path}")
    print(f"Index built successfully at {FIXED_INDEX_DIR}")
    return manifest

if __name__ == "__main__":
    build_fixed_window_index()

