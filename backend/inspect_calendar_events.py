import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
conn.row_factory = sqlite3.Row

print("=== ALL EVENT_HAS_DATE_RANGE RECORDS IN DB ===")
rows = conn.execute("""
    SELECT relationship_id, subject_id, object_value, source_page, source_row_id, source_document_id
    FROM document_relationships
    WHERE predicate = 'EVENT_HAS_DATE_RANGE'
""").fetchall()
for r in rows:
    print(f"[{r['relationship_id']}] (p.{r['source_page']}, row {r['source_row_id']}) {r['subject_id']}: {r['object_value']} (doc: {r['source_document_id'][:8]})")
