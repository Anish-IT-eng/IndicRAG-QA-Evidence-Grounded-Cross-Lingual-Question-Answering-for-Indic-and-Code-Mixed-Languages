import hashlib
import json
import time
from pathlib import Path

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 16):
            h.update(chunk)
    return h.hexdigest()

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
exp_dir = root / "backend/data/experiments/m10"
exp_dir.mkdir(parents=True, exist_ok=True)

# List of critical evidence artifacts to inventory
artifacts_to_track = [
    root / "backend/data/experiments/m9/m9_evaluation_dataset.jsonl",
    root / "backend/data/db/indicrag.db",
    root / "backend/data/indexes/official/faiss.index",
    exp_dir / "m10_phase_e_results.csv",
    exp_dir / "m10_phase_e_per_intent_results.csv",
    exp_dir / "m10_phase_f_end_to_end_results.csv",
    exp_dir / "m10_phase_g_statistical_results.csv",
    exp_dir / "m10_phase_h_per_query_results.csv",
    exp_dir / "m10_phase_h_claim_audit.csv",
    exp_dir / "m10_phase_h_citation_audit.csv",
    exp_dir / "m10_phase_h_metrics.json",
    root / "backend/app/retrieval/engine.py",
    root / "backend/app/generation/generator.py",
    root / "backend/app/retrieval/evidence_controller.py",
    root / "backend/app/models/schemas.py",
    root / "backend/app/api/main.py",
    root / "frontend/index.html"
]

inventory = {
    "milestone": "M10",
    "phase": "I",
    "title": "Production Promotion Readiness & Final Deployment Decision Evidence Inventory",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "target_decision": "RETAIN_AS_EXPERIMENTAL",
    "promotion_disposition": "DEFERRED_PENDING_M11_CONFIRMATORY_EVIDENCE",
    "production_default_verified": "production (engine.py line 395)",
    "evaluation_population": {
        "benchmark_dataset": "m9_evaluation_dataset.jsonl",
        "total_intent_groups": 60,
        "answerable_intent_groups": 45,
        "unanswerable_intent_groups": 15,
        "languages_per_intent": 4,
        "total_query_records": 240,
        "comparative_traces_evaluated": 480
    },
    "verified_metrics_summary": {
        "retrieval": {
            "ConfigA_Production": {
                "en_hit_5": "5/45 (0.1111)",
                "hi_hit_5": "2/45 (0.0444)",
                "hi_latn_hit_5": "6/45 (0.1333)",
                "en_hi_hit_5": "5/45 (0.1111)",
                "overall_hit_5": "18/180 (0.1000)",
                "overall_mrr": 0.0931,
                "overall_ndcg_5": 0.0784,
                "mean_retrieval_stage_latency_ms": 1097.10
            },
            "ConfigB_AdaptiveE6b": {
                "en_hit_5": "5/45 (0.1111)",
                "hi_hit_5": "4/45 (0.0889)",
                "hi_latn_hit_5": "6/45 (0.1333)",
                "en_hi_hit_5": "5/45 (0.1111)",
                "overall_hit_5": "20/180 (0.1111)",
                "overall_mrr": 0.1083,
                "overall_ndcg_5": 0.0914,
                "hi_retrieval_stage_latency_ms": 62.88,
                "mean_retrieval_stage_latency_ms": 849.87
            }
        },
        "answer_quality": {
            "ConfigA_Production": {
                "answerable_success": "59/180 (32.78%)",
                "clean_unnecessary_abstentions": "119/180 (66.11%)",
                "execution_errors": "2/180 (1.11%)",
                "unanswerable_correct_abstentions": "58/60 (96.67%)",
                "unanswerable_incorrect_answers": "2/60 (3.33%)"
            },
            "ConfigB_AdaptiveE6b": {
                "answerable_success": "61/180 (33.89%)",
                "clean_unnecessary_abstentions": "117/180 (65.00%)",
                "execution_errors": "2/180 (1.11%)",
                "unanswerable_correct_abstentions": "58/60 (96.67%)",
                "unanswerable_incorrect_answers": "2/60 (3.33%)",
                "latin_script_regressions": "0/135 (0.00%)"
            }
        },
        "grounding_and_citations": {
            "ConfigB_claims_audited": 85,
            "claim_support_precision": 1.0,
            "unsupported_claim_rate": 0.0,
            "rule_of_three_upper_bound_95ci": 0.0353,
            "ConfigB_citations_audited": 57,
            "citation_uuid_validity": 1.0,
            "citation_page_accuracy": 0.9825,
            "semantic_citation_support": 1.0
        },
        "statistical_inferences": {
            "independent_sampling_unit": "semantic_intent_group",
            "pilot_sample_size": "N=45 answerable intent groups",
            "devanagari_hit_5_exact_binomial_p": 0.6250,
            "devanagari_e2e_success_exact_binomial_p": 0.5000,
            "cluster_wilcoxon_exact_permutation_p": 0.5000,
            "pilot_two_sided_power": 0.6537,
            "confirmatory_sample_size_required_m11": 230,
            "confirmatory_query_records_total": 920,
            "unconditional_power_at_230": 0.8122
        },
        "operational_integration_status": {
            "engine_support": "Implemented in backend/app/retrieval/engine.py line 449",
            "runtime_default": "production (engine.py line 395)",
            "api_exposure": "None (QueryRequest schema in backend/app/models/schemas.py lacks rerank_strategy)",
            "frontend_ui_exposure": "None (frontend/index.html only exposes boolean use_reranker toggle)",
            "config_setting_exposure": "None (backend/app/core/config.py lacks RERANK_STRATEGY setting)",
            "regression_test_coverage": "Covered by backend/tests/test_retrieval_baselines.py (260/260 passed)",
            "fallback_mechanism": "Internal fallback to production if strategy != 'adaptive_e6b'"
        }
    },
    "evidence_inventory_artifacts": {
        p.name: {
            "path": str(p),
            "sha256": sha256_file(p),
            "size_bytes": p.stat().st_size
        } for p in artifacts_to_track
    }
}

out_file = exp_dir / "m10_phase_i_evidence_inventory.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(inventory, f, indent=2, ensure_ascii=False)

print(f"Generated Phase I evidence inventory at {out_file} ({len(artifacts_to_track)} artifacts tracked).")
