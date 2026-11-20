"""
Phase C: Controlled Retrieval Baselines Evaluation Script.
Executes Experiments E1 to E5 across all 4 language formulations (180 answerable queries).
Computes Hit@1, Hit@3, Hit@5, MRR, nDCG@5, Recall@5, Mean, Median, and p95 latencies.
Outputs:
- backend/data/experiments/m10/m10_baseline_ablation_results.csv
"""
import json
import csv
import math
import time
import sys
import os
import numpy as np

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

sys.path.insert(0, os.path.abspath("backend"))

from app.query.processor import process_query
from app.retrieval.engine import (
    get_official_index,
    get_cross_encoder,
    _rrf_fuse,
    _deduplicate,
    validate_versions,
    expand_to_parents,
)
from app.models.schemas import DocumentSource

def calc_ndcg(ranks, n_expected, k=5):
    dcg = sum(1.0 / math.log2(r + 1) for r in ranks if r <= k)
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, min(n_expected, k) + 1))
    return dcg / idcg if idcg > 0 else 0.0

def evaluate_config(queries, config_name, config_id, run_fn):
    print(f"\n--- Running Experiment: {config_name} ({config_id}) ---")
    results_by_lang = {l: [] for l in ["en", "hi", "hi-Latn", "en-hi"]}

    for q in queries:
        qid = q["query_id"]
        lang = q["query_language"]
        exp_pids = set(q.get("expected_passage_ids", []))
        if not exp_pids:
            continue

        t0 = time.perf_counter()
        retrieved_pids = run_fn(q)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        ranks = []
        for r_idx, pid in enumerate(retrieved_pids[:5], 1):
            if pid in exp_pids:
                ranks.append(r_idx)

        hit_1 = 1 if (ranks and ranks[0] == 1) else 0
        hit_3 = 1 if (ranks and ranks[0] <= 3) else 0
        hit_5 = 1 if (ranks and ranks[0] <= 5) else 0
        mrr = (1.0 / ranks[0]) if ranks else 0.0
        ndcg_5 = calc_ndcg(ranks, len(exp_pids), k=5)
        rec_5 = len(set(retrieved_pids[:5]) & exp_pids) / len(exp_pids)

        results_by_lang[lang].append({
            "hit_1": hit_1,
            "hit_3": hit_3,
            "hit_5": hit_5,
            "mrr": mrr,
            "ndcg_5": ndcg_5,
            "recall_5": rec_5,
            "latency_ms": lat_ms
        })

    summary_rows = []
    for lang in ["en", "hi", "hi-Latn", "en-hi"]:
        res_list = results_by_lang[lang]
        n = len(res_list)
        lats = [r["latency_ms"] for r in res_list]
        summary_rows.append({
            "experiment": config_name,
            "config_id": config_id,
            "language": lang,
            "sample_size": n,
            "hit_at_1": round(sum(r["hit_1"] for r in res_list) / n, 4),
            "hit_at_3": round(sum(r["hit_3"] for r in res_list) / n, 4),
            "hit_at_5": round(sum(r["hit_5"] for r in res_list) / n, 4),
            "mrr": round(sum(r["mrr"] for r in res_list) / n, 4),
            "ndcg_at_5": round(sum(r["ndcg_5"] for r in res_list) / n, 4),
            "recall_at_5": round(sum(r["recall_5"] for r in res_list) / n, 4),
            "mean_latency_ms": round(float(np.mean(lats)), 2),
            "median_latency_ms": round(float(np.median(lats)), 2),
            "p95_latency_ms": round(float(np.percentile(lats, 95)), 2),
        })

    # Overall
    all_res = [r for sub in results_by_lang.values() for r in sub]
    n_all = len(all_res)
    all_lats = [r["latency_ms"] for r in all_res]
    summary_rows.append({
        "experiment": config_name,
        "config_id": config_id,
        "language": "OVERALL",
        "sample_size": n_all,
        "hit_at_1": round(sum(r["hit_1"] for r in all_res) / n_all, 4),
        "hit_at_3": round(sum(r["hit_3"] for r in all_res) / n_all, 4),
        "hit_at_5": round(sum(r["hit_5"] for r in all_res) / n_all, 4),
        "mrr": round(sum(r["mrr"] for r in all_res) / n_all, 4),
        "ndcg_at_5": round(sum(r["ndcg_5"] for r in all_res) / n_all, 4),
        "recall_at_5": round(sum(r["recall_5"] for r in all_res) / n_all, 4),
        "mean_latency_ms": round(float(np.mean(all_lats)), 2),
        "median_latency_ms": round(float(np.median(all_lats)), 2),
        "p95_latency_ms": round(float(np.percentile(all_lats, 95)), 2),
    })

    for row in summary_rows:
        print(f"[{row['language']:7s}] Hit@1: {row['hit_at_1']:.4f} | Hit@5: {row['hit_at_5']:.4f} | MRR: {row['mrr']:.4f} | nDCG@5: {row['ndcg_at_5']:.4f} | Mean Lat: {row['mean_latency_ms']}ms")

    return summary_rows

def main():
    queries = []
    with open("backend/data/experiments/m9/m9_evaluation_dataset.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))

    answerable_queries = [q for q in queries if q["expected_status"] == "ANSWERED"]
    print(f"Loaded {len(answerable_queries)} answerable queries across 4 languages.")

    idx = get_official_index()
    cross_enc = get_cross_encoder()

    # E1: Current Production Pipeline (Depth=10 with ms-marco Reranker)
    def run_e1(q):
        qa = process_query(q["query_text"], enable_translation=False)
        query_str = qa.normalized_query or qa.original_query
        bm25_hits = idx.bm25_search(query_str, top_k=10)
        dense_hits = idx.dense_search(query_str, top_k=10)
        fused = _rrf_fuse(bm25_hits, dense_hits)
        for pid, score, meta in fused:
            if "text" not in meta:
                try: meta["text"] = idx.passage_texts[idx.passage_ids.index(pid)]
                except ValueError: pass
        fused = _deduplicate(fused)
        fused = validate_versions(fused, None, None, qa)
        pairs = [(query_str, meta.get("text", "")) for _, _, meta in fused]
        scores = cross_enc.predict(pairs)
        ranked = sorted(zip(fused, scores), key=lambda x: x[1], reverse=True)
        return [h[0][0] for h in ranked[:5]]

    # E2: No-Reranker Baseline (Depth=10, Hybrid RRF directly)
    def run_e2(q):
        qa = process_query(q["query_text"], enable_translation=False)
        query_str = qa.normalized_query or qa.original_query
        bm25_hits = idx.bm25_search(query_str, top_k=10)
        dense_hits = idx.dense_search(query_str, top_k=10)
        fused = _rrf_fuse(bm25_hits, dense_hits)
        for pid, score, meta in fused:
            if "text" not in meta:
                try: meta["text"] = idx.passage_texts[idx.passage_ids.index(pid)]
                except ValueError: pass
        fused = _deduplicate(fused)
        fused = validate_versions(fused, None, None, qa)
        return [h[0] for h in fused[:5]]

    # E3: Bi-Encoder Only Ranking (Dense FAISS FlatL2)
    def run_e3(q):
        qa = process_query(q["query_text"], enable_translation=False)
        query_str = qa.normalized_query or qa.original_query
        dense_hits = idx.dense_search(query_str, top_k=5)
        return [h[0] for h in dense_hits[:5]]

    # E4a: Reranker with Candidate Depth = 5
    def run_e4a(q):
        qa = process_query(q["query_text"], enable_translation=False)
        query_str = qa.normalized_query or qa.original_query
        bm25_hits = idx.bm25_search(query_str, top_k=5)
        dense_hits = idx.dense_search(query_str, top_k=5)
        fused = _rrf_fuse(bm25_hits, dense_hits)
        for pid, score, meta in fused:
            if "text" not in meta:
                try: meta["text"] = idx.passage_texts[idx.passage_ids.index(pid)]
                except ValueError: pass
        fused = _deduplicate(fused)
        fused = validate_versions(fused, None, None, qa)
        pairs = [(query_str, meta.get("text", "")) for _, _, meta in fused]
        scores = cross_enc.predict(pairs)
        ranked = sorted(zip(fused, scores), key=lambda x: x[1], reverse=True)
        return [h[0][0] for h in ranked[:5]]

    # E4b: Reranker with Candidate Depth = 20
    def run_e4b(q):
        qa = process_query(q["query_text"], enable_translation=False)
        query_str = qa.normalized_query or qa.original_query
        bm25_hits = idx.bm25_search(query_str, top_k=20)
        dense_hits = idx.dense_search(query_str, top_k=20)
        fused = _rrf_fuse(bm25_hits, dense_hits)
        for pid, score, meta in fused:
            if "text" not in meta:
                try: meta["text"] = idx.passage_texts[idx.passage_ids.index(pid)]
                except ValueError: pass
        fused = _deduplicate(fused)
        fused = validate_versions(fused, None, None, qa)
        pairs = [(query_str, meta.get("text", "")) for _, _, meta in fused]
        scores = cross_enc.predict(pairs)
        ranked = sorted(zip(fused, scores), key=lambda x: x[1], reverse=True)
        return [h[0][0] for h in ranked[:5]]

    # E5: Hybrid Retrieval without Reranker at Depth = 20
    def run_e5(q):
        qa = process_query(q["query_text"], enable_translation=False)
        query_str = qa.normalized_query or qa.original_query
        bm25_hits = idx.bm25_search(query_str, top_k=20)
        dense_hits = idx.dense_search(query_str, top_k=20)
        fused = _rrf_fuse(bm25_hits, dense_hits)
        for pid, score, meta in fused:
            if "text" not in meta:
                try: meta["text"] = idx.passage_texts[idx.passage_ids.index(pid)]
                except ValueError: pass
        fused = _deduplicate(fused)
        fused = validate_versions(fused, None, None, qa)
        return [h[0] for h in fused[:5]]

    all_rows = []
    all_rows.extend(evaluate_config(answerable_queries, "E1: Current Production Pipeline (Depth=10 + ms-marco)", "E1_PROD", run_e1))
    all_rows.extend(evaluate_config(answerable_queries, "E2: No-Reranker Hybrid Baseline (Depth=10)", "E2_NO_RERANK_D10", run_e2))
    all_rows.extend(evaluate_config(answerable_queries, "E3: Bi-Encoder Only Ranking (Dense FAISS)", "E3_BI_ENCODER_ONLY", run_e3))
    all_rows.extend(evaluate_config(answerable_queries, "E4a: Controlled Depth Reranking (Depth=5 + ms-marco)", "E4A_RERANK_D5", run_e4a))
    all_rows.extend(evaluate_config(answerable_queries, "E4b: Controlled Depth Reranking (Depth=20 + ms-marco)", "E4B_RERANK_D20", run_e4b))
    all_rows.extend(evaluate_config(answerable_queries, "E5: Controlled Depth Hybrid without Reranker (Depth=20)", "E5_NO_RERANK_D20", run_e5))

    out_csv = "backend/data/experiments/m10/m10_baseline_ablation_results.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nSaved all baseline ablation results to {out_csv}")

if __name__ == "__main__":
    main()
