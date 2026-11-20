import sys
sys.path.insert(0, 'backend')

from app.query.processor import process_query
from app.retrieval.engine import retrieve
from app.retrieval.evidence_controller import EvidenceController
from app.models.schemas import DocumentSource

controller = EvidenceController()

queries = [
    'What is the minimum attendance required?',
    'What attendance is required to sit for end semester exams?',
    'How much attendance is required to avoid an X grade?',
    'Is 70% attendance enough?',
    'Is 75% compulsory for SCSET students?',
    'What was the attendance rule in 2017?',
    'Can attendance be relaxed due to medical reasons?'
]

for i, q in enumerate(queries, 1):
    qa = process_query(q)
    res = retrieve(qa, collections=[DocumentSource.OFFICIAL], top_k=5)
    dec = controller.evaluate(res)
    print(f'=== Query {i}: {q} ===')
    print(f'Status: {dec.status.value}')
    print(f'Clarification Needed: {dec.clarification_needed}')
    print(f'Explanation: {dec.explanation}')
    docs = set(p.document_id for p in res.retrieved_passages)
    print(f'Retrieved Passages Count: {len(res.retrieved_passages)} across {len(docs)} docs')
    for p in res.retrieved_passages:
        doc_abbr = p.document_id[:8]
        is_cur = p.version_info.is_current if p.version_info else None
        sup = p.version_info.superseded_by if p.version_info else None
        print(f'  pid={p.passage_id[:8]} doc={doc_abbr} score={p.score:.3f} cur={is_cur} sup={sup}')
    print()
