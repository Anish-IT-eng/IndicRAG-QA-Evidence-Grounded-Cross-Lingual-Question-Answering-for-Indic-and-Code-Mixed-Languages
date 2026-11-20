import csv
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"

claims_csv = backend_dir / "data/experiments/m6/m6_phase2b_claim_grounding.csv"
eval_csv = backend_dir / "data/experiments/m6/m6_phase2b_query_eval.csv"
qual_csv = backend_dir / "data/dataset/m6_benchmark_qualification.csv"

with open(claims_csv, "r", encoding="utf-8") as f:
    claims = list(csv.DictReader(f))

with open(eval_csv, "r", encoding="utf-8") as f:
    eval_map = {r["candidate_id"]: r for r in csv.DictReader(f)}

with open(qual_csv, "r", encoding="utf-8") as f:
    qual_map = {r["candidate_id"]: r for r in csv.DictReader(f)}

print(f"Total claims in CSV: {len(claims)}")

# Split by cohort
claims_elig = [c for c in claims if c["cohort_group"] == "ELIGIBLE_PROVISIONAL"]
claims_excl = [c for c in claims if c["cohort_group"] != "ELIGIBLE_PROVISIONAL"]

print(f"Eligible claims: {len(claims_elig)}")
print(f"Excluded claims: {len(claims_excl)}")

# Breakdown of verdicts
def get_breakdown(claim_list):
    b = {"ENTAILED": 0, "CONTRADICTED": 0, "INSUFFICIENT_SUPPORT": 0}
    for c in claim_list:
        v = c["verdict"]
        b[v] = b.get(v, 0) + 1
    return b

print("Eligible claims breakdown:", get_breakdown(claims_elig))
print("Excluded claims breakdown:", get_breakdown(claims_excl))

# Inspect each contradicted or unsupported claim
discrepant_claims = [c for c in claims if c["verdict"] in ("CONTRADICTED", "INSUFFICIENT_SUPPORT")]
print(f"\nTotal discrepant claims across all 60 records: {len(discrepant_claims)}")

# Link each to controller status and generator presentation
presented_unsupported = 0
presented_contradicted = 0
suppressed_unsupported = 0
suppressed_contradicted = 0

for c in discrepant_claims:
    cid = c["candidate_id"]
    eval_info = eval_map.get(cid, {})
    ctrl_status = eval_info.get("controller_status", "unknown")
    v = c["verdict"]
    
    # Did this answer reach the user?
    # In generator.py:
    # If controller_status in (INSUFFICIENT, MISSING, CLARIFICATION_REQUIRED):
    #   Fast abstention / UNANSWERABLE returned -> suppressed!
    # If controller_status == CONFLICTING:
    #   ResponseStatus.CONFLICTING_VERSIONS returned -> presented with conflict warning!
    # If controller_status in (SUFFICIENT, PARTIAL):
    #   ResponseStatus.ANSWERED returned -> presented to user!
    
    was_presented = ctrl_status in ("sufficient", "partial", "conflicting")
    
    if v == "CONTRADICTED":
        if was_presented:
            presented_contradicted += 1
        else:
            suppressed_contradicted += 1
    elif v == "INSUFFICIENT_SUPPORT":
        if was_presented:
            presented_unsupported += 1
        else:
            suppressed_unsupported += 1

print("\n--- Claim Enforcement Presentation Analysis ---")
print(f"Contradicted claims presented to users: {presented_contradicted}")
print(f"Contradicted claims suppressed via controller abstention: {suppressed_contradicted}")
print(f"Unsupported claims presented to users: {presented_unsupported}")
print(f"Unsupported claims suppressed via controller abstention: {suppressed_unsupported}")

# Count candidate answers where ALL claims were entailed
cid_claims = {}
for c in claims:
    cid_claims.setdefault(c["candidate_id"], []).append(c)

all_entailed_cids = []
for cid, c_list in cid_claims.items():
    if all(c["verdict"] == "ENTAILED" for c in c_list):
        all_entailed_cids.append(cid)

print(f"\nTotal queries with 100% core claims entailed: {len(all_entailed_cids)} / {len(cid_claims)}")

