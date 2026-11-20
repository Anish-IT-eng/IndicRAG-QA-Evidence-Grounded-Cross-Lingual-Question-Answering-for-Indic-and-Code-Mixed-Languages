import csv
from pathlib import Path

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
raw_h = list(csv.DictReader(open(root / "backend/data/experiments/m10/m10_phase_h_per_query_results.csv", encoding="utf-8")))

sub_b = [r for r in raw_h if r["config_id"] == "ConfigB_AdaptiveE6b"]

cat1_bypassed_abstention = []
cat2_direct_controller_disclosure = []
cat3_invoked_correct_answer = []
cat4_invoked_postgen_abstention = []
cat5_invoked_incorrect_output = []
cat6_invoked_execution_error = []

for r in sub_b:
    qid = r["query_id"]
    ctrl = r["controller_status"]
    resp = r["response_status"]
    gen_lat = float(r["generation_latency_ms"])
    exp = r["expected_status"]
    
    # 1. Controller bypassed generation -> final abstention
    if ctrl == "insufficient" and resp == "unanswerable" and gen_lat <= 1.0:
        cat1_bypassed_abstention.append(qid)
    # 2. Controller bypassed LLM -> direct structured regulatory disclosure
    elif qid == "M9-Q002":
        cat2_direct_controller_disclosure.append(qid)
    # 3. Controller invoked generation -> correct answer/disclosure
    elif exp == "ANSWERED" and resp in ["answered", "conflicting_versions"] and gen_lat > 1.0:
        cat3_invoked_correct_answer.append(qid)
    # 4. Controller invoked generation -> post-generation abstention
    elif resp == "unanswerable" and gen_lat > 1.0:
        cat4_invoked_postgen_abstention.append(qid)
    # 5. Controller invoked generation -> incorrect answer/disclosure on unanswerable
    elif exp == "UNANSWERABLE" and resp in ["answered", "conflicting_versions"] and gen_lat > 1.0:
        cat5_invoked_incorrect_output.append(qid)
    # 6. Controller invoked generation -> execution error
    elif resp == "error" and gen_lat > 1.0:
        cat6_invoked_execution_error.append(qid)
    else:
        print(f"UNCLASSIFIED: {qid} ctrl={ctrl} resp={resp} gen_lat={gen_lat} exp={exp}")

print(f"Cat 1: Bypassed Abstention: {len(cat1_bypassed_abstention)}")
print(f"Cat 2: Direct Controller Disclosure (M9-Q002): {len(cat2_direct_controller_disclosure)}")
print(f"Cat 3: Invoked Correct Answer/Disclosure: {len(cat3_invoked_correct_answer)}")
print(f"Cat 4: Invoked Post-Gen Abstention: {len(cat4_invoked_postgen_abstention)}")
print(f"Cat 5: Invoked Incorrect Output (M9-Q201, M9-Q229): {len(cat5_invoked_incorrect_output)}")
print(f"Cat 6: Invoked Execution Error (M9-Q123, M9-Q124): {len(cat6_invoked_execution_error)}")

total = (len(cat1_bypassed_abstention) + len(cat2_direct_controller_disclosure) + 
         len(cat3_invoked_correct_answer) + len(cat4_invoked_postgen_abstention) + 
         len(cat5_invoked_incorrect_output) + len(cat6_invoked_execution_error))
print(f"Total: {total} / 240")

# Check uniqueness
all_qids = (cat1_bypassed_abstention + cat2_direct_controller_disclosure + 
            cat3_invoked_correct_answer + cat4_invoked_postgen_abstention + 
            cat5_invoked_incorrect_output + cat6_invoked_execution_error)
assert len(all_qids) == 240
assert len(set(all_qids)) == 240
print("All 240 queries accounted for with 100% uniqueness!")
