import csv
from collections import Counter
from pathlib import Path

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
raw_h = list(csv.DictReader(open(root / "backend/data/experiments/m10/m10_phase_h_per_query_results.csv", encoding="utf-8")))

sub_b = [r for r in raw_h if r["config_id"] == "ConfigB_AdaptiveE6b"]

print("Controller statuses:", Counter(r["controller_status"] for r in sub_b))
print("Response statuses:", Counter(r["response_status"] for r in sub_b))

# Cross tabulation
table = Counter((r["controller_status"], r["response_status"], float(r["generation_latency_ms"]) > 1.0) for r in sub_b)
print("\n=== Cross-Tabulation (controller_status, response_status, LLM_invoked) ===")
for k, count in sorted(table.items()):
    print(f"Controller: {k[0]:<22} | Response: {k[1]:<22} | LLM Invoked: {str(k[2]):<5} | Count: {count}")
