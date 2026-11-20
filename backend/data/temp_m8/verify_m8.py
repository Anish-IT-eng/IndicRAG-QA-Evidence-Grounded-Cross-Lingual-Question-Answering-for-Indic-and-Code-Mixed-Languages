import sys
sys.path.insert(0, "backend")
import sqlite3, pickle, faiss
from app.core.config import settings
from app.retrieval.engine import get_official_index, retrieve
from app.models.schemas import QueryAnalysis, DocumentSource

# 1. Database verification
conn = sqlite3.connect("backend/data/db/indicrag.db")
cursor = conn.cursor()
docs = cursor.execute("SELECT document_id, filename, page_count, title FROM documents").fetchall()
print(f"=== SQLite Documents ({len(docs)}) ===")
for d in docs:
    print(f"  [{d[0][:8]}...] {d[1]} (pages={d[2]}): {d[3][:50]}")

total_passages = cursor.execute("SELECT count(*) FROM passages").fetchone()[0]
child_passages = cursor.execute("SELECT count(*) FROM passages WHERE is_parent = 0").fetchone()[0]
parent_passages = cursor.execute("SELECT count(*) FROM passages WHERE is_parent = 1").fetchone()[0]
print(f"\n=== Passages in DB ===")
print(f"  Total: {total_passages}, Child: {child_passages}, Parent: {parent_passages}")

# 2. Index verification
idx = get_official_index()
print(f"\n=== Official Index ===")
print(f"  Passage count: {len(idx.passage_ids)}")
print(f"  FAISS ntotal: {idx.faiss_index.ntotal}, dim: {idx.faiss_index.d}")

# 3. Test retrieval on both historical and new topics
test_queries = [
    "What is the minimum attendance requirement?",
    "What are the penalties for unfair means during examinations?",
    "What is the role of the Proctorial Committee in student discipline?",
    "What are the requirements for the award of a B.Tech degree in the First Ordinances?"
]

print(f"\n=== Retrieval Verification ===")
for q in test_queries:
    qa = QueryAnalysis(original_query=q)
    res = retrieve(qa, collections=[DocumentSource.OFFICIAL], top_k=3)
    print(f"Query: \"{q}\"")
    print(f"  Hits returned: {len(res.retrieved_passages)}")
    for p in res.retrieved_passages[:2]:
        snippet = p.text[:100].replace("\n", " ")
        print(f"    - [{p.passage_id[:8]}...] (Doc: {p.document_id[:8]}..., Page {p.page_number}): {snippet}...")

