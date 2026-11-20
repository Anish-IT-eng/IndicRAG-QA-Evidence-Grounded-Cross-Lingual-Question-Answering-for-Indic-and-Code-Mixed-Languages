import sys
from pathlib import Path
import csv
import json

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.models.schemas import DocumentSource
from app.query.processor import process_query
from app.retrieval.engine import retrieve
from app.retrieval.evidence_controller import get_evidence_controller
from app.core.database import get_db

controller = get_evidence_controller()

cids = [
    '8820214e-35a3-4176-9a87-d6a681c62c24',
    'fe70960c-f447-4fd4-88c7-20572e422fb0',
    'b0a1c002-87a2-4102-9002-000000000002',
    '6776bafc-4389-4d2f-8025-d37a604d177b',
    'b0a1c001-87a1-4101-9001-000000000001',
    'b0a1c004-87a4-4104-9004-000000000004',
    'b0a1c006-87a6-4106-9006-000000000006',
    '01fc5ad1-43a1-443f-beda-e82970d2a7cb',
    'b0a1c005-87a5-4105-9005-000000000005',
    'c60a-e03-000000000003',
    'c60a-e08-000000000008',
    'c60a-h02-000000000012',
    'c60a-h05-000000000015',
]

with open(backend_dir / 'data/dataset/m6_benchmark_qualification.csv', 'r', encoding='utf-8') as f:
    qual_rows = {r['candidate_id']: r for r in csv.DictReader(f)}

with get_db() as conn:
    doc_map = {row['document_id']: dict(row) for row in conn.execute('SELECT * FROM documents').fetchall()}

results = []
for cid in cids:
    q_row = qual_rows[cid]
    q_text = q_row['original_question']
    qa = process_query(q_text)
    rr = retrieve(qa, collections=[DocumentSource.OFFICIAL], top_k=5, use_reranker=True)
    valid, conf = controller._split_passages(rr.retrieved_passages)
    
    dec = controller.evaluate(rr, attempt=1)
    
    top_valid = valid[0] if valid else None
    top_conf = conf[0] if conf else None
    
    doc_v = doc_map.get(top_valid.document_id, {}) if top_valid else {}
    doc_c = doc_map.get(top_conf.document_id, {}) if top_conf else {}
    
    print(f"=== Candidate: {cid} ===")
    print(f"Query: {q_text}")
    print(f"Expected State: {q_row.get('expected_evidence_state')}")
    print(f"Controller Status: {dec.status.value}")
    print(f"Top Valid: doc={doc_v.get('filename')} AY={doc_v.get('academic_year')} score={top_valid.score if top_valid else None:.3f}")
    if top_valid:
        print(f"  Valid Text: {top_valid.text[:100]}...")
    print(f"Top Conflicting: doc={doc_c.get('filename')} AY={doc_c.get('academic_year')} score={top_conf.score if top_conf else None:.3f}")
    if top_conf:
        print(f"  Conflicting Text: {top_conf.text[:100]}...")
    print(f"Explanation: {dec.explanation}\n")

