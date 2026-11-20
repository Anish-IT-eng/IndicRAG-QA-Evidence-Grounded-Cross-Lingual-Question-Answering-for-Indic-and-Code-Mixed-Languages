import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
conn.row_factory = sqlite3.Row

keywords = [
    "continuous", "two weeks", "2 weeks", "5 days", "five days",
    "10%", "relaxation", "condon", "medical certificate", "seven days", "7 days",
    "hod", "dean", "vice chancellor", "vc"
]

target_docs = [
    "SEAS-Ordinance-Rules-Regulations-2017.pdf",
    "Notification-Minimum-Attendance.pdf",
    "Academic-Rules-for-SCSET_UG.pdf",
    "BU-First-Ordinance-2016.pdf"
]

print("=== PASSAGES IN TARGET REGULATORY DOCUMENTS ===")
rows = conn.execute("""
    SELECT p.passage_id, p.document_id, d.filename, p.page_number, p.section, p.heading, p.clause, p.text
    FROM passages p
    JOIN documents d ON p.document_id = d.document_id
    WHERE d.filename IN (?, ?, ?, ?)
      AND (
          p.text LIKE '%attendance%' 
          OR p.text LIKE '%medical%' 
          OR p.text LIKE '%illness%'
          OR p.text LIKE '%relaxation%'
          OR p.text LIKE '%condon%'
      )
""", tuple(target_docs)).fetchall()

print(f"Total matching candidate passages: {len(rows)}")

for r in rows:
    text_lower = r["text"].lower()
    found_kw = [k for k in keywords if k in text_lower]
    if len(found_kw) >= 2 or "attendance" in text_lower and ("medical" in text_lower or "relaxation" in text_lower or "illness" in text_lower):
        print("="*80)
        print(f"Doc: {r['filename']} | Page: {r['page_number']} | Clause: {r['clause']} | Heading: {r['heading']}")
        print(f"Passage ID: {r['passage_id']}")
        print(f"Keywords matched: {found_kw}")
        print("TEXT:")
        print(r['text'])

print("\n" + "="*80)
print("=== RELATIONSHIPS FOR THESE PASSAGES ===")
for r in rows:
    pid = r['passage_id']
    rel_rows = conn.execute("""
        SELECT relationship_id, subject_id, predicate, object_value, source_page, cohort_scope, programme_scope
        FROM document_relationships
        WHERE source_passage_id = ?
    """, (pid,)).fetchall()
    if rel_rows:
        print(f"\nPassage {pid} (Doc: {r['filename']}, Page: {r['page_number']}) has {len(rel_rows)} relationships:")
        for rel in rel_rows:
            print(f"  [{rel['relationship_id']}] {rel['subject_id']} --({rel['predicate']})--> {rel['object_value']} (Cohort: {rel['cohort_scope']})")
