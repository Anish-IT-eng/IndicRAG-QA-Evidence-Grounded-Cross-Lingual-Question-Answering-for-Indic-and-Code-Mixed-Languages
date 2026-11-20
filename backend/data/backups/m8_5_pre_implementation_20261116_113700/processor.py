"""
Multilingual query processing pipeline.

Modules (in order):
1. Language & script identification  (langdetect + Unicode heuristics)
2. Unicode normalization & whitespace cleanup
3. Romanized-Hindi / code-mixed normalization
4. Optional transliteration placeholder
5. Query intent & complexity classification
6. Query decomposition for multi-part questions

Design principle:
  The original query is NEVER discarded.
  All derived versions are stored alongside the original so retrieval
  experiments can compare routes reproducibly.
"""
from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Any, Callable, Optional

import httpx

from app.core.config import settings
from app.core.logging_config import logger
from app.models.schemas import QueryAnalysis, QueryLanguage, QueryScript, QuestionType

# ─── Language detection ────────────────────────────────────────────────────────

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 42   # reproducible results
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not available; falling back to heuristic detection.")


def _has_devanagari(text: str) -> bool:
    return any("\u0900" <= c <= "\u097F" for c in text)


def _latin_ratio(text: str) -> float:
    alpha = [c for c in text if c.isalpha()]
    if not alpha:
        return 0.0
    return sum(1 for c in alpha if ord(c) < 128) / len(alpha)


# Common Romanized Hindi / Hinglish patterns
_HINGLISH_PATTERNS = [
    r"\b(kya|kaise|kitni|kitna|chahiye|hota|mujhe|aur|nahi|hai|hain|ka|ki|ke|ko|se|mein|pe|par|wala|wali|agar|toh|matlab)\b",
]
_HINGLISH_RE = re.compile("|".join(_HINGLISH_PATTERNS), re.IGNORECASE)


def detect_language_and_script(text: str) -> tuple[QueryLanguage, QueryScript]:
    """
    Returns (QueryLanguage, QueryScript).

    Priority:
    1. Devanagari script → Hindi
    2. Hinglish heuristics → CODE_MIXED or ROMANIZED_HINDI
    3. langdetect → English or Hindi (Latin)
    4. Default UNKNOWN
    """
    has_deva = _has_devanagari(text)
    latin_r = _latin_ratio(text)

    if has_deva and latin_r > 0.15:
        # Mixed Devanagari + Latin → code-mixed with Devanagari
        return QueryLanguage.CODE_MIXED, QueryScript.MIXED

    if has_deva:
        return QueryLanguage.HINDI, QueryScript.DEVANAGARI

    # All-Latin heuristics
    hinglish_matches = len(_HINGLISH_RE.findall(text))
    word_count = max(len(text.split()), 1)
    hinglish_ratio = hinglish_matches / word_count

    if hinglish_ratio >= 0.25:
        return QueryLanguage.CODE_MIXED, QueryScript.LATIN

    if hinglish_ratio >= 0.10:
        return QueryLanguage.ROMANIZED_HINDI, QueryScript.LATIN

    if _LANGDETECT_AVAILABLE:
        try:
            detected = detect(text)
            if detected == "en":
                return QueryLanguage.ENGLISH, QueryScript.LATIN
            if detected == "hi":
                # Hindi detected via langdetect but no Devanagari → Romanized
                return QueryLanguage.ROMANIZED_HINDI, QueryScript.LATIN
        except Exception:
            pass

    return QueryLanguage.ENGLISH, QueryScript.LATIN   # safe default


# ─── Normalization ─────────────────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    """
    Unicode NFC normalization + whitespace cleanup.
    Does NOT alter the semantic content.
    """
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


_CODE_MIXED_NORMALIZATIONS = {
    # Common abbreviations and contractions in Hinglish
    r"\bexam\b": "examination",
    r"\battendance\b": "attendance",
    r"\bmin\b": "minimum",
    r"\bmax\b": "maximum",
    r"\bsem\b": "semester",
    r"\bsems\b": "semesters",
    r"\bdept\b": "department",
    r"\buniv\b": "university",
}


def normalize_code_mixed(text: str) -> str:
    """
    Light normalization for Romanized Hindi / code-mixed queries.
    Expands common abbreviations. Does not translate.
    """
    result = text
    for pattern, replacement in _CODE_MIXED_NORMALIZATIONS.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result.strip()


# ─── Intent and complexity ─────────────────────────────────────────────────────

_NUMERICAL_PATTERNS = re.compile(
    r"\b(how many|kitne|kitni|percentage|percent|%|marks|credit|cgpa|sgpa|minimum|maximum|pass|fail)\b",
    re.IGNORECASE,
)
_MULTI_PART_PATTERNS = re.compile(
    r"\b(and|aur|also|additionally|furthermore|moreover|tatha|evam)\b",
    re.IGNORECASE,
)
_UNANSWERABLE_PATTERNS = re.compile(
    r"\b(not in policy|outside|hypothetical|if someone)\b",
    re.IGNORECASE,
)


def classify_question_type(text: str, lang: QueryLanguage) -> QuestionType:
    # Check code-mixed language first — it takes priority over keyword-based typing
    if lang in (QueryLanguage.CODE_MIXED, QueryLanguage.ROMANIZED_HINDI):
        return QuestionType.CODE_MIXED
    if _NUMERICAL_PATTERNS.search(text):
        return QuestionType.NUMERICAL
    if _MULTI_PART_PATTERNS.search(text):
        return QuestionType.MULTI_PART
    return QuestionType.DIRECT


def compute_complexity(text: str, lang: QueryLanguage, q_type: QuestionType) -> float:
    """
    Return a complexity score 0..1.
    Used by the adaptive router to decide whether to invoke MQR.
    """
    score = 0.0
    words = len(text.split())

    if words > 20:
        score += 0.2
    if q_type == QuestionType.MULTI_PART:
        score += 0.3
    if lang in (QueryLanguage.CODE_MIXED, QueryLanguage.ROMANIZED_HINDI):
        score += 0.2
    if q_type == QuestionType.CODE_MIXED:
        score += 0.1
    if re.search(r"\b(or|ya|either|versus)\b", text, re.IGNORECASE):
        score += 0.1
    if re.search(r"\b(previous|old|before|2022|2023|2024|last year)\b", text, re.IGNORECASE):
        score += 0.1    # version-dependent
    return min(score, 1.0)


# ─── Query decomposition ───────────────────────────────────────────────────────

def decompose_query(text: str, lang: QueryLanguage) -> list[str]:
    """
    Split a multi-part question into atomic sub-questions.
    Returns a list (may be just the original query if not decomposable).

    This is a heuristic splitter; a more sophisticated version can use
    the local LLM, but that adds latency and a model dependency.
    """
    # Split on conjunctions that separate genuinely separate clauses
    splits = re.split(
        r"\s+(?:and also|and|aur|tatha|evam|additionally|furthermore|moreover)\s+",
        text,
        flags=re.IGNORECASE,
    )
    if len(splits) <= 1:
        return [text]

    # Each split must be a plausible standalone question fragment
    sub_qs = []
    for part in splits:
        part = part.strip()
        if len(part.split()) >= 4:  # minimum meaningful length
            sub_qs.append(part)

    return sub_qs if len(sub_qs) > 1 else [text]


# ─── Translation ─────────────────────────────────────────────────────────────

@dataclass
class TranslationResult:
    original_query: str
    translated_query: Optional[str]
    source_language: QueryLanguage
    fallback_occurred: bool
    latency_ms: float
    error_message: Optional[str] = None


_TRANSLATE_SYSTEM_PROMPT = """You are an accurate, concise translator for university academic regulations.
Translate the user's query from Hindi, Hinglish, or Romanized Hindi into plain English.
Rules:
1. Preserve technical terms, numbers, dates, grade letters (O, A+, A, B+, B, C+, C, D, F, I, X), percentages, and regulation names.
2. Output ONLY the plain English translation. Do NOT add explanation, greetings, quotes, or conversational filler.
"""


def translate_query_to_english(
    query: str,
    source_lang: QueryLanguage,
    model_name: str = "qwen2.5:3b",
    base_url: str = settings.ollama_base_url,
    timeout: float = 30.0,
    custom_caller: Optional[Callable[[str, str], str]] = None,
) -> TranslationResult:
    """
    Translates non-English queries to English using local Ollama model (qwen2.5:3b).
    Preserves original query, handles failures gracefully with fallback.
    """
    if source_lang == QueryLanguage.ENGLISH:
        return TranslationResult(
            original_query=query,
            translated_query=query,
            source_language=source_lang,
            fallback_occurred=False,
            latency_ms=0.0,
        )

    t0 = time.perf_counter()
    prompt = f"Translate to English:\n{query}"

    try:
        if custom_caller:
            raw = custom_caller(prompt, _TRANSLATE_SYSTEM_PROMPT)
        else:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "system": _TRANSLATE_SYSTEM_PROMPT,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 128,
                },
            }
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(f"{base_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                raw = data.get("response", "")

        translated = raw.strip().strip('"').strip("'")
        lat = (time.perf_counter() - t0) * 1000

        if not translated:
            logger.warning("Translation model returned empty response for '%s'; falling back.", query)
            return TranslationResult(
                original_query=query,
                translated_query=None,
                source_language=source_lang,
                fallback_occurred=True,
                latency_ms=lat,
                error_message="Empty translation output",
            )

        logger.debug("Translated '%s' -> '%s' (%.2f ms)", query, translated, lat)
        return TranslationResult(
            original_query=query,
            translated_query=translated,
            source_language=source_lang,
            fallback_occurred=False,
            latency_ms=lat,
        )

    except Exception as exc:
        lat = (time.perf_counter() - t0) * 1000
        logger.warning("Translation failed for '%s' (%s); falling back to direct retrieval.", query, exc)
        return TranslationResult(
            original_query=query,
            translated_query=None,
            source_language=source_lang,
            fallback_occurred=True,
            latency_ms=lat,
            error_message=str(exc),
        )


# ─── Main pipeline ─────────────────────────────────────────────────────────────

def process_query(raw_query: str, enable_translation: bool = False) -> QueryAnalysis:
    """
    Full multilingual query processing pipeline.

    Returns a QueryAnalysis with all derived representations preserved.
    The original_query field is always the unmodified user input.
    """
    # 1. Normalize whitespace / Unicode (does not change semantics)
    normalized = normalize_text(raw_query)

    # 2. Detect language and script
    lang, script = detect_language_and_script(normalized)
    logger.debug("Language detected: %s / %s", lang, script)

    # 3. Language-specific normalization
    if lang in (QueryLanguage.CODE_MIXED, QueryLanguage.ROMANIZED_HINDI):
        expanded = normalize_code_mixed(normalized)
    else:
        expanded = normalized

    # 4. Question type classification
    q_type = classify_question_type(expanded, lang)

    # 5. Complexity scoring
    complexity = compute_complexity(expanded, lang, q_type)

    # 6. Multi-part detection & decomposition
    is_multi_part = q_type == QuestionType.MULTI_PART or complexity >= 0.5
    sub_questions = decompose_query(expanded, lang) if is_multi_part else []
    if len(sub_questions) <= 1:
        sub_questions = []
        is_multi_part = is_multi_part and complexity >= 0.5

    # 7. Intent keywords (simple extraction for BM25 query expansion hint)
    intent_kws = _extract_intent_keywords(expanded)

    # 8. Optional translation-assisted retrieval
    translated_text: Optional[str] = None
    if enable_translation and lang != QueryLanguage.ENGLISH:
        trans_res = translate_query_to_english(expanded, lang)
        if not trans_res.fallback_occurred:
            translated_text = trans_res.translated_query

    return QueryAnalysis(
        original_query=raw_query,
        detected_language=lang,
        detected_script=script,
        normalized_query=expanded if expanded != raw_query else None,
        romanized_query=None,   # placeholder for transliteration module
        translated_query=translated_text,
        query_type=q_type,
        is_multi_part=is_multi_part,
        sub_questions=sub_questions,
        intent_keywords=intent_kws,
        complexity_score=complexity,
    )


def _extract_intent_keywords(text: str) -> list[str]:
    """Extract content words as intent signals for retrieval."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "what", "how", "when",
        "where", "which", "who", "do", "does", "can", "for", "in",
        "of", "to", "and", "or", "at", "on", "by", "kya", "kaise",
        "kitna", "kitni", "ka", "ki", "ke", "ko", "se", "mein",
    }
    words = re.findall(r"\b[a-zA-Z\u0900-\u097F]{3,}\b", text)
    return [w.lower() for w in words if w.lower() not in stop_words][:10]
