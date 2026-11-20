def calc_metrics(tp, fn, fp, tn, cr=0):
    # Answer class (Positive = Answerable)
    ans_prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    ans_rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    ans_f1 = 2 * ans_prec * ans_rec / (ans_prec + ans_rec) if (ans_prec + ans_rec) > 0 else 0.0
    
    # Unanswerable class (Negative = Unanswerable)
    unans_prec = tn / (tn + fn) if (tn + fn) > 0 else 0.0 # Note: standard precision for negative class is TN / (TN + FN)
    unans_rec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    unans_f1 = 2 * unans_prec * unans_rec / (unans_prec + unans_rec) if (unans_prec + unans_rec) > 0 else 0.0
    
    macro_f1 = (ans_f1 + unans_f1) / 2.0
    total_queries = tp + fn + fp + tn + cr
    coverage = (tp + fp) / total_queries if total_queries > 0 else 0.0
    false_answers = fp
    
    return {
        "TP": tp, "FN": fn, "FP": fp, "TN": tn, "CR": cr,
        "answer_precision": ans_prec,
        "answerable_recall": ans_rec,
        "answerable_f1": ans_f1,
        "unanswerable_precision": unans_prec,
        "unanswerable_recall": unans_rec,
        "unanswerable_f1": unans_f1,
        "macro_f1": macro_f1,
        "coverage": coverage,
        "false_answers": false_answers
    }

print("=== 1. HISTORICAL PHASE 2B (Strict) ===")
m_hist = calc_metrics(tp=6, fn=21, fp=0, tn=2, cr=0)
for k, v in m_hist.items():
    print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

print("\n=== 2. REPORTED PHASE 2B.1 (Erroneous TP=19) ===")
m_err = calc_metrics(tp=19, fn=8, fp=0, tn=2, cr=0)
for k, v in m_err.items():
    print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

print("\n=== 3. CORRECTED OPERATIONAL PHASE 2B.2 (TP=17, FN=9, CR=1 separate) ===")
# Here N_pos = 26 evaluated binary, CR=1 reported separately
m_corr_sep = calc_metrics(tp=17, fn=9, fp=0, tn=2, cr=1)
for k, v in m_corr_sep.items():
    print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

print("\n=== 4. CORRECTED OPERATIONAL PHASE 2B.2 (TP=17, FN=10 where FN includes CR) ===")
# If binary requires N_pos = 27, and CR is not answered, fn = 9 + 1 = 10
m_corr_bin = calc_metrics(tp=17, fn=10, fp=0, tn=2, cr=0)
for k, v in m_corr_bin.items():
    print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

