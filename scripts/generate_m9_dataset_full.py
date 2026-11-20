"""
Builds the complete M9 evaluation dataset of 60 intent groups x 4 variants = 240 queries.
Outputs:
- backend/data/experiments/m9/m9_evaluation_dataset.jsonl
- backend/data/experiments/m9/m9_human_review_template.csv
- backend/data/experiments/m9/m9_dataset_schema.json
"""
import json
import csv
import os
import sqlite3

# Ensure directories
os.makedirs("backend/data/experiments/m9", exist_ok=True)

# Query DB for passage and document mappings
conn = sqlite3.connect("backend/data/db/indicrag.db")
c = conn.cursor()

doc_map = {}
for row in c.execute("SELECT document_id, filename FROM documents"):
    doc_map[row[1]] = row[0]

def get_passage_id(text_snippet, filename=None):
    sql = "SELECT p.passage_id, p.document_id FROM passages p JOIN documents d ON p.document_id = d.document_id WHERE p.text LIKE ?"
    params = [f"%{text_snippet}%"]
    if filename:
        sql += " AND d.filename LIKE ?"
        params.append(f"%{filename}%")
    row = c.execute(sql, params).fetchone()
    if row:
        return row[0], row[1]
    return "", ""

# Load or define the 60 intents
from m9_intent_definitions import INTENT_SPECS

dataset = []
review_rows = []

query_counter = 1

for spec in INTENT_SPECS:
    intent_id = spec["intent_id"]
    q_type = spec["query_type"]
    expected_status = spec["expected_status"]
    expected_doc_names = spec.get("expected_documents", [])
    expected_doc_ids = [doc_map[name] for name in expected_doc_names if name in doc_map]
    
    snippet = spec.get("passage_snippet", "")
    p_id, d_id = ("", "")
    if snippet:
        p_id, d_id = get_passage_id(snippet, expected_doc_names[0] if expected_doc_names else None)
    
    expected_p_ids = [p_id] if p_id else spec.get("explicit_passage_ids", [])
    if d_id and d_id not in expected_doc_ids:
        expected_doc_ids.append(d_id)
        
    expected_claims = spec["expected_claims"]
    expected_ans = spec["expected_answer"]
    constraints = spec.get("applicability_constraints", {})

    variants = [
        ("en", "LATIN", spec["variants"]["en"], "en"),
        ("hi", "DEVANAGARI", spec["variants"]["hi"], "hi"),
        ("hi-Latn", "LATIN", spec["variants"]["hi_latn"], "hi-Latn"),
        ("en-hi", "LATIN", spec["variants"]["hinglish"], "en-hi"),
    ]

    for lang, script, text, ans_lang in variants:
        qid = f"M9-Q{query_counter:03d}"
        query_counter += 1
        
        record = {
            "intent_id": intent_id,
            "query_id": qid,
            "query_text": text,
            "query_language": lang,
            "script": script,
            "query_type": q_type,
            "expected_answer_language": ans_lang,
            "expected_status": expected_status,
            "expected_document_ids": expected_doc_ids,
            "expected_passage_ids": expected_p_ids,
            "expected_claims": expected_claims,
            "expected_answer": expected_ans,
            "applicability_constraints": constraints,
            "human_review_status": "PROVISIONAL_NOT_HUMAN_VERIFIED",
            "reviewer_notes": f"Provisional {lang} translation for intent {intent_id}; requires native bilingual review."
        }
        dataset.append(record)
        
        review_rows.append({
            "intent_id": intent_id,
            "query_id": qid,
            "query_language": lang,
            "script": script,
            "query_text": text,
            "query_type": q_type,
            "expected_status": expected_status,
            "expected_doc_ids": ";".join(expected_doc_ids),
            "expected_passage_ids": ";".join(expected_p_ids),
            "expected_answer": expected_ans,
            "human_review_status": "PROVISIONAL_NOT_HUMAN_VERIFIED",
            "reviewer_correction": "",
            "translation_quality": "PENDING_REVIEW",
            "reviewer_notes": record["reviewer_notes"]
        })

# Write JSONL
with open("backend/data/experiments/m9/m9_evaluation_dataset.jsonl", "w", encoding="utf-8") as f:
    for rec in dataset:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# Write CSV template
with open("backend/data/experiments/m9/m9_human_review_template.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "intent_id", "query_id", "query_language", "script", "query_text",
        "query_type", "expected_status", "expected_doc_ids", "expected_passage_ids",
        "expected_answer", "human_review_status", "reviewer_correction",
        "translation_quality", "reviewer_notes"
    ])
    writer.writeheader()
    writer.writerows(review_rows)

print(f"Generated {len(dataset)} query records across {len(INTENT_SPECS)} intents.")
print(f"JSONL saved: backend/data/experiments/m9/m9_evaluation_dataset.jsonl")
print(f"CSV template saved: backend/data/experiments/m9/m9_human_review_template.csv")
