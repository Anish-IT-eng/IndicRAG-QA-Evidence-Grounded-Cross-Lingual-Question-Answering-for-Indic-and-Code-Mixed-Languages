import sys
sys.path.insert(0, 'backend')
from app.query.processor import process_query
from app.retrieval.multi_hop_reasoner import MultiHopReasoner

qa = process_query('विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?')
reasoner = MultiHopReasoner(max_hops=3, max_evidence_items=12)
ev = reasoner.reason(qa)
for idx, p in enumerate(ev.all_passages):
    print(f"[{idx+1}] ID: {p.passage_id} | Page: {p.page_number} | Doc: {p.document_id}")
    print(p.text[:200])
    print("-" * 50)
