"""Tests for evaluation metric functions."""
from __future__ import annotations

import pytest

from app.evaluation.metrics import (
    answerability_metrics,
    citation_precision,
    exact_match,
    hit_rate_at_k,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    token_f1,
)


class TestRetrievalMetrics:

    def test_recall_perfect(self):
        assert recall_at_k(["a", "b", "c"], ["a", "b"], k=5) == 1.0

    def test_recall_partial(self):
        assert recall_at_k(["a", "x", "y"], ["a", "b"], k=5) == 0.5

    def test_recall_none(self):
        assert recall_at_k(["x", "y"], ["a", "b"], k=5) == 0.0

    def test_recall_empty_gold(self):
        assert recall_at_k(["a", "b"], [], k=5) == 1.0

    def test_precision_at_k(self):
        assert precision_at_k(["a", "b", "c"], ["a", "b"], k=5) == 2 / 5

    def test_hit_rate_hit(self):
        assert hit_rate_at_k(["x", "a", "y"], ["a"], k=5) == 1.0

    def test_hit_rate_miss(self):
        assert hit_rate_at_k(["x", "y"], ["a"], k=5) == 0.0

    def test_mrr_first(self):
        assert mrr(["a", "b", "c"], ["a"]) == 1.0

    def test_mrr_second(self):
        assert mrr(["x", "a", "b"], ["a"]) == pytest.approx(0.5)

    def test_mrr_not_found(self):
        assert mrr(["x", "y"], ["a"]) == 0.0

    def test_ndcg_perfect(self):
        assert ndcg_at_k(["a", "b"], ["a", "b"], k=5) == pytest.approx(1.0)

    def test_ndcg_zero(self):
        assert ndcg_at_k(["x", "y"], ["a", "b"], k=5) == 0.0


class TestAnswerMetrics:

    def test_exact_match_exact(self):
        assert exact_match("75%", "75%") == 1.0

    def test_exact_match_case_insensitive(self):
        assert exact_match("Seventy Five Percent", "seventy five percent") == 1.0

    def test_exact_match_fail(self):
        assert exact_match("75%", "80%") == 0.0

    def test_token_f1_perfect(self):
        assert token_f1("the minimum attendance is 75%", "the minimum attendance is 75%") == pytest.approx(1.0)

    def test_token_f1_partial(self):
        f1 = token_f1("attendance is 75", "minimum attendance is 75 percent")
        assert 0.0 < f1 < 1.0

    def test_token_f1_no_overlap(self):
        assert token_f1("hello world", "foo bar baz") == 0.0

    def test_citation_precision_all_valid(self):
        assert citation_precision(["p1", "p2"], ["p1", "p2", "p3"]) == 1.0

    def test_citation_precision_partial(self):
        assert citation_precision(["p1", "p9"], ["p1", "p2"]) == pytest.approx(0.5)

    def test_citation_precision_empty(self):
        assert citation_precision([], ["p1"]) == 0.0


class TestAnswerabilityMetrics:

    def test_all_correct(self):
        preds = ["answered", "answered", "unanswerable", "unanswerable"]
        labels = ["answerable", "answerable", "unanswerable", "unanswerable"]
        m = answerability_metrics(preds, labels)
        assert m["f1"] == pytest.approx(1.0)
        assert m["false_answer_rate"] == 0.0
        assert m["unnecessary_abstention_rate"] == 0.0

    def test_false_answer(self):
        # Model answered when it should have abstained
        preds = ["answered"]
        labels = ["unanswerable"]
        m = answerability_metrics(preds, labels)
        assert m["false_answer_rate"] == pytest.approx(1.0)
        assert m["precision"] == 0.0

    def test_unnecessary_abstention(self):
        preds = ["unanswerable"]
        labels = ["answerable"]
        m = answerability_metrics(preds, labels)
        assert m["unnecessary_abstention_rate"] == pytest.approx(1.0)
        assert m["recall"] == 0.0
