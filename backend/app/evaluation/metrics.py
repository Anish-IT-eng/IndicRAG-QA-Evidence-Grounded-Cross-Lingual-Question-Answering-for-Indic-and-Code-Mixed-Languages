"""
Evaluation metrics implementation.

All metrics are computed independently from the generation pipeline.
Do NOT tune thresholds on test-set outputs.

Implemented metrics:
- Retrieval: Recall@K, Precision@K, Hit Rate@K, MRR, nDCG@K
- Answer: Exact Match, Token F1
- Answerability: Precision, Recall, F1, False Answer Rate, Unnecessary Abstention Rate
- Multilingual: all metrics broken down by query language
"""
from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from typing import Optional

from app.models.schemas import (
    AnswerabilityLabel,
    EvaluationMetrics,
    QAInstance,
    QueryLanguage,
    ResponseStatus,
)


# ─── Retrieval metrics ────────────────────────────────────────────────────────

def recall_at_k(
    retrieved_ids: list[str],
    gold_ids: list[str],
    k: int,
) -> float:
    if not gold_ids:
        return 1.0
    retrieved_k = set(retrieved_ids[:k])
    return len(retrieved_k & set(gold_ids)) / len(gold_ids)


def precision_at_k(
    retrieved_ids: list[str],
    gold_ids: list[str],
    k: int,
) -> float:
    if k == 0:
        return 0.0
    retrieved_k = retrieved_ids[:k]
    hits = sum(1 for pid in retrieved_k if pid in set(gold_ids))
    return hits / k


def hit_rate_at_k(
    retrieved_ids: list[str],
    gold_ids: list[str],
    k: int,
) -> float:
    """1 if any gold passage is in top-k, else 0."""
    return 1.0 if set(retrieved_ids[:k]) & set(gold_ids) else 0.0


def mrr(
    retrieved_ids: list[str],
    gold_ids: list[str],
) -> float:
    gold_set = set(gold_ids)
    for rank, pid in enumerate(retrieved_ids, 1):
        if pid in gold_set:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(
    retrieved_ids: list[str],
    gold_ids: list[str],
    k: int,
) -> float:
    gold_set = set(gold_ids)
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, pid in enumerate(retrieved_ids[:k], 1)
        if pid in gold_set
    )
    ideal_hits = min(len(gold_set), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0 else 0.0


# ─── Answer metrics ───────────────────────────────────────────────────────────

def _normalize_answer(text: str) -> str:
    """Lowercase, remove punctuation and extra whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def exact_match(prediction: str, reference: str) -> float:
    return 1.0 if _normalize_answer(prediction) == _normalize_answer(reference) else 0.0


def token_f1(prediction: str, reference: str) -> float:
    pred_tokens = _normalize_answer(prediction).split()
    ref_tokens = _normalize_answer(reference).split()
    if not pred_tokens or not ref_tokens:
        return 1.0 if not pred_tokens and not ref_tokens else 0.0
    pred_bag = defaultdict(int)
    for t in pred_tokens:
        pred_bag[t] += 1
    ref_bag = defaultdict(int)
    for t in ref_tokens:
        ref_bag[t] += 1
    common = sum(min(pred_bag[t], ref_bag[t]) for t in pred_bag)
    if common == 0:
        return 0.0
    precision = common / len(pred_tokens)
    recall = common / len(ref_tokens)
    return 2 * precision * recall / (precision + recall)


def citation_precision(
    cited_passage_ids: list[str],
    gold_passage_ids: list[str],
) -> float:
    if not cited_passage_ids:
        return 0.0
    gold_set = set(gold_passage_ids)
    return sum(1 for pid in cited_passage_ids if pid in gold_set) / len(cited_passage_ids)


# ─── Answerability metrics ────────────────────────────────────────────────────

def answerability_metrics(
    predictions: list[str],    # "answered" | "unanswerable"
    labels: list[str],         # "answerable" | "unanswerable"
) -> dict:
    tp = fp = tn = fn = 0
    for pred, label in zip(predictions, labels):
        pred_ans = pred == "answered"
        label_ans = label == "answerable"
        if pred_ans and label_ans:
            tp += 1
        elif pred_ans and not label_ans:
            fp += 1       # false answer
        elif not pred_ans and not label_ans:
            tn += 1
        else:
            fn += 1       # unnecessary abstention

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    total = len(predictions)
    false_answer_rate = fp / total if total > 0 else 0.0
    unnecessary_abstention_rate = fn / total if total > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_answer_rate": false_answer_rate,
        "unnecessary_abstention_rate": unnecessary_abstention_rate,
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
    }


# ─── Aggregate evaluation ─────────────────────────────────────────────────────

def compute_retrieval_metrics(
    instances: list[QAInstance],
    retrieved_ids_map: dict[str, list[str]],   # question_id → ordered passage IDs
) -> dict:
    """
    Compute retrieval metrics across all instances.
    Only uses instances that have gold_passage_ids.
    """
    has_gold = [i for i in instances if i.gold_passage_ids]
    if not has_gold:
        return {"error": "No instances with gold passage IDs found."}

    r5 = r10 = p5 = hr5 = mrr_sum = ndcg10 = 0.0
    n = len(has_gold)

    for inst in has_gold:
        retrieved = retrieved_ids_map.get(inst.question_id, [])
        gold = inst.gold_passage_ids
        r5 += recall_at_k(retrieved, gold, 5)
        r10 += recall_at_k(retrieved, gold, 10)
        p5 += precision_at_k(retrieved, gold, 5)
        hr5 += hit_rate_at_k(retrieved, gold, 5)
        mrr_sum += mrr(retrieved, gold)
        ndcg10 += ndcg_at_k(retrieved, gold, 10)

    return {
        "n_instances": n,
        "recall@5": r5 / n,
        "recall@10": r10 / n,
        "precision@5": p5 / n,
        "hit_rate@5": hr5 / n,
        "mrr": mrr_sum / n,
        "ndcg@10": ndcg10 / n,
    }


def compute_answer_metrics(
    instances: list[QAInstance],
    predictions: dict[str, dict],   # question_id → {"answer": str, "cited_ids": list[str]}
) -> dict:
    has_ref = [i for i in instances if i.reference_answer]
    if not has_ref:
        return {"error": "No instances with reference answers found."}

    em_sum = f1_sum = cit_sum = 0.0
    n = len(has_ref)
    ans_preds, ans_labels = [], []

    for inst in has_ref:
        pred = predictions.get(inst.question_id, {})
        pred_text = pred.get("answer", "")
        cited = pred.get("cited_ids", [])

        em_sum += exact_match(pred_text, inst.reference_answer)
        f1_sum += token_f1(pred_text, inst.reference_answer)
        cit_sum += citation_precision(cited, inst.gold_passage_ids)

        # Answerability
        pred_status = "unanswerable" if "UNANSWERABLE" in pred_text.upper() else "answered"
        ans_preds.append(pred_status)
        ans_labels.append(inst.answerability.value)

    ans_metrics = answerability_metrics(ans_preds, ans_labels)

    return {
        "n_instances": n,
        "exact_match": em_sum / n,
        "token_f1": f1_sum / n,
        "citation_precision": cit_sum / n,
        **ans_metrics,
    }


def compute_per_language_metrics(
    instances: list[QAInstance],
    predictions: dict[str, dict],
    retrieved_ids_map: dict[str, list[str]],
) -> dict[str, dict]:
    """Break down retrieval and answer metrics by query language."""
    groups: dict[str, list[QAInstance]] = defaultdict(list)
    for inst in instances:
        groups[inst.query_language.value].append(inst)

    result = {}
    for lang, lang_instances in groups.items():
        lang_preds = {qid: v for qid, v in predictions.items()
                      if any(i.question_id == qid for i in lang_instances)}
        lang_ret = {qid: v for qid, v in retrieved_ids_map.items()
                    if any(i.question_id == qid for i in lang_instances)}
        ret_m = compute_retrieval_metrics(lang_instances, lang_ret)
        ans_m = compute_answer_metrics(lang_instances, lang_preds)
        result[lang] = {**ret_m, **ans_m}
    return result
