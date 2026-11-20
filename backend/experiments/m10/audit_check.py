import csv
import json

def check_hindi_records():
    print("=== CHECKING PHASE H PER QUERY RESULTS ===")
    with open("backend/data/experiments/m10/m10_phase_h_per_query_results.csv", mode="r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    configs = sorted(set(r["config_id"] for r in rows))
    print("Config IDs found:", configs)

    for cid in configs:
        hi_rows = [r for r in rows if r["config_id"] == cid and r["language"] == "hi"]
        print(f"\n--- Config {cid}: {len(hi_rows)} Hindi queries ---")
        for r in hi_rows:
            hit5 = int(float(r["retrieval_hit_5"]))
            resp = r["response_status"]
            cat = r["correctness_category"]
            exp = r["expected_status"]
            ctrl = r["controller_status"]
            ceci = r["ceci_score"]
            qid = r["query_id"]
            # Print if hit5 == 1 or response_status != unanswerable
            if hit5 == 1 or resp != "unanswerable":
                print(f"{qid} (exp={exp}): hit5={hit5}, resp={resp}, cat={cat}, ctrl={ctrl}, ceci={ceci}")

def check_claims():
    print("\n=== CHECKING PHASE H CLAIM AUDIT ===")
    with open("backend/data/experiments/m10/m10_phase_h_claim_audit.csv", mode="r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Total rows in claim audit: {len(rows)}")
    if rows:
        print("Columns:", list(rows[0].keys()))
    
    by_config = {}
    for r in rows:
        cid = r.get("config_id") or r.get("config")
        by_config[cid] = by_config.get(cid, 0) + 1
    print("Claims by config:", by_config)

    # Check verified status / supported status
    for cid in by_config:
        cfg_rows = [r for r in rows if (r.get("config_id") or r.get("config")) == cid]
        supported = [r for r in cfg_rows if r.get("verdict") == "supported" or r.get("is_supported") == "True" or r.get("claim_supported") == "1"]
        print(f"Config {cid}: total {len(cfg_rows)}, supported: {len(supported)}")
        # Check verdict values
        verdicts = set(r.get("verdict") for r in cfg_rows)
        print(f"  Verdicts: {verdicts}")

def check_metrics_json():
    print("\n=== CHECKING PHASE H METRICS JSON ===")
    with open("backend/data/experiments/m10/m10_phase_h_metrics.json", mode="r", encoding="utf-8") as f:
        data = json.load(f)
    print("Keys in metrics JSON:", list(data.keys()))
    if "grounding" in data:
        print("Grounding section:", json.dumps(data["grounding"], indent=2))
    elif "claim_grounding" in data:
        print("Claim grounding section:", json.dumps(data["claim_grounding"], indent=2))
    else:
        for k in data:
            if "claim" in k.lower() or "audit" in k.lower() or "citation" in k.lower():
                print(f"Key {k}:", data[k])

if __name__ == "__main__":
    check_hindi_records()
    check_claims()
    check_metrics_json()
