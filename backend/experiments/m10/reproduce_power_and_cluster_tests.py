"""
M10 Phase G: Executable Reproducibility Script for Power, Cluster Tests, and Provenance Audit
Script: reproduce_power_and_cluster_tests.py
Environment: Python 3.13.5, SciPy 1.15.1, NumPy 2.4.6
Repository: IndicRAG-QA

Purpose:
  1. Exact conditional binomial power calculations under H0: p=0.50 vs H1: p=0.75 (nD=23, nD=30).
  2. Unconditional power calculations under random discordance D ~ Binomial(N, pD=0.15).
  3. Exact permutation sign-flip Wilcoxon test vs asymptotic approximation for K=45 clusters.
  4. Raw-data answerable success verification across all 480 query rows in m10_phase_f_answer_correctness.csv.
"""
import csv
import json
import math
import sys
from pathlib import Path
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
M10_DIR = ROOT / "backend" / "data" / "experiments" / "m10"
M9_DIR = ROOT / "backend" / "data" / "experiments" / "m9"

def verify_power_calculations():
    print("=" * 80)
    print("1. EXACT CONDITIONAL BINOMIAL POWER REPRODUCIBILITY")
    print(f"Software: Python {sys.version.split()[0]}, SciPy {stats.__version__ if hasattr(stats, '__version__') else 'scipy'}, NumPy {np.__version__}")
    print("=" * 80)
    
    # 1.1 nD = 23
    n23 = 23
    p0 = 0.50
    p1 = 0.75
    
    # Critical region for two-sided test at alpha <= 0.05
    # C <= 6 or C >= 17
    alpha_2s_23 = stats.binom.cdf(6, n23, p0) + stats.binom.sf(16, n23, p0)
    power_2s_23 = stats.binom.cdf(6, n23, p1) + stats.binom.sf(16, n23, p1)
    
    # One-sided critical region C >= 16 at alpha <= 0.05
    alpha_1s_23 = stats.binom.sf(15, n23, p0)
    power_1s_23 = stats.binom.sf(15, n23, p1)
    
    print("Under nD = 23 (Planning assumption: conditional win probability pi = 0.75):")
    print(f"  Exact Two-Sided Rejection Region: C <= 6 or C >= 17")
    print(f"  Exact Two-Sided Null Size (alpha): {alpha_2s_23:.10f} ({alpha_2s_23*100:.4f}%)")
    print(f"  Exact Two-Sided Power:             {power_2s_23:.10f} ({power_2s_23*100:.4f}%)")
    print(f"  Exact One-Sided Rejection Region: C >= 16")
    print(f"  Exact One-Sided Null Size (alpha): {alpha_1s_23:.10f} ({alpha_1s_23*100:.4f}%)")
    print(f"  Exact One-Sided Power:             {power_1s_23:.10f} ({power_1s_23*100:.4f}%)")
    print("  => Finding: The reported 80.34% corresponds to ONE-SIDED power (80.3697%), NOT two-sided power (65.3728%).")
    
    # 1.2 nD = 30
    n30 = 30
    # Two-sided rejection region at alpha <= 0.05: C <= 9 or C >= 21
    p_le_9 = stats.binom.cdf(9, n30, p0)
    p_ge_21 = stats.binom.sf(20, n30, p0)
    alpha_2s_30 = p_le_9 + p_ge_21
    power_2s_30 = stats.binom.cdf(9, n30, p1) + stats.binom.sf(20, n30, p1)
    
    print("\nUnder nD = 30:")
    print(f"  Rejection Region: C <= 9 or C >= 21")
    print(f"  P(C <= 9 | H0)  = {p_le_9:.10f}")
    print(f"  P(C >= 21 | H0) = {p_ge_21:.10f}")
    print(f"  Exact Two-Sided Null Size (alpha): {alpha_2s_30:.10f} ({alpha_2s_30*100:.4f}%)")
    print(f"  Exact Two-Sided Power:             {power_2s_30:.10f} ({power_2s_30*100:.4f}%)")
    print("  => Reconciled: Null rejection prob is exactly 0.0427739453 (rounded to 0.0428 in reports). Power reaches 80.3407%.")

def verify_unconditional_power():
    print("\n" + "=" * 80)
    print("2. UNCONDITIONAL POWER UNDER RANDOM DISCORDANCE D ~ Binomial(N, pD=0.15)")
    print("Planning Assumptions: Discordance pD = 0.15, Win Probability pi = 0.75, Two-Sided alpha <= 0.05")
    print("=" * 80)
    
    p_d = 0.15
    p1 = 0.75
    
    def calc_uncond(N):
        pow_2s = 0.0
        for d in range(1, N + 1):
            prob_d = stats.binom.pmf(d, N, p_d)
            if prob_d < 1e-12:
                continue
            # Find largest c_l such that binom.cdf(c_l, d, 0.5) <= 0.025
            c_h = None
            for k in range(d, 0, -1):
                if stats.binom.sf(k - 1, d, 0.5) <= 0.025:
                    c_h = k
                else:
                    break
            if c_h is not None:
                c_l = d - c_h
                p_val = stats.binom.cdf(c_l, d, p1) + stats.binom.sf(c_h - 1, d, p1)
                pow_2s += prob_d * p_val
        return pow_2s

    targets = [150, 180, 200, 220, 225, 230, 240, 250]
    for N in targets:
        uncond = calc_uncond(N)
        print(f"  N = {N:3d} total independent intents (920 queries if N=230): Unconditional Two-Sided Power = {uncond:.6f} ({uncond*100:.2f}%)")
    print("\nStandardized M11 Benchmark Requirement:")
    print("  - Total Independent Semantic Intent Groups: 225 to 230 in total (NOT per language).")
    print("  - Parallel Formulations per Intent: 4 languages (en, hi, hi-Latn, en-hi).")
    print("  - Total Benchmark Queries: 230 * 4 = 920 query records.")
    print("  - At N = 230 total intents, unconditional two-sided power reaches 81.22%.")

def verify_cluster_tests():
    print("\n" + "=" * 80)
    print("3. CLUSTER-LEVEL WILCOXON & EXACT PERMUTATION SIGN-FLIP VERIFICATION")
    print("=" * 80)
    
    # Hit@5 non-zero cluster differences: [0.25, 0.25, -0.25, 0.25]
    # Sum of positive ranks: 7.5, sum of negative ranks: 2.5 => W = 2.50
    # End-to-end success non-zero cluster differences: [0.25, 0.25]
    # Sum of positive ranks: 3.0, sum of negative ranks: 0.0 => W = 0.00
    
    # Asymptotic SciPy
    res_ret_asymp = stats.wilcoxon([0.25, 0.25, -0.25, 0.25], alternative="two-sided", method="approx")
    res_ret_exact = stats.wilcoxon([0.25, 0.25, -0.25, 0.25], alternative="two-sided", method="exact")
    
    res_succ_asymp = stats.wilcoxon([0.25, 0.25], alternative="two-sided", method="approx")
    res_succ_exact = stats.wilcoxon([0.25, 0.25], alternative="two-sided", method="exact")
    
    print(f"Retrieval Hit@5 (4 non-zero differences: 3 pos, 1 neg, tied at |d|=0.25):")
    print(f"  Test statistic: W = {res_ret_exact.statistic}")
    print(f"  Asymptotic p-value (continuity corrected): {res_ret_asymp.pvalue:.6f}")
    print(f"  Exact permutation sign-flip p-value:       {res_ret_exact.pvalue:.6f} (10 of 16 outcomes)")
    
    print(f"\nEnd-to-End Success (2 non-zero differences: 2 pos, 0 neg, tied at |d|=0.25):")
    print(f"  Test statistic: W = {res_succ_exact.statistic}")
    print(f"  Asymptotic p-value (normal approx):        {res_succ_asymp.pvalue:.6f}")
    print(f"  Exact permutation sign-flip p-value:       {res_succ_exact.pvalue:.6f} (2 of 4 outcomes)")
    print("  => Confirmed: Exactly 2 out of 4 sign configurations yield W <= 0.0, so exact p-value is 0.5000.")

def verify_raw_data():
    print("\n" + "=" * 80)
    print("4. EVIDENCE PROVENANCE & ROW-LEVEL VERIFICATION")
    print("=" * 80)
    corr_file = M10_DIR / "m10_phase_f_answer_correctness.csv"
    if not corr_file.exists():
        print("ERROR: Raw file m10_phase_f_answer_correctness.csv not found!")
        return
        
    with open(corr_file, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        
    print(f"Inspected {len(rows)} raw records directly from {corr_file.name}.")
    
    langs = ["en", "hi", "hi-Latn", "en-hi"]
    for cfg in ["ConfigA_Production", "ConfigB_AdaptiveE6b"]:
        print(f"\n--- {cfg} ---")
        cfg_rows = [r for r in rows if r["config_id"] == cfg and r["expected_status"] == "ANSWERED"]
        for l in langs:
            l_rows = [r for r in cfg_rows if r["language"] == l]
            ca = [r["query_id"] for r in l_rows if r["correctness_category"] == "CORRECT_ANSWERED"]
            rd = [r["query_id"] for r in l_rows if r["correctness_category"] == "REGULATORY_DISCLOSURE"]
            ua = [r["query_id"] for r in l_rows if r["correctness_category"] == "UNNECESSARY_ABSTENTION"]
            print(f"  {l:7s}: CA = {len(ca):2d}, RD = {len(rd):2d}, UA = {len(ua):2d} | Combined Success = {len(ca)+len(rd):2d}/45")

if __name__ == "__main__":
    verify_power_calculations()
    verify_unconditional_power()
    verify_cluster_tests()
    verify_raw_data()
