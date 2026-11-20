import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "backend"))

from app.models.schemas import DocumentSource, QueryScript, QueryLanguage
from app.query.processor import process_query
from app.retrieval.engine import get_official_index, retrieve

def test_engine_strategies():
    idx = get_official_index()
    if not idx.is_ready():
        idx.load()
        
    m9_file = root / "backend" / "data" / "experiments" / "m9" / "m9_evaluation_dataset.jsonl"
    with open(m9_file, "r", encoding="utf-8") as f:
        m9_queries = [json.loads(line) for line in f]
        
    # Test on M9-Q001 (en) and M9-Q002 (hi)
    q_en = next(q for q in m9_queries if q["query_id"] == "M9-Q001")
    q_hi = next(q for q in m9_queries if q["query_id"] == "M9-Q002")
    
    qa_en = process_query(q_en["query_text"])
    qa_hi = process_query(q_hi["query_text"])
    
    # 1. Production retrieve
    res_en_prod = retrieve(qa_en, [DocumentSource.OFFICIAL], top_k=5)
    res_hi_prod = retrieve(qa_hi, [DocumentSource.OFFICIAL], top_k=5)
    
    pids_en_prod = [p.passage_id for p in res_en_prod.retrieved_passages]
    pids_hi_prod = [p.passage_id for p in res_hi_prod.retrieved_passages]
    
    print(f"M9-Q001 (en) Prod PIDs: {pids_en_prod}")
    print(f"M9-Q001 (en) Target in top 5? {q_en['expected_passage_ids'][0] in pids_en_prod}")
    
    print(f"M9-Q002 (hi) Prod PIDs: {pids_hi_prod}")
    print(f"M9-Q002 (hi) Target in top 5? {q_hi['expected_passage_ids'][0] in pids_hi_prod}")

    # 2. Test dense search directly for M9-Q002
    dense_hits_hi = idx.dense_search(qa_hi.original_query, 10)
    pids_hi_dense = [h[0] for h in dense_hits_hi[:5]]
    print(f"\nM9-Q002 (hi) Dense PIDs: {pids_hi_dense}")
    print(f"M9-Q002 (hi) Dense Target in top 5? {q_hi['expected_passage_ids'][0] in pids_hi_dense}")

if __name__ == "__main__":
    test_engine_strategies()
