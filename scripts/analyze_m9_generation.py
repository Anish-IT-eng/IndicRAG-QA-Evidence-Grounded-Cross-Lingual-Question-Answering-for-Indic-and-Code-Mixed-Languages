"""
Aggregates and analyzes M9 generation, citation, and claim grounding results.
Outputs summary tables by language and overall system metrics.
"""
import csv
import json
from collections import defaultdict

ans_csv = "backend/data/experiments/m9/answer_generation_results.csv"
claim_csv = "backend/data/experiments/m9/claim_grounding_results.csv"
cit_csv = "backend/data/experiments/m9/citation_quality_results.csv"

def analyze():
    # 1. Answer Generation Metrics
    by_lang = defaultdict(lambda: {
        "total": 0, "answered": 0, "unanswerable": 0, "conflicting": 0, "clarification": 0,
        "status_correct": 0, "grounding_sum": 0.0, "total_claims": 0, "supported_claims": 0,
        "ret_lat_sum": 0.0, "gen_lat_sum": 0.0, "tot_lat_sum": 0.0, "citations_count": 0,
        "page_ver_count": 0, "cit_prec_sum": 0.0, "cit_rec_sum": 0.0, "lang_consistent": 0,
        "answerable_total": 0, "answerable_answered": 0, "unanswerable_total": 0, "unanswerable_correct": 0
    })

    with open(ans_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            lang = r["language"]
            d = by_lang[lang]
            d["total"] += 1
            status = r["response_status"].lower()
            if status == "answered":
                d["answered"] += 1
            elif status == "unanswerable":
                d["unanswerable"] += 1
            elif "conflict" in status:
                d["conflicting"] += 1
            elif "clarification" in status:
                d["clarification"] += 1

            if r["status_correct"] == "True":
                d["status_correct"] += 1

            exp_st = r["expected_status"].lower()
            if exp_st == "answered":
                d["answerable_total"] += 1
                if status == "answered":
                    d["answerable_answered"] += 1
            else:
                d["unanswerable_total"] += 1
                if status == "unanswerable":
                    d["unanswerable_correct"] += 1

            d["grounding_sum"] += float(r["grounding_ratio"])
            d["total_claims"] += int(r["total_claims"])
            d["supported_claims"] += int(r["supported_claims"])
            d["ret_lat_sum"] += float(r["retrieval_latency_ms"])
            d["gen_lat_sum"] += float(r["generation_latency_ms"])
            d["tot_lat_sum"] += float(r["total_latency_ms"])
            d["citations_count"] += int(r["citations_count"])
            if r["all_pages_verified"] == "True":
                d["page_ver_count"] += 1
            d["cit_prec_sum"] += float(r["citation_precision"])
            d["cit_rec_sum"] += float(r["citation_recall"])
            if r["language_consistent"] == "True":
                d["lang_consistent"] += 1

    print("=== ANSWER GENERATION SUMMARY BY LANGUAGE ===")
    for lang in ["en", "hi", "hi-Latn", "en-hi"]:
        d = by_lang[lang]
        tot = max(1, d["total"])
        ans_tot = max(1, d["answerable_total"])
        unans_tot = max(1, d["unanswerable_total"])
        print(f"\nLanguage: {lang.upper()} (N={d['total']})")
        print(f"  Response Status: Answered={d['answered']}, Unanswerable={d['unanswerable']}, Conflicting={d['conflicting']}, Clarification={d['clarification']}")
        print(f"  Status Correctness: {d['status_correct']}/{tot} ({d['status_correct']/tot*100:.2f}%)")
        print(f"  Answerable Coverage (Recall): {d['answerable_answered']}/{ans_tot} ({d['answerable_answered']/ans_tot*100:.2f}%)")
        print(f"  Abstention Precision on Unanswerable: {d['unanswerable_correct']}/{unans_tot} ({d['unanswerable_correct']/unans_tot*100:.2f}%)")
        print(f"  Mean Grounding Ratio: {d['grounding_sum']/tot*100:.2f}%")
        print(f"  Total Claims: {d['total_claims']} (Supported: {d['supported_claims']} = {d['supported_claims']/max(1, d['total_claims'])*100:.2f}%)")
        print(f"  Language Output Consistency: {d['lang_consistent']}/{tot} ({d['lang_consistent']/tot*100:.2f}%)")
        print(f"  Latencies: Mean Retrieval={d['ret_lat_sum']/tot:.1f}ms, Mean Generation={d['gen_lat_sum']/tot:.1f}ms, Mean Total={d['tot_lat_sum']/tot:.1f}ms")

    # 2. Citation Quality Metrics
    cit_stats = defaultdict(lambda: {"total": 0, "page_verified": 0, "expected_passage": 0})
    with open(cit_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            lang = r["language"]
            s = cit_stats[lang]
            s["total"] += 1
            if r["page_verified"] == "True":
                s["page_verified"] += 1
            if r["is_expected_passage"] == "True":
                s["expected_passage"] += 1

    print("\n=== CITATION QUALITY BREAKDOWN ===")
    for lang in ["en", "hi", "hi-Latn", "en-hi"]:
        s = cit_stats[lang]
        tot = max(1, s["total"])
        print(f"Language {lang}: Total Citations={s['total']}, Page Verified={s['page_verified']} ({s['page_verified']/tot*100:.2f}%), Expected Passage={s['expected_passage']} ({s['expected_passage']/tot*100:.2f}%)")

    # 3. Claim Grounding Breakdown
    claim_verdicts = defaultdict(lambda: defaultdict(int))
    with open(claim_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            lang = r["language"]
            v = r["verdict"].upper()
            claim_verdicts[lang][v] += 1

    print("\n=== CLAIM GROUNDING VERDICTS ===")
    for lang in ["en", "hi", "hi-Latn", "en-hi"]:
        v_dict = dict(claim_verdicts[lang])
        ent = v_dict.get("ENTAILED", 0)
        tot_c = sum(v_dict.values())
        pct = (ent / max(1, tot_c)) * 100
        print(f"Language {lang}: Total Claims={tot_c}, Entailed={ent} ({pct:.2f}%), Breakdown={v_dict}")

if __name__ == "__main__":
    analyze()
