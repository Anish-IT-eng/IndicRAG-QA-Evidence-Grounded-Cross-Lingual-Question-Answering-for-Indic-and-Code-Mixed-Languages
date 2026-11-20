import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
c = conn.cursor()

print("=== PASSAGES WITH 12.4 ===")
c.execute("SELECT p.passage_id, d.filename, p.section, p.heading, substr(p.text, 1, 200) FROM passages p JOIN documents d ON p.document_id=d.document_id WHERE p.text LIKE '%12.4%' OR p.section LIKE '%12.4%'")
for r in c.fetchall():
    print(r)

print("\n=== PASSAGES WITH 9.2 ===")
c.execute("SELECT p.passage_id, d.filename, p.section, p.heading, substr(p.text, 1, 200) FROM passages p JOIN documents d ON p.document_id=d.document_id WHERE p.text LIKE '%9.2%' OR p.section LIKE '%9.2%'")
for r in c.fetchall():
    print(r)

print("\n=== ATTENDANCE TEXT IN NOTIFICATION (0280358a) ===")
c.execute("SELECT text FROM passages WHERE passage_id='0280358a-ff3c-4964-88ab-419a9147b1f0'")
print(c.fetchone()[0])

print("\n=== ATTENDANCE TEXT IN SEAS 2017 (f88ec726) ===")
c.execute("SELECT text FROM passages WHERE passage_id='f88ec726-74ba-426f-a01f-4b9665c1a8b8'")
print(c.fetchone()[0])

