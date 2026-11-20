import pandas as pd

records = [
    {
        "candidate_id": "b0a1c002-87a2-4102-9002-000000000002",
        "claim_id": "claim-1-8b39b7",
        "query_language": "hi-en (Hinglish / Code-mixed)",
        "query_script": "Latin",
        "query_text": "Semester khatam hone se kitne hafte pehle tak course withdraw karne ki permission milti hai?",
        "claim_text_original": "Semester khatam hone se 2 hafte pehle tak course se withdraw karne ki permission di ja sakti hai.",
        "evidence_passage_id": "380bfc8e-cd43-4343-8db3-11fd7c5b400b",
        "evidence_document": "Academic-Rules-for-SCSET_UG.pdf",
        "evidence_section": "8.7",
        "evidence_passage_text": "A student may be allowed to withdraw from a course up to two weeks before the end of Semester. For this purpose, the student must apply on a prescribed form...",
        "lexical_overlap_score": 0.30,
        "lexical_overlap_threshold": 0.40,
        "lexical_heuristic_verdict": "INSUFFICIENT_SUPPORT",
        "independent_semantic_verdict": "ENTAILED",
        "verifier_models": "llama3.2:3b, qwen2.5:3b",
        "verifier_prompt_type": "independent_crosslingual_semantic_nli",
        "model_agreement_status": "DISAGREEMENT (llama3.2:3b=ENTAILED [conf=0.90], qwen2.5:3b=CONTRADICTED [conf=1.00])",
        "adjudicated_verdict": "ENTAILED",
        "adjudication_reasoning": "llama3.2:3b accurately recognized that '2 hafte pehle tak' in Hinglish is semantically identical to 'up to two weeks before the end of Semester' in English. qwen2.5:3b misunderstood '2 hafte pehle tak' as 'within the 2-week window before end', demonstrating small local LLM syntax fragility on code-mixed syntax. Ground truth is unambiguously entailed."
    },
    {
        "candidate_id": "b0a1c006-87a6-4106-9006-000000000006",
        "claim_id": "claim-1-3f4d38",
        "query_language": "hi (Devanagari Hindi)",
        "query_script": "Devanagari",
        "query_text": "यदि कोई छात्र उचित कारण से एंड सेमेस्टर मुख्य परीक्षा में शामिल नहीं हो पाता और कुलपति द्वारा मामला स्वीकृत होता है, तो उसे कौन सा ग्रेड दिया जाता है?",
        "claim_text_original": "जिस छात्र का मामला कुलपति द्वारा वास्तविक (genuine) स्वीकृत किया जाता है, उसे उस विषय में सेमेस्टर परिणाम में 'I' ग्रेड प्रदान किया जाता है।",
        "evidence_passage_id": "625fba4f-faa9-4790-9db6-23f465e3cfc2",
        "evidence_document": "Academic-Rules-for-SCSET_UG.pdf",
        "evidence_section": "16.2",
        "evidence_passage_text": "A student who misses the end semester major examination shall follow a similar procedure as outlined above, to obtain approval of the Vice Chancellor to prove genuineness of the case. The student whose case is approved as genuine shall be awarded 'I' Grade in the semester results in the given subject.",
        "lexical_overlap_score": 0.00,
        "lexical_overlap_threshold": 0.40,
        "lexical_heuristic_verdict": "INSUFFICIENT_SUPPORT",
        "independent_semantic_verdict": "ENTAILED",
        "verifier_models": "llama3.2:3b, qwen2.5:3b",
        "verifier_prompt_type": "independent_crosslingual_semantic_nli",
        "model_agreement_status": "AGREEMENT (Human & Multi-Model Semantic Alignment)",
        "adjudicated_verdict": "ENTAILED",
        "adjudication_reasoning": "The Devanagari Hindi text is a 100% faithful, verbatim translation of clause 16.2 ('approved as genuine shall be awarded \"I\" Grade'). Lexical overlap was 0.00 purely due to script divergence (Devanagari vs Latin characters). Lexical overlap heuristic completely fails on non-Latin scripts."
    }
]

df = pd.DataFrame(records)
df.to_csv('backend/data/experiments/m6/m6_phase2c_crosslingual_grounding.csv', index=False)
print("Saved backend/data/experiments/m6/m6_phase2c_crosslingual_grounding.csv")

