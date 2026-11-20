import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
conn.row_factory = sqlite3.Row

total = conn.execute('SELECT COUNT(*) FROM document_relationships').fetchone()[0]
print(f'Total relationships in DB: {total}')

# Group by document
docs = conn.execute("""
    SELECT d.document_id, d.filename, d.source_type, COUNT(r.relationship_id) as rel_count
    FROM documents d
    LEFT JOIN document_relationships r ON d.document_id = r.source_document_id
    GROUP BY d.document_id
    ORDER BY d.source_type, rel_count DESC
""").fetchall()

for d in docs:
    print(f"{d['filename']} ({d['source_type']}) [ID: {d['document_id']}]: {d['rel_count']} rels")

print("\n--- Non-official or User-Scoped Relationships ---")
uploaded_rels = conn.execute("""
    SELECT r.relationship_id, r.source_document_id, d.filename, r.subject_id, r.predicate, r.object_value, r.user_id, r.created_at
    FROM document_relationships r
    JOIN documents d ON r.source_document_id = d.document_id
    WHERE d.source_type != 'official' OR r.user_id IS NOT NULL
""").fetchall()

print(f"Total uploaded/user-scoped relationships: {len(uploaded_rels)}")
for u in uploaded_rels:
    print(dict(u))

print("\n--- Relationships by official documents ---")
off_rels = conn.execute("""
    SELECT d.filename, COUNT(r.relationship_id) as rel_count
    FROM document_relationships r
    JOIN documents d ON r.source_document_id = d.document_id
    WHERE d.source_type = 'official' AND r.user_id IS NULL
    GROUP BY d.filename
""").fetchall()
for o in off_rels:
    print(f"  {o['filename']}: {o['rel_count']}")

off_total = conn.execute("""
    SELECT COUNT(r.relationship_id)
    FROM document_relationships r
    JOIN documents d ON r.source_document_id = d.document_id
    WHERE d.source_type = 'official' AND r.user_id IS NULL
""").fetchone()[0]
print(f"Total official relationships: {off_total}")
