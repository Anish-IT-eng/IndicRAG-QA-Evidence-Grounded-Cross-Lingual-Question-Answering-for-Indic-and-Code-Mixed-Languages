import pandas as pd

df = pd.read_csv('backend/data/experiments/m6/m6_phase2b_query_eval.csv')
print("Columns in m6_phase2b_query_eval.csv:", df.columns.tolist())
print(df.head(2).to_dict(orient='records'))
