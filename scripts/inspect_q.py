import json
import sys

q_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 112
with open("backend/data/experiments/m9/m9_evaluation_dataset.jsonl", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i == q_idx:
            data = json.loads(line)
            print(f"Index {i}: {data['query_id']} ({data['query_language']}) -> {data['query_text']}")
            break
