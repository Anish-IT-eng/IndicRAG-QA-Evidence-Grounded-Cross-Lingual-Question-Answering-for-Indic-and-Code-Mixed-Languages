import csv
from pathlib import Path

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
phase_e = list(csv.DictReader(open(root / "backend/data/experiments/m10/m10_phase_e_per_intent_results.csv", encoding="utf-8")))

e1_rows = {r["query_id"]: r for r in phase_e if r["config_id"] == "E1_PROD_MSMARCO_D10"}
e6b_rows = {r["query_id"]: r for r in phase_e if r["config_id"] == "E6b_ADAPTIVE_BI_ENCODER"}

print(f"E1 rows: {len(e1_rows)}, E6b rows: {len(e6b_rows)}")

# Check Hindi Devanagari hits in E1 vs E6b
hi_e1_hits = [r["query_id"] for r in e1_rows.values() if r["language"] == "hi" and float(r["hit_5"]) > 0]
hi_e6b_hits = [r["query_id"] for r in e6b_rows.values() if r["language"] == "hi" and float(r["hit_5"]) > 0]
print(f"Hindi H@5 in E1: {len(hi_e1_hits)} -> {hi_e1_hits}")
print(f"Hindi H@5 in E6b: {len(hi_e6b_hits)} -> {hi_e6b_hits}")
