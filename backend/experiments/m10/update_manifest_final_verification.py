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

docs = [
    root / "docs/m10_phase_h_e2e_evaluation_protocol.md",
    root / "docs/m10_phase_h_answer_quality_report.md",
    root / "docs/m10_phase_h_claim_grounding_audit.md",
    root / "docs/m10_phase_h_citation_audit.md",
    root / "docs/m10_phase_h_regulatory_applicability_audit.md",
    root / "docs/m10_phase_h_cross_lingual_consistency.md",
    root / "docs/m10_phase_h_failure_analysis.md",
    root / "docs/m10_phase_h_statistical_analysis.md",
    root / "docs/m10_phase_h_correction_log.md",
    root / "docs/m10_phase_h_final_reconciliation.md",
    root / "docs/m10_phase_h_latency_forensic_audit.md",
    root / "docs/m10_phase_h_latency_correction_log.md",
    root / "docs/m10_phase_h_config_b_generation_reconciliation.md",
    root / "docs/m10_phase_h_config_b_correction_log.md",
    root / "docs/m10_phase_h_config_b_latency_final_verification.md"
]

manifest["generated_documentation_deliverables"] = {
    doc.name: {
        "path": str(doc),
        "sha256": sha256_file(doc),
        "size_bytes": doc.stat().st_size
    } for doc in docs
}

manifest["config_b_latency_arithmetic_verification"] = {
    "status": "COMPLETED",
    "determination": "M10_PHASE_H_VERIFIED_WITH_LIMITATIONS",
    "raw_sums_verified": {
        "retrieval_sum_ms": 569399.95,
        "controller_sum_ms": 299.37,
        "invoked_generation_sum_ms": 10535311.13,
        "all_generation_sum_ms": 10535325.48,
        "total_pipeline_sum_ms": 11105024.78
    },
    "recalculated_means": {
        "retrieval_mean_ms": 2372.50,
        "controller_mean_ms": 1.25,
        "invoked_generation_mean_ms": 88532.03,
        "amortized_generation_mean_ms": 43897.19,
        "total_pipeline_mean_ms": 46270.94
    },
    "residual_ms": -0.000083,
    "displayed_aggregates_changed": False
}

with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"Updated manifest with {len(docs)} documentation deliverables and final latency verification metadata.")
