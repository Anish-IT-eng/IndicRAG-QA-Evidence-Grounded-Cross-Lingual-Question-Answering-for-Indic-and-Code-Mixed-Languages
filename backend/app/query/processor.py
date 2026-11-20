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
from app.models.schemas import (
    FeedbackSubtype,
    QueryAnalysis,
    QueryLanguage,
    QueryScript,
    QuestionType,
    RegulatoryCondition,
    TemporalIntentMode,
)

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
    # Normalize repetitive collocations like "odd semester end semester exams" into standard academic phrasing
    text = re.sub(r"\bodd\s+semester\s+end\s+sem(?:ester)?\s+exam(?:ination)?s?\b", "End Semester Examinations for Odd Semester", text, flags=re.IGNORECASE)
    text = re.sub(r"\beven\s+semester\s+end\s+sem(?:ester)?\s+exam(?:ination)?s?\b", "End Semester Examinations for Even Semester", text, flags=re.IGNORECASE)
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


_MONTH_NAME_MAP = {
    "january": "01", "jan": "01",
    "february": "02", "feb": "02",
    "march": "03", "mar": "03",
    "april": "04", "apr": "04",
    "may": "05",
    "june": "06", "jun": "06",
    "july": "07", "jul": "07",
    "august": "08", "aug": "08",
    "september": "09", "sep": "09",
    "october": "10", "oct": "10",
    "november": "11", "nov": "11",
    "december": "12", "dec": "12",
}


def normalize_natural_dates(text: str) -> str:
    """
    Expands natural date expressions (e.g. '18 January 2027', '18th Jan 2027', 'January 18, 2027')
    to also include their ISO DD-MM-YYYY equivalent alongside the original terms for robust retrieval.
    """
    def _repl_dmy(m: re.Match) -> str:
        day_str = m.group(1)
        mon_str = m.group(2).lower()
        yr_str = m.group(3)
        mm = _MONTH_NAME_MAP.get(mon_str)
        if mm:
            try:
                day_int = int(day_str)
                iso_date = f"{day_int:02d}-{mm}-{yr_str}"
                return f"{iso_date} {m.group(0)}"
            except ValueError:
                pass
        return m.group(0)

    def _repl_mdy(m: re.Match) -> str:
        mon_str = m.group(1).lower()
        day_str = m.group(2)
        yr_str = m.group(3)
        mm = _MONTH_NAME_MAP.get(mon_str)
        if mm:
            try:
                day_int = int(day_str)
                iso_date = f"{day_int:02d}-{mm}-{yr_str}"
                return f"{iso_date} {m.group(0)}"
            except ValueError:
                pass
        return m.group(0)

    res = re.sub(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([a-zA-Z]+)\s+(\d{4})\b", _repl_dmy, text)
    res = re.sub(r"\b([a-zA-Z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,)?\s+(\d{4})\b", _repl_mdy, res)
    return res


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
    from app.query.feedback_repair import classify_feedback
    is_fb, _, _ = classify_feedback(text, lang)
    if is_fb:
        return QuestionType.FEEDBACK_CORRECTION
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


# ─── Temporal & Cohort Intent Extraction ────────────────────────────────────────

_HISTORICAL_YEARS = {"2016", "2017", "2018", "2019", "2020", "2021"}
_CURRENT_YEARS = {"2022", "2023", "2024", "2025", "2026", "2027"}

_HISTORICAL_KEYWORDS = [
    r"\b(in\s+201[6-9]|in\s+202[0-1])\b",
    r"\b(201[6-9]\s+batch|202[0-1]\s+batch)\b",
    r"\b(founding\s+batch|first\s+batch|earlier|previously|old\s+rule|historical)\b",
]

_CURRENT_KEYWORDS = [
    r"\b(current|currently|latest|now|present|active|new\s+rule)\b",
    r"\b(202[2-7]\s+batch|2022\s+onwards)\b",
]


class TemporalCohortIntent(dict):
    """
    Container for temporal and cohort intent that supports both dict and tuple access.
    """
    def __init__(self, mode, cohort, ay, prog, conds):
        super().__init__(
            mode=mode,
            cohort=cohort,
            academic_year=ay,
            programme=prog,
            target_conditions=conds,
        )
        self.mode = mode
        self.cohort = cohort
        self.academic_year = ay
        self.programme = prog
        self.target_conditions = conds

    def __iter__(self):
        return iter((self.mode, self.cohort, self.academic_year, self.programme, self.target_conditions))


def extract_temporal_and_cohort_intent(
    text: str,
) -> TemporalCohortIntent:
    """
    Extracts temporal intent mode, cohort, academic year, target programme,
    and target regulatory conditions from query text.
    """
    t_lower = text.lower()

    # 1. Academic Year Match (e.g. AY 2022-23, 2017-18)
    ay_match = re.search(r"\b(?:ay\s*)?(20\d{2})\s*[-/]\s*(\d{2,4})\b", t_lower)
    target_ay: Optional[str] = None
    if ay_match:
        y1 = ay_match.group(1)
        y2 = ay_match.group(2)
        if len(y2) == 4:
            y2 = y2[2:]
        target_ay = f"{y1}-{y2}"

    # 2. Year and Cohort Matching
    year_match = re.search(r"\b(201[6-9]|202[0-7])\b", t_lower)
    target_cohort: Optional[str] = None
    if year_match:
        target_cohort = year_match.group(1)
        if not target_ay:
            # Map single year to standard academic year span
            yr_int = int(target_cohort)
            target_ay = f"{yr_int}-{(yr_int + 1) % 100:02d}"

    # 3. Temporal Mode Determination
    mode = TemporalIntentMode.UNANCHORED
    is_historical = any(re.search(pat, t_lower) for pat in _HISTORICAL_KEYWORDS)
    if not is_historical and target_cohort and target_cohort in _HISTORICAL_YEARS:
        is_historical = True

    is_current = any(re.search(pat, t_lower) for pat in _CURRENT_KEYWORDS)
    if target_ay:
        yr_prefix = target_ay.split("-")[0]
        if yr_prefix in _CURRENT_YEARS:
            is_current = True
        elif yr_prefix in _HISTORICAL_YEARS:
            is_historical = True

    if is_historical:
        mode = TemporalIntentMode.EXPLICIT_HISTORICAL
    elif is_current:
        mode = TemporalIntentMode.EXPLICIT_CURRENT
    elif "batch" in t_lower or "cohort" in t_lower:
        mode = TemporalIntentMode.COHORT_BOUND

    # 4. Target Programme Extraction
    target_prog: Optional[str] = None
    if re.search(r"\b(scset|cse|computer\s+science)\b", t_lower):
        target_prog = "SCSET"
    elif re.search(r"\b(seas|engineering)\b", t_lower):
        target_prog = "SEAS"
    elif re.search(r"\b(som|management|mba|bba)\b", t_lower):
        target_prog = "SOM"
    elif re.search(r"\b(sol|law)\b", t_lower):
        target_prog = "SOL"
    elif re.search(r"\b(phd|doctoral|research\s+scholar)\b", t_lower):
        target_prog = "PHD"

    # 5. Regulatory Condition Extraction
    target_conds: list[RegulatoryCondition] = []
    if re.search(r"\b(end\s+sem|end\s+semester|exam\s+hall|sit\s+for|admit\s+card|eligible\s+for\s+exam)\b", t_lower) or "75%" in t_lower:
        target_conds.append(RegulatoryCondition.EXAM_ELIGIBILITY)
    if re.search(r"\b('x'\s+grade|x\s+grade|grade\s+'?x'?|course|repeat\s+course)\b", t_lower) or "70%" in t_lower:
        target_conds.append(RegulatoryCondition.COURSE_GRADING)
    if re.search(r"\b(medical|illness|hospital|relax|relaxation|condon)\b", t_lower):
        target_conds.append(RegulatoryCondition.MEDICAL_CONDONATION)
    if re.search(r"\b(ufm|malpractice|cheating|mobile\s+phone|discipline|proctor)\b", t_lower):
        target_conds.append(RegulatoryCondition.DISCIPLINARY_ACTION)
    if re.search(r"\b(duration|maximum\s+duration|promotion|probation|cgpa|sgpa)\b", t_lower):
        target_conds.append(RegulatoryCondition.ACADEMIC_PROGRESSION)
    if re.search(r"\b(branch\s+change|branch\s+transfer|curriculum|core\s+course)\b", t_lower):
        target_conds.append(RegulatoryCondition.PROGRAMME_REQUIREMENT)

    if "attendance" in t_lower and not target_conds:
        target_conds.append(RegulatoryCondition.COURSE_GRADING)

    return TemporalCohortIntent(mode, target_cohort, target_ay, target_prog, target_conds)


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

    # 3. Language-specific & date normalization
    expanded = normalize_natural_dates(normalized)
    if lang in (QueryLanguage.CODE_MIXED, QueryLanguage.ROMANIZED_HINDI):
        expanded = normalize_code_mixed(expanded)

    # 4. Question type classification
    from app.query.feedback_repair import classify_feedback
    is_fb, fb_subtype, fb_claim = classify_feedback(expanded, lang)
    if is_fb:
        q_type = QuestionType.FEEDBACK_CORRECTION
    else:
        q_type = classify_question_type(expanded, lang)
        fb_subtype = None
        fb_claim = None

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

    # 9. Extract Temporal, Cohort, Programme, and Condition Intent
    t_mode, t_cohort, t_ay, t_prog, t_conds = extract_temporal_and_cohort_intent(expanded)

    # 10. Multilingual Academic Event Intent Canonicalization
    from app.query.event_resolver import resolve_academic_event_intent
    event_intent = resolve_academic_event_intent(expanded)
    canonical_normalized = None
    if event_intent.event_category:
        if lang != QueryLanguage.ENGLISH:
            canonical_normalized = event_intent.canonical_english_query
        elif expanded != raw_query:
            canonical_normalized = expanded
    elif expanded != raw_query:
        canonical_normalized = expanded

    return QueryAnalysis(
        original_query=raw_query,
        detected_language=lang,
        detected_script=script,
        normalized_query=canonical_normalized,
        romanized_query=None,   # placeholder for transliteration module
        translated_query=translated_text,
        query_type=q_type,
        is_multi_part=is_multi_part,
        sub_questions=sub_questions,
        intent_keywords=intent_kws,
        complexity_score=complexity,
        temporal_intent_mode=t_mode,
        target_cohort=t_cohort,
        target_academic_year=t_ay,
        target_programme=t_prog,
        target_conditions=t_conds,
        feedback_subtype=fb_subtype,
        challenged_claim=fb_claim,
    )


def _extract_intent_keywords(text: str) -> list[str]:
    """Extract content words and date tokens as intent signals for retrieval."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "what", "how", "when",
        "where", "which", "who", "do", "does", "can", "for", "in",
        "of", "to", "and", "or", "at", "on", "by", "kya", "kaise",
        "kitna", "kitni", "ka", "ki", "ke", "ko", "se", "mein",
        "kab", "karo", "hote", "hoti", "hain", "hai", "tha", "thi", "the", "aur",
    }
    words = [w for w in re.split(r"[^\w\-]+", text) if len(w) >= 2]
    return [w.lower() for w in words if w.lower() not in stop_words][:10]
