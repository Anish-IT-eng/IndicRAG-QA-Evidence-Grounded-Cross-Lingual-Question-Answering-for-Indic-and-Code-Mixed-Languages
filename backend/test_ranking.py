import sys
sys.path.insert(0, 'backend')
from app.retrieval.engine import get_official_index

idx = get_official_index()
for q in [
    'When will odd semester examination start?',
    'When will odd semester examinations start?',
    'When will odd semester end semester examinations start?'
]:
    print('='*60)
    print('Query:', q)
    hits = idx.bm25_search(q, 5)
    for r, (pid, score, meta) in enumerate(hits):
        tidx = idx.passage_ids.index(pid)
        txt = idx.passage_texts[tidx]
        print(f"#{r+1} [p.{meta.get('page_number')}] score={score:.3f} | {txt[:80]}")
