import sqlite3

conn = sqlite3.connect("backend/data/db/indicrag.db")
c = conn.cursor()
r = c.execute("SELECT text FROM passages WHERE passage_id = '124457f2-1670-4208-88d5-84808860454c'").fetchone()
print(repr(r[0]))
conn.close()

