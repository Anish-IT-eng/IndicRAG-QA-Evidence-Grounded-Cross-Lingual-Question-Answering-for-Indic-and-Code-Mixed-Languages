import pandas as pd

df_neg = pd.read_csv('backend/data/dataset/m6_phase3_negative_candidates.csv')
for idx, r in df_neg.iterrows():
    tax = r['primary_taxonomy']
    lang = r['query_language']
    print(f"{idx+1}. [{tax}] ({lang}) ID: {r['candidate_id'][:8]}")
    print(f"   Q:    {r['original_question']}")
    print(f"   Exp:  {r['expected_evidence_state']}")
    print(f"   Ans:  {r['answerability']}")
    print(f"   Ref:  {r['reference_answer'][:100]}...")

