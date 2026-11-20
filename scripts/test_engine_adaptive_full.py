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
    rerank,
    RetrievalResult,
    RetrievedPassage,
    DocumentVersionInfo,
    classify_passage_condition
)

def retrieve_adaptive_test(
    query_analysis,
    collections,
    top_k=5,
    rerank_strategy="adaptive_e6b"
):
    primary_query = query_analysis.normalized_query or query_analysis.original_query
    indexes = [get_official_index()]
    
    is_devanagari = (
        getattr(query_analysis, "detected_script", None) == QueryScript.DEVANAGARI
        or (
            getattr(query_analysis, "detected_language", None) == QueryLanguage.HINDI
            and getattr(query_analysis, "detected_script", None) != QueryScript.MIXED
        )
        or any("\u0900" <= ch <= "\u097f" for ch in primary_query)
    )
    
    if rerank_strategy == "adaptive_e6b" and is_devanagari:
        # Route Devanagari directly to dense bi-encoder candidates
        all_candidates = []
        for idx in indexes:
            hits = idx.dense_search(primary_query, top_k * 2)
            for pid, score, meta in hits:
                if "text" not in meta:
                    try:
                        tidx = idx.passage_ids.index(pid)
                        meta["text"] = idx.passage_texts[tidx]
                    except ValueError:
                        pass
            all_candidates.extend(hits)
        top_candidates = all_candidates[:top_k]
        return [pid for pid, _, _ in top_candidates]
    else:
        # Production hybrid + cross-encoder
        all_candidates = []
        for idx in indexes:
            bm25_hits = idx.bm25_search(primary_query, top_k * 2)
            dense_hits = idx.dense_search(primary_query, top_k * 2)
            from app.retrieval.engine import _rrf_fuse
            fused = _rrf_fuse(bm25_hits, dense_hits)
            for pid, score, meta in fused:
                if "text" not in meta:
                    try:
                        tidx = idx.passage_ids.index(pid)
                        meta["text"] = idx.passage_texts[tidx]
                    except ValueError:
                        pass
            all_candidates.extend(fused)
            
        all_candidates = _deduplicate(all_candidates)
        all_candidates = validate_versions(all_candidates, None, None, query_analysis)
        all_candidates = rerank(primary_query, all_candidates, top_k=top_k * 2)
        all_candidates = expand_to_parents(all_candidates, indexes[0])
        top_candidates = all_candidates[:top_k]
        return [pid for pid, _, _ in top_candidates]

def main():
    m9_file = root / "backend" / "data" / "experiments" / "m9" / "m9_evaluation_dataset.jsonl"
    with open(m9_file, "r", encoding="utf-8") as f:
        m9_queries = [json.loads(line) for line in f]
        
    for lang in ["en", "hi", "hi-Latn", "en-hi"]:
        ans_queries = [q for q in m9_queries if q["query_language"] == lang and q.get("expected_status") == "ANSWERED"]
        hits = 0
        for q in ans_queries:
            qa = process_query(q["query_text"])
            top_pids = retrieve_adaptive_test(qa, [DocumentSource.OFFICIAL], top_k=5, rerank_strategy="adaptive_e6b")
            exp_pids = set(q.get("expected_passage_ids", []))
            if exp_pids & set(top_pids):
                hits += 1
        print(f"Adaptive E6b Hit@5 for {lang}: {hits}/{len(ans_queries)} = {hits/len(ans_queries):.4f}")

if __name__ == "__main__":
    main()
