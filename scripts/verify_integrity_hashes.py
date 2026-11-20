import hashlib
import json
import os
import sqlite3
from pathlib import Path

root = Path(__file__).resolve().parent.parent

def sha256_file(filepath):
    if not os.path.exists(filepath):
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 16):
            h.update(chunk)
    return h.hexdigest()

def check_integrity():
    targets = {
        # Frozen datasets
        "m9_evaluation_dataset": root / "backend/data/experiments/m9/m9_evaluation_dataset.jsonl",
        "m9_integrity_manifest": root / "backend/data/experiments/m9/m9_integrity_manifest.json",
        "m8_test_log": root / "backend/data/experiments/m9/m9_test_execution.log",
        
        # Database & indexes
        "indicrag_db": root / "backend/data/db/indicrag.db",
        "faiss_index": root / "backend/data/indexes/official/faiss.index",
        
        # Phase E artifacts
        "phase_e_results_csv": root / "backend/data/experiments/m10/m10_phase_e_results.csv",
        "phase_e_per_intent_csv": root / "backend/data/experiments/m10/m10_phase_e_per_intent_results.csv",
        "phase_e_resource_csv": root / "backend/data/experiments/m10/m10_phase_e_resource_results.csv",
        "phase_e_report_md": root / "docs/m10_phase_e_experimental_report.md",
        
        # Phase F artifacts
        "phase_f_baseline_snapshot": root / "backend/data/experiments/m10/m10_phase_f_baseline_snapshot.json",
        "phase_f_baseline_answers": root / "backend/data/experiments/m10/m10_phase_f_baseline_answers.csv",
        "phase_f_routing_trace": root / "backend/data/experiments/m10/m10_phase_f_routing_trace.csv",
        "phase_f_e2e_results": root / "backend/data/experiments/m10/m10_phase_f_end_to_end_results.csv",
        "phase_f_answer_correctness": root / "backend/data/experiments/m10/m10_phase_f_answer_correctness.csv",
        "phase_f_claim_grounding": root / "backend/data/experiments/m10/m10_phase_f_claim_grounding.csv",
        "phase_f_citation_audit": root / "backend/data/experiments/m10/m10_phase_f_citation_audit.csv",
        "phase_f_language_quality": root / "backend/data/experiments/m10/m10_phase_f_language_quality.csv",
        "phase_f_resource_results": root / "backend/data/experiments/m10/m10_phase_f_resource_results.csv",
        "phase_f_integrity_manifest": root / "backend/data/experiments/m10/m10_phase_f_integrity_manifest.json",
        "phase_f_test_log": root / "backend/data/experiments/m10/m10_phase_f_test_execution.log",
        
        # Phase F reports
        "phase_f_baseline_audit_md": root / "docs/m10_phase_f_baseline_audit.md",
        "phase_f_regulatory_audit_md": root / "docs/m10_phase_f_regulatory_applicability_audit.md",
        "phase_f_abstention_safety_md": root / "docs/m10_phase_f_abstention_safety_analysis.md",
        "phase_f_statistical_comparison_md": root / "docs/m10_phase_f_statistical_comparison.md",
        "phase_f_final_report_md": root / "docs/m10_phase_f_final_evaluation_report.md",
    }
    
    hashes = {}
    print("--- COMPUTED SHA-256 HASHES ---")
    for name, path in targets.items():
        h = sha256_file(str(path))
        hashes[name] = h
        print(f"{name:<35}: {h}")
        
    # Check DB stats
    conn = sqlite3.connect(str(root / "backend/data/db/indicrag.db"))
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM documents")
    docs = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM passages")
    passages = c.fetchone()[0]
    conn.close()
    print(f"\nCorpus Database: Documents={docs}, Passages={passages}")

    # Check manifest match
    with open(root / "backend/data/experiments/m10/m10_phase_f_integrity_manifest.json", "r") as f:
        m = json.load(f)
    print("\nIntegrity Manifest Stored Hashes vs Computed:")
    manifest_hashes = m.get("file_hashes", {})
    match_all = True
    for key, path_key in [
        ("m10_phase_f_end_to_end_results_csv", "phase_f_e2e_results"),
        ("m10_phase_f_answer_correctness_csv", "phase_f_answer_correctness"),
        ("m10_phase_f_claim_grounding_csv", "phase_f_claim_grounding"),
        ("m10_phase_f_citation_audit_csv", "phase_f_citation_audit"),
        ("m10_phase_f_language_quality_csv", "phase_f_language_quality"),
        ("m10_phase_f_resource_results_csv", "phase_f_resource_results"),
        ("m10_phase_f_routing_trace_csv", "phase_f_routing_trace"),
        ("m10_phase_f_baseline_answers_csv", "phase_f_baseline_answers"),
        ("m10_phase_f_baseline_snapshot_json", "phase_f_baseline_snapshot"),
        ("m10_phase_f_test_execution_log", "phase_f_test_log"),
    ]:
        stored = manifest_hashes.get(key)
        computed = hashes.get(path_key)
        match = (stored == computed)
        print(f"  {key:<40}: Stored={stored[:12]}... Computed={computed[:12]}... Match={match}")
        if not match:
            match_all = False
            
    print(f"\nManifest verification result: {'ALL MATCH' if match_all else 'MISMATCH FOUND'}")
    return hashes

if __name__ == "__main__":
    check_integrity()
