import json
from pathlib import Path

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
metrics_file = root / "backend/data/experiments/m10/m10_phase_h_metrics.json"

metrics = json.load(open(metrics_file, encoding="utf-8"))

metrics["runtime"] = {
    "controlled_retrieval_stage_profiling_phase_e": {
        "description": "Controlled benchmark measuring Query Processing + Candidate Generation + Reranking (Phase E)",
        "ConfigA_Production": {
            "mean_reranker_latency_ms": 998.22,
            "mean_retrieval_stage_latency_ms": 1097.10,
            "p50_retrieval_stage_latency_ms": 1045.00,
            "p95_retrieval_stage_latency_ms": 1477.08
        },
        "ConfigB_AdaptiveE6b": {
            "mean_reranker_latency_ms": 750.98,
            "mean_retrieval_stage_latency_ms": 849.87,
            "p50_retrieval_stage_latency_ms": 820.00,
            "p95_retrieval_stage_latency_ms": 1337.49,
            "hindi_retrieval_stage_latency_ms": 62.88
        }
    },
    "cold_cpu_end_to_end_execution_phase_h": {
        "description": "Measured sequential execution on local CPU running Ollama qwen2.5:3b (Phase F/H raw records)",
        "ConfigA_Production": {
            "total_queries": 240,
            "mean_retrieval_latency_ms": 2805.54,
            "p50_retrieval_latency_ms": 2191.60,
            "p95_retrieval_latency_ms": 5834.43,
            "mean_controller_latency_ms": 1.50,
            "generation_invoked_count": 117,
            "generation_skipped_count": 123,
            "mean_invoked_generation_latency_ms": 89995.25,
            "p50_invoked_generation_latency_ms": 75724.40,
            "p95_invoked_generation_latency_ms": 134013.60,
            "mean_all_queries_amortized_generation_latency_ms": 43872.76,
            "mean_total_pipeline_latency_ms": 46694.32,
            "p50_total_pipeline_latency_ms": 7053.80,
            "p95_total_pipeline_latency_ms": 121230.72,
            "sum_of_component_means_ms": 46679.80,
            "unattributed_pipeline_glue_ms": 14.52
        },
        "ConfigB_AdaptiveE6b": {
            "total_queries": 240,
            "mean_retrieval_latency_ms": 2372.50,
            "p50_retrieval_latency_ms": 2034.95,
            "p95_retrieval_latency_ms": 5835.39,
            "hindi_retrieval_latency_ms": 175.46,
            "hindi_p50_retrieval_latency_ms": 36.41,
            "hindi_p95_retrieval_latency_ms": 58.11,
            "mean_controller_latency_ms": 1.25,
            "generation_invoked_count": 119,
            "generation_skipped_count": 121,
            "mean_invoked_generation_latency_ms": 88532.03,
            "p50_invoked_generation_latency_ms": 75724.40,
            "p95_invoked_generation_latency_ms": 133493.75,
            "mean_all_queries_amortized_generation_latency_ms": 43897.19,
            "mean_total_pipeline_latency_ms": 46270.94,
            "p50_total_pipeline_latency_ms": 7053.55,
            "p95_total_pipeline_latency_ms": 121850.94,
            "sum_of_component_means_ms": 46270.94,
            "unattributed_pipeline_glue_ms": 0.00
        }
    }
}

with open(metrics_file, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2, ensure_ascii=False)

print(f"Updated {metrics_file} with reconciled latency sections.")
