import json
with open('backend/data/experiments/m9/m9_evaluation_dataset.jsonl', 'r', encoding='utf-8') as f:
    for i in range(10):
        line = f.readline()
        d = json.loads(line)
        print(d['query_id'], '| pids:', d.get('expected_passage_ids'), '| dids:', d.get('expected_document_ids'))
