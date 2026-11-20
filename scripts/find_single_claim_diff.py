import pandas as pd

df_p2b = pd.read_csv('backend/data/experiments/m6/m6_phase2b_claim_grounding.csv')
print("P2B value counts:")
print(df_p2b['verdict'].value_counts())

df_p2b1 = pd.read_csv('backend/data/experiments/m6/m6_phase2b1_claim_enforcement_audit.csv')
print("\nP2B1 value counts:")
print(df_p2b1['verdict'].value_counts())

for i in range(len(df_p2b)):
    v1 = df_p2b.iloc[i]['verdict']
    v2 = df_p2b1.iloc[i]['verdict']
    if v1 != v2:
        print(f"Row {i} changed! v1={v1}, v2={v2}")
        print(df_p2b.iloc[i])
        print(df_p2b1.iloc[i])

