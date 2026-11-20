import hashlib
import json
from pathlib import Path

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 16):
            h.update(chunk)
    return h.hexdigest()

root = Path("c:/Users/anish/Desktop/IndicRAG-QA")
manifest_path = root / "backend/data/experiments/m10/m10_phase_h_manifest.json"
manifest = json.load(open(manifest_path, encoding="utf-8"))

print(f"Manifest timestamp: {manifest.get('timestamp')}")
print(f"Manifest determination: {manifest.get('target_determination')}\n")

matches = []
mismatches = []
missing = []

# Check input artifacts
print("=== Checking Input Artifacts ===")
for name, meta in manifest.get("input_artifacts", {}).items():
    p = Path(meta["path"])
    if not p.exists():
        missing.append((name, str(p)))
        print(f"MISSING: {name} at {p}")
    else:
        actual_hash = sha256_file(p)
        expected_hash = meta["sha256"]
        if actual_hash == expected_hash:
            matches.append((name, "input"))
            print(f"MATCH: {name}")
        else:
            mismatches.append((name, "input", expected_hash, actual_hash))
            print(f"MISMATCH: {name}\n  Expected: {expected_hash}\n  Actual:   {actual_hash}")

# Check generated data deliverables
print("\n=== Checking Generated Data Deliverables ===")
for name, meta in manifest.get("generated_data_deliverables", {}).items():
    p = Path(meta["path"])
    if not p.exists():
        missing.append((name, str(p)))
        print(f"MISSING: {name} at {p}")
    else:
        actual_hash = sha256_file(p)
        expected_hash = meta["sha256"]
        if actual_hash == expected_hash:
            matches.append((name, "data_deliverable"))
            print(f"MATCH: {name}")
        else:
            mismatches.append((name, "data_deliverable", expected_hash, actual_hash))
            print(f"MISMATCH: {name}\n  Expected: {expected_hash}\n  Actual:   {actual_hash}")

# Check generated documentation deliverables
print("\n=== Checking Generated Documentation Deliverables ===")
for name, meta in manifest.get("generated_documentation_deliverables", {}).items():
    p = Path(meta["path"])
    if not p.exists():
        missing.append((name, str(p)))
        print(f"MISSING: {name} at {p}")
    else:
        actual_hash = sha256_file(p)
        expected_hash = meta["sha256"]
        if actual_hash == expected_hash:
            matches.append((name, "doc_deliverable"))
            print(f"MATCH: {name}")
        else:
            mismatches.append((name, "doc_deliverable", expected_hash, actual_hash))
            print(f"MISMATCH: {name}\n  Expected: {expected_hash}\n  Actual:   {actual_hash}")

print(f"\nSummary: {len(matches)} matches, {len(mismatches)} mismatches, {len(missing)} missing.")
