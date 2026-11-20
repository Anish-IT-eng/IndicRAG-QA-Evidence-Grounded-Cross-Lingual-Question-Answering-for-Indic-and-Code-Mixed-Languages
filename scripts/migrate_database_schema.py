"""
Database Migration: Add validation_status to qa_instances and synchronize all 103 candidate records.
Maintains review_status = 'pending' for all records (zero human approvals).
"""
import csv
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "backend/data/db/indicrag.db"

# 1. Connect to SQLite DB
conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

# Check existing columns in qa_instances
cursor = conn.execute("PRAGMA table_info(qa_instances)")
columns = [row["name"] for row in cursor.fetchall()]

if "validation_status" not in columns:
    print("Adding 'validation_status' column to qa_instances table...")
    conn.execute("ALTER TABLE qa_instances ADD COLUMN validation_status TEXT DEFAULT 'pending'")
    conn.commit()
    print("Column added.")
else:
    print("'validation_status' column already exists.")

# 2. Load authoritative candidate files
with open(REPO_ROOT / "backend/data/dataset/candidates_auto_validated.csv", encoding="utf-8") as f:
    auto_val_rows = list(csv.DictReader(f))

with open(REPO_ROOT / "backend/data/dataset/candidates_needs_review.csv", encoding="utf-8") as f:
    needs_rev_rows = list(csv.DictReader(f))

with open(REPO_ROOT / "backend/data/dataset/candidates_rejected.csv", encoding="utf-8") as f:
    rejected_rows = list(csv.DictReader(f))

# Note: Candidate dd359bb2 was demoted from auto_validated to needs_review due to "बैठने के लिए" imprecision.
# Let's adjust in-memory mapping accordingly:
auto_val_ids = {r["candidate_id"] for r in auto_val_rows if r["candidate_id"] != "dd359bb2-a9ab-48d1-a231-77c1a9e13455"}
needs_rev_ids = {r["candidate_id"] for r in needs_rev_rows} | {"dd359bb2-a9ab-48d1-a231-77c1a9e13455"}
rejected_ids = {r["candidate_id"] for r in rejected_rows}

print(f"Authoritative sets: auto_validated={len(auto_val_ids)}, needs_review={len(needs_rev_ids)}, rejected={len(rejected_ids)}")
assert len(auto_val_ids) + len(needs_rev_ids) + len(rejected_ids) == 103

# 3. Load all 103 candidate metadata from source files
with open(REPO_ROOT / "backend/data/dataset/human_review_pilot_82.csv", encoding="utf-8") as f:
    pilot_82 = {r["question_id"]: r for r in csv.DictReader(f)}

with open(REPO_ROOT / "backend/data/dataset/multilingual_expansion_combined.csv", encoding="utf-8") as f:
    multi_21 = {r["question_id"]: r for r in csv.DictReader(f)}

all_103_meta = {}
all_103_meta.update(pilot_82)
all_103_meta.update(multi_21)
assert len(all_103_meta) == 103

# 4. Insert or update all 103 records in SQLite
for qid, m in all_103_meta.items():
    if qid in auto_val_ids:
        val_status = "auto_validated"
    elif qid in rejected_ids:
        val_status = "auto_rejected"
    else:
        val_status = "needs_review"

    # Human review status is strictly preserved as 'pending'
    rev_status = "pending"

    # Format JSON fields
    pids = m.get("gold_passage_ids", "[]")
    if not pids.startswith("["):
        pids = json.dumps([pids]) if pids else "[]"
    quotes = m.get("gold_evidence_quotes", "[]")
    if not quotes.startswith("["):
        quotes = json.dumps([quotes]) if quotes else "[]"

    conn.execute("""
        INSERT INTO qa_instances (
            question_id, original_question, query_language, query_script,
            question_type, answerability, reference_answer, gold_passage_ids,
            source_document_id, page_number, section, gold_evidence_quotes,
            validation_status, review_status, reviewer_notes, created_at, updated_at
        ) VALUES (
            :qid, :q, :lang, :script,
            :qtype, :ans_label, :ans, :pids,
            :doc_id, :page, :sec, :quotes,
            :val_status, :rev_status, :notes, :created, :updated
        )
        ON CONFLICT(question_id) DO UPDATE SET
            validation_status = excluded.validation_status,
            review_status = excluded.review_status,
            updated_at = excluded.updated_at
    """, {
        "qid": qid,
        "q": m.get("original_question", ""),
        "lang": m.get("query_language", "en"),
        "script": m.get("query_script", "Latin"),
        "qtype": m.get("question_type", "direct"),
        "ans_label": m.get("answerability", "answerable"),
        "ans": m.get("reference_answer", ""),
        "pids": pids,
        "doc_id": m.get("source_document_id", ""),
        "page": int(m["page_number"]) if m.get("page_number") and str(m["page_number"]).isdigit() else None,
        "sec": m.get("section", ""),
        "quotes": quotes,
        "val_status": val_status,
        "rev_status": rev_status,
        "notes": m.get("reviewer_notes", ""),
        "created": datetime.utcnow().isoformat(),
        "updated": datetime.utcnow().isoformat(),
    })

conn.commit()

# 5. Verify database counts
total_in_db = conn.execute("SELECT count(*) FROM qa_instances").fetchone()[0]
val_counts = conn.execute("SELECT validation_status, count(*) FROM qa_instances GROUP BY validation_status").fetchall()
rev_counts = conn.execute("SELECT review_status, count(*) FROM qa_instances GROUP BY review_status").fetchall()

print(f"\nDatabase Migration Complete!")
print(f"Total qa_instances in DB: {total_in_db}")
print("Validation Status Breakdown in DB:")
for row in val_counts:
    print(f"  {row[0]}: {row[1]}")
print("Human Review Status Breakdown in DB:")
for row in rev_counts:
    print(f"  {row[0]}: {row[1]}")

conn.close()

