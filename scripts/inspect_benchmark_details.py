import pandas as pd

df_bench = pd.read_csv('backend/data/dataset/m6_expanded_benchmark_n60.csv')
df_pilot = pd.read_csv('backend/data/experiments/m6/m6_phase2b2_confusion_matrix.csv')

merged = pd.merge(df_pilot, df_bench, on='candidate_id')
print(f"Merged count: {len(merged)}")
print("Distribution of benchmark expected_evidence_state in eligible pilot:")
print(merged['expected_evidence_state'].value_counts())
print("\nBenchmark expected_evidence_state vs controller_status:")
print(pd.crosstab(merged['expected_evidence_state'], merged['historical_controller_status']))
