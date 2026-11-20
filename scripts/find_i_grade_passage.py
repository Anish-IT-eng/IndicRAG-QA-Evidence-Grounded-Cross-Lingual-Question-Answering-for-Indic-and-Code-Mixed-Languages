import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
c = conn.cursor()

c.execute("SELECT passage_id, document_id, section, heading, text FROM passages WHERE text LIKE '%grade%' AND text LIKE '%genuine%' AND text LIKE '%Vice Chancellor%'")
rows = c.fetchall()
print(f"Passages matching 'I' grade and Vice Chancellor: {len(rows)}")
for r in rows:
    print(r[0], r[2], r[3])
    print(r[4][:300])
    print("=" * 60)

