import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
conn.row_factory = sqlite3.Row

print("=== 1. Notification-Minimum-Attendance.pdf ===")
rows = conn.execute("""
    SELECT p.passage_id, p.page_number, p.section, p.heading, p.clause, p.text
    FROM passages p
    JOIN documents d ON p.document_id = d.document_id
    WHERE d.filename = 'Notification-Minimum-Attendance.pdf'
""").fetchall()

for r in rows:
    print(f"\n--- Page {r['page_number']} | Heading: {r['heading']} | Clause: {r['clause']}")
    print(r['text'])

print("\n=== 2. SEAS-Ordinance-Rules-Regulations-2017.pdf (Clauses 28 to 35) ===")
rows2 = conn.execute("""
    SELECT p.passage_id, p.page_number, p.section, p.heading, p.clause, p.text
    FROM passages p
    JOIN documents d ON p.document_id = d.document_id
    WHERE d.filename = 'SEAS-Ordinance-Rules-Regulations-2017.pdf'
      AND (p.text LIKE '%attendance%' OR p.text LIKE '%clause 30%' OR p.heading LIKE '%attendance%')
""").fetchall()

for r in rows2:
    print(f"\n--- Page {r['page_number']} | Heading: {r['heading']} | Clause: {r['clause']}")
    print(r['text'])
