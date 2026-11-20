import pandas as pd

df = pd.read_csv('backend/data/experiments/m6/m6_phase2b_query_eval.csv')
pilot = df[df['cohort_group'] == 'ELIGIBLE_PROVISIONAL'].copy()

for i, (idx, r) in enumerate(pilot.iterrows()):
    print(f"{i+1:2d}. id={r['candidate_id'][:20]} | lang={r['query_language']:6s} | gold={r['gold_answerability']:12s} | ctrl={r['controller_status']:12s} | cov={r['coverage_score']:.2f}")
    print(f"    q={r['original_question']}")

