import sqlite3
from pathlib import Path

db_path = Path("c:/Users/anish/Desktop/IndicRAG-QA/backend/data/db/indicrag.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

pids = [
    "0280358a-ff3c-4964-88ab-419a9147b1f0",
    "f88ec726-74ba-426f-a01f-4b9665c1a8b8",
    "f6d95cc5-2c08-4aee-ba5c-72429cbef467"
]

for pid in pids:
    c.execute("SELECT passage_id, document_id, page_number, text FROM passages WHERE passage_id = ?", (pid,))
    row = c.fetchone()
    if row:
        doc_id, page, content = row[1], row[2], row[3]
        c.execute("SELECT filename FROM documents WHERE document_id = ?", (doc_id,))
        doc_row = c.fetchone()
        doc_name = doc_row[0] if doc_row else "Unknown"
        print(f"Passage: {pid}")
        print(f"  Doc: {doc_id} ({doc_name}), Page: {page}")
        print(f"  Snippet: {content[:100]}...\n")
    else:
        print(f"Passage: {pid} NOT FOUND\n")
conn.close()
