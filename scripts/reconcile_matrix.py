import pandas as pd

df = pd.read_csv('backend/data/experiments/m6/m6_phase2b1_conflict_audit.csv')

print(f"Total rows in conflict audit: {len(df)}")
print(df['controller_status'].value_counts())
print()
print("Gold answerability distribution:")
print(df['gold_answerability'].value_counts())

# Strict Historical Phase 2B:
# Answerable = (controller_status == 'partial') | (controller_status == 'sufficient')
# Unanswerable = (controller_status == 'conflicting') | (controller_status == 'insufficient') | (controller_status == 'missing')

print("\n--- 1. HISTORICAL PHASE 2B MAPPING ---")
tp_hist = df[(df['gold_answerability'] == 'answerable') & (df['controller_status'].isin(['sufficient', 'partial']))]
fn_hist = df[(df['gold_answerability'] == 'answerable') & (~df['controller_status'].isin(['sufficient', 'partial']))]
fp_hist = df[(df['gold_answerability'] == 'unanswerable') & (df['controller_status'].isin(['sufficient', 'partial']))]
tn_hist = df[(df['gold_answerability'] == 'unanswerable') & (~df['controller_status'].isin(['sufficient', 'partial']))]

print(f"TP: {len(tp_hist)} (expected 6)")
print(f"FN: {len(fn_hist)} (expected 21)")
print(f"FP: {len(fp_hist)} (expected 0)")
print(f"TN: {len(tn_hist)} (expected 2)")

print("\nLet's see FN queries in historical mapping:")
print("FN controller_status counts:")
print(fn_hist['controller_status'].value_counts())
# In fn_hist: conflicting = 13, insufficient = 8!
# Wait! Total answerable = 27. Total unanswerable = 2. Total = 29.
# insufficient: total in df is 10. 8 are answerable, 2 are unanswerable!

print("\n--- 2. WHAT HAPPENS IF IDENTICAL RULES ARE RECLASSIFIED ---")
print("Reclassification recommendations across all 29 rows:")
print(df['reclassification_recommendation'].value_counts())

# What were the 13 conflicting queries recommended for?
conf_13 = df[df['controller_status'] == 'conflicting']
print("\nRecommendations for the 13 conflicting queries:")
print(conf_13['reclassification_recommendation'].value_counts())

