import csv
import json
from pathlib import Path

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
results_path = root / "backend/data/experiments/m10/m10_phase_f_end_to_end_results.csv"

rows = list(csv.DictReader(open(results_path, encoding="utf-8")))

for r in rows:
    if r["query_id"] in ["M9-Q201", "M9-Q229"] and r["config_id"] == "ConfigA_Production":
        print(f"=== {r['query_id']} ({r['language']}) Expected: {r['expected_status']} Response: {r['response_status']} ===")
        print("Query:", r["query_text"])
        print("Answer:", r["final_answer"])
        print("CECI:", r["ceci_score"], "Citations:", r["citations_count"])
