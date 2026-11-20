import csv
from pathlib import Path

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
rows = list(csv.DictReader(open(root / "backend/data/experiments/m10/m10_phase_h_per_query_results.csv", encoding="utf-8")))

for cfg in ["ConfigA_Production", "ConfigB_AdaptiveE6b"]:
    hi_ans = [r for r in rows if r["config_id"] == cfg and r["language"] == "hi" and r["expected_status"] == "ANSWERED"]
    print(f"=== {cfg} (Hindi Answerable N={len(hi_ans)}) ===")
    
    cat1_ret_and_succ = []
    cat2_ret_and_abst = []
    cat3_ret_and_fail = []
    cat4_not_ret_and_abst = []
    cat5_other = []
    
    for r in hi_ans:
        qid = r["query_id"]
        hit5 = float(r["retrieval_hit_5"]) > 0
        succ = r["response_status"] in ["answered", "clarification_needed", "conflicting_versions"]
        
        if hit5 and succ:
            cat1_ret_and_succ.append(qid)
        elif hit5 and r["response_status"] == "unanswerable":
            cat2_ret_and_abst.append(qid)
        elif hit5 and not succ:
            cat3_ret_and_fail.append(qid)
        elif not hit5 and r["response_status"] == "unanswerable":
            cat4_not_ret_and_abst.append(qid)
        else:
            cat5_other.append(qid)
            
    print(f"1. Relevant evidence retrieved & correct answer/disclosure produced ({len(cat1_ret_and_succ)}): {cat1_ret_and_succ}")
    print(f"2. Relevant evidence retrieved but unnecessarily abstained ({len(cat2_ret_and_abst)}): {cat2_ret_and_abst}")
    print(f"3. Relevant evidence retrieved but answer incorrect ({len(cat3_ret_and_fail)}): {cat3_ret_and_fail}")
    print(f"4. Relevant evidence not retrieved ({len(cat4_not_ret_and_abst)}): {cat4_not_ret_and_abst}")
    print(f"5. Other explicitly justified outcome ({len(cat5_other)}): {cat5_other}")
    print(f"Total: {len(cat1_ret_and_succ) + len(cat2_ret_and_abst) + len(cat3_ret_and_fail) + len(cat4_not_ret_and_abst) + len(cat5_other)}\n")
