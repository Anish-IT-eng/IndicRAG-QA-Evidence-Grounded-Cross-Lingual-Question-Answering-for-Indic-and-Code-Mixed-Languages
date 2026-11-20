import csv
import math
from pathlib import Path
from scipy import stats

root = Path(__file__).resolve().parent.parent
exp_dir = root / "backend" / "data" / "experiments" / "m10"

def verify_stats():
    # 1. From Phase E per-intent results:
    p_e = exp_dir / "m10_phase_e_per_intent_results.csv"
    with open(p_e, "r", encoding="utf-8") as f:
        e_rows = list(csv.DictReader(f))
        
    e1_hi = {r["query_id"]: int(float(r["hit_5"])) for r in e_rows if r["config_id"] == "E1_PROD_MSMARCO_D10" and r["language"] == "hi"}
    e6b_hi = {r["query_id"]: int(float(r["hit_5"])) for r in e_rows if r["config_id"] == "E6b_ADAPTIVE_BI_ENCODER" and r["language"] == "hi"}
    
    print(f"Total Devanagari queries: E1={len(e1_hi)}, E6b={len(e6b_hi)}")
    print(f"E1 hits: {sum(e1_hi.values())}/45 -> {sum(e1_hi.values())/45:.4f}")
    print(f"E6b hits: {sum(e6b_hi.values())}/45 -> {sum(e6b_hi.values())/45:.4f}")
    
    # Paired contingency table:
    # a: Both 1
    # b: E1=1, E6b=0
    # c: E1=0, E6b=1
    # d: Both 0
    a = sum(1 for qid in e1_hi if e1_hi[qid] == 1 and e6b_hi[qid] == 1)
    b = sum(1 for qid in e1_hi if e1_hi[qid] == 1 and e6b_hi[qid] == 0)
    c = sum(1 for qid in e1_hi if e1_hi[qid] == 0 and e6b_hi[qid] == 1)
    d = sum(1 for qid in e1_hi if e1_hi[qid] == 0 and e6b_hi[qid] == 0)
    
    print("\nContingency Table (Phase E E1 vs E6b Devanagari Hit@5):")
    print(f"Both Successful (a): {a}")
    print(f"Config A (E1) Only (b): {b}")
    print(f"Config B (E6b) Only (c): {c}")
    print(f"Neither Successful (d): {d}")
    print(f"Total: {a+b+c+d}")
    
    # McNemar test
    # If b=0 and c=2 (or whatever b and c are):
    # Asymptotic without continuity correction: (b - c)^2 / (b + c)
    # With Edwards continuity correction: (|b - c| - 1)^2 / (b + c)
    # Exact binomial: 2 * binom.cdf(min(b,c), b+c, 0.5)
    if b + c > 0:
        chi2_asymp = (b - c)**2 / (b + c)
        p_asymp = 1 - stats.chi2.cdf(chi2_asymp, df=1)
        
        chi2_cc = (abs(b - c) - 1)**2 / (b + c)
        p_cc = 1 - stats.chi2.cdf(chi2_cc, df=1)
        
        p_exact = 2 * stats.binom.cdf(min(b, c), b + c, 0.5)
        print(f"\nMcNemar Asymptotic (no cc): chi2={chi2_asymp:.4f}, p={p_asymp:.4f}")
        print(f"McNemar with Continuity Correction: chi2={chi2_cc:.4f}, p={p_cc:.4f}")
        print(f"McNemar Exact Binomial: p={p_exact:.4f}")
    else:
        print("b + c == 0")

    # What if b=0 and c=4 (if E1 had 0 hits and E6b had 4 hits)?
    print("\n--- Sensitivity / Scenario Analysis ---")
    for test_b, test_c in [(0, 2), (0, 4), (1, 3), (2, 4), (0, 3)]:
        chi2_a = (test_b - test_c)**2 / (test_b + test_c)
        p_a = 1 - stats.chi2.cdf(chi2_a, df=1)
        chi2_c = (abs(test_b - test_c) - 1)**2 / (test_b + test_c)
        p_c = 1 - stats.chi2.cdf(chi2_c, df=1)
        p_ex = 2 * stats.binom.cdf(min(test_b, test_c), test_b + test_c, 0.5)
        print(f"If b={test_b}, c={test_c}: Asymp p={p_a:.4f}, CC p={p_c:.4f}, Exact p={p_ex:.4f}")

    # Check query IDs that hit in E1 vs E6b
    print("\nDevanagari query-level breakdown:")
    for qid in sorted(e1_hi.keys()):
        h1 = e1_hi[qid]
        h2 = e6b_hi[qid]
        if h1 != 0 or h2 != 0:
            print(f"  {qid}: E1={h1}, E6b={h2}")

if __name__ == "__main__":
    verify_stats()
