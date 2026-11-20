import sqlite3
from pathlib import Path

db_path = Path("backend/data/db/indicrag.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

docs = c.execute("SELECT document_id, filename, is_current FROM documents").fetchall()
print(f"=== DOCUMENTS ({len(docs)}) ===")
for d in docs:
    print(f"ID: {d['document_id']} | Filename: {d['filename']} | Current: {d['is_current']}")

print("\n=== CHILD PASSAGES PER DOCUMENT ===")
for d in docs:
    doc_id = d["document_id"]
    rows = c.execute(
        "SELECT passage_id, parent_passage_id, page_number, section, heading, text "
        "FROM passages WHERE document_id = ? AND parent_passage_id IS NOT NULL",
        (doc_id,)
    ).fetchall()
    print(f"\nDocument: {d['filename']} ({len(rows)} child passages)")
    for r in rows[:4]:
        clean_text = " ".join(r["text"].split())[:100]
        print(f"  [{r['passage_id']}] Page {r['page_number']} | Sec: {r['section']} | Heading: {r['heading']}")
        print(f"    Text: {clean_text}...")

conn.close()

