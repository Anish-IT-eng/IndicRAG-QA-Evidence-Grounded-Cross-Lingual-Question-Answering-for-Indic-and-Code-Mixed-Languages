"""
Audit script for M6 Phase 2A verification outcomes and qualification analysis.
"""
import csv
import json
import sqlite3
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "backend"
csv_path = backend_dir / "data" / "dataset" / "m6_expanded_benchmark_n60.csv"
jsonl_path = backend_dir / "data" / "dataset" / "m6_candidate_verification.jsonl"
reconcil_path = backend_dir / "data" / "dataset" / "m6_candidate_reconciliation.csv"
db_path = backend_dir / "data" / "db" / "indicrag.db"

with open(csv_path, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

with open(jsonl_path, "r", encoding="utf-8") as f:
    events = [json.loads(line) for line in f]

events_by_id = {e["candidate_id"]: e for e in events}

print(f"Total rows in benchmark: {len(rows)}")
print(f"Total verification events: {len(events)}")

# Task 1: Verification status totals
status_counts = {}
ans_by_status = {}
lang_by_status = {}
tax_by_status = {}

for r in rows:
    st = r["final_status"]
    ans = r["answerability"]
    lang = r["query_language"]
    
    # Extract primary taxonomy from event or row
    ev = events_by_id.get(r["candidate_id"])
    tax = ev.get("primary_taxonomy") if ev else "direct_factual"
    if not tax and r.get("clause") and "Out-of-Scope" in r.get("clause", ""):
        tax = "out_of_domain"
    elif not tax:
        tax = "direct_factual"
    
    status_counts[st] = status_counts.get(st, 0) + 1
    ans_by_status.setdefault(st, {})[ans] = ans_by_status.setdefault(st, {}).get(ans, 0) + 1
    lang_by_status.setdefault(st, {})[lang] = lang_by_status.setdefault(st, {}).get(lang, 0) + 1
    tax_by_status.setdefault(st, {})[tax] = tax_by_status.setdefault(st, {}).get(tax, 0) + 1

print("\n--- STATUS COUNTS ---")
for st, cnt in sorted(status_counts.items()):
    print(f"  {st}: {cnt}")

print("\n--- ANSWERABILITY BY STATUS ---")
for st, d in sorted(ans_by_status.items()):
    print(f"  {st}: {d}")

print("\n--- LANGUAGE BY STATUS ---")
for st, d in sorted(lang_by_status.items()):
    print(f"  {st}: {d}")

print("\n--- TAXONOMY BY STATUS ---")
for st, d in sorted(tax_by_status.items()):
    print(f"  {st}: {d}")

# Task 1 continued: Check SQLite quotations, passage grounding, metadata
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

answerables = [r for r in rows if r["answerability"] == "answerable"]
print(f"\nTotal answerable records: {len(answerables)}")

valid_quotes = 0
valid_passages = 0
valid_doc = 0

for idx, r in enumerate(answerables):
    p_id = None
    try:
        raw_quotes = json.loads(r["gold_evidence_quotes"])
    except Exception:
        raw_quotes = [r["gold_evidence_quotes"]]
    
    doc_id = r["source_document_id"]
    
    # Check if doc exists
    doc_row = c.execute("SELECT * FROM documents WHERE document_id = ?", (doc_id,)).fetchone()
    if doc_row:
        valid_doc += 1
    
    # Check quotes in DB
    found_quote = True
    for q in raw_quotes:
        match = c.execute("SELECT passage_id FROM passages WHERE document_id = ? AND instr(text, ?) > 0", (doc_id, q)).fetchall()
        if not match:
            # Check across entire passages table in case doc_id differs or whitespace/newlines
            match_any = c.execute("SELECT passage_id, document_id FROM passages WHERE instr(text, ?) > 0", (q,)).fetchall()
            print(f"Row {idx} [{r['candidate_id']}] quote failed in doc {doc_id[:8]}: {q[:50]!r} (found in any doc: {match_any})")
            found_quote = False
            break
    if found_quote and raw_quotes:
        valid_quotes += 1

print(f"Answerables with valid document IDs: {valid_doc}/{len(answerables)}")
print(f"Answerables with exact verbatim SQLite quotes: {valid_quotes}/{len(answerables)}")

conn.close()
