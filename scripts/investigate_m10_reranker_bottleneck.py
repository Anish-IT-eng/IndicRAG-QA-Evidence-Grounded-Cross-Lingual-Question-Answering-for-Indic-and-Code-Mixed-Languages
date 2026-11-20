"""
Phase B: Reranker Bottleneck Investigation Script.
Performs candidate-level analysis on all 45 answerable Devanagari Hindi queries,
and conducts a controlled cross-script scoring audit with the production cross-encoder.
Outputs:
- backend/data/experiments/m10/m10_hindi_candidate_tracing.csv
- backend/data/experiments/m10/m10_cross_script_scoring_audit.csv
"""
import json
import csv
import sys
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

sys.path.insert(0, os.path.abspath("backend"))

from app.query.processor import process_query
from app.retrieval.engine import (
    get_official_index,
    get_cross_encoder,
    _rrf_fuse,
    _deduplicate,
    validate_versions,
    expand_to_parents,
)
from app.retrieval.evidence_controller import get_evidence_controller
from app.models.schemas import DocumentSource

def run_candidate_analysis():
    # Load dataset
    queries = []
    with open("backend/data/experiments/m9/m9_evaluation_dataset.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))

    hi_answerable = [q for q in queries if q["query_language"] == "hi" and q["expected_status"] == "ANSWERED"]
    print(f"Found {len(hi_answerable)} answerable Devanagari Hindi queries.")

    idx = get_official_index()
    cross_enc = get_cross_encoder()
    controller = get_evidence_controller()

    records = []
    category_counts = {"A_never_retrieved": 0, "B_retrieved_but_demoted": 0, "C_rejected_by_controller": 0, "D_retained_in_top5": 0}

    for q in hi_answerable:
        qid = q["query_id"]
        iid = q["intent_id"]
        q_text = q["query_text"]
        exp_pids = set(q.get("expected_passage_ids", []))

        q_analysis = process_query(q_text, enable_translation=False)
        query_str = q_analysis.normalized_query or q_analysis.original_query

        # Step 1: Candidate generation
        bm25_hits = idx.bm25_search(query_str, top_k=10)
        dense_hits = idx.dense_search(query_str, top_k=10)

        bm25_pids = [h[0] for h in bm25_hits]
        dense_pids = [h[0] for h in dense_hits]

        # Step 2: RRF Fusion
        fused = _rrf_fuse(bm25_hits, dense_hits)
        for pid, score, meta in fused:
            if "text" not in meta:
                try:
                    tidx = idx.passage_ids.index(pid)
                    meta["text"] = idx.passage_texts[tidx]
                except ValueError:
                    pass

        fused = _deduplicate(fused)
        fused = validate_versions(fused, None, None, q_analysis)

        initial_pids = [h[0] for h in fused]
        initial_ranks = {h[0]: r for r, h in enumerate(fused, 1)}
        initial_scores = {h[0]: h[1] for h in fused}

        # Check candidate presence
        expected_in_candidates = bool(exp_pids & set(initial_pids))
        best_initial_rank = min([initial_ranks[p] for p in exp_pids if p in initial_ranks], default=999)

        # Step 3: Reranking
        pairs = [(query_str, meta.get("text", "")) for _, _, meta in fused]
        raw_scores = cross_enc.predict(pairs) if cross_enc else [0.0] * len(fused)
        
        ranked = sorted(zip(fused, raw_scores), key=lambda x: x[1], reverse=True)
        reranked_pids = [h[0][0] for h in ranked]
        reranked_ranks = {h[0][0]: r for r, h in enumerate(ranked, 1)}
        reranked_scores = {h[0][0]: float(rs) for h, rs in ranked}

        best_rerank_rank = min([reranked_ranks[p] for p in exp_pids if p in reranked_ranks], default=999)

        # Step 4: Final top 5
        top_5_pids = reranked_pids[:5]
        expected_in_top5 = bool(exp_pids & set(top_5_pids))

        # Categorize failure mode
        failure_mode = "UNKNOWN"
        if not expected_in_candidates:
            failure_mode = "A_NEVER_RETRIEVED"
            category_counts["A_never_retrieved"] += 1
        elif expected_in_candidates and best_initial_rank <= 5 and best_rerank_rank > 5:
            failure_mode = "B_DEMOTED_BY_RERANKER"
            category_counts["B_retrieved_but_demoted"] += 1
        elif expected_in_candidates and best_initial_rank > 5 and best_rerank_rank > 5:
            failure_mode = "A_LOW_CANDIDATE_RANK_NOT_RECOVERED"
            category_counts["A_never_retrieved"] += 1
        elif expected_in_top5:
            failure_mode = "D_RETAINED_IN_TOP5"
            category_counts["D_retained_in_top5"] += 1

        records.append({
            "query_id": qid,
            "intent_id": iid,
            "query_text": q_text,
            "expected_passage_ids": ";".join(exp_pids),
            "expected_in_bm25": bool(exp_pids & set(bm25_pids)),
            "expected_in_dense": bool(exp_pids & set(dense_pids)),
            "expected_in_candidates": expected_in_candidates,
            "best_initial_rank": best_initial_rank if best_initial_rank != 999 else "NOT_FOUND",
            "best_rerank_rank": best_rerank_rank if best_rerank_rank != 999 else "NOT_FOUND",
            "expected_in_top5": expected_in_top5,
            "failure_mode": failure_mode,
            "top1_candidate_pid": initial_pids[0] if initial_pids else "",
            "top1_reranked_pid": reranked_pids[0] if reranked_pids else "",
            "raw_cross_enc_score_top1": round(reranked_scores.get(reranked_pids[0], 0.0), 4) if reranked_pids else 0.0,
            "raw_cross_enc_score_expected": round(min([reranked_scores[p] for p in exp_pids if p in reranked_scores], default=-99.0), 4)
        })

    # Save candidate tracing CSV
    out_csv = "backend/data/experiments/m10/m10_hindi_candidate_tracing.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved {len(records)} Hindi candidate tracing rows to {out_csv}")
    print(f"Failure Mode Breakdown: {category_counts}")

def run_cross_script_audit():
    cross_enc = get_cross_encoder()
    if not cross_enc:
        print("Cross-encoder not available!")
        return

    # Select 5 representative intent groups with known ground truth passages
    diagnostic_cases = [
        {
            "intent_id": "M9-INT-01",
            "topic": "Minimum Attendance Requirement (75%)",
            "passage_text": "Clause 30.1 Requirement of Minimum Attendance: Every student must attend at least 75% of the total number of lectures, tutorials, and practicals conducted in a course to be eligible to appear in the End Semester Examination.",
            "en_query": "What is the minimum attendance required to appear in the end semester examination?",
            "hi_latn_query": "End semester exam mein appear hone ke liye minimum attendance kitni chahiye?",
            "en_hi_query": "End sem examination ke liye minimum attendance requirement kya hai?",
            "hi_query": "अंतिम सेमेस्टर परीक्षा में बैठने के लिए न्यूनतम उपस्थिति कितनी आवश्यक है?"
        },
        {
            "intent_id": "M9-INT-02",
            "topic": "Attendance Condonation on Medical Grounds",
            "passage_text": "Clause 30.1(v) A student may be granted relaxation in attendance up to a maximum of 10% on medical grounds, provided the student was hospitalized or bedridden for at least two weeks.",
            "en_query": "Can attendance be relaxed on medical grounds?",
            "hi_latn_query": "Kya medical grounds par attendance relax ho sakti hai?",
            "en_hi_query": "Medical grounds par attendance relaxation mil sakti hai kya?",
            "hi_query": "क्या चिकित्सा आधार पर उपस्थिति में छूट मिल सकती है?"
        },
        {
            "intent_id": "M9-INT-05",
            "topic": "Passing Marks and Minimum CGPA",
            "passage_text": "Clause 18.2 A student must obtain a minimum of grade 'D' in each course and maintain a minimum Cumulative Grade Point Average (CGPA) of 4.50 to be eligible for the award of degree.",
            "en_query": "What is the minimum passing grade and CGPA required for degree award?",
            "hi_latn_query": "Degree ke liye minimum passing grade aur CGPA kitna chahiye?",
            "en_hi_query": "Degree award ke liye minimum passing grade aur CGPA requirement kya hai?",
            "hi_query": "डिग्री प्राप्त करने के लिए न्यूनतम उत्तीर्ण ग्रेड और सीजीपीए क्या है?"
        },
        {
            "intent_id": "M9-INT-10",
            "topic": "Supplementary Examination Eligibility",
            "passage_text": "Clause 22.1 A student who secures an 'F' or 'I' grade in a course is eligible to appear in the Supplementary Examination conducted before the commencement of the next academic year.",
            "en_query": "Who is eligible to appear in the supplementary examination?",
            "hi_latn_query": "Supplementary exam mein kaun appear ho sakta hai?",
            "en_hi_query": "Supplementary examination appear karne ki eligibility criteria kya hai?",
            "hi_query": "पूरक परीक्षा में बैठने के लिए कौन पात्र है?"
        },
        {
            "intent_id": "M9-INT-35",
            "topic": "Mobile Phone Malpractice Penalty",
            "passage_text": "Clause 28.4 Possession of a mobile phone or any unauthorized electronic device inside the examination hall is strictly prohibited and constitutes Unfair Means (UFM), resulting in cancellation of the examination.",
            "en_query": "What is the penalty for possessing a mobile phone in the examination hall?",
            "hi_latn_query": "Exam hall mein mobile phone milne par kya penalty hoti hai?",
            "en_hi_query": "Examination hall mein mobile phone possess karne par kya punishment hai?",
            "hi_query": "परीक्षा हॉल में मोबाइल फोन पाए जाने पर क्या दंड दिया जाता है?"
        }
    ]

    audit_rows = []
    print("\n--- Running Cross-Script Scoring Audit with ms-marco-MiniLM-L-6-v2 ---")

    for case in diagnostic_cases:
        p_text = case["passage_text"]
        
        pairs = [
            (case["en_query"], p_text),
            (case["hi_latn_query"], p_text),
            (case["en_hi_query"], p_text),
            (case["hi_query"], p_text),
        ]
        
        scores = cross_enc.predict(pairs)
        
        row = {
            "intent_id": case["intent_id"],
            "topic": case["topic"],
            "en_score": round(float(scores[0]), 4),
            "hi_latn_score": round(float(scores[1]), 4),
            "en_hi_score": round(float(scores[2]), 4),
            "hi_devanagari_score": round(float(scores[3]), 4),
            "devanagari_vs_en_diff": round(float(scores[3]) - float(scores[0]), 4)
        }
        audit_rows.append(row)
        print(f"[{case['intent_id']}] EN: {row['en_score']:.2f} | Latn: {row['hi_latn_score']:.2f} | Hinglish: {row['en_hi_score']:.2f} | Devanagari: {row['hi_devanagari_score']:.2f} (Diff: {row['devanagari_vs_en_diff']:.2f})")

    out_csv = "backend/data/experiments/m10/m10_cross_script_scoring_audit.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(audit_rows[0].keys()))
        writer.writeheader()
        writer.writerows(audit_rows)
    print(f"Saved cross-script scoring audit to {out_csv}")

if __name__ == "__main__":
    run_candidate_analysis()
    run_cross_script_audit()
