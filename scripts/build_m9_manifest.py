import hashlib
import json
import os

def get_hash(path):
    if not os.path.exists(path):
        return "FILE_NOT_FOUND"
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

benchmarks = {
    "m3_final_dataset": {
        "path": "backend/data/dataset/final_verified_dataset.csv",
        "sha256": get_hash("backend/data/dataset/final_verified_dataset.csv")
    },
    "m6_expanded_benchmark_n60": {
        "path": "backend/data/dataset/m6_expanded_benchmark_n60.csv",
        "sha256": get_hash("backend/data/dataset/m6_expanded_benchmark_n60.csv")
    },
    "m6_qualification_ledger": {
        "path": "backend/data/dataset/m6_benchmark_qualification.csv",
        "sha256": get_hash("backend/data/dataset/m6_benchmark_qualification.csv")
    },
    "m6_phase3_negative_candidates": {
        "path": "backend/data/experiments/m6/m6_phase3_1_negative_benchmark_audit.csv",
        "sha256": get_hash("backend/data/experiments/m6/m6_phase3_1_negative_benchmark_audit.csv")
    }
}

artifacts = {
    "backend/data/experiments/m9/m9_evaluation_dataset.jsonl": get_hash("backend/data/experiments/m9/m9_evaluation_dataset.jsonl"),
    "backend/data/experiments/m9/m9_dataset_schema.json": get_hash("backend/data/experiments/m9/m9_dataset_schema.json"),
    "backend/data/experiments/m9/m9_human_review_template.csv": get_hash("backend/data/experiments/m9/m9_human_review_template.csv"),
    "backend/data/experiments/m9/language_detection_results.csv": get_hash("backend/data/experiments/m9/language_detection_results.csv"),
    "backend/data/experiments/m9/language_confusion_matrix.csv": get_hash("backend/data/experiments/m9/language_confusion_matrix.csv"),
    "backend/data/experiments/m9/query_normalization_results.csv": get_hash("backend/data/experiments/m9/query_normalization_results.csv"),
    "backend/data/experiments/m9/retrieval_metrics_by_language.csv": get_hash("backend/data/experiments/m9/retrieval_metrics_by_language.csv"),
    "backend/data/experiments/m9/cross_lingual_evidence_consistency.csv": get_hash("backend/data/experiments/m9/cross_lingual_evidence_consistency.csv"),
    "backend/data/experiments/m9/m9_ablation_results.csv": get_hash("backend/data/experiments/m9/m9_ablation_results.csv"),
    "backend/data/experiments/m9/m9_test_execution.log": get_hash("backend/data/experiments/m9/m9_test_execution.log"),
    "backend/data/experiments/m9/m9_test_results.xml": get_hash("backend/data/experiments/m9/m9_test_results.xml"),
    "backend/data/db/indicrag.db": get_hash("backend/data/db/indicrag.db"),
    "docs/m9_cross_lingual_architecture_audit.md": get_hash("docs/m9_cross_lingual_architecture_audit.md"),
    "docs/m9_dataset_design.md": get_hash("docs/m9_dataset_design.md"),
    "docs/m9_language_detection_analysis.md": get_hash("docs/m9_language_detection_analysis.md"),
    "docs/m9_retrieval_evaluation.md": get_hash("docs/m9_retrieval_evaluation.md"),
    "docs/m9_statistical_evaluation.md": get_hash("docs/m9_statistical_evaluation.md"),
    "docs/m9_error_analysis.md": get_hash("docs/m9_error_analysis.md"),
    "backend/data/experiments/m9/answer_generation_results.csv": get_hash("backend/data/experiments/m9/answer_generation_results.csv"),
    "backend/data/experiments/m9/claim_grounding_results.csv": get_hash("backend/data/experiments/m9/claim_grounding_results.csv"),
    "backend/data/experiments/m9/citation_quality_results.csv": get_hash("backend/data/experiments/m9/citation_quality_results.csv"),
    "docs/m9_answer_grounding_analysis.md": get_hash("docs/m9_answer_grounding_analysis.md"),
    "docs/m9_final_evaluation_report.md": get_hash("docs/m9_final_evaluation_report.md"),
}

manifest = {
    "milestone": "M9",
    "determination": "M9_EVALUATION_COMPLETED",
    "audit_timestamp": "2026-11-17T14:10:00+05:30",
    "auditor_role": "Senior Multilingual NLP Architect, Information Retrieval Specialist & Evaluation Auditor",
    "preflight_and_corpus_verification": {
        "official_documents": 7,
        "child_passages": 253,
        "parent_passages": 53,
        "total_db_passages": 306,
        "faiss_vector_count": 253,
        "faiss_dimensions": 384,
        "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "human_verified_benchmark_examples": 0,
        "benchmark_review_status": "PROVISIONAL_NOT_HUMAN_VERIFIED"
    },
    "frozen_benchmark_hashes": benchmarks,
    "test_suite_execution": {
        "total_collected": 257,
        "total_executed": 257,
        "passed": 257,
        "failed": 0,
        "skipped": 0,
        "pass_rate": 100.0,
        "duration_seconds": 303.52,
        "execution_log": "backend/data/experiments/m9/m9_test_execution.log",
        "junit_xml": "backend/data/experiments/m9/m9_test_results.xml"
    },
    "dataset_summary": {
        "semantic_intent_groups": 60,
        "total_queries": 240,
        "language_distribution": {
            "english": 60,
            "hindi_devanagari": 60,
            "romanized_hindi": 60,
            "hinglish": 60
        },
        "answerable_intents": 45,
        "unanswerable_intents": 15
    },
    "artifacts_sha256": artifacts
}

with open("backend/data/experiments/m9/m9_integrity_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print("Integrity manifest generated: backend/data/experiments/m9/m9_integrity_manifest.json")
