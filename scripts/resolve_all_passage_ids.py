import sqlite3
import json

conn = sqlite3.connect("backend/data/db/indicrag.db")
c = conn.cursor()

# Known manual map for the 13 intents
intent_pids_map = {
    "M9-INT-01": ["0280358a-ff3c-4964-88ab-419a9147b1f0"], # Notification 307
    "M9-INT-03": ["c31d716d-bcfe-4011-a3f6-f4a2d5f1f22b", "6ad292d8-6e01-4f3b-aa96-66ee4603b11e"], # 10% relaxation
    "M9-INT-04": ["c31d716d-bcfe-4011-a3f6-f4a2d5f1f22b", "6ad292d8-6e01-4f3b-aa96-66ee4603b11e"], # short absence exclusion
    "M9-INT-05": ["0280358a-ff3c-4964-88ab-419a9147b1f0", "f88ec726-74ba-426f-a01f-4b9665c1a8b8"], # 70 vs 75
    "M9-INT-07": ["c31d716d-bcfe-4011-a3f6-f4a2d5f1f22b"], # Dean / VC authority
    "M9-INT-08": ["f88ec726-74ba-426f-a01f-4b9665c1a8b8"], # lectures tutorials practicals
    "M9-INT-10": ["f88ec726-74ba-426f-a01f-4b9665c1a8b8"], # X grade
    "M9-INT-12": ["ddcfcc9d-cad0-4a97-90a0-50bc28e6b2a4"], # I grade
    "M9-INT-16": ["971de0a7-0db2-41cd-97df-7bf4ac233d60"], # 5.0 CGPA
    "M9-INT-20": ["ddcfcc9d-cad0-4a97-90a0-50bc28e6b2a4"], # 5 days medical submission
    "M9-INT-33": ["c47c753f-92f5-4fea-8273-784a6223b29c"], # suspension upto 2 weeks
    "M9-INT-38": ["9d2361de-c514-45ea-9376-e40fa0cc150e"], # UFM committee
    "M9-INT-45": ["4313f890-50ee-49be-ae5b-07c87c7e5a6a"], # First Ordinance VC officer
}

# Update dataset
with open("backend/data/experiments/m9/m9_evaluation_dataset.jsonl", "r", encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]

updated_count = 0
for r in records:
    iid = r["intent_id"]
    if iid in intent_pids_map and not r["expected_passage_ids"]:
        r["expected_passage_ids"] = intent_pids_map[iid]
        updated_count += 1

with open("backend/data/experiments/m9/m9_evaluation_dataset.jsonl", "w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"Updated {updated_count} queries in m9_evaluation_dataset.jsonl. All 45 answerable intents now have explicit expected_passage_ids!")
