import csv
import statistics
from pathlib import Path

def percentile(data, p):
    sorted_d = sorted(data)
    idx = (len(sorted_d) - 1) * p / 100.0
    floor = int(idx)
    ceil = floor + 1
    if ceil < len(sorted_d):
        return sorted_d[floor] + (sorted_d[ceil] - sorted_d[floor]) * (idx - floor)
    return sorted_d[floor]

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
raw_h = list(csv.DictReader(open(root / "backend/data/experiments/m10/m10_phase_h_per_query_results.csv", encoding="utf-8")))

for cfg in ["ConfigA_Production", "ConfigB_AdaptiveE6b"]:
    sub = [r for r in raw_h if r["config_id"] == cfg]
    print(f"\n==================== {cfg} (N={len(sub)}) ====================")
    
    ret_vals = [float(r["retrieval_latency_ms"]) for r in sub]
    ctrl_vals = [float(r["controller_latency_ms"]) for r in sub]
    gen_vals = [float(r["generation_latency_ms"]) for r in sub]
    tot_vals = [float(r["total_latency_ms"]) for r in sub]
    
    gen_invoked = [l for l in gen_vals if l > 1.0]
    gen_skipped = [l for l in gen_vals if l <= 1.0]
    
    # Successful vs failed generations among invoked
    invoked_rows = [r for r in sub if float(r["generation_latency_ms"]) > 1.0]
    succ_gen = [r for r in invoked_rows if r["response_status"] in ["answered", "conflicting_versions", "clarification_needed"]]
    unans_gen = [r for r in invoked_rows if r["response_status"] == "unanswerable"]
    err_gen = [r for r in invoked_rows if r["response_status"] == "error"]
    
    print(f"Retrieval Latency (ms):")
    print(f"  Mean: {statistics.mean(ret_vals):.2f} | p50: {percentile(ret_vals, 50):.2f} | p95: {percentile(ret_vals, 95):.2f}")
    
    print(f"Evidence Controller Latency (ms):")
    print(f"  Mean: {statistics.mean(ctrl_vals):.2f} | p50: {percentile(ctrl_vals, 50):.2f} | p95: {percentile(ctrl_vals, 95):.2f}")
    
    print(f"Generation Invocation Counts:")
    print(f"  Total Benchmark Queries: {len(sub)}")
    print(f"  Generation Invoked: {len(invoked_rows)}")
    print(f"    - Produced Direct Answer / Disclosure: {len(succ_gen)}")
    print(f"    - Concluded Unanswerable post-generation: {len(unans_gen)}")
    print(f"    - Generation Error: {len(err_gen)}")
    print(f"  Generation Skipped (Abstained by Controller): {len(gen_skipped)}")
    
    print(f"Generation Latency (ms):")
    print(f"  Among Invoked ({len(invoked_rows)}): Mean: {statistics.mean(gen_invoked):.2f} | p50: {percentile(gen_invoked, 50):.2f} | p95: {percentile(gen_invoked, 95):.2f}")
    print(f"  Across All 240 Queries (amortized with 0s): Mean: {statistics.mean(gen_vals):.2f} | p50: {percentile(gen_vals, 50):.2f} | p95: {percentile(gen_vals, 95):.2f}")
    
    print(f"Total Pipeline Latency (ms):")
    print(f"  Measured Mean: {statistics.mean(tot_vals):.2f} | p50: {percentile(tot_vals, 50):.2f} | p95: {percentile(tot_vals, 95):.2f}")
    
    sum_means = statistics.mean(ret_vals) + statistics.mean(ctrl_vals) + statistics.mean(gen_vals)
    print(f"  Sum of Component Means: {sum_means:.2f} ms")
    print(f"  Unattributed Overhead (Pipeline glue / logging): {statistics.mean(tot_vals) - sum_means:.2f} ms")
