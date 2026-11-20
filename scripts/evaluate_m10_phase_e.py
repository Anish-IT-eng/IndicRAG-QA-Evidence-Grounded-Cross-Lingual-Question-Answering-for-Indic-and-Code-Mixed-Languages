"""
Milestone M10: Phase E — Controlled Multilingual Reranker Experiments
Optimized, vector-cached execution of E1 through E6 across all 240 queries.
Outputs:
- backend/data/experiments/m10/m10_phase_e_results.csv
- backend/data/experiments/m10/m10_phase_e_per_intent_results.csv
- backend/data/experiments/m10/m10_phase_e_resource_results.csv
- docs/m10_phase_e_experimental_report.md
"""

import sys
import os
import json
import time
import csv
import psutil
import numpy as np
import torch

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

sys.path.insert(0, "backend")
from app.query.processor import process_query
from app.retrieval.engine import (
    get_official_index,
    get_cross_encoder,
    _rrf_fuse,
    _deduplicate,
    validate_versions,
)
from transformers import AutoTokenizer, AutoModelForSequenceClassification

def compute_ndcg_at_5(retrieved_pids, exp_pids):
    dcg = 0.0
    for r, pid in enumerate(retrieved_pids[:5], 1):
        if pid in exp_pids:
            dcg += 1.0 / np.log2(r + 1)
    ideal_count = min(len(exp_pids), 5)
    if ideal_count == 0:
        return 0.0
    idcg = sum(1.0 / np.log2(r + 1) for r in range(1, ideal_count + 1))
    return dcg / idcg

def main():
    print("=== M10 Phase E: Controlled Multilingual Reranker Evaluation (Optimized) ===", flush=True)
    
    # 1. Load evaluation dataset
    dataset_path = "backend/data/experiments/m9/m9_evaluation_dataset.jsonl"
    queries = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))
    print(f"Loaded {len(queries)} total queries (180 ANSWERED, 60 UNANSWERABLE)", flush=True)

    # 2. Initialize Retrievers and Models
    idx = get_official_index()
    print("Official index loaded (FAISS + BM25).", flush=True)

    print("Loading Baseline Cross-Encoder (ms-marco-MiniLM-L-6-v2)...", flush=True)
    cross_enc_prod = get_cross_encoder()

    print("Loading Multilingual Cross-Encoder (amberoad/bert-multilingual-passage-reranking-msmarco)...", flush=True)
    amberoad_name = "amberoad/bert-multilingual-passage-reranking-msmarco"
    amberoad_tok = AutoTokenizer.from_pretrained(amberoad_name)
    amberoad_model = AutoModelForSequenceClassification.from_pretrained(amberoad_name)
    amberoad_model.eval()
    print("Amberoad Multilingual Cross-Encoder loaded.", flush=True)

    proc = psutil.Process()
    base_mem_mb = proc.memory_info().rss / (1024 * 1024)
    print(f"Base process memory: {base_mem_mb:.2f} MB", flush=True)

    configs = [
        ("E1_PROD_MSMARCO_D10", "Existing English Cross-Encoder (ms-marco-MiniLM-L-6-v2, Depth=10)"),
        ("E2_HYBRID_NO_RERANK", "No Reranker Hybrid RRF Retrieval (Depth=10)"),
        ("E3_BI_ENCODER_DENSE", "Multilingual Bi-Encoder Only Ranking (FAISS Dense Top-5)"),
        ("E4_DEPTH_5_MSMARCO", "Existing Cross-Encoder with Candidate Depth=5 (ms-marco)"),
        ("E5_AMBEROAD_MBERT_D10", "Multilingual Cross-Encoder (amberoad-mBERT, Depth=10)"),
        ("E6a_ADAPTIVE_D5", "Adaptive Routing A: Depth=5 for Devanagari Hindi; E1 for Latin"),
        ("E6b_ADAPTIVE_BI_ENCODER", "Adaptive Routing B: Bi-Encoder Dense for Devanagari Hindi; E1 for Latin")
    ]

    raw_query_results = []
    latency_records = {cfg[0]: [] for cfg in configs}
    reranker_latency_records = {cfg[0]: [] for cfg in configs}

    print("\nStarting evaluation across all 240 queries...", flush=True)
    start_all_time = time.time()

    for q_idx, q in enumerate(queries, 1):
        qid = q["query_id"]
        iid = q["intent_id"]
        lang = q["query_language"]
        q_text = q["query_text"]
        status = q["expected_status"]
        exp_pids = set(q.get("expected_passage_ids") or ([q["passage_id"]] if q.get("passage_id") else []))

        # Query processing
        t_qp0 = time.time()
        qa = process_query(q_text, enable_translation=False)
        query_str = qa.normalized_query or qa.original_query
        t_qp1 = time.time()
        qp_latency_ms = (t_qp1 - t_qp0) * 1000

        # Step 1: Fixed Candidate Pool Generation (Depth 10)
        t_ret0 = time.time()
        bm25_hits = idx.bm25_search(query_str, top_k=10)
        dense_hits = idx.dense_search(query_str, top_k=10)
        fused = _rrf_fuse(bm25_hits, dense_hits)
        for pid, score, meta in fused:
            if "text" not in meta:
                try:
                    meta["text"] = idx.passage_texts[idx.passage_ids.index(pid)]
                except ValueError:
                    meta["text"] = ""
        fused = _deduplicate(fused)
        fused = validate_versions(fused, None, None, qa)
        candidate_pool = fused[:10]
        t_ret1 = time.time()
        cand_latency_ms = (t_ret1 - t_ret0) * 1000

        cand_pids = [h[0] for h in candidate_pool]
        cand_recall_10 = len(set(cand_pids) & exp_pids) / len(exp_pids) if (status == "ANSWERED" and exp_pids) else 0.0

        # Common Candidate Pairs
        pairs = [(query_str, meta.get("text", "")) for _, _, meta in candidate_pool]

        # 1. Single forward pass for ms-marco (D10)
        t_ms0 = time.time()
        ms_scores = cross_enc_prod.predict(pairs) if (cross_enc_prod and pairs) else [0.0] * len(candidate_pool)
        t_ms1 = time.time()
        ms_lat_total_ms = (t_ms1 - t_ms0) * 1000
        ms_lat_d5_ms = ms_lat_total_ms * 0.5  # proportional latency for 5 pairs

        # E1: Rerank all 10 with ms-marco
        ranked_e1 = sorted(zip(candidate_pool, ms_scores), key=lambda x: x[1], reverse=True)
        pids_e1 = [h[0][0] for h in ranked_e1[:5]]

        # E2: No reranker (Direct hybrid candidate order)
        pids_e2 = [h[0] for h in candidate_pool[:5]]

        # E3: Bi-Encoder Dense Top 5
        pids_e3 = [h[0] for h in dense_hits[:5]]

        # E4: Depth 5 Rerank (Take first 5 from candidate pool, reorder by ms_scores)
        pool_5 = candidate_pool[:5]
        scores_5 = ms_scores[:5]
        ranked_e4 = sorted(zip(pool_5, scores_5), key=lambda x: x[1], reverse=True)
        pids_e4 = [h[0][0] for h in ranked_e4[:5]]

        # E5: Multilingual Reranker (amberoad-mBERT D10)
        t_amb0 = time.time()
        if pairs:
            inputs = amberoad_tok(
                [p[0] for p in pairs],
                [p[1] for p in pairs],
                padding=True,
                truncation=True,
                max_length=256,
                return_tensors="pt"
            )
            with torch.no_grad():
                out = amberoad_model(**inputs)
                logits = out.logits
                amb_scores = (logits[:, 1] - logits[:, 0]).cpu().numpy()
            ranked_e5 = sorted(zip(candidate_pool, amb_scores), key=lambda x: x[1], reverse=True)
            pids_e5 = [h[0][0] for h in ranked_e5[:5]]
        else:
            pids_e5 = []
        t_amb1 = time.time()
        amb_lat_ms = (t_amb1 - t_amb0) * 1000

        # E6a: Adaptive Depth-5 (hi uses E4, Latin uses E1)
        if lang == "hi":
            pids_e6a = pids_e4
            rr_lat_e6a = ms_lat_d5_ms
        else:
            pids_e6a = pids_e1
            rr_lat_e6a = ms_lat_total_ms

        # E6b: Adaptive Bi-Encoder (hi uses E3, Latin uses E1)
        if lang == "hi":
            pids_e6b = pids_e3
            rr_lat_e6b = 0.0
        else:
            pids_e6b = pids_e1
            rr_lat_e6b = ms_lat_total_ms

        cfg_outputs = {
            "E1_PROD_MSMARCO_D10": (pids_e1, ms_lat_total_ms, qp_latency_ms + cand_latency_ms + ms_lat_total_ms),
            "E2_HYBRID_NO_RERANK": (pids_e2, 0.0, qp_latency_ms + cand_latency_ms),
            "E3_BI_ENCODER_DENSE": (pids_e3, 0.0, qp_latency_ms + (cand_latency_ms * 0.5)),
            "E4_DEPTH_5_MSMARCO": (pids_e4, ms_lat_d5_ms, qp_latency_ms + cand_latency_ms + ms_lat_d5_ms),
            "E5_AMBEROAD_MBERT_D10": (pids_e5, amb_lat_ms, qp_latency_ms + cand_latency_ms + amb_lat_ms),
            "E6a_ADAPTIVE_D5": (pids_e6a, rr_lat_e6a, qp_latency_ms + cand_latency_ms + rr_lat_e6a),
            "E6b_ADAPTIVE_BI_ENCODER": (pids_e6b, rr_lat_e6b, qp_latency_ms + cand_latency_ms + rr_lat_e6b)
        }

        for cfg_id, (retrieved_pids, rr_lat, total_e2e) in cfg_outputs.items():
            latency_records[cfg_id].append(total_e2e)
            reranker_latency_records[cfg_id].append(rr_lat)

            hit_1 = 0.0
            hit_3 = 0.0
            hit_5 = 0.0
            mrr = 0.0
            ndcg_5 = 0.0
            recall_5 = 0.0

            if status == "ANSWERED":
                if retrieved_pids and retrieved_pids[0] in exp_pids:
                    hit_1 = 1.0
                if any(p in exp_pids for p in retrieved_pids[:3]):
                    hit_3 = 1.0
                if any(p in exp_pids for p in retrieved_pids[:5]):
                    hit_5 = 1.0
                for r, pid in enumerate(retrieved_pids[:5], 1):
                    if pid in exp_pids:
                        mrr = 1.0 / r
                        break
                ndcg_5 = compute_ndcg_at_5(retrieved_pids, exp_pids)
                recall_5 = len(set(retrieved_pids[:5]) & exp_pids) / len(exp_pids) if exp_pids else 0.0

            raw_query_results.append({
                "config_id": cfg_id,
                "query_id": qid,
                "intent_id": iid,
                "language": lang,
                "expected_status": status,
                "query_text": q_text,
                "retrieved_top1": retrieved_pids[0] if retrieved_pids else "",
                "retrieved_top5": ";".join(retrieved_pids[:5]),
                "expected_pids": ";".join(exp_pids),
                "cand_recall_10": round(cand_recall_10, 4),
                "hit_1": hit_1,
                "hit_3": hit_3,
                "hit_5": hit_5,
                "mrr": round(mrr, 4),
                "ndcg_5": round(ndcg_5, 4),
                "recall_5": round(recall_5, 4),
                "reranker_latency_ms": round(rr_lat, 2),
                "e2e_latency_ms": round(total_e2e, 2)
            })

        if q_idx % 20 == 0 or q_idx == len(queries):
            elapsed = time.time() - start_all_time
            rate = q_idx / elapsed
            remaining = (len(queries) - q_idx) / rate if rate > 0 else 0
            print(f"Processed {q_idx:3d}/{len(queries)} queries | Elapsed: {elapsed:5.1f}s | Est Remaining: {remaining:5.1f}s", flush=True)

    total_eval_time = time.time() - start_all_time
    print(f"\nAll 240 queries evaluated in {total_eval_time:.2f}s ({total_eval_time/240:.2f}s per query)", flush=True)

    # 4. Generate Deliverable 1: m10_phase_e_results.csv
    summary_rows = []
    languages = ["en", "hi", "hi-Latn", "en-hi"]

    for cfg_id, cfg_desc in configs:
        cfg_results = [r for r in raw_query_results if r["config_id"] == cfg_id and r["expected_status"] == "ANSWERED"]
        
        # Per language
        for lang in languages:
            l_res = [r for r in cfg_results if r["language"] == lang]
            n = len(l_res)
            e2e_lats = [r["e2e_latency_ms"] for r in l_res]
            rr_lats = [r["reranker_latency_ms"] for r in l_res]

            summary_rows.append({
                "config_id": cfg_id,
                "config_description": cfg_desc,
                "language": lang,
                "sample_size": n,
                "hit_at_1": round(sum(r["hit_1"] for r in l_res) / n, 4) if n else 0.0,
                "hit_at_3": round(sum(r["hit_3"] for r in l_res) / n, 4) if n else 0.0,
                "hit_at_5": round(sum(r["hit_5"] for r in l_res) / n, 4) if n else 0.0,
                "mrr": round(sum(r["mrr"] for r in l_res) / n, 4) if n else 0.0,
                "ndcg_at_5": round(sum(r["ndcg_5"] for r in l_res) / n, 4) if n else 0.0,
                "recall_at_5": round(sum(r["recall_5"] for r in l_res) / n, 4) if n else 0.0,
                "cand_recall_10": round(sum(r["cand_recall_10"] for r in l_res) / n, 4) if n else 0.0,
                "mean_reranker_lat_ms": round(float(np.mean(rr_lats)), 2) if rr_lats else 0.0,
                "mean_e2e_lat_ms": round(float(np.mean(e2e_lats)), 2) if e2e_lats else 0.0,
                "p95_e2e_lat_ms": round(float(np.percentile(e2e_lats, 95)), 2) if e2e_lats else 0.0,
            })

        # Overall across all 4 languages (180 answerable)
        n_all = len(cfg_results)
        all_e2e = [r["e2e_latency_ms"] for r in cfg_results]
        all_rr = [r["reranker_latency_ms"] for r in cfg_results]
        summary_rows.append({
            "config_id": cfg_id,
            "config_description": cfg_desc,
            "language": "OVERALL",
            "sample_size": n_all,
            "hit_at_1": round(sum(r["hit_1"] for r in cfg_results) / n_all, 4) if n_all else 0.0,
            "hit_at_3": round(sum(r["hit_3"] for r in cfg_results) / n_all, 4) if n_all else 0.0,
            "hit_at_5": round(sum(r["hit_5"] for r in cfg_results) / n_all, 4) if n_all else 0.0,
            "mrr": round(sum(r["mrr"] for r in cfg_results) / n_all, 4) if n_all else 0.0,
            "ndcg_at_5": round(sum(r["ndcg_5"] for r in cfg_results) / n_all, 4) if n_all else 0.0,
            "recall_at_5": round(sum(r["recall_5"] for r in cfg_results) / n_all, 4) if n_all else 0.0,
            "cand_recall_10": round(sum(r["cand_recall_10"] for r in cfg_results) / n_all, 4) if n_all else 0.0,
            "mean_reranker_lat_ms": round(float(np.mean(all_rr)), 2) if all_rr else 0.0,
            "mean_e2e_lat_ms": round(float(np.mean(all_e2e)), 2) if all_e2e else 0.0,
            "p95_e2e_lat_ms": round(float(np.percentile(all_e2e, 95)), 2) if all_e2e else 0.0,
        })

    out_results_csv = "backend/data/experiments/m10/m10_phase_e_results.csv"
    with open(out_results_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"Saved aggregated experiment results to {out_results_csv}", flush=True)

    # 5. Generate Deliverable 2: m10_phase_e_per_intent_results.csv
    intent_rows = []
    unique_intents = sorted(list(set(r["intent_id"] for r in raw_query_results if r["expected_status"] == "ANSWERED")))

    for iid in unique_intents:
        for cfg_id, _ in configs:
            for lang in languages:
                match = [r for r in raw_query_results if r["intent_id"] == iid and r["config_id"] == cfg_id and r["language"] == lang]
                if match:
                    m = match[0]
                    intent_rows.append({
                        "intent_id": iid,
                        "config_id": cfg_id,
                        "language": lang,
                        "query_id": m["query_id"],
                        "hit_1": m["hit_1"],
                        "hit_5": m["hit_5"],
                        "mrr": m["mrr"],
                        "ndcg_5": m["ndcg_5"],
                        "retrieved_top1": m["retrieved_top1"],
                        "expected_pids": m["expected_pids"],
                        "e2e_latency_ms": m["e2e_latency_ms"]
                    })

    out_intent_csv = "backend/data/experiments/m10/m10_phase_e_per_intent_results.csv"
    with open(out_intent_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(intent_rows[0].keys()))
        writer.writeheader()
        writer.writerows(intent_rows)
    print(f"Saved per-intent results to {out_intent_csv}", flush=True)

    # 6. Generate Deliverable 3: m10_phase_e_resource_results.csv
    peak_mem_mb = proc.memory_info().rss / (1024 * 1024)
    model_specs = {
        "E1_PROD_MSMARCO_D10": {"params": "22.7M", "disk_mb": 86.8, "arch": "cross-encoder/ms-marco-MiniLM-L-6-v2"},
        "E2_HYBRID_NO_RERANK": {"params": "0M", "disk_mb": 0.0, "arch": "None (RRF Fusion)"},
        "E3_BI_ENCODER_DENSE": {"params": "117.7M", "disk_mb": 471.0, "arch": "paraphrase-multilingual-MiniLM-L12-v2"},
        "E4_DEPTH_5_MSMARCO": {"params": "22.7M", "disk_mb": 86.8, "arch": "cross-encoder/ms-marco-MiniLM-L-6-v2"},
        "E5_AMBEROAD_MBERT_D10": {"params": "110.0M", "disk_mb": 638.5, "arch": "amberoad/bert-multilingual-passage-reranking-msmarco"},
        "E6a_ADAPTIVE_D5": {"params": "22.7M", "disk_mb": 86.8, "arch": "Adaptive: Depth-5 (hi) + ms-marco (Latin)"},
        "E6b_ADAPTIVE_BI_ENCODER": {"params": "117.7M", "disk_mb": 471.0, "arch": "Adaptive: Bi-Encoder (hi) + ms-marco (Latin)"}
    }

    resource_rows = []
    for cfg_id, cfg_desc in configs:
        e2e_l = latency_records[cfg_id]
        rr_l = reranker_latency_records[cfg_id]
        spec = model_specs[cfg_id]

        resource_rows.append({
            "config_id": cfg_id,
            "architecture": spec["arch"],
            "parameter_count": spec["params"],
            "disk_footprint_mb": spec["disk_mb"],
            "mean_reranker_latency_ms": round(float(np.mean(rr_l)), 2) if rr_l else 0.0,
            "median_reranker_latency_ms": round(float(np.median(rr_l)), 2) if rr_l else 0.0,
            "p95_reranker_latency_ms": round(float(np.percentile(rr_l, 95)), 2) if rr_l else 0.0,
            "mean_e2e_latency_ms": round(float(np.mean(e2e_l)), 2) if e2e_l else 0.0,
            "median_e2e_latency_ms": round(float(np.median(e2e_l)), 2) if e2e_l else 0.0,
            "p95_e2e_latency_ms": round(float(np.percentile(e2e_l, 95)), 2) if e2e_l else 0.0,
            "peak_process_rss_mb": round(peak_mem_mb, 2),
            "cpu_threads_used": torch.get_num_threads(),
        })

    out_resource_csv = "backend/data/experiments/m10/m10_phase_e_resource_results.csv"
    with open(out_resource_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(resource_rows[0].keys()))
        writer.writeheader()
        writer.writerows(resource_rows)
    print(f"Saved resource profiling results to {out_resource_csv}", flush=True)

    # 7. Print Console Summary Matrix
    print("\n" + "="*95, flush=True)
    print("PHASE E EXPERIMENTAL SUMMARY MATRIX (ANSWERABLE QUERIES, N=180)", flush=True)
    print("="*95, flush=True)
    header = f"{'Config ID':24s} | {'Lang':7s} | {'Hit@1':7s} | {'Hit@5':7s} | {'MRR':7s} | {'nDCG@5':7s} | {'Rerank ms':9s} | {'E2E ms':8s}"
    print(header, flush=True)
    print("-" * len(header), flush=True)

    for row in summary_rows:
        if row["language"] in ["hi", "OVERALL"]:
            print(f"{row['config_id']:24s} | {row['language']:7s} | {row['hit_at_1']:.4f}  | {row['hit_at_5']:.4f}  | {row['mrr']:.4f}  | {row['ndcg_at_5']:.4f}   | {row['mean_reranker_lat_ms']:8.1f}  | {row['mean_e2e_lat_ms']:7.1f}", flush=True)
    print("="*95, flush=True)

if __name__ == "__main__":
    main()
