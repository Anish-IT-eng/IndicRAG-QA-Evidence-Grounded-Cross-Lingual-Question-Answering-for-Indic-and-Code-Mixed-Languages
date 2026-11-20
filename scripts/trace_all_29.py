import pandas as pd

df = pd.read_csv('backend/data/experiments/m6/m6_phase2b1_conflict_audit.csv')

print("=== AUDIT OF ALL 29 PILOT QUERIES ===")
for i, r in df.iterrows():
    print(f"[{i:2d}] ID: {r['candidate_id'][:20]} | Gold: {r['gold_answerability']:12s} | Orig: {r['controller_status']:12s} | Rec: {r['reclassification_recommendation']:22s}")

