"""
Dataset schema, generation helpers, and annotation workflow for IndicRAG-QA.

Workflow:
1. Generate candidate QA pairs using the local LLM (Ollama).
2. Export for human review.
3. Human annotators review and approve/reject.
4. Build train/dev/test splits.

IMPORTANT: LLM-generated candidates are always marked review_status=PENDING.
Never mark examples as approved without human review.
"""
from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx



from app.core.config import settings
from app.core.database import get_db
from app.core.logging_config import logger
from app.models.schemas import (
    AnswerabilityLabel,
    QAInstance,
    QueryLanguage,
    QueryScript,
    QuestionType,
    ReviewStatus,
)


# ─── Database helpers ──────────────────────────────────────────────────────────

def save_qa_instance(qa: QAInstance) -> None:
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO qa_instances (
                question_id, original_question, normalized_question,
                translated_question, query_language, query_script,
                question_type, answerability, reference_answer,
                gold_passage_ids, source_document_id, page_number,
                section, source_version, effective_date,
                program_applicability, expected_response_language,
                validation_status, review_status, reviewer_notes, gold_evidence_quotes,
                split, created_at, updated_at
            ) VALUES (
                :question_id, :original_question, :normalized_question,
                :translated_question, :query_language, :query_script,
                :question_type, :answerability, :reference_answer,
                :gold_passage_ids, :source_document_id, :page_number,
                :section, :source_version, :effective_date,
                :program_applicability, :expected_response_language,
                :validation_status, :review_status, :reviewer_notes, :gold_evidence_quotes,
                :split, :created_at, :updated_at
            )
        """, {
            "question_id": qa.question_id,
            "original_question": qa.original_question,
            "normalized_question": qa.normalized_question,
            "translated_question": qa.translated_question,
            "query_language": qa.query_language.value,
            "query_script": qa.query_script.value,
            "question_type": qa.question_type.value,
            "answerability": qa.answerability.value,
            "reference_answer": qa.reference_answer,
            "gold_passage_ids": json.dumps(qa.gold_passage_ids),
            "source_document_id": qa.source_document_id,
            "page_number": qa.page_number,
            "section": qa.section,
            "source_version": qa.source_version,
            "effective_date": qa.effective_date,
            "program_applicability": json.dumps(qa.program_applicability or []),
            "expected_response_language": qa.expected_response_language.value,
            "validation_status": getattr(qa, "validation_status", ValidationStatus.NEEDS_REVIEW).value if hasattr(getattr(qa, "validation_status", None), "value") else str(getattr(qa, "validation_status", "pending")),
            "review_status": qa.review_status.value,
            "reviewer_notes": qa.reviewer_notes,
            "gold_evidence_quotes": json.dumps(qa.gold_evidence_quotes),
            "split": qa.split,
            "created_at": qa.created_at.isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })


def load_all_instances(
    review_status: Optional[str] = None,
    split: Optional[str] = None,
) -> list[dict]:
    with get_db() as conn:
        conditions = []
        params = []
        if review_status:
            conditions.append("review_status = ?")
            params.append(review_status)
        if split:
            conditions.append("split = ?")
            params.append(split)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = conn.execute(
            f"SELECT * FROM qa_instances {where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


# ─── LLM-based candidate generation ───────────────────────────────────────────

_GENERATION_SYSTEM = """You are a multilingual QA dataset generator for university academic regulations.
Given an excerpt from Bennett University official documents, generate diverse question-answer pairs.

STRICT RULES:
1. Questions should primarily be ANSWERABLE from the provided passage, with an accurate reference answer and the exact supporting quote.
2. You may also include at most one plausible UNANSWERABLE question that asks about something NOT specified in the passage (with answer=null and gold_quote=null).
3. Support query languages: English ("en"), Devanagari Hindi ("hi"), Romanized Hindi ("hi-Latn"), and Hindi-English code-mixed ("hi-en").
4. Output MUST be valid JSON only. Do not add introductory or concluding text."""

_GENERATION_PROMPT = """Document excerpt (document_id: {doc_id}, page: {page}):
---
{passage}
---

Task: Write {n_questions} different questions that a student might ask about the excerpt above.
Languages to use: {languages}

Rules:
- Questions must be specific to Bennett University regulations mentioned in the text.
- Do NOT output placeholder text like "Question text". Write actual real questions.
- For answerable questions, provide the exact factual answer and the quote from the excerpt.
- For unanswerable questions, ask about a policy/rule not covered in this excerpt, setting answer=null and gold_quote=null.

Format: Return a JSON array of objects:
[
  {{
    "question": "What is the minimum attendance required for exams?",
    "answer": "75 percent attendance is required.",
    "answerability": "answerable",
    "question_type": "direct",
    "language": "en",
    "gold_quote": "A student must have a minimum of 75% attendance"
  }}
]"""


async def generate_candidate_questions(
    passage_text: str,
    document_id: str,
    passage_id: str,
    page_number: Optional[int],
    section: Optional[str],
    source_document_id: Optional[str],
    n_questions: int = 5,
    languages: list[str] = None,
) -> list[QAInstance]:
    """
    Use the local LLM to propose candidate QA pairs from a passage.

    All generated instances are marked review_status=PENDING.
    They must be manually reviewed before use in experiments.
    """
    if languages is None:
        languages = ["en", "hi-Latn", "hi-en"]  # start with script-agnostic ones

    prompt = _GENERATION_PROMPT.format(
        doc_id=document_id,
        page=page_number or "N/A",
        passage=passage_text[:1500],  # keep under context window
        n_questions=n_questions,
        languages=", ".join(languages),
    )

    logger.info(
        "Generating %d candidate QA pairs for passage %s…",
        n_questions, passage_id,
    )

    raw = ""
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "system": _GENERATION_SYSTEM,
                    "stream": False,
                    "options": {"temperature": 0.4, "num_predict": 1200},
                },
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "").strip()
    except Exception as exc:
        logger.error("LLM generation failed: %s", exc)
        return []

    # Parse JSON from LLM output
    candidates: list[QAInstance] = []
    items: list[dict] = []
    try:
        import re
        # Strategy 1: Look for outer JSON array [ ... ]
        json_match = re.search(r"\[.*\]", raw, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                if isinstance(parsed, list):
                    items = parsed
            except json.JSONDecodeError:
                items = []

        # Strategy 2: If no array, extract individual JSON objects { ... }
        if not items:
            for m in re.finditer(r"\{[^{}]*\}", raw, re.DOTALL):
                try:
                    obj = json.loads(m.group(0))
                    if isinstance(obj, dict) and "question" in obj:
                        items.append(obj)
                except json.JSONDecodeError:
                    continue

        if not items:
            logger.warning("No parseable QA items found in LLM output for passage %s", passage_id)
            return []

        for item in items:
            if not isinstance(item, dict):
                continue
            q_text = str(item.get("question", "")).strip()
            if not q_text or len(q_text) < 8 or "question text" in q_text.lower():
                continue

            lang_raw = str(item.get("language", "en")).strip()
            lang_map = {
                "en": QueryLanguage.ENGLISH,
                "english": QueryLanguage.ENGLISH,
                "hi": QueryLanguage.HINDI,
                "hindi": QueryLanguage.HINDI,
                "hi-latn": QueryLanguage.ROMANIZED_HINDI,
                "hinglish": QueryLanguage.ROMANIZED_HINDI,
                "hi-en": QueryLanguage.CODE_MIXED,
                "code-mixed": QueryLanguage.CODE_MIXED,
                "code_mixed": QueryLanguage.CODE_MIXED,
            }
            lang = lang_map.get(lang_raw.lower(), QueryLanguage.ENGLISH)

            ans_raw = str(item.get("answerability", "answerable")).lower().strip()
            ans_label = (
                AnswerabilityLabel.UNANSWERABLE
                if "unanswerable" in ans_raw or item.get("answer") is None
                else AnswerabilityLabel.ANSWERABLE
            )

            # Determine script
            if lang == QueryLanguage.HINDI:
                script = QueryScript.DEVANAGARI
            elif lang == QueryLanguage.CODE_MIXED:
                script = QueryScript.MIXED
            else:
                script = QueryScript.LATIN

            qa = QAInstance(
                question_id=str(uuid.uuid4()),
                original_question=str(item.get("question", "")).strip(),
                query_language=lang,
                query_script=script,
                question_type=_parse_q_type(str(item.get("question_type", "direct"))),
                answerability=ans_label,
                reference_answer=str(item["answer"]).strip() if item.get("answer") is not None else None,
                gold_passage_ids=[passage_id],
                source_document_id=source_document_id,
                page_number=page_number,
                section=section,
                expected_response_language=lang,
                review_status=ReviewStatus.PENDING,  # ALWAYS pending until human reviews
                reviewer_notes="LLM-generated candidate — awaiting human verification.",
                gold_evidence_quotes=[str(item["gold_quote"]).strip()] if item.get("gold_quote") else [],
            )
            candidates.append(qa)

    except Exception as exc:
        logger.error("Failed to parse LLM output: %s\nRaw: %s", exc, raw[:200])

    logger.info("Generated %d candidates (all PENDING review).", len(candidates))
    return candidates


def _parse_q_type(s: str) -> QuestionType:
    mapping = {
        "direct": QuestionType.DIRECT,
        "numerical": QuestionType.NUMERICAL,
        "multi_part": QuestionType.MULTI_PART,
        "table": QuestionType.TABLE,
        "code_mixed": QuestionType.CODE_MIXED,
        "unanswerable": QuestionType.UNANSWERABLE,
    }
    return mapping.get(s.lower(), QuestionType.DIRECT)


# ─── Export for human review ───────────────────────────────────────────────────

def export_for_review(
    output_path: Path,
    status_filter: str = "pending",
) -> int:
    """
    Export pending QA instances to a CSV for human review.
    Returns number of instances exported.
    """
    instances = load_all_instances(review_status=status_filter)
    if not instances:
        logger.info("No instances with status=%s to export.", status_filter)
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "question_id", "original_question", "query_language", "query_script",
        "question_type", "answerability", "reference_answer",
        "gold_passage_ids", "source_document_id", "page_number",
        "section", "gold_evidence_quotes",
        "review_status", "reviewer_notes",
        # Columns for reviewer to fill:
        "REVIEWER_APPROVE",    # yes/no
        "REVIEWER_CORRECTION", # corrected answer if needed
        "REVIEWER_NOTES",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for inst in instances:
            row = dict(inst)
            row["REVIEWER_APPROVE"] = ""
            row["REVIEWER_CORRECTION"] = ""
            row["REVIEWER_NOTES"] = ""
            writer.writerow(row)

    logger.info("Exported %d instances to %s.", len(instances), output_path)
    return len(instances)


def import_reviewed_csv(input_path: Path) -> dict[str, int]:
    """
    Import reviewer decisions from a completed CSV.
    Updates review_status in the database.
    Returns counts of approved/rejected/revised.
    """
    counts = {"approved": 0, "rejected": 0, "requires_revision": 0, "skipped": 0}
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            decision = (row.get("REVIEWER_APPROVE") or "").strip().lower()
            qid = row.get("question_id", "").strip()
            if not qid:
                continue
            if decision == "yes":
                new_status = "approved"
                counts["approved"] += 1
            elif decision == "no":
                new_status = "rejected"
                counts["rejected"] += 1
            elif decision == "revise":
                new_status = "requires_revision"
                counts["requires_revision"] += 1
            else:
                counts["skipped"] += 1
                continue
            notes = (row.get("REVIEWER_NOTES") or "").strip()
            correction = (row.get("REVIEWER_CORRECTION") or "").strip()

            with get_db() as conn:
                conn.execute("""
                    UPDATE qa_instances
                    SET review_status = ?, reviewer_notes = ?,
                        reference_answer = CASE WHEN ? != '' THEN ? ELSE reference_answer END,
                        updated_at = datetime('now')
                    WHERE question_id = ?
                """, (new_status, notes, correction, correction, qid))
    logger.info("Import complete: %s", counts)
    return counts
# ─── Dataset splitting ─────────────────────────────────────────────────────────
def create_splits(
    train_ratio: float = 0.7,
    dev_ratio: float = 0.15,
    # test gets the rest — 0.15
    seed: int = 42,
) -> dict[str, int]:
    """
    Assign train/dev/test splits to approved instances.

    CRITICAL RULE: Related language variants of the same rule must stay
    in the same split. We group by (source_document_id, section) before splitting.

    Never looks at test-set labels for any threshold tuning.
    """
    import random
    rng = random.Random(seed)

    instances = load_all_instances(review_status="approved")
    if not instances:
        logger.warning("No approved instances to split.")
        return {"train": 0, "dev": 0, "test": 0}

    # Group by (source_document_id, section) to keep variants together
    groups: dict[str, list[dict]] = {}
    for inst in instances:
        key = f"{inst.get('source_document_id')}::{inst.get('section') or ''}"
        groups.setdefault(key, []).append(inst)

    group_list = list(groups.values())
    rng.shuffle(group_list)

    n = len(group_list)
    n_train = max(1, round(n * train_ratio))
    n_dev   = max(1, round(n * dev_ratio))

    train_groups = group_list[:n_train]
    dev_groups   = group_list[n_train:n_train + n_dev]
    test_groups  = group_list[n_train + n_dev:]

    counts = {"train": 0, "dev": 0, "test": 0}

    def _assign(groups_subset, split_name):
        with get_db() as conn:
            for grp in groups_subset:
                for inst in grp:
                    conn.execute(
                        "UPDATE qa_instances SET split=? WHERE question_id=?",
                        (split_name, inst["question_id"]),
                    )
                    counts[split_name] += 1

    _assign(train_groups, "train")
    _assign(dev_groups, "dev")
    _assign(test_groups, "test")

    logger.info("Split complete: %s", counts)
    return counts
