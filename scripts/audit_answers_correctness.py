import csv
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent.parent
exp_dir = root / "backend" / "data" / "experiments" / "m10"

def audit_answers():
    corr_file = exp_dir / "m10_phase_f_answer_correctness.csv"
    e2e_file = exp_dir / "m10_phase_f_end_to_end_results.csv"
    
    with open(corr_file, "r", encoding="utf-8") as f:
        corr_rows = list(csv.DictReader(f))
    with open(e2e_file, "r", encoding="utf-8") as f:
        e2e_rows = list(csv.DictReader(f))
        
    print(f"Correctness rows: {len(corr_rows)}")
    print(f"E2E rows: {len(e2e_rows)}")
    
    # Check denominators
    qids_a = {r["query_id"] for r in e2e_rows if r["config_id"] == "ConfigA_Production"}
    qids_b = {r["query_id"] for r in e2e_rows if r["config_id"] == "ConfigB_AdaptiveE6b"}
    print(f"Unique QIDs Config A: {len(qids_a)}, Config B: {len(qids_b)}")
    print(f"Sets match exactly: {qids_a == qids_b}")
    
    # Gold breakdown
    # Check expected_status counts
    gold_counts = Counter(r["expected_status"] for r in e2e_rows if r["config_id"] == "ConfigA_Production")
    print(f"Gold expected_status: {gold_counts}")
    
    for cfg in ["ConfigA_Production", "ConfigB_AdaptiveE6b"]:
        rows = [r for r in corr_rows if r["config_id"] == cfg]
        cats = Counter(r["correctness_category"] for r in rows)
        print(f"\n[{cfg}] Category counts:")
        for cat, cnt in sorted(cats.items()):
            print(f"  {cat:<30}: {cnt}")
            
        # By language
        print(f"\n[{cfg}] Breakdown by Language:")
        for lang in ["en", "hi", "hi-Latn", "en-hi"]:
            l_rows = [r for r in rows if r["language"] == lang]
            l_cats = Counter(r["correctness_category"] for r in l_rows)
            ans_queries = sum(1 for r in l_rows if r["expected_status"] == "ANSWERED")
            unans_queries = sum(1 for r in l_rows if r["expected_status"] == "UNANSWERABLE")
            
            ans_recall = (l_cats.get("CORRECT_ANSWERED", 0) + l_cats.get("REGULATORY_DISCLOSURE", 0)) / ans_queries if ans_queries else 0.0
            cor_abst = l_cats.get("CORRECT_ABSTENTION", 0) / unans_queries if unans_queries else 0.0
            unnec_abst = l_cats.get("UNNECESSARY_ABSTENTION", 0) / ans_queries if ans_queries else 0.0
            
            print(f"  {lang:<8}: AnsRecall={ans_recall:.4f} ({l_cats.get('CORRECT_ANSWERED', 0)}+{l_cats.get('REGULATORY_DISCLOSURE', 0)}/{ans_queries}), CorAbst={cor_abst:.4f} ({l_cats.get('CORRECT_ABSTENTION', 0)}/{unans_queries}), UnnecAbst={unnec_abst:.4f} ({l_cats.get('UNNECESSARY_ABSTENTION', 0)}/{ans_queries})")

if __name__ == "__main__":
    audit_answers()
