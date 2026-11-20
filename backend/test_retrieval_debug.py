import sys
sys.path.insert(0, 'backend')

from app.retrieval.engine import retrieve
from app.query.processor import process_query

queries = [
    'When will odd semester end semester examinations start?',
    'When will odd semester examinations start?',
    'When will the odd semester make-up examination date sheet be displayed?',
    'What happens on 18 January 2027?'
]

for q in queries:
    print('='*75)
    print('QUERY:', q)
    qa = process_query(q)
    res = retrieve(qa, collections=['official'], top_k=3, use_reranker=True)
    for i, p in enumerate(res.retrieved_passages):
        print(f"Rank {i+1} [p.{p.page_number}] score={p.score:.3f} rerank={p.rerank_score}")
        print(f"   Text: {p.text[:140]}...")
