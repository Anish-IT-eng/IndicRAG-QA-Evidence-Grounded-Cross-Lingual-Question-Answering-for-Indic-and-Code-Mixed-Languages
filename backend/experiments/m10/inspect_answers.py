import csv
import json
from pathlib import Path

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
results_path = root / "backend/data/experiments/m10/m10_phase_f_end_to_end_results.csv"

rows = list(csv.DictReader(open(results_path, encoding="utf-8")))

answered_a = [r for r in rows if r["config_id"] == "ConfigA_Production" and r["final_answer"]]
answered_b = [r for r in rows if r["config_id"] == "ConfigB_AdaptiveE6b" and r["final_answer"]]

print(f"Config A rows with final_answer: {len(answered_a)}")
print(f"Config B rows with final_answer: {len(answered_b)}")

# Let's inspect some sample answers
for r in answered_b[:5]:
    print("---", r["query_id"], r["language"], r["response_status"])
    print(r["final_answer"][:200])
