import sqlite3

conn = sqlite3.connect("backend/data/db/indicrag.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=== PASSAGES FROM ORDINANCE (Pages 25-32) ===")
rows = c.execute(
    "SELECT passage_id, parent_passage_id, page_number, heading, text "
    "FROM passages WHERE document_id = 'b6f9aad0-4cbd-4915-bc0b-262e14b6e3a2' "
    "AND page_number BETWEEN 25 AND 32 AND parent_passage_id IS NOT NULL"
).fetchall()
for r in rows:
    print(f"[{r['passage_id']}] Page {r['page_number']} | Heading: {r['heading']}")
    print(f"Text: {r['text'][:250]}...\n")

print("\n=== PASSAGES FROM SCSET_UG (Pages 1-15) ===")
rows = c.execute(
    "SELECT passage_id, parent_passage_id, page_number, heading, text "
    "FROM passages WHERE document_id = 'b787fd22-eb2f-42ed-9ef7-ef098e5ff8b6' "
    "AND parent_passage_id IS NOT NULL"
).fetchall()
for r in rows:
    print(f"[{r['passage_id']}] Page {r['page_number']} | Heading: {r['heading']}")
    print(f"Text: {r['text'][:180]}...\n")

conn.close()
