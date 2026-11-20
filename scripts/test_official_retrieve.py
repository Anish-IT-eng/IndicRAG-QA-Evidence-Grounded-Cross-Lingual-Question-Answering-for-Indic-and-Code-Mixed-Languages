import sys
sys.path.insert(0, 'backend')
from app.models.schemas import DocumentSource
from app.query.processor import process_query
from app.retrieval.engine import retrieve
from app.retrieval.evidence_controller import get_evidence_controller

q = "What are the three options available to a student for doing the final semester?"
qa = process_query(q)
res = retrieve(qa, [DocumentSource.OFFICIAL], use_reranker=True, use_pdr=True)
ctrl = get_evidence_controller()
dec = ctrl.evaluate(res)
print(f"Evidence Decision: status={dec.status}")
print(f"Valid passages count: {len(dec.valid_passages)}")
print(f"Explanation: {dec.explanation}")
