import json
import csv
from collections import Counter

print("=== INSPECTING M9 EVALUATION DATASET (JSONL) ===")
with open("backend/data/experiments/m9/m9_evaluation_dataset.jsonl", "r", encoding="utf-8") as f:
    m9_rows = [json.loads(line) for line in f if line.strip()]

print(f"Total rows: {len(m9_rows)}")
print(f"Keys: {list(m9_rows[0].keys())}")
print("query_language distribution:", Counter(r["query_language"] for r in m9_rows))
print("expected_status distribution:", Counter(r["expected_status"] for r in m9_rows))
print("query_type distribution:", Counter(r["query_type"] for r in m9_rows))
print("Unique intents:", len(set(r["intent_id"] for r in m9_rows)))

print("\n=== INSPECTING M6 EXPANDED BENCHMARK (N=60) ===")
with open("backend/data/dataset/m6_expanded_benchmark_n60.csv", "r", encoding="utf-8") as f:
    m6_rows = list(csv.DictReader(f))
print(f"Total rows: {len(m6_rows)}")
print("answerability distribution:", Counter(r["answerability"] for r in m6_rows))
print("question_type distribution:", Counter(r["question_type"] for r in m6_rows))

print("\n=== INSPECTING M3 FINAL DATASET (N=15) ===")
with open("backend/data/dataset/final_verified_dataset.csv", "r", encoding="utf-8") as f:
    m3_rows = list(csv.DictReader(f))
print(f"Total rows: {len(m3_rows)}")
print("answerability distribution:", Counter(r["answerability"] for r in m3_rows))
print("question_type distribution:", Counter(r["question_type"] for r in m3_rows))
