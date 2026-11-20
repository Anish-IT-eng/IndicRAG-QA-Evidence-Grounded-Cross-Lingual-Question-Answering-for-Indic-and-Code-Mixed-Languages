import sys
sys.path.insert(0, 'backend')
from app.query.processor import process_query
from app.retrieval.engine import retrieve, get_official_index
from app.retrieval.evidence_controller import get_evidence_controller

q = "What is the minimum duration of the B.Tech program?"
qa = process_query(q)
idx = get_official_index()
res = retrieve(qa, [idx], use_reranker=True, use_pdr=True)
print(f"Retrieved {len(res.passages)} passages.")
for p in res.passages[:5]:
    print(f"[{p.passage_id}] score={p.score:.4f} doc={p.document_filename} page={p.page_number}")
    print(f"  {p.text[:120]}...\n")

ctrl = get_evidence_controller()
dec = ctrl.evaluate_evidence(qa, res.passages)
print(f"Evidence Decision: status={dec.status}, sufficient_count={dec.sufficient_count}, top_score={dec.top_score}")
print(f"Explanation: {dec.explanation}")

