import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
conn.row_factory = sqlite3.Row

docs = [
    "Notification-Minimum-Attendance.pdf",
    "SEAS-Ordinance-Rules-Regulations-2017.pdf",
    "Academic-Rules-for-SCSET_UG.pdf",
    "Students-Discipline-Conduct-Rules-2024.pdf"
]

print("=== ALL ATTENDANCE PASSAGES IN KEY DOCUMENTS ===")
rows = conn.execute("""
    SELECT p.passage_id, p.document_id, d.filename, p.page_number, p.section, p.heading, p.clause, p.text
    FROM passages p
    JOIN documents d ON p.document_id = d.document_id
    WHERE d.filename IN (?, ?, ?, ?)
      AND p.text LIKE '%attendance%'
    ORDER BY d.filename, p.page_number
""", tuple(docs)).fetchall()

for r in rows:
    print("="*80)
    print(f"File: {r['filename']} (Doc ID: {r['document_id']}) | Page: {r['page_number']} | Clause: {r['clause']}")
    print(f"Heading: {r['heading']} | Section: {r['section']}")
    print(f"Passage ID: {r['passage_id']}")
    print("TEXT:")
    print(r['text'])
