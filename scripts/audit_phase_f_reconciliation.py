import csv
import json
import math
import os
import sqlite3
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
exp_dir = root / "backend" / "data" / "experiments" / "m10"

def audit_all():
    print("=== TASK 1: PHASE E vs PHASE F RECONCILIATION ===")
    phase_e_file = exp_dir / "m10_phase_e_results.csv"
    phase_f_file = exp_dir / "m10_phase_f_end_to_end_results.csv"
    
    with open(phase_e_file, "r", encoding="utf-8") as f:
        e_rows = list(csv.DictReader(f))
    with open(phase_f_file, "r", encoding="utf-8") as f:
        f_rows = list(csv.DictReader(f))
        
    print(f"Phase E rows: {len(e_rows)}")
    print(f"Phase F rows: {len(f_rows)}")
    
    # Phase E summary by config & lang
    print("\nPhase E Metrics:")
    for r in e_rows:
        cfg = r.get("config_id")
        lang = r.get("language")
        if cfg in ["E1_PROD_MSMARCO_D10", "E6b_ADAPTIVE_BI_ENCODER"]:
            print(f"[{cfg}] [{lang}] Hit@1={r.get('hit_1')}, Hit@3={r.get('hit_3')}, Hit@5={r.get('hit_5')}, MRR={r.get('mrr')}, nDCG@5={r.get('ndcg_5')}, Latency={r.get('latency_ms')}")
            
    print("\nPhase F Metrics summary:")
    # Group F rows by config and language
    f_by_cfg_lang = {}
    for r in f_rows:
        cfg = r["config_id"]
        lang = r["language"]
        key = (cfg, lang)
        f_by_cfg_lang.setdefault(key, []).append(r)
        
    for (cfg, lang), rows in sorted(f_by_cfg_lang.items()):
        total = len(rows)
        ans_rows = [r for r in rows if r["expected_status"] == "ANSWERED"]
        hits5 = sum(int(r["retrieval_hit_5"]) for r in ans_rows)
        ans_count = sum(1 for r in ans_rows if r["response_status"].lower() in ["answered", "clarification_needed"])
        mean_ret_lat = sum(float(r["retrieval_latency_ms"]) for r in rows) / total
        print(f"[{cfg}] [{lang}] Total={total}, Ans={len(ans_rows)}, Hits@5={hits5}/{len(ans_rows)} ({hits5/len(ans_rows):.4f}), AnsCount={ans_count}, MeanRetLat={mean_ret_lat:.2f}ms")

    # Overall across languages in Phase F
    for cfg in ["ConfigA_Production", "ConfigB_AdaptiveE6b"]:
        rows = [r for r in f_rows if r["config_id"] == cfg]
        ans_rows = [r for r in rows if r["expected_status"] == "ANSWERED"]
        hits5 = sum(int(r["retrieval_hit_5"]) for r in ans_rows)
        mean_ret_lat = sum(float(r["retrieval_latency_ms"]) for r in rows) / len(rows)
        print(f"[{cfg}] [OVERALL] Total={len(rows)}, Ans={len(ans_rows)}, Hits@5={hits5}/{len(ans_rows)} ({hits5/len(ans_rows):.4f}), MeanRetLat={mean_ret_lat:.2f}ms")

if __name__ == "__main__":
    audit_all()
