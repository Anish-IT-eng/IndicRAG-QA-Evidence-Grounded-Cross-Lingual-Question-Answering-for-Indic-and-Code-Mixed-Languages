import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
conn.row_factory = sqlite3.Row

print("=== SEARCHING ALL PASSAGES FOR '5 days' OR 'five days' OR '7 days' OR 'seven days' ===")
rows = conn.execute("""
    SELECT p.passage_id, d.filename, p.page_number, p.clause, p.heading, p.text
    FROM passages p
    JOIN documents d ON p.document_id = d.document_id
    WHERE p.text LIKE '%5 days%' OR p.text LIKE '%five days%' OR p.text LIKE '%7 days%' OR p.text LIKE '%seven days%'
""").fetchall()

for r in rows:
    print(f"\n[Doc: {r['filename']}, Page: {r['page_number']}] Clause: {r['clause']} | Heading: {r['heading']}")
    print(r['text'][:300] + "...")

print("\n=== SEARCHING ALL RELATIONSHIPS FOR '5' OR '7' OR 'week' OR 'dean' OR 'medical' ===")
rel_rows = conn.execute("""
    SELECT r.relationship_id, d.filename, r.source_page, r.subject_id, r.predicate, r.object_value
    FROM document_relationships r
    JOIN documents d ON r.source_document_id = d.document_id
    WHERE r.object_value LIKE '%5%' 
       OR r.object_value LIKE '%7%'
       OR r.object_value LIKE '%week%'
       OR r.object_value LIKE '%dean%'
       OR r.object_value LIKE '%medical%'
       OR r.predicate LIKE '%EXCEPTION%'
""").fetchall()
print(f"Total matching relationships: {len(rel_rows)}")
for r in rel_rows:
    if any(k in r['object_value'].lower() for k in ['day', 'week', 'medic', 'relax', 'illness', 'condon']):
        print(f"[{r['relationship_id']}] ({r['filename']} p.{r['source_page']}) {r['subject_id']} --({r['predicate']})--> {r['object_value']}")
