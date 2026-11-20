import sqlite3
import csv
import faiss
from pathlib import Path

db_path = Path("backend/data/db/indicrag.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

docs = c.execute("SELECT COUNT(*) FROM documents WHERE source_type='official'").fetchone()[0]
child = c.execute("SELECT COUNT(*) FROM passages WHERE is_parent=0 AND source_type='official'").fetchone()[0]
parent = c.execute("SELECT COUNT(*) FROM passages WHERE is_parent=1 AND source_type='official'").fetchone()[0]
all_pass = c.execute("SELECT COUNT(*) FROM passages WHERE source_type='official'").fetchone()[0]

# Historical passages from m8_1_passage_lineage.csv
csv_path = Path("backend/data/experiments/m8/m8_1_passage_lineage.csv")
with open(csv_path, "r", encoding="utf-8") as f:
    lineage_rows = list(csv.DictReader(f))

lineage_pids = [r["passage_id"] for r in lineage_rows]
placeholders = ','.join('?' for _ in lineage_pids)
hist_in_db = c.execute(f"SELECT COUNT(*) FROM passages WHERE passage_id IN ({placeholders})", lineage_pids).fetchone()[0]

# Check review_status values in qa_instances
qa_reviews = c.execute("SELECT review_status, COUNT(*) FROM qa_instances GROUP BY review_status").fetchall()
human_verified = c.execute("SELECT COUNT(*) FROM qa_instances WHERE review_status='verified' OR review_status='human_verified'").fetchone()[0]

faiss_path = Path("backend/data/indexes/official/faiss.index")
idx = faiss.read_index(str(faiss_path))

print(f"Official Documents: {docs}")
print(f"Child Passages (is_parent=0): {child}")
print(f"Parent Passages (is_parent=1): {parent}")
print(f"Total Passages: {all_pass}")
print(f"Historical Passages in Lineage CSV: {len(lineage_rows)}")
print(f"Historical Passages Verified in DB: {hist_in_db}")
print(f"QA review breakdown: {qa_reviews}")
print(f"Human-verified benchmark examples: {human_verified}")
print(f"FAISS Vectors (ntotal): {idx.ntotal}")
print(f"FAISS Dimensions (d): {idx.d}")



