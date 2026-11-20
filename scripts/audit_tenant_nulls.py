import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
conn.row_factory = sqlite3.Row

print("=== CHECKING FOR ANY USER UPLOAD DOCUMENT WITH user_id IS NULL ===")
docs = conn.execute("""
    SELECT document_id, filename, source_type, metadata
    FROM documents
    WHERE source_type != 'official'
""").fetchall()

for d in docs:
    print(f"Doc {d['document_id']} ({d['filename']}): source_type={d['source_type']}, metadata={d['metadata']}")

print("\n=== CHECKING FOR ANY USER UPLOAD RELATIONSHIP WITH user_id IS NULL ===")
rels = conn.execute("""
    SELECT r.relationship_id, r.source_document_id, d.filename, d.source_type, r.user_id
    FROM document_relationships r
    JOIN documents d ON r.source_document_id = d.document_id
    WHERE d.source_type != 'official' AND r.user_id IS NULL
""").fetchall()
print(f"Total user-uploaded relationships with user_id IS NULL: {len(rels)}")
