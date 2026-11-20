import sqlite3
conn = sqlite3.connect('backend/data/db/indicrag.db')
c = conn.cursor()
c.execute("SELECT text FROM passages WHERE passage_id='625fba4f-faa9-4790-9db6-23f465e3cfc2'")
print(c.fetchone()[0])

