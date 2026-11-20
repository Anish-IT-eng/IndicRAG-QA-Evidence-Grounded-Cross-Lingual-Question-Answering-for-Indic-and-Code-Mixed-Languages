"""
Evaluates End-to-End Answer Generation, Grounding, and Citations for M9.
Supports incremental resumption: skips already completed query IDs and
immediately appends every finished query to CSV.
Outputs:
- backend/data/experiments/m9/answer_generation_results.csv
- backend/data/experiments/m9/claim_grounding_results.csv
- backend/data/experiments/m9/citation_quality_results.csv
"""
import asyncio
import json
import csv
import time
import sys
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

sys.path.insert(0, os.path.abspath("backend"))

from app.query.processor import process_query, _has_devanagari
from app.retrieval.engine import retrieve
from app.retrieval.evidence_controller import get_evidence_controller
from app.generation.generator import generate_answer
from app.generation.claim_grounding import get_claim_grounding_verifier
from app.models.schemas import DocumentSource, ResponseStatus, EvidenceStatus
from app.core.config import settings

settings.ollama_timeout = 180
settings.generation_max_tokens = 300

# Load dataset
queries = []
with open("backend/data/experiments/m9/m9_evaluation_dataset.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            queries.append(json.loads(line))

ans_csv = "backend/data/experiments/m9/answer_generation_results.csv"
claim_csv = "backend/data/experiments/m9/claim_grounding_results.csv"
cit_csv = "backend/data/experiments/m9/citation_quality_results.csv"

# Check already completed query IDs
completed_qids = set()
if os.path.exists(ans_csv):
    try:
        with open(ans_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("query_id"):
                    completed_qids.add(row["query_id"])
    except Exception as e:
        print(f"Error reading existing results: {e}", flush=True)

print(f"Total dataset queries: {len(queries)}. Already completed: {len(completed_qids)}", flush=True)

ans_fieldnames = [
    "query_id", "intent_id", "language", "query_text", "expected_status",
    "response_status", "status_correct", "controller_status", "ceci_score",
    "citations_count", "all_pages_verified", "citation_precision", "citation_recall",
    "total_claims", "supported_claims", "grounding_ratio", "language_consistent",
    "retrieval_latency_ms", "generation_latency_ms", "total_latency_ms", "final_answer"
]

claim_fieldnames = [
    "query_id", "intent_id", "language", "claim_index", "claim_text",
    "verdict", "numeric_verified", "date_verified", "negation_verified",
    "semantic_entailed", "explanation"
]

cit_fieldnames = [
    "query_id", "intent_id", "language", "passage_id", "document_id",
    "document_name", "authoritative_page", "cited_page", "page_verified",
    "is_expected_passage"
]

# Initialize CSV headers if files do not exist
if not os.path.exists(ans_csv) or os.path.getsize(ans_csv) == 0:
    with open(ans_csv, "w", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=ans_fieldnames).writeheader()

if not os.path.exists(claim_csv) or os.path.getsize(claim_csv) == 0:
    with open(claim_csv, "w", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=claim_fieldnames).writeheader()

if not os.path.exists(cit_csv) or os.path.getsize(cit_csv) == 0:
    with open(cit_csv, "w", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=cit_fieldnames).writeheader()

controller = get_evidence_controller()
claim_verifier = get_claim_grounding_verifier()

async def run_evaluation():
    ans_file = open(ans_csv, "a", encoding="utf-8", newline="")
    ans_writer = csv.DictWriter(ans_file, fieldnames=ans_fieldnames)

    claim_file = open(claim_csv, "a", encoding="utf-8", newline="")
    claim_writer = csv.DictWriter(claim_file, fieldnames=claim_fieldnames)

    cit_file = open(cit_csv, "a", encoding="utf-8", newline="")
    cit_writer = csv.DictWriter(cit_file, fieldnames=cit_fieldnames)

    remaining = [q for q in queries if q["query_id"] not in completed_qids]
    print(f"Beginning evaluation of remaining {len(remaining)} queries...", flush=True)

    for idx, q in enumerate(remaining, len(completed_qids) + 1):
        qid = q["query_id"]
        intent_id = q["intent_id"]
        lang = q["query_language"]
        q_text = q["query_text"]
        exp_status_str = q["expected_status"]
        exp_pids = set(q.get("expected_passage_ids", []))

        t0 = time.perf_counter()

        # 1. Query Processing
        t_proc_0 = time.perf_counter()
        q_analysis = process_query(q_text, enable_translation=False)
        t_proc = (time.perf_counter() - t_proc_0) * 1000.0

        # 2. Retrieval
        t_ret_0 = time.perf_counter()
        ret_res = retrieve(
            q_analysis,
            collections=[DocumentSource.OFFICIAL],
            top_k=5,
            use_reranker=True,
            use_mqr=False,
            use_pdr=True
        )
        t_ret = (time.perf_counter() - t_ret_0) * 1000.0

        # 3. Evidence Controller
        t_ctrl_0 = time.perf_counter()
        ev_decision = controller.evaluate(ret_res)
        t_ctrl = (time.perf_counter() - t_ctrl_0) * 1000.0

        # 4. Generation
        t_gen_0 = time.perf_counter()
        response = await generate_answer(q_analysis, ev_decision)
        t_gen = (time.perf_counter() - t_gen_0) * 1000.0
        t_total = (time.perf_counter() - t0) * 1000.0

        status_val = response.status.value if hasattr(response.status, "value") else str(response.status)
        status_correct = (status_val.upper() == exp_status_str.upper())

        ans_text = response.answer or ""
        lang_consistent = True
        if lang == "en":
            lang_consistent = not _has_devanagari(ans_text)
        elif lang == "hi":
            if status_val == "answered":
                lang_consistent = _has_devanagari(ans_text)
        elif lang in ("hi-Latn", "en-hi"):
            lang_consistent = True

        # Citations
        cited_pids = set(c.passage_id for c in response.citations)
        citations_count = len(response.citations)
        all_pages_verified = all(c.page_verified for c in response.citations) if response.citations else True

        cit_prec = 0.0
        cit_rec = 0.0
        if exp_pids and cited_pids:
            cit_prec = len(cited_pids & exp_pids) / len(cited_pids)
            cit_rec = len(cited_pids & exp_pids) / len(exp_pids)
        elif not exp_pids and not cited_pids:
            cit_prec = 1.0
            cit_rec = 1.0

        for c in response.citations:
            cit_writer.writerow({
                "query_id": qid,
                "intent_id": intent_id,
                "language": lang,
                "passage_id": c.passage_id,
                "document_id": c.document_id,
                "document_name": getattr(c, "filename", getattr(c, "document_name", "")),
                "authoritative_page": c.page,
                "cited_page": c.cited_page if c.cited_page is not None else c.page,
                "page_verified": c.page_verified,
                "is_expected_passage": (c.passage_id in exp_pids),
            })
        cit_file.flush()

        # Claim Grounding Analysis
        claims_result = None
        supported_claims = 0
        total_claims = 0
        grounding_ratio = 1.0 if status_val != "answered" else 0.0

        if status_val == "answered" and ev_decision.valid_passages:
            claims_result = claim_verifier.verify_claims(ans_text, ev_decision.valid_passages)
            total_claims = len(claims_result.claims)
            grounding_ratio = claims_result.grounding_ratio
            for c_idx, claim in enumerate(claims_result.claims, 1):
                is_supported = (claim.verdict.value == "entailed" if hasattr(claim.verdict, "value") else str(claim.verdict) == "entailed")
                if is_supported:
                    supported_claims += 1
                claim_writer.writerow({
                    "query_id": qid,
                    "intent_id": intent_id,
                    "language": lang,
                    "claim_index": c_idx,
                    "claim_text": claim.claim_text,
                    "verdict": claim.verdict.value if hasattr(claim.verdict, "value") else str(claim.verdict),
                    "numeric_verified": claim.numeric_verified,
                    "date_verified": claim.date_verified,
                    "negation_verified": claim.negation_verified,
                    "semantic_entailed": is_supported,
                    "explanation": claim.explanation,
                })
            claim_file.flush()

        ans_writer.writerow({
            "query_id": qid,
            "intent_id": intent_id,
            "language": lang,
            "query_text": q_text,
            "expected_status": exp_status_str,
            "response_status": status_val,
            "status_correct": status_correct,
            "controller_status": ev_decision.status.value,
            "ceci_score": round(ev_decision.ceci_score, 4) if ev_decision.ceci_score is not None else 0.0,
            "citations_count": citations_count,
            "all_pages_verified": all_pages_verified,
            "citation_precision": round(cit_prec, 4),
            "citation_recall": round(cit_rec, 4),
            "total_claims": total_claims,
            "supported_claims": supported_claims,
            "grounding_ratio": round(grounding_ratio, 4),
            "language_consistent": lang_consistent,
            "retrieval_latency_ms": round(t_ret, 1),
            "generation_latency_ms": round(t_gen, 1),
            "total_latency_ms": round(t_total, 1),
            "final_answer": ans_text,
        })
        ans_file.flush()

        print(f"[{idx}/240] {qid} ({lang}) -> status: {status_val} (correct: {status_correct}) in {t_total:.1f}ms", flush=True)

    ans_file.close()
    claim_file.close()
    cit_file.close()
    print("\n--- All 240 generation evaluations successfully finished! ---", flush=True)

if __name__ == "__main__":
    asyncio.run(run_evaluation())
