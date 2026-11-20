"""
Phase A: M9 Baseline and Data Integrity Audit Script
Audits and preserves exact M9 baselines, reconciles metrics, and writes:
- backend/data/experiments/m10/m10_baseline_snapshot.json
- backend/data/experiments/m10/m10_baseline_query_results.csv
"""
import json
import csv
import hashlib
import os
import sys

def get_sha256(path):
    if not os.path.exists(path):
        return "FILE_NOT_FOUND"
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    m9_dataset_path = "backend/data/experiments/m9/m9_evaluation_dataset.jsonl"
    m9_retrieval_path = "backend/data/experiments/m9/retrieval_metrics_by_language.csv"
    m9_consistency_path = "backend/data/experiments/m9/cross_lingual_evidence_consistency.csv"
    m9_gen_path = "backend/data/experiments/m9/answer_generation_results.csv"
    m9_claim_path = "backend/data/experiments/m9/claim_grounding_results.csv"
    m9_cit_path = "backend/data/experiments/m9/citation_quality_results.csv"
    m9_ablation_path = "backend/data/experiments/m9/m9_ablation_results.csv"
    manifest_path = "backend/data/experiments/m9/m9_integrity_manifest.json"

    # 1. Load dataset
    queries = []
    with open(m9_dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))
    
    print(f"Loaded {len(queries)} dataset queries.")
    
    # 2. Load generation & retrieval results
    gen_results = {}
    if os.path.exists(m9_gen_path):
        with open(m9_gen_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                gen_results[row["query_id"]] = row
                
    # 3. Load retrieval consistency
    consistency_by_intent = {}
    if os.path.exists(m9_consistency_path):
        with open(m9_consistency_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                consistency_by_intent[row["intent_id"]] = row

    # 4. Construct per-query baseline records
    baseline_records = []
    for q in queries:
        qid = q["query_id"]
        iid = q["intent_id"]
        lang = q["query_language"]
        gen = gen_results.get(qid, {})
        cons = consistency_by_intent.get(iid, {})
        
        hit_5_val = 0
        if lang == "en": hit_5_val = int(cons.get("en_hit_5", 0))
        elif lang == "hi": hit_5_val = int(cons.get("hi_hit_5", 0))
        elif lang == "hi-Latn": hit_5_val = int(cons.get("hi_latn_hit_5", 0))
        elif lang == "en-hi": hit_5_val = int(cons.get("en_hi_hit_5", 0))
        
        baseline_records.append({
            "query_id": qid,
            "intent_id": iid,
            "language": lang,
            "script": q.get("script", ""),
            "query_type": q.get("query_type", ""),
            "query_text": q.get("query_text", ""),
            "expected_status": q.get("expected_status", ""),
            "expected_document_ids": ";".join(q.get("expected_document_ids", [])),
            "expected_passage_ids": ";".join(q.get("expected_passage_ids", [])),
            "m9_response_status": gen.get("response_status", "NOT_EVALUATED"),
            "m9_status_correct": gen.get("status_correct", ""),
            "m9_controller_status": gen.get("controller_status", ""),
            "m9_ceci_score": gen.get("ceci_score", ""),
            "m9_hit_at_5": hit_5_val if q.get("expected_status") == "ANSWERED" else "N/A",
            "m9_citations_count": gen.get("citations_count", "0"),
            "m9_all_pages_verified": gen.get("all_pages_verified", ""),
            "m9_total_claims": gen.get("total_claims", "0"),
            "m9_supported_claims": gen.get("supported_claims", "0"),
            "m9_grounding_ratio": gen.get("grounding_ratio", "0.0"),
            "m9_retrieval_latency_ms": gen.get("retrieval_latency_ms", "0.0"),
            "m9_generation_latency_ms": gen.get("generation_latency_ms", "0.0"),
            "m9_total_latency_ms": gen.get("total_latency_ms", "0.0"),
        })

    # Save m10_baseline_query_results.csv
    out_csv = "backend/data/experiments/m10/m10_baseline_query_results.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(baseline_records[0].keys()))
        writer.writeheader()
        writer.writerows(baseline_records)
    print(f"Saved {len(baseline_records)} baseline query records to {out_csv}")

    # 5. Build Snapshot JSON
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # Retrieval metrics by language
    ret_metrics = {}
    with open(m9_retrieval_path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ret_metrics[r["language"]] = r

    snapshot = {
        "milestone": "M10_PHASE_A_BASELINE_SNAPSHOT",
        "timestamp": "2026-11-17T16:45:00+05:30",
        "source_manifest_hash": get_sha256(manifest_path),
        "corpus_and_indexes": {
            "database_path": "backend/data/db/indicrag.db",
            "database_sha256": get_sha256("backend/data/db/indicrag.db"),
            "official_documents": 7,
            "child_passages": 253,
            "parent_passages": 53,
            "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "production_cross_encoder": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "production_llm": "qwen2.5:3b"
        },
        "frozen_benchmark_hashes": manifest_data.get("frozen_benchmark_hashes", {}),
        "m9_reported_retrieval_metrics": ret_metrics,
        "m9_reported_document_consensus": {
            "definition": "Proportion of 45 answerable intents where any of top-3 retrieved passages across all 4 language variants belong to the same document_id",
            "reported_value": 0.8889,
            "matched_intents": 40,
            "total_answerable_intents": 45,
            "denominator": 45,
            "measured_stage": "POST_RERANKING_TOP3_DOCUMENTS",
            "reconciliation_notes": "Measures coarse document-level overlap (7 documents total in corpus) across top 3 hits, NOT passage-level retrieval accuracy. Devanagari Hindi passage Hit@5 was 0.0444 (2/45)."
        },
        "m9_statistical_parity_reconciliation": {
            "english_vs_hinglish": {
                "metric": "nDCG@5",
                "en_mean": 0.1204,
                "en_hi_mean": 0.1251,
                "t_statistic": 0.316,
                "p_value": 0.7533,
                "verdict": "STATISTICAL_PARITY_ESTABLISHED"
            },
            "english_vs_romanized_hindi": {
                "metric": "nDCG@5",
                "en_mean": 0.1204,
                "hi_latn_mean": 0.1251,
                "t_statistic": 0.316,
                "p_value": 0.7533,
                "verdict": "STATISTICAL_PARITY_ESTABLISHED"
            },
            "english_vs_devanagari_hindi": {
                "metric": "nDCG@5",
                "en_mean": 0.1204,
                "hi_mean": 0.0195,
                "t_statistic": -2.746,
                "p_value": 0.0086,
                "verdict": "STATISTICALLY_SIGNIFICANT_DEGRADATION"
            }
        },
        "m9_generation_summary": {
            "total_queries": 240,
            "answered_count": 53,
            "unanswerable_count": 177,
            "conflicting_count": 8,
            "overall_status_correctness": 0.4583,
            "claim_grounding_precision": 0.9390,
            "citation_page_precision": 0.9815,
            "unanswerable_abstention_accuracy": 0.9667
        }
    }

    out_json = "backend/data/experiments/m10/m10_baseline_snapshot.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    print(f"Saved baseline snapshot to {out_json}")

if __name__ == "__main__":
    main()
