import csv
from pathlib import Path
from collections import Counter

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
raw_h = list(csv.DictReader(open(root / "backend/data/experiments/m10/m10_phase_h_per_query_results.csv", encoding="utf-8")))

sub_b = [r for r in raw_h if r["config_id"] == "ConfigB_AdaptiveE6b"]

print(f"Total Config B rows: {len(sub_b)}")

# Inspect M9-Q201 and M9-Q229
for qid in ["M9-Q201", "M9-Q229"]:
    match = [r for r in sub_b if r["query_id"] == qid][0]
    print(f"\n=== {qid} ===")
    for k, v in match.items():
        if k in ["query_id", "language", "expected_status", "response_status", "status_correct", 
                 "correctness_category", "controller_status", "ceci_score", "retrieval_latency_ms", 
                 "controller_latency_ms", "generation_latency_ms", "total_latency_ms", "final_answer"]:
            print(f"  {k}: {v}")

# Inspect all queries where response_status is NOT unanswerable
non_unans = [r for r in sub_b if r["response_status"] != "unanswerable"]
print(f"\nNon-unanswerable count in Config B: {len(non_unans)}")
for r in non_unans:
    gen_lat = float(r["generation_latency_ms"])
    print(f"  {r['query_id']} ({r['language']}): exp={r['expected_status']} resp={r['response_status']} gen_lat={gen_lat} ctrl={r['controller_status']}")
