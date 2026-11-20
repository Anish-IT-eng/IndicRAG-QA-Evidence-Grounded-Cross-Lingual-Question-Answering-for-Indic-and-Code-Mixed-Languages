import sys
from pathlib import Path
sys.path.insert(0, str(Path('backend').resolve()))

import json
import sqlite3
import pandas as pd
import requests

conn = sqlite3.connect('backend/data/db/indicrag.db')
c = conn.cursor()

df_claims = pd.read_csv('backend/data/experiments/m6/m6_phase2b1_claim_enforcement_audit.csv')
target_ids = ['b0a1c002-87a2-4102-9002-000000000002', 'b0a1c006-87a6-4106-9006-000000000006']
subset = df_claims[df_claims['candidate_id'].isin(target_ids)]

for idx, r in subset.iterrows():
    cid = r['candidate_id']
    print(f"\n=======================================================")
    print(f"Candidate: {cid}")
    print(f"Claim ID: {r['claim_id']}")
    print(f"Claim Text: {r['claim_text']}")
    print(f"Current Lexical Overlap Verdict: {r['verdict']}")
    print(f"Explanation: {r['explanation']}")
    
    df_conf = pd.read_csv('backend/data/experiments/m6/m6_phase2b1_conflict_audit.csv')
    crow = df_conf[df_conf['candidate_id'] == cid].iloc[0]
    pidA = crow['top_valid_passage_id']
    
    c.execute("SELECT text FROM passages WHERE passage_id=?", (pidA,))
    textA = c.fetchone()[0]
    print(f"\nPassage A ({crow['top_valid_doc_filename']}):\n{textA[:200]}...")
    
    prompt = f"""You are an independent semantic entailment verifier for QA evaluation.
Given the official reference passage and a statement/claim in Romanized Hindi or Hindi, determine if the statement is factually ENTAILED by the passage, CONTRADICTED by the passage, or INSUFFICIENT_SUPPORT (unsupported).
Do not reject a statement simply because it is in Hindi or Hinglish while the passage is in English.

Passage:
\"\"\"{textA}\"\"\"

Statement:
\"\"\"{r['claim_text']}\"\"\"

Respond in JSON format:
{{
  "verdict": "ENTAILED" | "CONTRADICTED" | "INSUFFICIENT_SUPPORT",
  "confidence": 0.0 to 1.0,
  "explanation": "concise explanation of semantic correspondence"
}}
"""
    for model in ["qwen2.5:3b", "llama3.2:3b"]:
        try:
            resp = requests.post("http://127.0.0.1:11434/api/generate", json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=30)
            if resp.status_code == 200:
                print(f"\nModel {model} output:")
                print(resp.json().get('response'))
            else:
                print(f"Model {model} returned status {resp.status_code}")
        except Exception as e:
            print(f"Model {model} failed: {e}")
