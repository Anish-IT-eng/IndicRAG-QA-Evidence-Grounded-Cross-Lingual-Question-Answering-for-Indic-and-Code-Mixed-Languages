import csv
import json

with open('backend/data/experiments/m9/answer_generation_results.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total rows: {len(rows)}")
by_lang = {}
for r in rows:
    lang = r['language']
    by_lang.setdefault(lang, []).append(r)

for lang, q_list in by_lang.items():
    ans_count = sum(1 for q in q_list if q['response_status'].lower() == 'answered')
    unans_count = sum(1 for q in q_list if q['response_status'].lower() == 'unanswerable')
    status_correct = sum(1 for q in q_list if q['status_correct'].lower() == 'true')
    print(f"Lang {lang}: total={len(q_list)}, answered={ans_count}, unanswerable={unans_count}, status_correct={status_correct}")
