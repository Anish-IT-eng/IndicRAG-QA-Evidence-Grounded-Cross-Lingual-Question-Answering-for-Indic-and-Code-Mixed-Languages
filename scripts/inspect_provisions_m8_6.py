import sqlite3
from pathlib import Path

db_path = Path("backend/data/db/indicrag.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=== SEAS 2017 Page 28-29 Passages ===")
rows = c.execute("SELECT passage_id, page_number, chunk_index, text FROM passages WHERE document_id='b6f9aad0-4cbd-4915-bc0b-262e14b6e3a2' AND page_number IN (28, 29)").fetchall()
for r in rows:
    print(f"PID: {r[0]}, Page: {r[1]}, Chunk: {r[2]}")
    print(r[3][:300])
    print("---")



