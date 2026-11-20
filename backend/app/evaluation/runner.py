"""
Reproducible evaluation runner.

Usage:
  python -m app.evaluation.runner --split test --run-name baseline_bm25

This script:
1. Loads QA instances from the database.
2. Runs retrieval for each instance.
3. Calls the generation pipeline.
4. Computes metrics.
5. Saves results to the evaluation_runs table.
6. Writes a per-instance result CSV.

NEVER tunes thresholds against the test set.
All threshold calibration happens on the dev split.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.core.database import get_db, init_db
from app.core.logging_config import logger, setup_logging
from app.evaluation.dataset import load_all_instances
from app.evaluation.metrics import (
    compute_answer_metrics,
    compute_per_language_metrics,
    compute_retrieval_metrics,
)
from app.models.schemas import (
    DocumentSource,
    EvaluationMetrics,
    QAInstance,
    QueryLanguage,
    QueryScript,
    QuestionType,
    AnswerabilityLabel,
    ReviewStatus,
)
from app.query.processor import process_query
from app.retrieval.engine import get_official_index, retrieve
from app.retrieval.evidence_controller import get_evidence_controller
from app.generation.generator import generate_answer


async def run_evaluation(
    split: str = "test",
    run_name: str = "unnamed_run",
    collections: list[DocumentSource] = None,
    use_reranker: bool = True,
    use_mqr: bool = False,
    use_pdr: bool = True,
    top_k: int = None,
    max_instances: int = None,
) -> EvaluationMetrics:
    """
    Run full evaluation on a dataset split.

    Args:
        split: Which split to evaluate (train / dev / test).
        run_name: Human-readable name for this experiment.
        collections: Which document collections to search.
        use_reranker, use_mqr, use_pdr: Feature flags.
        top_k: Override retrieval top-k.
        max_instances: Limit instances (for quick testing).

    Returns:
        EvaluationMetrics with all computed values.
    """
    if collections is None:
        collections = [DocumentSource.OFFICIAL]
    if top_k is None:
        top_k = settings.retrieval_top_k

    setup_logging()
    init_db()

    # Load instances
    raw = load_all_instances(review_status="approved", split=split)
    if not raw:
        logger.error("No approved instances in split=%s. Aborting.", split)
        raise RuntimeError(f"No approved instances in split='{split}'.")

    if max_instances:
        raw = raw[:max_instances]

    logger.info("Evaluating %d instances from split=%s…", len(raw), split)

    evidence_ctrl = get_evidence_controller()
    retrieved_ids_map: dict[str, list[str]] = {}
    predictions: dict[str, dict] = {}
    instances: list[QAInstance] = []

    run_start = time.perf_counter()

    for row in raw:
        qid = row["question_id"]
        question = row["original_question"]

        # Reconstruct QAInstance
        inst = QAInstance(
            question_id=qid,
            original_question=question,
            query_language=QueryLanguage(row.get("query_language", "en")),
            query_script=QueryScript(row.get("query_script", "Latin")),
            question_type=QuestionType(row.get("question_type", "direct")),
            answerability=AnswerabilityLabel(row.get("answerability", "answerable")),
            reference_answer=row.get("reference_answer"),
            gold_passage_ids=json.loads(row.get("gold_passage_ids") or "[]"),
            source_document_id=row.get("source_document_id"),
            page_number=row.get("page_number"),
            review_status=ReviewStatus.APPROVED,
        )
        instances.append(inst)

        try:
            # Query processing
            query_analysis = process_query(question)

            # Retrieval
            retrieval_result = retrieve(
                query_analysis=query_analysis,
                collections=collections,
                top_k=top_k,
                use_reranker=use_reranker,
                use_mqr=use_mqr,
                use_pdr=use_pdr,
            )

            retrieved_ids_map[qid] = [
                p.passage_id for p in retrieval_result.retrieved_passages
            ]

            # Evidence evaluation
            evidence_decision = evidence_ctrl.evaluate(retrieval_result)

            # Generation
            response = await generate_answer(
                query_analysis=query_analysis,
                evidence_decision=evidence_decision,
                debug=False,
            )

            predictions[qid] = {
                "answer": response.answer or "",
                "cited_ids": [c.passage_id for c in response.citations],
                "status": response.status.value,
                "latency_ms": response.latency_ms,
            }

        except Exception as exc:
            logger.error("Instance %s failed: %s", qid, exc)
            retrieved_ids_map[qid] = []
            predictions[qid] = {"answer": "", "cited_ids": [], "status": "error", "latency_ms": 0}

    run_end = time.perf_counter()
    total_ms = (run_end - run_start) * 1000

    # Compute metrics
    ret_metrics = compute_retrieval_metrics(instances, retrieved_ids_map)
    ans_metrics = compute_answer_metrics(instances, predictions)
    lang_metrics = compute_per_language_metrics(instances, predictions, retrieved_ids_map)

    mean_latency = sum(
        p.get("latency_ms", 0) for p in predictions.values()
    ) / max(len(predictions), 1)

    metrics = EvaluationMetrics(
        run_name=run_name,
        config={
            "split": split,
            "use_reranker": use_reranker,
            "use_mqr": use_mqr,
            "use_pdr": use_pdr,
            "top_k": top_k,
            "collections": [c.value for c in collections],
            "ollama_model": settings.ollama_model,
            "embedding_model": settings.embedding_model,
        },
        recall_at_5=ret_metrics.get("recall@5"),
        recall_at_10=ret_metrics.get("recall@10"),
        precision_at_5=ret_metrics.get("precision@5"),
        mrr=ret_metrics.get("mrr"),
        ndcg_at_10=ret_metrics.get("ndcg@10"),
        exact_match=ans_metrics.get("exact_match"),
        token_f1=ans_metrics.get("token_f1"),
        citation_precision=ans_metrics.get("citation_precision"),
        answerability_precision=ans_metrics.get("precision"),
        answerability_recall=ans_metrics.get("recall"),
        answerability_f1=ans_metrics.get("f1"),
        false_answer_rate=ans_metrics.get("false_answer_rate"),
        unnecessary_abstention_rate=ans_metrics.get("unnecessary_abstention_rate"),
        per_language=lang_metrics,
        mean_latency_ms=mean_latency,
        notes=f"Total wall time: {total_ms/1000:.1f}s for {len(instances)} instances.",
    )

    # Save to DB
    _save_run(metrics)

    # Write per-instance CSV
    output_dir = settings.dataset_dir / "eval_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{run_name}_{split}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv"
    _write_results_csv(csv_path, instances, predictions, retrieved_ids_map)

    logger.info("Evaluation complete. Results saved to %s", csv_path)
    return metrics


def _save_run(metrics: EvaluationMetrics) -> None:
    with get_db() as conn:
        conn.execute("""
            INSERT INTO evaluation_runs (run_id, run_name, timestamp, config_json, metrics_json, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            metrics.run_id,
            metrics.run_name,
            metrics.timestamp.isoformat(),
            json.dumps(metrics.config),
            metrics.model_dump_json(),
            metrics.notes,
        ))
    logger.info("Run saved: %s", metrics.run_id)


def _write_results_csv(
    path: Path,
    instances: list[QAInstance],
    predictions: dict[str, dict],
    retrieved_ids_map: dict[str, list[str]],
) -> None:
    fields = [
        "question_id", "question", "language", "type", "answerability",
        "reference_answer", "predicted_answer", "status",
        "retrieved_passage_ids", "gold_passage_ids",
        "latency_ms",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for inst in instances:
            pred = predictions.get(inst.question_id, {})
            writer.writerow({
                "question_id": inst.question_id,
                "question": inst.original_question,
                "language": inst.query_language.value,
                "type": inst.question_type.value,
                "answerability": inst.answerability.value,
                "reference_answer": inst.reference_answer or "",
                "predicted_answer": pred.get("answer", ""),
                "status": pred.get("status", ""),
                "retrieved_passage_ids": json.dumps(retrieved_ids_map.get(inst.question_id, [])),
                "gold_passage_ids": json.dumps(inst.gold_passage_ids),
                "latency_ms": pred.get("latency_ms", 0),
            })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IndicRAG-QA Evaluation Runner")
    parser.add_argument("--split", default="dev", choices=["train", "dev", "test"])
    parser.add_argument("--run-name", default="eval_run")
    parser.add_argument("--use-reranker", action="store_true", default=True)
    parser.add_argument("--no-reranker", dest="use_reranker", action="store_false")
    parser.add_argument("--use-mqr", action="store_true", default=False)
    parser.add_argument("--use-pdr", action="store_true", default=True)
    parser.add_argument("--no-pdr", dest="use_pdr", action="store_false")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--max-instances", type=int, default=None)
    args = parser.parse_args()

    metrics = asyncio.run(run_evaluation(
        split=args.split,
        run_name=args.run_name,
        use_reranker=args.use_reranker,
        use_mqr=args.use_mqr,
        use_pdr=args.use_pdr,
        top_k=args.top_k,
        max_instances=args.max_instances,
    ))

    print("\n" + "="*60)
    print(f"Run: {metrics.run_name}")
    print(f"Recall@5:  {metrics.recall_at_5:.3f}" if metrics.recall_at_5 else "Recall@5: N/A")
    print(f"Recall@10: {metrics.recall_at_10:.3f}" if metrics.recall_at_10 else "Recall@10: N/A")
    print(f"MRR:       {metrics.mrr:.3f}" if metrics.mrr else "MRR: N/A")
    print(f"Token F1:  {metrics.token_f1:.3f}" if metrics.token_f1 else "Token F1: N/A")
    print(f"Ans F1:    {metrics.answerability_f1:.3f}" if metrics.answerability_f1 else "Ans F1: N/A")
    print(f"Latency:   {metrics.mean_latency_ms:.0f}ms")
    print("="*60)
