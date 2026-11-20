"""
Script to build the M9 Cross-Lingual Evaluation Dataset.
Constructs 60 semantic question intent groups x 4 language variants = 240 query records.
Links real document and passage IDs from indicrag.db for answerable queries.
Generates:
1. backend/data/experiments/m9/m9_evaluation_dataset.jsonl
2. backend/data/experiments/m9/m9_dataset_schema.json
3. backend/data/experiments/m9/m9_human_review_template.csv
"""
import json
import csv
import os
import sqlite3

os.makedirs("backend/data/experiments/m9", exist_ok=True)

# Connect to database to verify passages
conn = sqlite3.connect("backend/data/db/indicrag.db")
c = conn.cursor()

# Map documents
doc_map = {}
for row in c.execute("SELECT document_id, filename FROM documents"):
    doc_map[row[1]] = row[0]

# Schema Definition
schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "M9CrossLingualEvaluationDatasetRecord",
    "type": "object",
    "required": [
        "intent_id",
        "query_id",
        "query_text",
        "query_language",
        "script",
        "query_type",
        "expected_answer_language",
        "expected_status",
        "expected_document_ids",
        "expected_passage_ids",
        "expected_claims",
        "expected_answer",
        "applicability_constraints",
        "human_review_status",
        "reviewer_notes"
    ],
    "properties": {
        "intent_id": {"type": "string"},
        "query_id": {"type": "string"},
        "query_text": {"type": "string"},
        "query_language": {"type": "string", "enum": ["en", "hi", "hi-Latn", "en-hi"]},
        "script": {"type": "string", "enum": ["LATIN", "DEVANAGARI", "MIXED"]},
        "query_type": {"type": "string", "enum": ["DIRECT", "NUMERICAL", "MULTI_PART", "HISTORICAL", "UNANSWERABLE", "COMPARATIVE"]},
        "expected_answer_language": {"type": "string", "enum": ["en", "hi", "hi-Latn", "en-hi"]},
        "expected_status": {"type": "string", "enum": ["ANSWERED", "UNANSWERABLE", "CLARIFICATION_NEEDED"]},
        "expected_document_ids": {"type": "array", "items": {"type": "string"}},
        "expected_passage_ids": {"type": "array", "items": {"type": "string"}},
        "expected_claims": {"type": "array", "items": {"type": "string"}},
        "expected_answer": {"type": "string"},
        "applicability_constraints": {"type": "object"},
        "human_review_status": {"type": "string", "enum": ["PROVISIONAL_NOT_HUMAN_VERIFIED", "HUMAN_VERIFIED", "FLAGGED_AMBIGUOUS"]},
        "reviewer_notes": {"type": "string"}
    }
}

with open("backend/data/experiments/m9/m9_dataset_schema.json", "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2)

print("Schema saved to backend/data/experiments/m9/m9_dataset_schema.json")
