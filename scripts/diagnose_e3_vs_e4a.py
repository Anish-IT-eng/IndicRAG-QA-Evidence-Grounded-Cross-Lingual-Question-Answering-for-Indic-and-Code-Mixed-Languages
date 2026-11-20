import json, sys, os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
sys.path.insert(0, 'backend')
from app.query.processor import process_query
from app.retrieval.engine import get_official_index, get_cross_encoder, _rrf_fuse, _deduplicate, validate_versions

with open('backend/data/experiments/m9/m9_evaluation_dataset.jsonl', 'r', encoding='utf-8') as f:
    queries = [json.loads(line) for line in f if line.strip()]

hi_queries = [q for q in queries if q['query_language'] == 'hi' and q['expected_status'] == 'ANSWERED']
idx = get_official_index()
cross_enc = get_cross_encoder()

e3_hits = []
e4a_hits = []

for q in hi_queries:
    qid = q['query_id']
    exp_pids = set(q.get('expected_passage_ids') or [q.get('passage_id')])
    qa = process_query(q['query_text'], enable_translation=False)
    qstr = qa.normalized_query or qa.original_query
    
    # E3: Dense only top 5
    dense_5 = idx.dense_search(qstr, top_k=5)
    e3_pids = [h[0] for h in dense_5[:5]]
    e3_hit = bool(exp_pids & set(e3_pids))
    if e3_hit: e3_hits.append(qid)
    
    # E4a: Hybrid depth 5 + rerank
    bm25_5 = idx.bm25_search(qstr, top_k=5)
    dense_5_b = idx.dense_search(qstr, top_k=5)
    fused_5 = _rrf_fuse(bm25_5, dense_5_b)
    for pid, score, meta in fused_5:
        if 'text' not in meta:
            try: meta['text'] = idx.passage_texts[idx.passage_ids.index(pid)]
            except ValueError: pass
    fused_5 = _deduplicate(fused_5)
    fused_5 = validate_versions(fused_5, None, None, qa)
    pairs = [(qstr, meta.get('text', '')) for _, _, meta in fused_5]
    scores = cross_enc.predict(pairs)
    ranked = sorted(zip(fused_5, scores), key=lambda x: x[1], reverse=True)
    e4a_pids = [h[0][0] for h in ranked[:5]]
    e4a_hit = bool(exp_pids & set(e4a_pids))
    if e4a_hit: e4a_hits.append(qid)
    
    if e4a_hit != e3_hit:
        print(f"Diff on {qid}: E3={e3_hit}, E4a={e4a_hit}")
        print(f"  Query: {q['query_text']}")
        print(f"  Dense top 5: {[p[:8] for p in e3_pids]}")
        print(f"  E4a top 5: {[p[:8] for p in e4a_pids]}")
        print(f"  Exp PIDs: {[p[:8] for p in exp_pids]}")

print(f"E3 Total Hits: {len(e3_hits)} / 45 ({len(e3_hits)/45:.4f})")
print(f"E4a Total Hits: {len(e4a_hits)} / 45 ({len(e4a_hits)/45:.4f})")
