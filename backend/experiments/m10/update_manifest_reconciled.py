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
    root / "docs/m10_phase_h_final_reconciliation.md"
]

manifest["generated_documentation_deliverables"] = {
    doc.name: {
        "path": str(doc),
        "sha256": sha256_file(doc),
        "size_bytes": doc.stat().st_size
    } for doc in docs
}

manifest["reconciliation_audit"] = {
    "status": "COMPLETED",
    "determination": "M10_PHASE_H_VERIFIED_WITH_LIMITATIONS",
    "outcome_partition_verified": True,
    "retrieval_standardization_verified": True,
    "devanagari_traces_verified": True,
    "latency_definitions_verified": True,
    "claim_audit_methodology_documented": True
}

with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"Updated manifest with {len(docs)} documentation deliverables and reconciliation metadata.")
