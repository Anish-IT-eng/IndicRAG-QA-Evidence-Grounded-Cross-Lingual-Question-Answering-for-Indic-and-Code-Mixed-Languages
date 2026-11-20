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
raw_f = list(csv.DictReader(open(root / "backend/data/experiments/m10/m10_phase_f_end_to_end_results.csv", encoding="utf-8")))

print(f"Total rows in Phase F: {len(raw_f)}")
print("Columns in Phase F:", list(raw_f[0].keys()))

# Check non-zero generation latency queries
for cfg in ["ConfigA_Production", "ConfigB_AdaptiveE6b"]:
    sub = [r for r in raw_f if r["config_id"] == cfg]
    gen_lats = [float(r["generation_latency_ms"]) for r in sub]
    gen_invoked = [l for l in gen_lats if l > 1.0] # invoked generation
    gen_skipped = [l for l in gen_lats if l <= 1.0]
    
    print(f"\n=== {cfg} ===")
    print(f"Total queries: {len(sub)}")
    print(f"Generation invoked (lat > 1ms): {len(gen_invoked)} queries")
    print(f"Generation skipped / abstained (lat <= 1ms): {len(gen_skipped)} queries")
    if gen_invoked:
        print(f"  Invoked Gen Latency: mean={statistics.mean(gen_invoked):.2f} ms | p50={percentile(gen_invoked, 50):.2f} ms | p95={percentile(gen_invoked, 95):.2f} ms")
        print(f"  Invoked Gen Latency: min={min(gen_invoked):.2f} ms | max={max(gen_invoked):.2f} ms")
    print(f"  All-queries Gen Latency (including zeros): mean={statistics.mean(gen_lats):.2f} ms")
