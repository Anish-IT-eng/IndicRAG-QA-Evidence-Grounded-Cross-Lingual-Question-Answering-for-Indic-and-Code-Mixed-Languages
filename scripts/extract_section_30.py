import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
c = conn.cursor()

print("="*70)
print("SCSET UG RULES 2022 - Passages with 30 or Attendance:")
print("="*70)
c.execute("""
    SELECT d.filename, p.passage_id, p.parent_passage_id, p.is_parent, p.page_number, p.section, p.heading, p.text
    FROM passages p
    JOIN documents d ON p.document_id = d.document_id
    WHERE d.filename LIKE '%SCSET%'
      AND (p.text LIKE '%Attendance%' OR p.text LIKE '%30.%' OR p.text LIKE '%relaxation%')
    ORDER BY p.page_number, p.chunk_index
""")
for fn, pid, ppid, is_p, page, sec, head, text in c.fetchall():
    print(f"Doc: {fn} | Page: {page} | PID: {pid} | Parent: {ppid} | is_parent: {is_p}")
    print(f"Section: {sec} | Heading: {head}")
    print(text)
    print("-"*60)

print("\n" + "="*70)
print("SEAS ORDINANCES 2017 - Pages 28, 29, 30:")
print("="*70)
c.execute("""
    SELECT d.filename, p.passage_id, p.parent_passage_id, p.is_parent, p.page_number, p.section, p.heading, p.text
    FROM passages p
    JOIN documents d ON p.document_id = d.document_id
    WHERE d.filename LIKE '%SEAS%'
      AND p.page_number IN (28, 29, 30)
    ORDER BY p.page_number, p.chunk_index
""")
for fn, pid, ppid, is_p, page, sec, head, text in c.fetchall():
    print(f"Doc: {fn} | Page: {page} | PID: {pid} | Parent: {ppid} | is_parent: {is_p}")
    print(f"Section: {sec} | Heading: {head}")
    print(text)
    print("-"*60)
