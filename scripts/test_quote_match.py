import sqlite3

conn = sqlite3.connect("backend/data/db/indicrag.db")
c = conn.cursor()
r = c.execute("SELECT passage_id, heading, text FROM passages WHERE passage_id = 'ee63431f-398b-4717-aa04-8c456a3ab928'").fetchone()
print("ID:", r[0])
print("Heading:", r[1])
print("Text:\n", r[2])
conn.close()
