"""
Phase G: Ablation Experiments.
Compares retrieval and ranking interventions across the M9 answerable benchmark (180 queries):
1. Config-1: Pure BM25 Lexical
2. Config-2: Pure Dense Semantic (paraphrase-multilingual-MiniLM-L12-v2)
3. Config-3: Raw Query + Hybrid RRF (BM25 + Dense)
4. Config-4: Normalized Query + Hybrid RRF
5. Config-5: Production Adaptive Routing (AdaptiveRouter + Reranker + PDR)

Outputs:
- backend/data/experiments/m9/m9_ablation_results.csv
"""
import json
import csv
import math
import time
import sys
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

sys.path.insert(0, os.path.abspath("backend"))

from app.query.processor import process_query, normalize_text
from app.retrieval.engine import (
    retrieve,
    get_official_index,
    _rrf_fuse,
    rerank,
    expand_to_parents,
    validate_versions,
)
from app.retrieval.router import route_query, RoutingStrategy
from app.models.schemas import DocumentSource, QueryAnalysis, QueryLanguage

# Load dataset
queries = []
with open("backend/data/experiments/m9/m9_evaluation_dataset.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            queries.append(json.loads(line))

ans_queries = [q for q in queries if q["expected_status"] == "ANSWERED"]
print(f"Loaded {len(ans_queries)} answerable queries for ablation experiments.", flush=True)

idx = get_official_index()

def eval_candidate_pids(candidates, expected_pids):
    retrieved_pids = [pid for pid, _, _ in candidates[:5]]
    ranks = [r for r, pid in enumerate(retrieved_pids, 1) if pid in expected_pids]
    hit_1 = 1 if (ranks and ranks[0] == 1) else 0
    hit_3 = 1 if (ranks and ranks[0] <= 3) else 0
    hit_5 = 1 if (ranks and ranks[0] <= 5) else 0
    rr = 1.0 / ranks[0] if ranks else 0.0
    dcg = sum(1.0 / math.log2(r + 1) for r in ranks)
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, min(len(expected_pids), 5) + 1))
    ndcg_5 = dcg / idcg if idcg > 0 else 0.0
    rec_5 = len(set(retrieved_pids) & set(expected_pids)) / len(expected_pids) if expected_pids else 0.0
    return hit_1, hit_3, hit_5, rr, ndcg_5, rec_5

configs = [
    ("Config-1: Pure BM25 Lexical", "PURE_BM25"),
    ("Config-2: Pure Dense Semantic", "PURE_DENSE"),
    ("Config-3: Raw Query + Hybrid RRF", "RAW_HYBRID_RRF"),
    ("Config-4: Normalized Query + Hybrid RRF", "NORMALIZED_HYBRID_RRF"),
    ("Config-5: Production Adaptive Routing", "ADAPTIVE_ROUTER"),
]

ablation_results = []

for cfg_name, cfg_id in configs:
    print(f"\nRunning ablation: {cfg_name}...", flush=True)
    t_cfg_start = time.perf_counter()
    
    per_lang_stats = {
        "en": {"hit_1": 0, "hit_3": 0, "hit_5": 0, "mrr": 0.0, "ndcg_5": 0.0, "rec_5": 0.0, "lat": 0.0, "n": 0},
        "hi": {"hit_1": 0, "hit_3": 0, "hit_5": 0, "mrr": 0.0, "ndcg_5": 0.0, "rec_5": 0.0, "lat": 0.0, "n": 0},
        "hi-Latn": {"hit_1": 0, "hit_3": 0, "hit_5": 0, "mrr": 0.0, "ndcg_5": 0.0, "rec_5": 0.0, "lat": 0.0, "n": 0},
        "en-hi": {"hit_1": 0, "hit_3": 0, "hit_5": 0, "mrr": 0.0, "ndcg_5": 0.0, "rec_5": 0.0, "lat": 0.0, "n": 0},
    }
    
    for q in ans_queries:
        lang = q["query_language"]
        raw_text = q["query_text"]
        expected_pids = set(q.get("expected_passage_ids", []))
        
        t0 = time.perf_counter()
        
        if cfg_id == "PURE_BM25":
            qa = process_query(raw_text, enable_translation=False)
            q_text = qa.normalized_query or raw_text
            candidates = idx.bm25_search(q_text, 5)
            
        elif cfg_id == "PURE_DENSE":
            qa = process_query(raw_text, enable_translation=False)
            q_text = qa.normalized_query or raw_text
            candidates = idx.dense_search(q_text, 5)
            
        elif cfg_id == "RAW_HYBRID_RRF":
            bm25_hits = idx.bm25_search(raw_text, 10)
            dense_hits = idx.dense_search(raw_text, 10)
            candidates = _rrf_fuse(bm25_hits, dense_hits)[:5]
            
        elif cfg_id == "NORMALIZED_HYBRID_RRF":
            qa = process_query(raw_text, enable_translation=False)
            q_text = qa.normalized_query or raw_text
            bm25_hits = idx.bm25_search(q_text, 10)
            dense_hits = idx.dense_search(q_text, 10)
            candidates = _rrf_fuse(bm25_hits, dense_hits)[:5]
            
        elif cfg_id == "ADAPTIVE_ROUTER":
            qa = process_query(raw_text, enable_translation=False)
            ret_res = retrieve(qa, collections=[DocumentSource.OFFICIAL], top_k=5, use_reranker=True, use_pdr=True)
            candidates = [(p.passage_id, p.score, {"text": p.text, "document_id": p.document_id}) for p in ret_res.retrieved_passages]
            
        lat = (time.perf_counter() - t0) * 1000.0
        
        h1, h3, h5, rr, ndcg, rec = eval_candidate_pids(candidates, expected_pids)
        
        st = per_lang_stats[lang]
        st["hit_1"] += h1
        st["hit_3"] += h3
        st["hit_5"] += h5
        st["mrr"] += rr
        st["ndcg_5"] += ndcg
        st["rec_5"] += rec
        st["lat"] += lat
        st["n"] += 1

    # Record metrics for each language and overall
    total_n = sum(st["n"] for st in per_lang_stats.values())
    total_h1 = sum(st["hit_1"] for st in per_lang_stats.values())
    total_h3 = sum(st["hit_3"] for st in per_lang_stats.values())
    total_h5 = sum(st["hit_5"] for st in per_lang_stats.values())
    total_mrr = sum(st["mrr"] for st in per_lang_stats.values())
    total_ndcg = sum(st["ndcg_5"] for st in per_lang_stats.values())
    total_lat = sum(st["lat"] for st in per_lang_stats.values())
    
    for lang in ["en", "hi", "hi-Latn", "en-hi"]:
        st = per_lang_stats[lang]
        n = st["n"]
        ablation_results.append({
            "configuration": cfg_name,
            "config_id": cfg_id,
            "language": lang,
            "sample_size": n,
            "hit_at_1": round(st["hit_1"] / n, 4) if n else 0.0,
            "hit_at_3": round(st["hit_3"] / n, 4) if n else 0.0,
            "hit_at_5": round(st["hit_5"] / n, 4) if n else 0.0,
            "mrr": round(st["mrr"] / n, 4) if n else 0.0,
            "ndcg_at_5": round(st["ndcg_5"] / n, 4) if n else 0.0,
            "avg_latency_ms": round(st["lat"] / n, 2) if n else 0.0,
        })
        
    ablation_results.append({
        "configuration": cfg_name,
        "config_id": cfg_id,
        "language": "OVERALL",
        "sample_size": total_n,
        "hit_at_1": round(total_h1 / total_n, 4),
        "hit_at_3": round(total_h3 / total_n, 4),
        "hit_at_5": round(total_h5 / total_n, 4),
        "mrr": round(total_mrr / total_n, 4),
        "ndcg_at_5": round(total_ndcg / total_n, 4),
        "avg_latency_ms": round(total_lat / total_n, 2),
    })
    
    print(f"Completed {cfg_name} in {time.perf_counter()-t_cfg_start:.2f}s | Overall Hit@5: {total_h5/total_n:.4f} | MRR: {total_mrr/total_n:.4f}", flush=True)

# Write CSV
with open("backend/data/experiments/m9/m9_ablation_results.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "configuration", "config_id", "language", "sample_size",
        "hit_at_1", "hit_at_3", "hit_at_5", "mrr", "ndcg_at_5", "avg_latency_ms"
    ])
    writer.writeheader()
    writer.writerows(ablation_results)

print("\nAblation experiments finished! Output saved to backend/data/experiments/m9/m9_ablation_results.csv", flush=True)
