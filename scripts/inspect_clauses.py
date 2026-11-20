import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
c = conn.cursor()

print("=== 1. DOCUMENTS TABLE ===")
c.execute("SELECT document_id, filename, source_type, created_at FROM documents")
docs = c.fetchall()
for d in docs:
    print(d)

print("\n=== 2. PASSAGES FOR MAKEUP EXAM ===")
c.execute("""
    SELECT p.passage_id, d.filename, p.section, p.heading, p.clause, p.page_number, substr(p.text, 1, 150)
    FROM passages p
    JOIN documents d ON p.document_id = d.document_id
    WHERE p.is_parent=0 AND (
        p.text LIKE '%makeup%' OR p.text LIKE '%make up%' OR p.text LIKE '%make -up%'
    ) AND (p.text LIKE '%end semester%' OR p.text LIKE '%mid term%')
""")
makeup_rows = c.fetchall()
print(f"Total makeup passages: {len(makeup_rows)}")
for r in makeup_rows:
    print(f"Doc: {r[1]} | P_ID: {r[0]} | Sec: {r[2]} | Heading: {r[3]} | Clause: {r[4]} | Page: {r[5]}")
    print(f"  Snippet: {r[6]}...")

print("\n=== 3. PASSAGES FOR ATTENDANCE (70% vs 75%) ===")
c.execute("""
    SELECT p.passage_id, d.filename, p.section, p.heading, p.clause, p.page_number, substr(p.text, 1, 150)
    FROM passages p
    JOIN documents d ON p.document_id = d.document_id
    WHERE p.is_parent=0 AND (
        p.text LIKE '%75%%' OR p.text LIKE '%70%%' OR p.text LIKE '%attendance%' OR p.text LIKE '%condonation%'
    )
""")
att_rows = c.fetchall()
print(f"Total attendance passages: {len(att_rows)}")
for r in att_rows:
    print(f"Doc: {r[1]} | P_ID: {r[0]} | Sec: {r[2]} | Heading: {r[3]} | Clause: {r[4]} | Page: {r[5]}")
    print(f"  Snippet: {r[6]}...")

