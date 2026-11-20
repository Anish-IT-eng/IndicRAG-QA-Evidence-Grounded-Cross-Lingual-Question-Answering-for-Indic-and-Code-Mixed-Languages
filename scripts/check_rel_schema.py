import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='document_relationships'").fetchone()[0]
print("=== SCHEMA OF document_relationships ===")
print(schema)

indices = conn.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='document_relationships'").fetchall()
print("\n=== INDICES ===")
for idx in indices:
    if idx[0]:
        print(idx[0])
