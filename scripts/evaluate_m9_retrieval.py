"""
Evaluates Cross-Lingual Retrieval across all 240 queries in the M9 dataset.
Computes Hit@1, Hit@3, Hit@5, MRR, nDCG@5, Recall@5, Latency.
Computes Cross-Lingual Consistency across the 60 semantic intent groups.
Outputs:
- backend/data/experiments/m9/retrieval_metrics_by_language.csv
- backend/data/experiments/m9/cross_lingual_evidence_consistency.csv
"""
import json
import csv
import math
import time
import sys
import os

# Set offline mode so HuggingFace uses local cached models without hanging
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

sys.path.insert(0, os.path.abspath("backend"))

from app.query.processor import process_query
from app.retrieval.engine import retrieve
from app.models.schemas import DocumentSource

# Load dataset
queries = []
with open("backend/data/experiments/m9/m9_evaluation_dataset.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            queries.append(json.loads(line))

intent_groups = {}
for q in queries:
    intent_groups.setdefault(q["intent_id"], []).append(q)

retrieval_traces = []
per_query_metrics = []

print(f"Starting retrieval evaluation for {len(queries)} queries...")
t_start = time.perf_counter()

for idx, q in enumerate(queries, 1):
    qid = q["query_id"]
    intent_id = q["intent_id"]
    lang = q["query_language"]
    q_text = q["query_text"]
    expected_pids = set(q.get("expected_passage_ids", []))
    expected_dids = set(q.get("expected_document_ids", []))
    is_answerable = (q["expected_status"] == "ANSWERED")
    
    t0 = time.perf_counter()
    q_analysis = process_query(q_text, enable_translation=False)
    ret_res = retrieve(
        q_analysis,
        collections=[DocumentSource.OFFICIAL],
        top_k=5,
        use_reranker=True,
        use_mqr=False,
        use_pdr=True
    )
    lat_ms = (time.perf_counter() - t0) * 1000.0
    
    retrieved_pids = [p.passage_id for p in ret_res.retrieved_passages]
    retrieved_dids = [p.document_id for p in ret_res.retrieved_passages]
    
    # Calculate metrics if answerable
    hit_1 = 0
    hit_3 = 0
    hit_5 = 0
    rr = 0.0
    ndcg_5 = 0.0
    recall_5 = 0.0
    
    if is_answerable and expected_pids:
        # Check hits
        ranks = []
        for r_idx, pid in enumerate(retrieved_pids[:5], 1):
            if pid in expected_pids:
                ranks.append(r_idx)
                
        if ranks:
            first_rank = ranks[0]
            if first_rank == 1:
                hit_1 = 1
            if first_rank <= 3:
                hit_3 = 1
            if first_rank <= 5:
                hit_5 = 1
            rr = 1.0 / first_rank
            
            # nDCG@5 calculation
            dcg = sum(1.0 / math.log2(r + 1) for r in ranks)
            # Ideal DCG
            idcg = sum(1.0 / math.log2(r + 1) for r in range(1, min(len(expected_pids), 5) + 1))
            ndcg_5 = dcg / idcg if idcg > 0 else 0.0
            
            retrieved_expected_count = len(set(retrieved_pids[:5]) & expected_pids)
            recall_5 = retrieved_expected_count / len(expected_pids)
    elif is_answerable and expected_dids and not expected_pids:
        # Document-level fallback if passage IDs not specified
        for r_idx, did in enumerate(retrieved_dids[:5], 1):
            if did in expected_dids:
                if r_idx == 1: hit_1 = 1
                if r_idx <= 3: hit_3 = 1
                if r_idx <= 5: hit_5 = 1
                rr = 1.0 / r_idx
                recall_5 = 1.0
                ndcg_5 = 1.0 / math.log2(r_idx + 1)
                break
                
    m_record = {
        "query_id": qid,
        "intent_id": intent_id,
        "language": lang,
        "query_type": q["query_type"],
        "is_answerable": is_answerable,
        "hit_1": hit_1,
        "hit_3": hit_3,
        "hit_5": hit_5,
        "mrr": rr,
        "ndcg_5": ndcg_5,
        "recall_5": recall_5,
        "latency_ms": lat_ms,
        "retrieved_pids": retrieved_pids,
        "retrieved_dids": retrieved_dids,
    }
    per_query_metrics.append(m_record)
    
    if idx % 20 == 0 or idx == len(queries):
        print(f"Processed {idx}/{len(queries)} queries...", flush=True)

# Compute Aggregated Metrics By Language
metrics_by_lang = {}
for lang in ["en", "hi", "hi-Latn", "en-hi"]:
    subset = [m for m in per_query_metrics if m["language"] == lang]
    ans_subset = [m for m in subset if m["is_answerable"]]
    unans_subset = [m for m in subset if not m["is_answerable"]]
    
    n_ans = len(ans_subset)
    metrics_by_lang[lang] = {
        "language": lang,
        "total_queries": len(subset),
        "answerable_queries": n_ans,
        "unanswerable_queries": len(unans_subset),
        "hit_at_1": sum(m["hit_1"] for m in ans_subset) / n_ans if n_ans else 0.0,
        "hit_at_3": sum(m["hit_3"] for m in ans_subset) / n_ans if n_ans else 0.0,
        "hit_at_5": sum(m["hit_5"] for m in ans_subset) / n_ans if n_ans else 0.0,
        "mrr": sum(m["mrr"] for m in ans_subset) / n_ans if n_ans else 0.0,
        "ndcg_at_5": sum(m["ndcg_5"] for m in ans_subset) / n_ans if n_ans else 0.0,
        "recall_at_5": sum(m["recall_5"] for m in ans_subset) / n_ans if n_ans else 0.0,
        "avg_latency_ms": sum(m["latency_ms"] for m in subset) / len(subset) if subset else 0.0,
    }

# Save metrics_by_language.csv
with open("backend/data/experiments/m9/retrieval_metrics_by_language.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "language", "total_queries", "answerable_queries", "unanswerable_queries",
        "hit_at_1", "hit_at_3", "hit_at_5", "mrr", "ndcg_at_5", "recall_at_5", "avg_latency_ms"
    ])
    writer.writeheader()
    for lang in ["en", "hi", "hi-Latn", "en-hi"]:
        writer.writerow(metrics_by_lang[lang])

# Cross-Lingual Evidence Consistency Analysis
consistency_rows = []
for intent_id, q_list in intent_groups.items():
    # Map by language
    by_lang = {m["language"]: m for m in per_query_metrics if m["intent_id"] == intent_id}
    
    en_pids = set(by_lang.get("en", {}).get("retrieved_pids", [])[:5])
    hi_pids = set(by_lang.get("hi", {}).get("retrieved_pids", [])[:5])
    hilatn_pids = set(by_lang.get("hi-Latn", {}).get("retrieved_pids", [])[:5])
    enhi_pids = set(by_lang.get("en-hi", {}).get("retrieved_pids", [])[:5])
    
    all_pids = en_pids | hi_pids | hilatn_pids | enhi_pids
    common_pids = en_pids & hi_pids & hilatn_pids & enhi_pids
    
    jaccard = len(common_pids) / len(all_pids) if all_pids else 0.0
    
    # Document consistency
    en_dids = set(by_lang.get("en", {}).get("retrieved_dids", [])[:3])
    hi_dids = set(by_lang.get("hi", {}).get("retrieved_dids", [])[:3])
    hilatn_dids = set(by_lang.get("hi-Latn", {}).get("retrieved_dids", [])[:3])
    enhi_dids = set(by_lang.get("en-hi", {}).get("retrieved_dids", [])[:3])
    doc_overlap = len(en_dids & hi_dids & hilatn_dids & enhi_dids) > 0
    
    # Check hit consistency for answerable intents
    is_ans = by_lang.get("en", {}).get("is_answerable", False)
    all_hit_5 = False
    if is_ans:
        all_hit_5 = all(by_lang[l].get("hit_5", 0) == 1 for l in ["en", "hi", "hi-Latn", "en-hi"] if l in by_lang)
        
    consistency_rows.append({
        "intent_id": intent_id,
        "is_answerable": is_ans,
        "en_hit_5": by_lang.get("en", {}).get("hit_5", 0),
        "hi_hit_5": by_lang.get("hi", {}).get("hit_5", 0),
        "hi_latn_hit_5": by_lang.get("hi-Latn", {}).get("hit_5", 0),
        "en_hi_hit_5": by_lang.get("en-hi", {}).get("hit_5", 0),
        "all_languages_hit_top5": all_hit_5,
        "top5_passage_jaccard_overlap": round(jaccard, 4),
        "document_level_consensus": doc_overlap,
        "divergent_language": "NONE" if all_hit_5 else (
            "hi" if by_lang.get("hi", {}).get("hit_5", 0) == 0 else (
                "hi-Latn" if by_lang.get("hi-Latn", {}).get("hit_5", 0) == 0 else "en-hi"
            )
        )
    })

# Save cross_lingual_evidence_consistency.csv
with open("backend/data/experiments/m9/cross_lingual_evidence_consistency.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "intent_id", "is_answerable", "en_hit_5", "hi_hit_5", "hi_latn_hit_5",
        "en_hi_hit_5", "all_languages_hit_top5", "top5_passage_jaccard_overlap",
        "document_level_consensus", "divergent_language"
    ])
    writer.writeheader()
    writer.writerows(consistency_rows)

print("\n--- Cross-Lingual Retrieval Performance Summary ---")
for lang, m in metrics_by_lang.items():
    print(f"Language: {lang:7s} | Hit@1: {m['hit_at_1']:.4f} | Hit@3: {m['hit_at_3']:.4f} | Hit@5: {m['hit_at_5']:.4f} | MRR: {m['mrr']:.4f} | nDCG@5: {m['ndcg_at_5']:.4f} | Latency: {m['avg_latency_ms']:.1f}ms")

ans_cons = [r for r in consistency_rows if r["is_answerable"]]
full_hit_rate = sum(1 for r in ans_cons if r["all_languages_hit_top5"]) / len(ans_cons) if ans_cons else 0.0
mean_jaccard = sum(r["top5_passage_jaccard_overlap"] for r in ans_cons) / len(ans_cons) if ans_cons else 0.0
doc_cons_rate = sum(1 for r in ans_cons if r["document_level_consensus"]) / len(ans_cons) if ans_cons else 0.0

print(f"\n--- Cross-Lingual Consistency Metrics (Across 45 Answerable Intents) ---")
print(f"Full 4-Language Top-5 Agreement Rate: {full_hit_rate*100:.2f}% ({sum(1 for r in ans_cons if r['all_languages_hit_top5'])}/{len(ans_cons)})")
print(f"Document-Level Consensus Rate:       {doc_cons_rate*100:.2f}% ({sum(1 for r in ans_cons if r['document_level_consensus'])}/{len(ans_cons)})")
print(f"Mean Top-5 Evidence Jaccard Overlap:  {mean_jaccard:.4f}")
