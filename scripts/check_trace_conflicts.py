import json
from collections import Counter

trace_records = []
with open('backend/data/experiments/m6/m6_phase2b_controller_trace.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        ev = json.loads(line)
        trace_records.append(ev)

pilot_records = [r for r in trace_records if r.get('cohort_group') == 'ELIGIBLE_PROVISIONAL']
conf_13 = [r for r in pilot_records if r.get('controller_status', '').lower() == 'conflicting']
print(f"Total CONFLICTING in pilot trace: {len(conf_13)}")
for i, r in enumerate(conf_13):
    print(f"{i+1:2d}. candidate_id={r['candidate_id']} | query={r['query'][:70]}")
