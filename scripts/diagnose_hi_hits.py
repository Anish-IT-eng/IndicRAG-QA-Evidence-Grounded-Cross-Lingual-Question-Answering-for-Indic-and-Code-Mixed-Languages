import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "backend"))

from app.models.schemas import DocumentSource, QueryScript, QueryLanguage
from app.query.processor import process_query
from app.retrieval.engine import (
    get_official_index,
    _deduplicate,
    validate_versions,
    expand_to_parents,
)

def diagnose():
    idx = get_official_index()
    if not idx.is_ready():
        idx.load()
        
    m9_file = root / "backend" / "data" / "experiments" / "m9" / "m9_evaluation_dataset.jsonl"
    with open(m9_file, "r", encoding="utf-8") as f:
        m9_queries = [json.loads(line) for line in f]
        
    target_qids = ["M9-Q002", "M9-Q010", "M9-Q014", "M9-Q030"]
    for qid in target_qids:
        q = next(item for item in m9_queries if item["query_id"] == qid)
        qa = process_query(q["query_text"])
        exp_pids = set(q.get("expected_passage_ids", []))
        
        # Step 1: dense search
        hits = idx.dense_search(qa.original_query, 10)
        pids_s1 = [h[0] for h in hits[:5]]
        
        # Step 2: deduplicate
        dedup = _deduplicate(hits)
        pids_s2 = [h[0] for h in dedup[:5]]
        
        # Step 3: validate_versions
        val = validate_versions(dedup, None, None, qa)
        pids_s3 = [h[0] for h in val[:5]]
        
        # Step 4: expand_to_parents
        exp = expand_to_parents(val, idx)
        pids_s4 = [h[0] for h in exp[:5]]
        
        print(f"\n--- {qid} ---")
        print(f"Target: {exp_pids}")
        print(f"Step 1 (Dense top 5): {pids_s1} -> Hit: {bool(exp_pids & set(pids_s1))}")
        print(f"Step 2 (Dedup top 5): {pids_s2} -> Hit: {bool(exp_pids & set(pids_s2))}")
        print(f"Step 3 (Validate top 5): {pids_s3} -> Hit: {bool(exp_pids & set(pids_s3))}")
        print(f"Step 4 (Parents top 5): {pids_s4} -> Hit: {bool(exp_pids & set(pids_s4))}")

if __name__ == "__main__":
    diagnose()
