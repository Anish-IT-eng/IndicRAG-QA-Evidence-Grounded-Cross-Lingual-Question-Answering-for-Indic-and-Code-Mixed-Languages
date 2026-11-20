import json
import pandas as pd

m_p2b = json.load(open('backend/data/experiments/m6/m6_phase2b_manifest.json'))
print("Keys in m_p2b:", list(m_p2b.keys()))
for k, v in m_p2b.items():
    if 'claim' in k.lower():
        print(k, v)

# Let's inspect STATUS.md or docs/m6_phase2b_controller_report.md or docs/m6_phase2b1_integrity_audit.md
doc_p2b = open('docs/m6_phase2b_pilot_evaluation.md', 'r', encoding='utf-8').read()
for line in doc_p2b.split('\n'):
    if 'entailed' in line.lower() or 'claim' in line.lower():
        print(line[:120])
