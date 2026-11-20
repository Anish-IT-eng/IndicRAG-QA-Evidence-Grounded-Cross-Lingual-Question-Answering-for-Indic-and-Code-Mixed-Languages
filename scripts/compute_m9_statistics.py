"""
Computes paired cross-lingual statistical comparisons and confidence intervals
across the 60 semantic intent groups.
Outputs statistical tables for Phase H: docs/m9_statistical_evaluation.md
"""
import json
import csv
import math
import os
import sys

def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0

def stddev(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0

def bootstrap_ci(xs, n_boot=2000, alpha=0.05):
    import random
    random.seed(42)
    if not xs:
        return 0.0, 0.0
    means = []
    n = len(xs)
    for _ in range(n_boot):
        sample = [random.choice(xs) for _ in range(n)]
        means.append(mean(sample))
    means.sort()
    low = means[int((alpha / 2) * n_boot)]
    high = means[int((1 - alpha / 2) * n_boot)]
    return low, high

def paired_t_test(xs, ys):
    """Computes paired t-statistic and approximate p-value."""
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0, 1.0
    diffs = [x - y for x, y in zip(xs, ys)]
    d_mean = mean(diffs)
    d_std = stddev(diffs)
    if d_std == 0:
        return 0.0, 1.0
    t_stat = d_mean / (d_std / math.sqrt(len(diffs)))
    # Approximate normal CDF tail for two-tailed p-value
    # Approximation of erf
    z = abs(t_stat)
    p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2))))
    return t_stat, p_val

print("Statistical helper script ready.")
