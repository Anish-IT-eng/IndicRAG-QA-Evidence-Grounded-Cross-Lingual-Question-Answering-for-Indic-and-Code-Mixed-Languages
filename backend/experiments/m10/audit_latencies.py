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
rows = list(csv.DictReader(open(root / "backend/data/experiments/m10/m10_phase_h_per_query_results.csv", encoding="utf-8")))

for cfg in ["ConfigA_Production", "ConfigB_AdaptiveE6b"]:
    sub = [r for r in rows if r["config_id"] == cfg]
    print(f"==================== {cfg} (N={len(sub)}) ====================")
    
    for timing_col in ["retrieval_latency_ms", "controller_latency_ms", "generation_latency_ms", "total_latency_ms"]:
        vals = [float(r[timing_col]) for r in sub]
        mean = statistics.mean(vals)
        p50 = percentile(vals, 50)
        p95 = percentile(vals, 95)
        print(f"  {timing_col:<24}: mean={mean:.2f} ms | p50={p50:.2f} ms | p95={p95:.2f} ms")
        
    print("\n  -- By Language Retrieval Latency --")
    for lang in ["en", "hi", "hi-Latn", "en-hi"]:
        l_vals = [float(r["retrieval_latency_ms"]) for r in sub if r["language"] == lang]
        print(f"    {lang:<10}: mean={statistics.mean(l_vals):.2f} ms | p50={percentile(l_vals, 50):.2f} ms | p95={percentile(l_vals, 95):.2f} ms")
        
    print("\n  -- By Language Total Latency --")
    for lang in ["en", "hi", "hi-Latn", "en-hi"]:
        l_vals = [float(r["total_latency_ms"]) for r in sub if r["language"] == lang]
        print(f"    {lang:<10}: mean={statistics.mean(l_vals):.2f} ms | p50={percentile(l_vals, 50):.2f} ms | p95={percentile(l_vals, 95):.2f} ms")
    print()
