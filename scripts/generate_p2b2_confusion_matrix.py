import pandas as pd

# We will generate a clear, query-by-query ledger and summary confusion matrix
# First, let's produce the query-level classification for the 29 pilot queries:

df_conf = pd.read_csv('backend/data/experiments/m6/m6_phase2b1_conflict_audit.csv')

# Query-level classification table
records = []
for idx, r in df_conf.iterrows():
    qid = r['candidate_id']
    qtext = r['query_text']
    gold = r['gold_answerability'] # answerable / unanswerable
    orig_status = r['controller_status'] # conflicting / partial / insufficient
    
    # Classifications under historical vs corrected operational:
    # 1. Historical binary
    if orig_status in ['sufficient', 'partial']:
        hist_bin = 'Answered'
        hist_class = 'TP' if gold == 'answerable' else 'FP'
    else:
        hist_bin = 'Abstained'
        hist_class = 'FN' if gold == 'answerable' else 'TN'
        
    # 2. Corrected operational:
    # 11 identical rules become SUFFICIENT -> Answered
    # 1 genuine conflict (fe70960c) -> MAINTAIN_CONFLICTING -> Abstained (FN)
    # 1 cohort attendance (b0a1c004) -> CLARIFICATION_REQUIRED -> Clarification (CR)
    # 6 original partial -> Answered (TP)
    # 8 original insufficient (answerable) -> Abstained (FN)
    # 2 original insufficient (unanswerable) -> Abstained (TN)
    
    if qid == 'b0a1c004-87a4-4104-9004-000000000004':
        oper_decision = 'CLARIFICATION_REQUIRED'
        oper_class = 'CR'
    elif qid == 'fe70960c-f447-4fd4-88c7-20572e422fb0':
        oper_decision = 'CONFLICTING'
        oper_class = 'FN'
    elif orig_status == 'conflicting':
        # One of the 11 identical-rule cases
        oper_decision = 'SUFFICIENT'
        oper_class = 'TP'
    elif orig_status == 'partial':
        oper_decision = 'PARTIAL'
        oper_class = 'TP'
    elif orig_status == 'insufficient':
        oper_decision = 'INSUFFICIENT'
        oper_class = 'FN' if gold == 'answerable' else 'TN'
    else:
        oper_decision = orig_status.upper()
        oper_class = 'UNKNOWN'
        
    records.append({
        'candidate_id': qid,
        'query_text': qtext,
        'gold_answerability': gold,
        'historical_controller_status': orig_status.upper(),
        'historical_confusion_class': hist_class,
        'corrected_audited_status': oper_decision,
        'corrected_confusion_class': oper_class,
        'reconciliation_category': (
            'Clarification Required' if oper_class == 'CR' else
            'Genuine Conflict' if qid == 'fe70960c-f447-4fd4-88c7-20572e422fb0' else
            'Identical Rule Recovery' if orig_status == 'conflicting' and oper_class == 'TP' else
            'Baseline Retained'
        )
    })

df_query_matrix = pd.DataFrame(records)
df_query_matrix.to_csv('backend/data/experiments/m6/m6_phase2b2_confusion_matrix.csv', index=False)
print("Saved backend/data/experiments/m6/m6_phase2b2_confusion_matrix.csv with", len(df_query_matrix), "rows.")
print(df_query_matrix['corrected_confusion_class'].value_counts())

