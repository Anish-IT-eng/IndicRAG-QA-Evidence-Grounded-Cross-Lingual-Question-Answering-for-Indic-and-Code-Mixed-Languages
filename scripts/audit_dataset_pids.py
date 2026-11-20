import json
import sqlite3

conn = sqlite3.connect("backend/data/db/indicrag.db")
c = conn.cursor()

with open("backend/data/experiments/m9/m9_evaluation_dataset.jsonl", "r", encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]

missing_pids = set()
for r in records:
    if r["expected_status"] == "ANSWERED" and not r["expected_passage_ids"]:
        missing_pids.add(r["intent_id"])

print(f"Total answerable queries: {len([r for r in records if r['expected_status'] == 'ANSWERED'])}")
print(f"Intents missing expected_passage_ids: {len(missing_pids)}: {sorted(list(missing_pids))}")
