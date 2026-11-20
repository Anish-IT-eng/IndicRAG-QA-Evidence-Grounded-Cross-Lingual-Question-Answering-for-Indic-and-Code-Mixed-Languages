import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
c = conn.cursor()

print('Official Documents in indicrag.db:')
for row in c.execute("SELECT document_id, filename, title FROM documents WHERE source_type='OFFICIAL'"):
    print(f'  {row[0]} | {row[1]} | {row[2]}')

print('\nPassage counts by document:')
for row in c.execute("""
    SELECT d.filename, count(p.passage_id) 
    FROM documents d 
    JOIN passages p ON d.document_id = p.document_id 
    GROUP BY d.filename
"""):
    print(f'  {row[0]}: {row[1]} passages')

print('\nSample headings / sections in passages:')
for row in c.execute("SELECT DISTINCT heading FROM passages WHERE heading IS NOT NULL AND heading != '' LIMIT 25"):
    print(f'  - {row[0]}')
