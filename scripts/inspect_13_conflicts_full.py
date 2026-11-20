import pandas as pd

df = pd.read_csv('backend/data/experiments/m6/m6_phase2b1_conflict_audit.csv')
conf_13 = df[df['controller_status'].str.lower() == 'conflicting']

print("=== DETAILED TEXT ANALYSIS OF THE 13 CONFLICTING QUERIES ===")
for i, (idx, r) in enumerate(conf_13.iterrows()):
    print(f"\n--- [{i+1}/13] ID: {r['candidate_id']} (idx={idx}) ---")
    print(f"Query: {r['query_text']}")
    print(f"Gold Answerability: {r['gold_answerability']}")
    print(f"Doc A: {r['top_valid_doc_filename']} | ID: {r['top_valid_passage_id']}")
    print(f"Doc A Text:\n{r['top_valid_text_snippet']}")
    print(f"Doc B: {r['top_conflicting_doc_filename']} | ID: {r['top_conflicting_passage_id']}")
    print(f"Doc B Text:\n{r['top_conflicting_text_snippet']}")
    print(f"Recommendation in CSV: {r['reclassification_recommendation']}")
    print(f"Genuine conflict in CSV: {r['genuine_regulatory_conflict']}")
    print(f"Justification: {r['audit_justification']}")

