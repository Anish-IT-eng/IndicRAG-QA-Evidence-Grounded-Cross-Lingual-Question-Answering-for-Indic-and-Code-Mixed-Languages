import json

with open('backend/data/experiments/m6/m6_phase2b_controller_trace.jsonl', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i < 3:
            ev = json.loads(line)
            print(f"Record {i}:", list(ev.keys()))
            print("decision field:", ev.get('decision'), ev.get('status'), ev.get('state'), ev.get('controller_state'))

