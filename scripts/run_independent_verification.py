"""
Run Independent Model Verification and Deterministic Validation over QA candidates.

Usage:
    python scripts/run_independent_verification.py --file human_review_pilot_82.csv
    python scripts/run_independent_verification.py --file human_review_pilot_82.csv --deterministic-only
    python scripts/run_independent_verification.py --model-a qwen2.5:3b --model-b llama3.2:3b

Outputs:
    - backend/data/dataset/auto_validation_results.csv
    - backend/data/dataset/auto_validation_audit.jsonl
    - docs/m3_independent_verification_report.md
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

try:
    import pyarrow.dataset as _pds
    if not hasattr(_pds, "ParquetFragmentScanOptions"):
        _pds.ParquetFragmentScanOptions = type("ParquetFragmentScanOptions", (), {})
except ImportError:
    pass

from app.core.database import init_db
from app.core.logging_config import setup_logging, logger
from app.evaluation.model_verifier import (
    IndependentModelVerifier,
    IndependentVerificationPipeline,
)


def main():
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Run Independent Model Verification and Deterministic Validation on QA candidates."
    )
    parser.add_argument(
        "--file", default="human_review_pilot_82.csv",
        help="Input candidate CSV (filename in backend/data/dataset/ or absolute path)."
    )
    parser.add_argument(
        "--model-a", default="qwen2.5:3b",
        help="Ollama model for Verifier A (default: qwen2.5:3b)."
    )
    parser.add_argument(
        "--family-a", default="qwen",
        help="Model family for Verifier A (default: qwen)."
    )
    parser.add_argument(
        "--model-b", default="llama3.2:3b",
        help="Ollama model for Verifier B (default: llama3.2:3b)."
    )
    parser.add_argument(
        "--family-b", default="llama",
        help="Model family for Verifier B (default: llama)."
    )
    parser.add_argument(
        "--deterministic-only", action="store_true",
        help="Run deterministic validation checks only without calling LLMs."
    )
    parser.add_argument(
        "--output-csv", default=None,
        help="Destination path for validation CSV."
    )
    parser.add_argument(
        "--output-jsonl", default=None,
        help="Destination path for audit JSONL log."
    )
    parser.add_argument(
        "--output-report", default=None,
        help="Destination path for markdown summary report."
    )

    args = parser.parse_args()

    # Resolve paths
    csv_path = Path(args.file)
    if not csv_path.is_absolute():
        csv_path = REPO_ROOT / "backend" / "data" / "dataset" / args.file
    if not csv_path.exists():
        print(f"ERROR: Input file not found: {csv_path}")
        sys.exit(1)

    out_csv = Path(args.output_csv) if args.output_csv else (
        REPO_ROOT / "backend" / "data" / "dataset" / "auto_validation_results.csv"
    )
    out_jsonl = Path(args.output_jsonl) if args.output_jsonl else (
        REPO_ROOT / "backend" / "data" / "dataset" / "auto_validation_audit.jsonl"
    )
    out_report = Path(args.output_report) if args.output_report else (
        REPO_ROOT / "docs" / "m3_independent_verification_report.md"
    )

    init_db()

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        candidates = list(reader)

    print(f"\nLoaded {len(candidates)} candidates from {csv_path.name}")
    print(f"Verifier A: {args.model_a} ({args.family_a})")
    print(f"Verifier B: {args.model_b} ({args.family_b})")
    print(f"Deterministic only: {args.deterministic_only}\n")

    if args.deterministic_only:
        # Dummy callers for deterministic mode
        verifier_a = IndependentModelVerifier(
            model_name="deterministic_only",
            model_family="none",
            custom_caller=lambda p, s: '{"verdict": "UNCERTAIN", "explanation": "deterministic-only mode"}'
        )
        verifier_b = IndependentModelVerifier(
            model_name="deterministic_only",
            model_family="none",
            custom_caller=lambda p, s: '{"verdict": "UNCERTAIN", "explanation": "deterministic-only mode"}'
        )
    else:
        verifier_a = IndependentModelVerifier(
            model_name=args.model_a,
            model_family=args.family_a,
        )
        verifier_b = IndependentModelVerifier(
            model_name=args.model_b,
            model_family=args.family_b,
        )

    pipeline = IndependentVerificationPipeline(
        verifier_a=verifier_a,
        verifier_b=verifier_b,
    )

    results = pipeline.run_pipeline(
        candidates,
        skip_llm_if_deterministic_reject=True,
    )

    # Export outputs
    pipeline.export_results_csv(results, out_csv)
    pipeline.export_audit_jsonl(results, out_jsonl)
    report_text = pipeline.generate_summary_report(
        results,
        model_a_name=args.model_a,
        model_b_name=args.model_b,
        output_path=out_report,
    )

    print(report_text)
    print("\nVerification pipeline execution finished successfully.")
    print(f"CSV results: {out_csv}")
    print(f"Audit JSONL: {out_jsonl}")
    print(f"Summary Report: {out_report}")


if __name__ == "__main__":
    main()

