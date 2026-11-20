import sys
sys.path.insert(0, 'backend')
from app.retrieval.engine import get_official_index, _rrf_fuse, rerank
from app.query.processor import process_query

idx = get_official_index()
q = 'When will odd semester examinations start?'

# Test with candidate_k = 25
bm25_hits = idx.bm25_search(q, 25)
dense_hits = idx.dense_search(q, 25)
fused = _rrf_fuse(bm25_hits, dense_hits)

for pid, score, meta in fused:
    tidx = idx.passage_ids.index(pid)
    meta["text"] = idx.passage_texts[tidx]

reranked = rerank(q, fused, top_k=5)
print("=== RERANKED RESULTS WITH CANDIDATE_K = 25 ===")
for i, (pid, score, meta) in enumerate(reranked):
    print(f"Rank {i+1} [p.{meta.get('page_number')}] score={score:.3f} | {meta['text'][:120]}")
