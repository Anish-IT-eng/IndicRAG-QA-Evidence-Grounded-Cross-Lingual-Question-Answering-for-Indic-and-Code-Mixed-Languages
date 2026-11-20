import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
c = conn.cursor()

pids = [
    '1163039d-b53d-46f4-b717-1f6c094830a6', 
    '54dd6b69-655f-4b93-a19d-ec24808a9002', 
    '2071c939-093c-42e7-923f-80eda1e10f7f', 
    'dc9034e1-88aa-4a45-ad01-34fd28c21411', 
    '6fe359c2-0587-4d92-ac5e-78a7760d65c0',
    '278fa408-518b-4c53-9cc2-c49ac347c87a'
]

for pid in pids:
    c.execute("""
        SELECT p.passage_id, d.filename, p.section, p.heading, p.text 
        FROM passages p 
        JOIN documents d ON p.document_id = d.document_id 
        WHERE p.passage_id=?
    """, (pid,))
    r = c.fetchone()
    if r:
        print(f"=== Passage {r[0]} | File: {r[1]} | Section: {r[2]} | Heading: {r[3]} ===")
        print(r[4])
        print("="*60)
