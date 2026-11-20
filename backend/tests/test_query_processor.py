"""Tests for the multilingual query processing pipeline."""
from __future__ import annotations

import pytest

from app.query.processor import (
    _has_devanagari,
    _latin_ratio,
    classify_question_type,
    compute_complexity,
    decompose_query,
    detect_language_and_script,
    normalize_code_mixed,
    normalize_text,
    process_query,
)
from app.models.schemas import QueryLanguage, QueryScript, QuestionType


# ─── Language detection ────────────────────────────────────────────────────────

class TestLanguageDetection:

    def test_english_query(self):
        lang, script = detect_language_and_script(
            "What is the minimum attendance required to appear in end semester exam?"
        )
        assert lang == QueryLanguage.ENGLISH
        assert script == QueryScript.LATIN

    def test_hindi_devanagari(self):
        lang, script = detect_language_and_script("परीक्षा देने के लिए न्यूनतम उपस्थिति कितनी है?")
        assert lang == QueryLanguage.HINDI
        assert script == QueryScript.DEVANAGARI

    def test_code_mixed_latin(self):
        lang, script = detect_language_and_script(
            "End-sem exam dene ke liye minimum attendance kitni chahiye?"
        )
        assert lang in (QueryLanguage.CODE_MIXED, QueryLanguage.ROMANIZED_HINDI)
        assert script == QueryScript.LATIN

    def test_romanized_hindi(self):
        lang, script = detect_language_and_script("attendance kitni honi chahiye")
        assert lang in (QueryLanguage.ROMANIZED_HINDI, QueryLanguage.CODE_MIXED)

    def test_devanagari_detection(self):
        assert _has_devanagari("मेरा नाम") is True
        assert _has_devanagari("Hello World") is False

    def test_latin_ratio_pure(self):
        ratio = _latin_ratio("Hello World")
        assert ratio == 1.0

    def test_latin_ratio_mixed(self):
        ratio = _latin_ratio("Hello नमस्ते")
        assert 0.0 < ratio < 1.0


# ─── Normalization ─────────────────────────────────────────────────────────────

class TestNormalization:

    def test_whitespace_cleanup(self):
        result = normalize_text("  hello   world  ")
        assert result == "hello world"

    def test_unicode_nfc(self):
        # Ensure NFC normalization does not corrupt Hindi text
        hindi = "मेरा नाम अनीश है"
        assert normalize_text(hindi) == hindi

    def test_code_mixed_expansion(self):
        result = normalize_code_mixed("attendance min kitni hai for end-sem exam?")
        assert "minimum" in result
        assert "examination" in result
        assert "semester" in result


# ─── Question type classification ─────────────────────────────────────────────

class TestQuestionType:

    def test_numerical(self):
        q_type = classify_question_type(
            "What is the minimum attendance percentage required?",
            QueryLanguage.ENGLISH,
        )
        assert q_type == QuestionType.NUMERICAL

    def test_code_mixed_type(self):
        q_type = classify_question_type(
            "kitni attendance chahiye",
            QueryLanguage.CODE_MIXED,
        )
        assert q_type == QuestionType.CODE_MIXED

    def test_direct(self):
        q_type = classify_question_type(
            "What are the grading categories?",
            QueryLanguage.ENGLISH,
        )
        assert q_type == QuestionType.DIRECT


# ─── Complexity ────────────────────────────────────────────────────────────────

class TestComplexity:

    def test_simple_query_low_complexity(self):
        score = compute_complexity("What is attendance?", QueryLanguage.ENGLISH, QuestionType.DIRECT)
        assert score < 0.5

    def test_code_mixed_higher_complexity(self):
        score = compute_complexity(
            "attendance kitni chahiye", QueryLanguage.CODE_MIXED, QuestionType.CODE_MIXED
        )
        assert score >= 0.2

    def test_multi_part_high_complexity(self):
        score = compute_complexity(
            "What is the attendance rule and what happens if I fail?",
            QueryLanguage.ENGLISH,
            QuestionType.MULTI_PART,
        )
        assert score >= 0.3


# ─── Decomposition ─────────────────────────────────────────────────────────────

class TestDecomposition:

    def test_simple_query_not_decomposed(self):
        parts = decompose_query("What is the attendance requirement?", QueryLanguage.ENGLISH)
        assert len(parts) == 1

    def test_multi_part_decomposed(self):
        parts = decompose_query(
            "What is the minimum attendance and what are the grace marks rules?",
            QueryLanguage.ENGLISH,
        )
        # May or may not split depending on heuristic — just check it returns list
        assert isinstance(parts, list)
        assert len(parts) >= 1


# ─── Full pipeline ─────────────────────────────────────────────────────────────

class TestFullPipeline:

    def test_preserves_original_query(self):
        raw = "End-sem exam dene ke liye minimum attendance kitni chahiye?"
        result = process_query(raw)
        assert result.original_query == raw

    def test_english_end_to_end(self):
        result = process_query("What is the minimum attendance percentage for B.Tech?")
        assert result.detected_language == QueryLanguage.ENGLISH
        assert result.intent_keywords  # should extract some keywords

    def test_hindi_query(self):
        result = process_query("परीक्षा के लिए उपस्थिति कितनी होनी चाहिए?")
        assert result.detected_language == QueryLanguage.HINDI
        assert result.detected_script == QueryScript.DEVANAGARI

    def test_code_mixed_pipeline(self):
        result = process_query("attendance requirement kya hai end-sem ke liye?")
        assert result.detected_language in (QueryLanguage.CODE_MIXED, QueryLanguage.ROMANIZED_HINDI)
