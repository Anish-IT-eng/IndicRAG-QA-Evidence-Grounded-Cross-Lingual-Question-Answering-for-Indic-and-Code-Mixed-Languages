import pandas as pd

df_p2b = pd.read_csv('backend/data/experiments/m6/m6_phase2b_claim_grounding.csv')
df_p2b1 = pd.read_csv('backend/data/experiments/m6/m6_phase2b1_claim_enforcement_audit.csv')

print(f"P2B total rows: {len(df_p2b)}")
print(f"P2B.1 total rows: {len(df_p2b1)}")

# Merge on claim_id or (candidate_id, claim_id)
merged = pd.merge(df_p2b, df_p2b1, on=['candidate_id', 'claim_id'], suffixes=('_p2b', '_p2b1'))

deltas = merged[merged['verdict_p2b'] != merged['verdict_p2b1']]
print(f"\nNumber of verdict deltas: {len(deltas)}")
for idx, r in deltas.iterrows():
    print(f"Candidate: {r['candidate_id']}")
    print(f"Claim ID: {r['claim_id']}")
    print(f"Claim Text: {r['claim_text_p2b']}")
    print(f"Verdict P2B: {r['verdict_p2b']} -> Verdict P2B.1: {r['verdict_p2b1']}")
    print(f"Explanation P2B: {r.get('explanation_p2b')}")
    print(f"Explanation P2B.1: {r.get('explanation_p2b1')}")
    print(f"Discrepancies P2B1: {r.get('discrepancies_p2b1')}")
    print("-" * 50)

