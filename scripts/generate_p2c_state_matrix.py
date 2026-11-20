import pandas as pd
import numpy as np

df_exp = pd.read_csv('backend/data/experiments/m6/m6_phase2c_expected_states.csv')
df_conf = pd.read_csv('backend/data/experiments/m6/m6_phase2b2_confusion_matrix.csv')
merged = pd.merge(df_exp, df_conf[['candidate_id', 'corrected_audited_status']], on='candidate_id')

STATES = ['SUFFICIENT', 'PARTIAL', 'INSUFFICIENT', 'CONFLICTING', 'MISSING', 'CLARIFICATION_REQUIRED']

# 1. Historical Matrix
y_true = merged['independent_expected_state'].tolist()
y_hist = merged['historical_controller_status'].tolist()
matrix_hist = pd.DataFrame(0, index=STATES, columns=STATES)
for t, p in zip(y_true, y_hist):
    if t in STATES and p in STATES:
        matrix_hist.loc[t, p] += 1

# 2. Reclassified Operational Matrix
y_corr = merged['corrected_audited_status'].tolist()
matrix_corr = pd.DataFrame(0, index=STATES, columns=STATES)
for t, p in zip(y_true, y_corr):
    if t in STATES and p in STATES:
        matrix_corr.loc[t, p] += 1

# Combine into a single auditable CSV
matrix_hist['version'] = 'Historical_Phase2B'
matrix_corr['version'] = 'Reclassified_Operational_Phase2C'

combined_matrices = pd.concat([matrix_hist, matrix_corr])
combined_matrices.to_csv('backend/data/experiments/m6/m6_phase2c_state_confusion_matrix.csv')
print("Saved backend/data/experiments/m6/m6_phase2c_state_confusion_matrix.csv")

print("\n--- Reclassified Operational Matrix ---")
print(matrix_corr.drop(columns=['version']))

acc_corr = sum(matrix_corr.loc[s, s] for s in STATES) / len(merged)
print(f"Reclassified 6-State Accuracy: {acc_corr:.4f} ({sum(matrix_corr.loc[s, s] for s in STATES)}/{len(merged)})")
