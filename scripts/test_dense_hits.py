import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "backend"))

import numpy as np
from app.models.schemas import DocumentSource, QueryScript, QueryLanguage
from app.query.processor import process_query
from app.retrieval.engine import get_official_index, get_embedding_model

def verify_dense_rerank_devanagari():
    idx = get_official_index()
    if not idx.is_ready():
        idx.load()
        
    m9_file = root / "backend" / "data" / "experiments" / "m9" / "m9_evaluation_dataset.jsonl"
    with open(m9_file, "r", encoding="utf-8") as f:
        m9_queries = [json.loads(line) for line in f]
        
    hi_queries = [q for q in m9_queries if q["query_language"] == "hi" and q.get("expected_status") == "ANSWERED"]
    print(f"Total answerable Devanagari queries: {len(hi_queries)}")
    
    hits_5 = 0
    model = get_embedding_model()
    
    for item in hi_queries:
        q_text = item["query_text"]
        exp_pids = set(item.get("expected_passage_ids", []))
        
        # Dense search top 10
        dense_hits = idx.dense_search(q_text, 10)
        bm25_hits = idx.bm25_search(q_text, 10)
        
        # Compute dense similarity for all dense_hits
        pids_e3 = [h[0] for h in dense_hits[:5]]
        
        # Check if hit in top 5
        if exp_pids & set(pids_e3):
            hits_5 += 1
            print(f"Hit on {item['query_id']}: {exp_pids & set(pids_e3)}")
            
    print(f"Total Hits@5 for pure dense E3: {hits_5}/{len(hi_queries)} = {hits_5 / len(hi_queries):.4f}")

if __name__ == "__main__":
    verify_dense_rerank_devanagari()
