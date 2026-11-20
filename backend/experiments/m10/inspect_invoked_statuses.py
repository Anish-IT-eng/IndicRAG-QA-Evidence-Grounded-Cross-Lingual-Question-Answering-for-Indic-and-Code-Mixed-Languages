import csv
from collections import Counter
from pathlib import Path

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
raw_f = list(csv.DictReader(open(root / "backend/data/experiments/m10/m10_phase_f_end_to_end_results.csv", encoding="utf-8")))

sub_a = [r for r in raw_f if r["config_id"] == "ConfigA_Production"]

invoked_a = [r for r in sub_a if float(r["generation_latency_ms"]) > 1.0]
skipped_a = [r for r in sub_a if float(r["generation_latency_ms"]) <= 1.0]

print("=== Config A Invoked Generation Response Statuses ===")
print(Counter(r["response_status"] for r in invoked_a))
print(Counter(r["expected_status"] for r in invoked_a))

print("\n=== Config A Skipped Generation Response Statuses ===")
print(Counter(r["response_status"] for r in skipped_a))
print(Counter(r["expected_status"] for r in skipped_a))
