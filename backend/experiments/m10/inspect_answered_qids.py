import csv
import json
from pathlib import Path

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
results_path = root / "backend/data/experiments/m10/m10_phase_f_end_to_end_results.csv"

rows = list(csv.DictReader(open(results_path, encoding="utf-8")))

for cfg in ["ConfigA_Production", "ConfigB_AdaptiveE6b"]:
    sub = [r for r in rows if r["config_id"] == cfg and r["response_status"] in ["answered", "clarification_needed", "conflicting_versions"]]
    print(f"=== {cfg}: {len(sub)} answers ===")
    by_lang = {}
    for r in sub:
        by_lang.setdefault(r["language"], []).append(r["query_id"])
    for l, qids in by_lang.items():
        print(f"  {l} ({len(qids)}): {qids}")
