import pandas as pd

df = pd.read_csv('backend/data/experiments/m6/m6_phase2b1_claim_enforcement_audit.csv')
print("Cross-tabulation of cohort_group vs verdict:")
print(pd.crosstab(df['cohort_group'], df['verdict'], margins=True))

print("\nLet's check EXCLUDED_NEEDS_REVIEW and EXCLUDED_AUTO_REJECTED:")
for cg in ['ELIGIBLE_PROVISIONAL', 'EXCLUDED_NEEDS_REVIEW', 'EXCLUDED_AUTO_REJECTED']:
    sub = df[df['cohort_group'] == cg]
    print(f"\n--- {cg} (total claims: {len(sub)}) ---")
    print(sub['verdict'].value_counts())

