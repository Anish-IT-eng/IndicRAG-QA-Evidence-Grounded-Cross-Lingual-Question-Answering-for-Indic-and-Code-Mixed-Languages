import os
import hashlib
import json
import csv
from pathlib import Path

def compute_sha256(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def inspect_csv(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return len(rows), list(rows[0].keys()) if rows else [], rows

def inspect_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return len(rows), list(rows[0].keys()) if rows else [], rows

def inspect_json(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)
    return data

datasets = {
    "M3 Final Dataset (N=15)": {
        "path": "backend/data/dataset/final_verified_dataset.csv",
        "expected_sha256": "093b00ad0f19acda806f2302731ccf2de28838c1b29c6ef16d55cbc5e7e2d520",
        "baseline_ref": "m10_baseline_snapshot.json (and m8_1, m8_6, m8_7, m8_8, m9 manifests)",
        "tier": "TIER_1_DIRECTLY_HASH_VERIFIED_AGAINST_HISTORICAL_BASELINE",
        "frozen": "FROZEN"
    },
    "M6 Expanded Benchmark (N=60)": {
        "path": "backend/data/dataset/m6_expanded_benchmark_n60.csv",
        "expected_sha256": "a528ac583d8c060b91a7febce652885e4045fcc76d644e49e876ddeb5d1db4ae",
        "baseline_ref": "m10_baseline_snapshot.json (and m8_1, m8_6, m8_7, m8_8, m9 manifests)",
        "tier": "TIER_1_DIRECTLY_HASH_VERIFIED_AGAINST_HISTORICAL_BASELINE",
        "frozen": "FROZEN"
    },
    "M6 Benchmark Qualification Ledger": {
        "path": "backend/data/dataset/m6_benchmark_qualification.csv",
        "expected_sha256": "db8c2b5e02d6177b335a283f9ac62f99729fb36ef142aa1af81c99528efd3b13",
        "baseline_ref": "m10_baseline_snapshot.json (and m8_1, m8_6, m8_7, m8_8, m9 manifests)",
        "tier": "TIER_1_DIRECTLY_HASH_VERIFIED_AGAINST_HISTORICAL_BASELINE",
        "frozen": "FROZEN"
    },
    "M6 Phase 3 Negative Benchmark (N=33)": {
        "path": "backend/data/experiments/m6/m6_phase3_1_negative_benchmark_audit.csv",
        "expected_sha256": "be02da59b85d2895b8c60f52266540c27e39c4e8fb39810b1152cf74ea69b05c",
        "baseline_ref": "m10_baseline_snapshot.json (and m8_8, m9 manifests)",
        "tier": "TIER_1_DIRECTLY_HASH_VERIFIED_AGAINST_HISTORICAL_BASELINE",
        "frozen": "FROZEN"
    },
    "M6 Phase 3 Negative Candidates Pool": {
        "path": "backend/data/dataset/m6_phase3_negative_candidates.csv",
        "expected_sha256": "492b0b1be3ce0c00fdcf453c971c48cb15176496e15806142c0aaff66050aeaa",
        "baseline_ref": "m8_1, m8_6, m8_7 integrity manifests",
        "tier": "TIER_1_DIRECTLY_HASH_VERIFIED_AGAINST_HISTORICAL_BASELINE",
        "frozen": "FROZEN"
    },
    "M9 Evaluation Dataset (N=240)": {
        "path": "backend/data/experiments/m9/m9_evaluation_dataset.jsonl",
        "expected_sha256": "f1829bdcad4512b6481005a944ab65da6dbd2858de5cc83a4a289d15bd506c2f",
        "baseline_ref": "m10_phase_f_baseline_snapshot.json (and m9_integrity_manifest.json)",
        "tier": "TIER_1_DIRECTLY_HASH_VERIFIED_AGAINST_HISTORICAL_BASELINE",
        "frozen": "FROZEN"
    },
    "M9 Answer Generation Results Baseline": {
        "path": "backend/data/experiments/m9/answer_generation_results.csv",
        "expected_sha256": "8dd71a906d704a9e2dfce55dee3d977555f6e59d5deb7a20eef8fc3ce0b13943",
        "baseline_ref": "m10_phase_f_baseline_snapshot.json (m9_answers_csv_sha256)",
        "tier": "TIER_1_DIRECTLY_HASH_VERIFIED_AGAINST_HISTORICAL_BASELINE",
        "frozen": "FROZEN"
    },
    "M10 Baseline Snapshot": {
        "path": "backend/data/experiments/m10/m10_baseline_snapshot.json",
        "expected_sha256": "06370db7b83ed53c5beb18b1a0a4f9b7877a5c46e83b8e5c47586bccea2fd693",
        "baseline_ref": "SELF_REFERENCING_SNAPSHOT",
        "tier": "TIER_2_RECORDED_HASH_WITHOUT_INDEPENDENT_BASELINE",
        "frozen": "FROZEN"
    },
    "M10 Phase F Baseline Snapshot": {
        "path": "backend/data/experiments/m10/m10_phase_f_baseline_snapshot.json",
        "expected_sha256": "ece587035b7e22c4755c8dcbbab091f8255e78c293f917d9960eb969f8fce24b",
        "baseline_ref": "SELF_REFERENCING_SNAPSHOT",
        "tier": "TIER_2_RECORDED_HASH_WITHOUT_INDEPENDENT_BASELINE",
        "frozen": "FROZEN"
    },
    "R4 Comprehensive Test Results": {
        "path": "docs/r4_test_results.json",
        "expected_sha256": "364ab44b00f4f084461f9ae7b86cd1910aaace0ad3d838af5ae996dfd1d3b198",
        "baseline_ref": "R4_TEST_EXECUTION_OUTPUT",
        "tier": "TIER_2_DYNAMIC_TEST_EXECUTION_OUTPUT",
        "frozen": "VERSIONED_OUTPUT"
    },
    "R4.1 Multilingual Audit": {
        "path": "docs/r4_1_multilingual_audit.json",
        "expected_sha256": "da50986309daca1fdcf7d0bcbc13fc87df2dddf921e99799408a047664d964bc",
        "baseline_ref": "R4_1_AUDIT_EXECUTION_OUTPUT",
        "tier": "TIER_2_DYNAMIC_TEST_EXECUTION_OUTPUT",
        "frozen": "VERSIONED_OUTPUT"
    },
    "R2.1 Regression Test Results": {
        "path": "docs/r2_1_regression_test_results.json",
        "expected_sha256": "97a78044061c08a71e8be5de3574c4ffce0063e76a7b8874dedbcd66429c53c8",
        "baseline_ref": "R2_1_REGRESSION_OUTPUT",
        "tier": "TIER_2_DYNAMIC_TEST_EXECUTION_OUTPUT",
        "frozen": "VERSIONED_OUTPUT"
    },
    "R3 Test Results": {
        "path": "docs/r3_test_results.json",
        "expected_sha256": "c8309769ab5000fbe139bdde6da5a7aa2324eeed806c12096152542f3be35b78",
        "baseline_ref": "R3_TEST_EXECUTION_OUTPUT",
        "tier": "TIER_2_DYNAMIC_TEST_EXECUTION_OUTPUT",
        "frozen": "VERSIONED_OUTPUT"
    },
}

inventory = {}

print("=== R6 BENCHMARK INTEGRITY AUDIT ===")
all_passed = True

for name, meta in datasets.items():
    rel_path = meta["path"]
    p = Path(rel_path)
    if not p.exists():
        print(f"[-] MISSING: {name} at {rel_path}")
        all_passed = False
        continue
    
    sha = compute_sha256(p)
    size_bytes = p.stat().st_size
    expected_sha = meta["expected_sha256"]
    match = (sha == expected_sha) if expected_sha else None
    
    if match is False:
        all_passed = False
        print(f"[!] MISMATCH: {name} | actual={sha[:8]}... expected={expected_sha[:8]}...")
    else:
        print(f"[+] MATCH: {name} ({meta['tier'][:15]}) -> {sha[:12]}...")

    count = 0
    cols = []
    languages = set()
    answerable_count = 0
    unanswerable_count = 0
    categories = set()
    verification_tier = "AUTOMATED_VALIDATION_PENDING_HUMAN"
    
    if p.suffix == ".csv":
        count, cols, rows = inspect_csv(p)
        for r in rows:
            if "query_language" in r and r["query_language"]:
                languages.add(r["query_language"])
            elif "language" in r and r["language"]:
                languages.add(r["language"])
            else:
                languages.add("English")
                
            ans_val = str(r.get("answerability", r.get("answerable", r.get("is_answerable", "")))).lower()
            if ans_val in ("false", "0", "no", "unanswerable"):
                unanswerable_count += 1
            elif ans_val in ("true", "1", "yes", "answerable"):
                answerable_count += 1
            else:
                if "negative" in rel_path:
                    unanswerable_count += 1
                else:
                    answerable_count += 1
                    
            cat = r.get("question_type", r.get("category", r.get("semantic_category", "")))
            if cat:
                categories.add(cat)
                
    elif p.suffix == ".jsonl":
        count, cols, rows = inspect_jsonl(p)
        for r in rows:
            if "query_language" in r:
                languages.add(r["query_language"])
            status = r.get("expected_status", "")
            if status == "UNANSWERABLE":
                unanswerable_count += 1
            elif status == "ANSWERED":
                answerable_count += 1
            cat = r.get("query_type")
            if cat:
                categories.add(cat)
        verification_tier = "PROVISIONAL_NOT_HUMAN_VERIFIED"
                
    elif p.suffix == ".json":
        data = inspect_json(p)
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict):
            count = len(data.get("results", data.get("queries", data)))
        verification_tier = "SYSTEM_LOG_SNAPSHOT"

    inventory[name] = {
        "file_path": rel_path,
        "sha256": sha,
        "size_bytes": size_bytes,
        "record_count": count,
        "languages": sorted(list(languages)),
        "answerable_count": answerable_count,
        "unanswerable_count": unanswerable_count,
        "categories": sorted(list(categories)),
        "verification_tier": verification_tier,
        "frozen_status": meta["frozen"],
        "columns": cols,
        "baseline_reference": meta["baseline_ref"],
        "expected_sha256": expected_sha,
        "actual_sha256": sha,
        "hash_match": match,
        "classification_tier": meta["tier"]
    }

with open("docs/r6_dataset_integrity_manifest.json", "w", encoding="utf-8") as f:
    json.dump(inventory, f, indent=2)

print("\nResult:", "ALL_HASHES_MATCH_VERIFIED" if all_passed else "HASH_MISMATCH_DETECTED")
print("Updated docs/r6_dataset_integrity_manifest.json successfully.")
