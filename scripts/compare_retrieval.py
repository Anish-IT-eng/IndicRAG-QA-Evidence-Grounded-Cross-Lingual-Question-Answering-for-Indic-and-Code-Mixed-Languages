import sys
sys.path.insert(0, 'backend')
from app.query.processor import process_query
from app.retrieval.engine import retrieve
from app.models.schemas import DocumentSource

qa_en = process_query('When do odd semester end semester examinations start and finish?')
qa_hi = process_query('विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?')

print("EN norm:", qa_en.normalized_query)
print("HI norm:", qa_hi.normalized_query)

res_en = retrieve(query_analysis=qa_en, collections=[DocumentSource.OFFICIAL], top_k=6, use_reranker=True)
res_hi = retrieve(query_analysis=qa_hi, collections=[DocumentSource.OFFICIAL], top_k=6, use_reranker=True)

print("\n--- EN PASSAGES ---")
for p in res_en.retrieved_passages[:6]:
    print(p.passage_id, p.page_number, p.heading)

print("\n--- HI PASSAGES ---")
for p in res_hi.retrieved_passages[:6]:
    print(p.passage_id, p.page_number, p.heading)
