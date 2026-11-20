import csv
import json
from pathlib import Path

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
m9_answers = root / "backend/data/experiments/m9/answer_generation_results.csv"

rows = list(csv.DictReader(open(m9_answers, encoding="utf-8")))
print(f"Total rows in M9 answers: {len(rows)}")
for r in rows:
    if int(r.get("citations_count", 0) or 0) > 0:
        print(f"Query {r['query_id']} ({r['language']}) citations_count: {r['citations_count']}")
        print("  Citations field:", r.get("citations", "N/A"))
        print("  Answer:", r.get("final_answer", "")[:120])
        break
