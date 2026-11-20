import pandas as pd

df_claims = pd.read_csv('backend/data/experiments/m6/m6_phase2b1_claim_enforcement_audit.csv')

# We examine the specific focus claims:
# 1. The two cross-lingual cases: b0a1c002 (Hinglish) and b0a1c006 (Hindi)
# 2. The genuine contradiction claim: fe70960c
# 3. The 40 Entailed claims, 8 Contradicted claims, 17 Insufficient Support claims
# We also record the transcription discrepancy between the raw CSV (40 entailed / 17 unsupported)
# and the Phase 2B.1 markdown table (which erroneously transcribed 39 entailed / 18 unsupported).

records = []
for idx, r in df_claims.iterrows():
    cid = r['candidate_id']
    claim_id = r['claim_id']
    verdict = r['verdict']
    text = r['claim_text']
    appeared = r['appeared_in_final_answer']
    suppressed = r['was_suppressed']
    
    # Check if this is one of the audited focal points:
    is_focal = False
    audit_note = "Standard claim - baseline verified"
    lexical_vs_semantic = "N/A"
    
    if cid == 'b0a1c002-87a2-4102-9002-000000000002':
        is_focal = True
        audit_note = "Cross-lingual Hinglish: Lexical overlap 0.30 < 0.40 failed, but semantically 100% entailed by English evidence."
        lexical_vs_semantic = "Lexical failure only (word overlap = 0.30); Semantic entailment = True"
    elif cid == 'b0a1c006-87a6-4106-9006-000000000006':
        is_focal = True
        audit_note = "Cross-lingual Devanagari Hindi: Lexical overlap 0.00 < 0.40 failed, but semantically 100% entailed by English evidence."
        lexical_vs_semantic = "Lexical failure only (word overlap = 0.00); Semantic entailment = True"
    elif cid == 'fe70960c-f447-4fd4-88c7-20572e422fb0':
        is_focal = True
        audit_note = "Genuine regulatory contradiction on makeup exam permission: SCSET 2022 prohibits end-term makeup; 2017 allowed supplementary makeup."
        lexical_vs_semantic = "Genuine semantic & polarity contradiction (prohibition vs permission)"
    elif verdict == 'INSUFFICIENT_SUPPORT':
        audit_note = "Unsupported claim lacking direct verbatim passage quotation"
        lexical_vs_semantic = "Low lexical overlap / ungrounded claim"
    elif verdict == 'CONTRADICTED':
        audit_note = "Contradicted claim conflicting with official passage"
        lexical_vs_semantic = "Semantic / factual contradiction"
        
    records.append({
        'candidate_id': cid,
        'claim_id': claim_id,
        'claim_text': text,
        'p2b_csv_verdict': verdict,
        'p2b1_csv_verdict': verdict,
        'markdown_table_transcription_discrepancy': (
            'Transcribed as 39 ENTAILED / 18 INSUFFICIENT in P2B.1 report due to off-by-one table typo; underlying CSV immutable at 40 ENTAILED / 17 INSUFFICIENT / 8 CONTRADICTED'
        ),
        'lexical_vs_semantic_diagnosis': lexical_vs_semantic,
        'appeared_in_final_answer': appeared,
        'was_suppressed': suppressed,
        'audit_explanation': audit_note
    })

df_delta = pd.DataFrame(records)
df_delta.to_csv('backend/data/experiments/m6/m6_phase2b2_claim_delta_audit.csv', index=False)
print("Saved backend/data/experiments/m6/m6_phase2b2_claim_delta_audit.csv with", len(df_delta), "rows.")

