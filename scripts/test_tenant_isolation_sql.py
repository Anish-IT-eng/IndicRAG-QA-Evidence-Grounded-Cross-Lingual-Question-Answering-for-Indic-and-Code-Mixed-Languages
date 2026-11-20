import sqlite3

conn = sqlite3.connect('backend/data/db/indicrag.db')
conn.row_factory = sqlite3.Row

# Test with user_id = None
res_none = conn.execute("""
    SELECT COUNT(*) 
    FROM document_relationships r
    JOIN documents d ON r.source_document_id = d.document_id
    WHERE (r.user_id = ? OR (r.user_id IS NULL AND d.source_type = 'official'))
""", (None,)).fetchone()[0]

# Test with user_id = 'test-user-7d753800'
res_user = conn.execute("""
    SELECT COUNT(*) 
    FROM document_relationships r
    JOIN documents d ON r.source_document_id = d.document_id
    WHERE (r.user_id = ? OR (r.user_id IS NULL AND d.source_type = 'official'))
""", ('test-user-7d753800',)).fetchone()[0]

# Total official relationships
res_off = conn.execute("""
    SELECT COUNT(*) 
    FROM document_relationships r
    JOIN documents d ON r.source_document_id = d.document_id
    WHERE r.user_id IS NULL AND d.source_type = 'official'
""").fetchone()[0]

# Total for test-user-7d753800
res_uonly = conn.execute("""
    SELECT COUNT(*) 
    FROM document_relationships r
    WHERE r.user_id = 'test-user-7d753800'
""").fetchone()[0]

print(f"Total official count: {res_off}")
print(f"Total user-only count: {res_uonly}")
print(f"Query count when user_id=None: {res_none} (matches official: {res_none == res_off})")
print(f"Query count when user_id='test-user-7d753800': {res_user} (matches official + user: {res_user == res_off + res_uonly})")
