import csv
import statistics
from decimal import Decimal
from pathlib import Path
from collections import Counter

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
raw_h = list(csv.DictReader(open(root / "backend/data/experiments/m10/m10_phase_h_per_query_results.csv", encoding="utf-8")))

sub_b = [r for r in raw_h if r["config_id"] == "ConfigB_AdaptiveE6b"]
print(f"Total Config B rows: {len(sub_b)}")

# Inspect M9-Q002
q002 = [r for r in sub_b if r["query_id"] == "M9-Q002"][0]
print(f"M9-Q002: gen_lat={q002['generation_latency_ms']}, ctrl_lat={q002['controller_latency_ms']}, ret_lat={q002['retrieval_latency_ms']}, tot_lat={q002['total_latency_ms']}")

# Let's inspect all generation latency values among bypassed vs invoked
# Bypassed = controller == 'insufficient' (120) + M9-Q002 (1) = 121
bypassed = [r for r in sub_b if r["controller_status"] == "insufficient" or r["query_id"] == "M9-Q002"]
invoked = [r for r in sub_b if r["controller_status"] != "insufficient" and r["query_id"] != "M9-Q002"]

print(f"\nBypassed count: {len(bypassed)}")
print(f"Invoked count: {len(invoked)}")

bypassed_lats = [float(r["generation_latency_ms"]) for r in bypassed]
print("Bypassed generation latency distribution:", Counter(bypassed_lats))

invoked_lats = [float(r["generation_latency_ms"]) for r in invoked]
print(f"Invoked generation latency min: {min(invoked_lats)}, max: {max(invoked_lats)}")

# Exact Decimal sums
all_gen_dec = [Decimal(r["generation_latency_ms"]) for r in sub_b]
invoked_gen_dec = [Decimal(r["generation_latency_ms"]) for r in invoked]
bypassed_gen_dec = [Decimal(r["generation_latency_ms"]) for r in bypassed]

sum_all_gen = sum(all_gen_dec)
sum_invoked_gen = sum(invoked_gen_dec)
sum_bypassed_gen = sum(bypassed_gen_dec)

print(f"\nExact sum of ALL 240 generation latencies: {sum_all_gen} ms")
print(f"Exact sum of 119 INVOKED generation latencies: {sum_invoked_gen} ms")
print(f"Exact sum of 121 BYPASSED generation latencies: {sum_bypassed_gen} ms")

mean_invoked = sum_invoked_gen / Decimal(len(invoked))
mean_amortized = sum_all_gen / Decimal(len(sub_b))

print(f"Recalculated Conditional Generation Mean (over 119): {mean_invoked} ms (rounded: {round(float(mean_invoked), 2)})")
print(f"Recalculated Population Amortized Generation Mean (over 240): {mean_amortized} ms (rounded: {round(float(mean_amortized), 2)})")

# Total Pipeline Latency
all_tot_dec = [Decimal(r["total_latency_ms"]) for r in sub_b]
all_ret_dec = [Decimal(r["retrieval_latency_ms"]) for r in sub_b]
all_ctrl_dec = [Decimal(r["controller_latency_ms"]) for r in sub_b]

sum_all_tot = sum(all_tot_dec)
sum_all_ret = sum(all_ret_dec)
sum_all_ctrl = sum(all_ctrl_dec)

mean_tot = sum_all_tot / Decimal(len(sub_b))
mean_ret = sum_all_ret / Decimal(len(sub_b))
mean_ctrl = sum_all_ctrl / Decimal(len(sub_b))

print(f"\nExact sum of ALL 240 total pipeline latencies: {sum_all_tot} ms")
print(f"Exact sum of ALL 240 retrieval latencies: {sum_all_ret} ms")
print(f"Exact sum of ALL 240 controller latencies: {sum_all_ctrl} ms")

print(f"\nMean Total Pipeline Latency: {mean_tot} ms (rounded: {round(float(mean_tot), 2)})")
print(f"Mean Retrieval Latency: {mean_ret} ms (rounded: {round(float(mean_ret), 2)})")
print(f"Mean Controller Latency: {mean_ctrl} ms (rounded: {round(float(mean_ctrl), 2)})")

sum_of_means = mean_ret + mean_ctrl + mean_amortized
diff_mean = mean_tot - sum_of_means
print(f"\nSum of Component Means: {sum_of_means} ms (rounded: {round(float(sum_of_means), 2)})")
print(f"Exact Residual (Mean Total - Sum of Means): {diff_mean} ms")

# Per-query residuals
per_query_diffs = [float(Decimal(r["total_latency_ms"]) - (Decimal(r["retrieval_latency_ms"]) + Decimal(r["controller_latency_ms"]) + Decimal(r["generation_latency_ms"]))) for r in sub_b]
print(f"Per-query residual min: {min(per_query_diffs)}, max: {max(per_query_diffs)}, mean: {sum(per_query_diffs)/len(per_query_diffs)}")
