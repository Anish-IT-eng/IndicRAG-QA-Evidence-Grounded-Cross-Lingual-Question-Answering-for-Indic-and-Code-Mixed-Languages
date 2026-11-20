import csv
from pathlib import Path

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
raw_h = list(csv.DictReader(open(root / "backend/data/experiments/m10/m10_phase_h_per_query_results.csv", encoding="utf-8")))

diffs = []
for r in raw_h:
    ret = float(r["retrieval_latency_ms"])
    ctrl = float(r["controller_latency_ms"])
    gen = float(r["generation_latency_ms"])
    tot = float(r["total_latency_ms"])
    diff = tot - (ret + ctrl + gen)
    diffs.append(abs(diff))

print(f"Max difference between total and sum of components: {max(diffs):.4f} ms")
print(f"Mean difference: {sum(diffs)/len(diffs):.4f} ms")
