"""
Generate Source-Grounded Multilingual Candidates (Devanagari Hindi & Code-Mixed).

Targets official passages from Bennett University B.Tech regulations:
- Clause 30: Minimum Attendance & Condonation
- Clause 20.4: Grading Scale & Grade Points
- Clause 17: Supplementary Examinations & C+ Grade Cap
- Clause 16: Make-up Examinations & 5-Day Medical Notice
- Clause 6 & 7: Semester Duration & Course Categories
- Academic Calendar 2026-27: Critical Deadlines

Uses local Ollama models (llama3.2:3b / qwen2.5:3b).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

try:
    import pyarrow.dataset as _pds
    if not hasattr(_pds, "ParquetFragmentScanOptions"):
        _pds.ParquetFragmentScanOptions = type("ParquetFragmentScanOptions", (), {})
except ImportError:
    pass

from app.core.config import settings
from app.core.database import init_db, get_db
from app.core.logging_config import setup_logging, logger
from app.models.schemas import (
    AnswerabilityLabel,
    QueryLanguage,
    QueryScript,
    QuestionType,
    ReviewStatus,
)


_SYSTEM_PROMPT = """You are a rigorous, multilingual academic regulation QA dataset generator for Bennett University.
Generate question-answer pairs strictly grounded in the provided official university regulation excerpt.

STRICT REQUIREMENTS:
1. Every factual claim in the question and answer MUST be directly supported by the excerpt.
2. For "hi", output purely in Hindi using Devanagari script.
3. For "hi-en", output in natural campus code-mixed Hindi (Hinglish).
4. For gold_quote, you MUST extract an EXACT verbatim substring from the excerpt text.
5. Output ONLY a valid JSON array of objects. Do not write introductory or concluding prose."""

_USER_PROMPT_TEMPLATE = """Official regulation excerpt:
---
{passage_text}
---

Generate {n_pairs} QA pairs:
- At least one in pure Devanagari Hindi (language: "hi", script: "Devanagari")
- At least one in Code-mixed Hindi-English (language: "hi-en", script: "Mixed" or "Latin")

Format requirement - return ONLY a JSON array:
[
  {{
    "question": "प्रश्न देवनागरी में",
    "answer": "उत्तर देवनागरी में",
    "answerability": "answerable",
    "question_type": "direct",
    "language": "hi",
    "gold_quote": "exact substring from excerpt"
  }},
  {{
    "question": "Code-mixed Hinglish question",
    "answer": "Code-mixed Hinglish answer",
    "answerability": "code_mixed",
    "language": "hi-en",
    "gold_quote": "exact substring from excerpt"
  }}
]"""


def extract_json_array(raw: str) -> list[dict]:
    raw = raw.strip()
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    # Fallback to individual objects
    items = []
    for m in re.finditer(r"\{[^{}]*\}", raw, re.DOTALL):
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict) and "question" in obj:
                items.append(obj)
        except json.JSONDecodeError:
            continue
    return items


def select_target_passages() -> list[dict]:
    """Retrieve key passages for academic regulations with strong grounding."""
    with get_db() as conn:
        passages = conn.execute("""
            SELECT p.passage_id, p.document_id, p.page_number, p.section, p.heading, p.text, d.filename, d.academic_year
            FROM passages p
            JOIN documents d ON p.document_id = d.document_id
            WHERE d.filename = 'Academic-Rules-for-SCSET_UG.pdf'
              AND p.is_parent = 0
              AND (
                p.section IN ('30', '20.4', '17', '16.1', '16.2', '7', '6', '2', '1')
                OR p.heading LIKE '%Attendance%'
                OR p.heading LIKE '%Grading%'
                OR p.heading LIKE '%Supplementary%'
                OR p.heading LIKE '%Makeup%'
              )
            ORDER BY p.page_number ASC
        """).fetchall()
        return [dict(p) for p in passages]


def main():
    setup_logging()
    init_db()
    parser = argparse.ArgumentParser(description="Generate Devanagari Hindi and Code-Mixed QA candidates.")
    parser.add_argument("--model", default="llama3.2:3b", help="Local Ollama model to use for generation")
    parser.add_argument("--max-passages", type=int, default=8, help="Number of official passages to process")
    parser.add_argument("--output", default="backend/data/dataset/multilingual_expansion_candidates.csv", help="Output CSV path")
    args = parser.parse_args()

    passages = select_target_passages()[:args.max_passages]
    print(f"\nLoaded {len(passages)} key official regulation passages.")
    print(f"Generator Model: {args.model}")

    out_csv = Path(args.output)
    if not out_csv.is_absolute():
        out_csv = REPO_ROOT / args.output
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    generated_candidates: list[dict] = []

    for i, p in enumerate(passages, 1):
        p_text = p["text"].strip()
        print(f"\n[{i}/{len(passages)}] Passage {p['passage_id'][:8]} (Page {p['page_number']}, Section {p['section']}): {p['heading']}")
        
        prompt = _USER_PROMPT_TEMPLATE.format(passage_text=p_text[:1200], n_pairs=2)
        payload = {
            "model": args.model,
            "prompt": prompt,
            "system": _SYSTEM_PROMPT,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 500}
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(f"{settings.ollama_base_url}/api/generate", json=payload)
                resp.raise_for_status()
                raw_out = resp.json().get("response", "")
            
            items = extract_json_array(raw_out)
            valid_items = 0
            for item in items:
                q = str(item.get("question") or "").strip()
                ans = str(item.get("answer") or "").strip()
                lang = str(item.get("language") or "hi").strip().lower()
                qtype = str(item.get("question_type") or "direct").strip()
                quote = str(item.get("gold_quote") or "").strip()

                if not q or len(q) < 8 or "प्रश्न" in q:
                    continue

                # Script classification
                has_devanagari = bool(re.search(r"[\u0900-\u097F]", q))
                if lang == "hi" and has_devanagari:
                    script = "Devanagari"
                elif has_devanagari:
                    script = "Mixed"
                else:
                    script = "Latin"

                cand = {
                    "question_id": str(uuid.uuid4()),
                    "original_question": q,
                    "query_language": lang,
                    "query_script": script,
                    "question_type": qtype,
                    "answerability": "answerable",
                    "reference_answer": ans,
                    "gold_passage_ids": json.dumps([p["passage_id"]]),
                    "source_document_id": p["document_id"],
                    "page_number": p["page_number"],
                    "section": p["section"],
                    "gold_evidence_quotes": json.dumps([quote] if quote else []),
                    "review_status": "pending",
                    "reviewer_notes": f"Generated via {args.model} multilingual expansion.",
                    "REVIEWER_APPROVE": "",
                    "REVIEWER_CORRECTION": "",
                    "REVIEWER_NOTES": "",
                }
                generated_candidates.append(cand)
                valid_items += 1
            print(f"  Generated {valid_items} valid candidates.")
        except Exception as e:
            print(f"  Error generating for passage {p['passage_id']}: {e}")

    print(f"\nTotal new multilingual candidates generated: {len(generated_candidates)}")
    if generated_candidates:
        fields = list(generated_candidates[0].keys())
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(generated_candidates)
        print(f"Exported to: {out_csv}")


if __name__ == "__main__":
    main()

