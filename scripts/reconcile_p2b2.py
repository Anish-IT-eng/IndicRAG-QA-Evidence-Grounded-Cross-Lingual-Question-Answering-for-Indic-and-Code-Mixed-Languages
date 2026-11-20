import pandas as pd
import json

df_conf = pd.read_csv('backend/data/experiments/m6/m6_phase2b1_conflict_audit.csv')
conf_13 = df_conf[df_conf['controller_status'].str.lower() == 'conflicting']

print(f"Total conflicting queries: {len(conf_13)}")
for i, (idx, r) in enumerate(conf_13.iterrows()):
    print(f"{i+1:2d}. idx={idx:2d} id={r['candidate_id']} rec={r['reclassification_recommendation']} conflict={r['genuine_regulatory_conflict']}")
    print(f"    q={r['query_text'][:80]}")
    print(f"    docA={r['top_valid_doc_filename']} ({r['top_valid_passage_id']})")
    print(f"    docB={r['top_conflicting_doc_filename']} ({r['top_conflicting_passage_id']})")
