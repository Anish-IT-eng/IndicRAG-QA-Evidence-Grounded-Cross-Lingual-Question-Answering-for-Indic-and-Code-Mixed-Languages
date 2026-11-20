import json, sys, os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
sys.path.insert(0, os.path.abspath("backend"))

from app.query.processor import process_query
from app.retrieval.engine import get_official_index, _rrf_fuse

idx = get_official_index()

with open('backend/data/experiments/m9/m9_evaluation_dataset.jsonl', 'r', encoding='utf-8') as f:
    queries = [json.loads(line) for line in f if line.strip()]

ans_q = [q for q in queries if q['expected_status'] == 'ANSWERED'][:5]

for q in ans_q:
    raw_text = q['query_text']
    exp_pids = set(q.get('expected_passage_ids', []))
    exp_dids = set(q.get('expected_document_ids', []))
    
    bm25_hits = idx.bm25_search(raw_text, 5)
    dense_hits = idx.dense_search(raw_text, 5)
    fused = _rrf_fuse(bm25_hits, dense_hits)
    
    ret_pids = [pid for pid, _, _ in fused[:5]]
    ret_dids = [meta.get('document_id') for _, _, meta in fused[:5]]
    
    ranks = []
    if exp_pids:
        ranks = [r for r, pid in enumerate(ret_pids, 1) if pid in exp_pids]
    elif exp_dids:
        ranks = [r for r, did in enumerate(ret_dids, 1) if did in exp_dids]
    print(q['query_id'], q['query_language'], '| Ranks:', ranks, '| Pids:', ret_pids[:2], '| Dids:', ret_dids[:2])
