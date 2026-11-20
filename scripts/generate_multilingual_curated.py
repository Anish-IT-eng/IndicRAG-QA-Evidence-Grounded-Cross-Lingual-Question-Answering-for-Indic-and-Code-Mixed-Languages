"""
Curated Multilingual Candidate Generator (Devanagari Hindi & Code-Mixed).
Uses local Ollama qwen2.5:3b with strict few-shot prompting and exact substring validation.
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
from app.evaluation.model_verifier import DeterministicValidator

SYSTEM_PROMPT = """You are an academic regulation QA dataset generator for Bennett University.
Your task is to generate natural, realistic student questions and accurate evidence-grounded answers based strictly on the provided excerpt.

RULES:
1. The excerpt is written in ENGLISH.
2. The "gold_quote" MUST BE an EXACT, VERBATIM substring copied directly from the excerpt. Never translate the quote.
3. For language "hi": Generate fluent conversational Hindi in Devanagari script. Use common university terms naturally (e.g. परीक्षा, अटेंडेंस, सेमेस्टर, ग्रेड, सीजीपीए).
4. For language "hi-en": Generate natural Indian campus code-mixed Hindi (Hinglish, e.g. "End-sem exam ke liye minimum attendance kitni required hai?").
5. Return ONLY a valid JSON array of objects. Do not write introductory or concluding prose."""

FEW_SHOT_PROMPT = """Official regulation excerpt:
---
30.1 Attendance Rules
(ii) A student must have a minimum attendance of 70% in a course during a semester, in lectures, tutorials or practical’s taken together (as applicable). A student with less than 70 % attendances in a course will be awarded ‘X’ grade in that course irrespective of his/her performance in the tests during the semester.
(v) A relaxation of up to 10% may be given on the following special /exceptional grounds:
(a) Any continuous illness of two weeks --like contagious diseases -- supported by a proper medical certificate.
---

Generate 2 QA pairs:
1. Devanagari Hindi (language: "hi", script: "Devanagari")
2. Code-mixed Hinglish (language: "hi-en", script: "Latin")

Example output JSON format:
[
  {{
    "question": "कोर्स में बैठने के लिए न्यूनतम कितनी अटेंडेंस होना अनिवार्य है?",
    "answer": "छात्र को सेमेस्टर में किसी कोर्स के लिए न्यूनतम 70% अटेंडेंस होना अनिवार्य है।",
    "language": "hi",
    "script": "Devanagari",
    "question_type": "numerical",
    "answerability": "answerable",
    "gold_quote": "A student must have a minimum attendance of 70% in a course during a semester"
  }},
  {{
    "question": "Agar attendance 70% se kam ho to kaun sa grade award kiya jata hai?",
    "answer": "Agar attendance 70% se kam hoti hai to us course mein 'X' grade award kiya jata hai.",
    "language": "hi-en",
    "script": "Latin",
    "question_type": "direct",
    "answerability": "answerable",
    "gold_quote": "A student with less than 70 % attendances in a course will be awarded ‘X’ grade in that course"
  }}
]

Now generate 2 QA pairs for this excerpt:
---
{passage_text}
---
"""


def find_best_substring(needle: str, haystack: str) -> str | None:
    """Find exact or whitespace-normalized substring in haystack."""
    if not needle:
        return None
    needle_clean = needle.strip().strip('"').strip("'")
    if needle_clean in haystack:
        return needle_clean
    
    # Try normalizing quotes / dashes
    haystack_norm = haystack.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    needle_norm = needle_clean.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    if needle_norm in haystack_norm:
        idx = haystack_norm.find(needle_norm)
        return haystack[idx:idx + len(needle_norm)]

    # Sentence-based fallback: if the needle matches a substantial portion of a sentence in haystack
    sentences = [s.strip() for s in re.split(r"[.\n]", haystack) if len(s.strip()) > 20]
    for s in sentences:
        if needle_clean.lower() in s.lower() or s.lower() in needle_clean.lower():
            return s
            
    return None


def select_key_passages() -> list[dict]:
    with get_db() as conn:
        passages = conn.execute("""
            SELECT p.passage_id, p.document_id, p.page_number, p.section, p.heading, p.text, d.filename, d.academic_year
            FROM passages p
            JOIN documents d ON p.document_id = d.document_id
            WHERE p.is_parent = 0
              AND (
                p.passage_id IN (
                    'c31d716d-bcfe-4011-a3f6-f4a2d5f1f22b',
                    'a40fe16a-d0c7-4f22-97ba-5534bf3ab8f0',
                    '5fd38f8d-e1ec-406e-aa70-06317b4e3d72',
                    '5f9028f1-69ee-4e2d-9aa0-68ca2f510deb',
                    '380bfc8e-cd43-4343-8db3-11fd7c5b400b',
                    '9773d6a7-12e2-4b0e-9b5f-45a8be226a95',
                    '4fb20336-4a76-4e21-8422-f3d9e08a4c27',
                    'cfb81e36-8477-4083-aa37-f671c6202263',
                    '1163039d-b53d-46f4-b717-1f6c094830a6',
                    '505e552e-35e0-4b5d-98ba-10dff85f4eab',
                    'dc9034e1-88aa-4a45-ad01-34fd28c21411',
                    '625fba4f-8898-4228-aa96-ae1a01150c26',
                    'bbaac776-23eb-4535-85f9-6f181b238d3f',
                    '1d109788-cb9e-49b0-b53d-24959db62fa9',
                    '23db7904-e3c3-455b-bf48-b4b600a9446f'
                )
              )
            ORDER BY d.filename, p.page_number
        """).fetchall()
        return [dict(p) for p in passages]


def main():
    setup_logging()
    init_db()
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--output", default="backend/data/dataset/multilingual_expansion_curated.csv")
    args = parser.parse_args()

    passages = select_key_passages()
    print(f"Targeting {len(passages)} official passages for multilingual expansion.")
    print(f"Generator model: {args.model}")

    validator = DeterministicValidator()
    out_path = REPO_ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)

    candidates: list[dict] = []
    audit_records: list[dict] = []

    for i, p in enumerate(passages, 1):
        p_text = p["text"]
        print(f"\n[{i}/{len(passages)}] Passage {p['passage_id'][:8]} | P.{p['page_number']} | Sec {p['section']}: {str(p['heading'])[:40]}")
        prompt = FEW_SHOT_PROMPT.format(passage_text=p_text[:1200])

        payload = {
            "model": args.model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 600}
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(f"{settings.ollama_base_url}/api/generate", json=payload)
                resp.raise_for_status()
                raw_out = resp.json().get("response", "")

            # Extract JSON array
            m = re.search(r"\[.*\]", raw_out, re.DOTALL)
            if not m:
                print("  [WARN] No JSON array detected in response.")
                continue

            items = json.loads(m.group(0))
            for item in items:
                q = str(item.get("question") or "").strip()
                ans = str(item.get("answer") or "").strip()
                lang = str(item.get("language") or "hi").strip().lower()
                qtype = str(item.get("question_type") or "direct").strip()
                ans_label = str(item.get("answerability") or "answerable").strip()
                raw_quote = str(item.get("gold_quote") or "").strip()

                if not q or len(q) < 8 or "प्रश्न" in q:
                    continue

                # Verify and ground quote
                matched_quote = find_best_substring(raw_quote, p_text)
                if not matched_quote:
                    print(f"  [REJECT] Quote not in passage: '{raw_quote[:40]}...'")
                    continue

                has_devanagari = bool(re.search(r"[\u0900-\u097F]", q))
                if lang == "hi" and has_devanagari:
                    script = "Devanagari"
                elif has_devanagari:
                    script = "Mixed"
                else:
                    script = "Latin"

                cand_id = str(uuid.uuid4())
                cand = {
                    "question_id": cand_id,
                    "original_question": q,
                    "query_language": lang,
                    "query_script": script,
                    "question_type": qtype,
                    "answerability": ans_label,
                    "reference_answer": ans,
                    "gold_passage_ids": json.dumps([p["passage_id"]]),
                    "source_document_id": p["document_id"],
                    "page_number": p["page_number"],
                    "section": p["section"] or "",
                    "gold_evidence_quotes": json.dumps([matched_quote]),
                    "review_status": "pending",
                    "reviewer_notes": f"Generated via {args.model} curated multilingual expansion.",
                    "REVIEWER_APPROVE": "",
                    "REVIEWER_CORRECTION": "",
                    "REVIEWER_NOTES": "",
                }

                # Run through DeterministicValidator
                val_res = validator.validate_candidate({
                    "question_id": cand_id,
                    "original_question": q,
                    "reference_answer": ans,
                    "answerability": ans_label,
                    "query_language": lang,
                    "query_script": script,
                    "question_type": qtype,
                    "source_document_id": p["document_id"],
                    "gold_passage_ids": [p["passage_id"]],
                    "gold_evidence_quotes": [matched_quote],
                    "created_at": datetime.utcnow().isoformat(),
                })

                if val_res.passed:
                    candidates.append(cand)
                    print(f"  [VALIDATED] [{lang}/{script}] {q[:45]}...")
                    print(f"    Quote: \"{matched_quote[:55]}...\"")
                else:
                    print(f"  [DET_FAIL] Issues: {val_res.issues}")

        except Exception as e:
            print(f"  [ERROR] {e}")

    # Write out candidates
    if candidates:
        fieldnames = list(candidates[0].keys())
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(candidates)
        print(f"\nSuccessfully wrote {len(candidates)} high-quality multilingual candidates to {out_path}")
    else:
        print("\nNo candidates passed deterministic validation.")


if __name__ == "__main__":
    main()

