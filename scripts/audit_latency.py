import csv
import json
import numpy as np
from pathlib import Path

root = Path(__file__).resolve().parent.parent
exp_dir = root / "backend" / "data" / "experiments" / "m10"

def audit_latencies():
    # 1. Phase E Resource Results
    pe_res = exp_dir / "m10_phase_e_resource_results.csv"
    with open(pe_res, "r", encoding="utf-8") as f:
        pe_rows = list(csv.DictReader(f))
        
    print("--- Phase E Resource Results ---")
    for r in pe_rows:
        if r.get("config_id") in ["E1_PROD_MSMARCO_D10", "E6b_ADAPTIVE_BI_ENCODER"]:
            print(r)
            
    # 2. Phase F Resource Results
    pf_res = exp_dir / "m10_phase_f_resource_results.csv"
    with open(pf_res, "r", encoding="utf-8") as f:
        pf_rows = list(csv.DictReader(f))
        
    print("\n--- Phase F Resource Results ---")
    for r in pf_rows:
        print(r)
        
    # 3. Phase F raw per-query latencies
    pf_e2e = exp_dir / "m10_phase_f_end_to_end_results.csv"
    with open(pf_e2e, "r", encoding="utf-8") as f:
        f_rows = list(csv.DictReader(f))
        
    print("\n--- Phase F Per-Language Retrieval Latencies ---")
    for cfg in ["ConfigA_Production", "ConfigB_AdaptiveE6b"]:
        cfg_rows = [r for r in f_rows if r["config_id"] == cfg]
        print(f"\nConfiguration: {cfg}")
        for lang in ["en", "hi", "hi-Latn", "en-hi"]:
            l_rows = [r for r in cfg_rows if r["language"] == lang]
            l_ret = [float(r["retrieval_latency_ms"]) for r in l_rows]
            print(f"  {lang:<8} (N={len(l_ret)}): Mean={np.mean(l_ret):.2f}ms, Median={np.median(l_ret):.2f}ms, P95={np.percentile(l_ret, 95):.2f}ms, P99={np.percentile(l_ret, 99):.2f}ms, Max={np.max(l_ret):.2f}ms")
            
    # Reconcile Phase E 849.9ms with Phase F 836.0ms:
    print("\n--- Reconciling Phase E 849.9ms vs Phase F 836.0ms ---")
    # In Phase E:
    # E1 mean e2e latency: 1097.1 ms (retrieval + reranker).
    # E6b for Latin: ms-marco reranker (1097.1ms). For hi: bi-encoder dense (106.3ms in Phase E).
    # (3 * 1097.1 + 106.3) / 4 = (3291.3 + 106.3) / 4 = 3397.6 / 4 = 849.4 ms!
    # In Phase F:
    # Config B retrieval mean across 240 queries:
    b_ret = [float(r["retrieval_latency_ms"]) for r in f_rows if r["config_id"] == "ConfigB_AdaptiveE6b"]
    print(f"Phase F Config B overall mean retrieval latency: {np.mean(b_ret):.2f} ms")
    print(f"Phase F Config B hi mean retrieval latency: {np.mean([float(r['retrieval_latency_ms']) for r in f_rows if r['config_id'] == 'ConfigB_AdaptiveE6b' and r['language'] == 'hi']):.2f} ms")
    print(f"Phase F Config B Latin mean retrieval latency: {np.mean([float(r['retrieval_latency_ms']) for r in f_rows if r['config_id'] == 'ConfigB_AdaptiveE6b' and r['language'] != 'hi']):.2f} ms")

if __name__ == "__main__":
    audit_latencies()
