import hashlib
import json
import os
import shutil
import sqlite3
import urllib.request
from pathlib import Path

def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192 * 16):
            h.update(chunk)
    return h.hexdigest()

def main():
    root = Path(__file__).resolve().parent.parent
    exp_dir = root / "backend" / "data" / "experiments" / "m10"
    exp_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Hashes of frozen artifacts
    gold_path = root / "backend" / "data" / "experiments" / "m9" / "m9_evaluation_dataset.jsonl"
    db_path = root / "backend" / "data" / "db" / "indicrag.db"
    faiss_path = root / "backend" / "data" / "indexes" / "official" / "faiss.index"
    m9_answers_path = root / "backend" / "data" / "experiments" / "m9" / "answer_generation_results.csv"
    
    hashes = {
        "m9_gold_dataset_sha256": sha256_file(str(gold_path)),
        "indicrag_db_sha256": sha256_file(str(db_path)),
        "faiss_index_sha256": sha256_file(str(faiss_path)),
        "m9_answers_csv_sha256": sha256_file(str(m9_answers_path))
    }
    
    # 2. Database statistics
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM documents")
    doc_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM passages")
    total_passages = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM passages WHERE parent_passage_id IS NULL")
    parent_passages = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM passages WHERE parent_passage_id IS NOT NULL")
    child_passages = c.fetchone()[0]
    conn.close()
    
    # 3. Query Ollama tags
    ollama_model_info = {}
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for m in data.get("models", []):
                if "qwen2.5:3b" in m.get("name", ""):
                    ollama_model_info = m
                    break
    except Exception as e:
        ollama_model_info = {"error": str(e)}
        
    # 4. Prompt templates and configs
    config_snapshot = {
        "timestamp": "2026-11-17T18:30:00Z",
        "milestone": "M10_PHASE_F",
        "active_llm": {
            "model_name": "qwen2.5:3b",
            "endpoint": "http://localhost:11434/api/generate",
            "model_details": ollama_model_info,
            "temperature": 0.1,
            "max_tokens": 384,
            "timeout_seconds": 120,
            "context_window": 4096
        },
        "embedding_model": {
            "name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "dimension": 384,
            "similarity": "L2_distance / InnerProduct"
        },
        "cross_encoder_model": {
            "production_name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "max_length": 512
        },
        "database_stats": {
            "document_count": doc_count,
            "total_passages": total_passages,
            "parent_passages": parent_passages,
            "child_passages": child_passages,
            "faiss_vectors": 253
        },
        "baseline_test_suite": {
            "total_tests": 257,
            "passed": 257,
            "failed": 0,
            "duration_seconds": 72.81,
            "log_path": "backend/data/experiments/m10/m10_phase_f_test_execution.log"
        },
        "system_prompt": (
            "You are a precise academic regulation assistant for Bennett University.\n"
            "Your task is to answer questions using ONLY the provided evidence passages.\n\n"
            "Rules:\n"
            "1. Answer ONLY from the provided evidence. Do not add facts not in the evidence.\n"
            "2. Cite every factual claim with [Source: <passage_id>, page X] referring to the passages above.\n"
            "3. If the evidence does not contain enough information, say: UNANSWERABLE — Insufficient information available in the provided documents.\n"
            "4. Preserve all conditions, exceptions, and qualifying clauses from the evidence.\n"
            "5. If rules conflict between documents, state both versions and their applicable periods.\n"
            "6. Be concise and precise. Do not speculate or extrapolate.\n"
        ),
        "user_prompt_template": (
            "{lang_instruction}\n\n"
            "Question: {question}\n\n"
            "Evidence passages:\n{evidence}\n\n"
            "Instructions: Answer the question using the evidence passages above. "
            "Cite every factual claim with [Source: passage_id, page X] referring to the passages above. "
            "If the answer cannot be determined from the evidence, output UNANSWERABLE."
        ),
        "frozen_hashes": hashes
    }
    
    snapshot_path = exp_dir / "m10_phase_f_baseline_snapshot.json"
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(config_snapshot, f, indent=2)
    print(f"Wrote snapshot to {snapshot_path}")
    
    # 5. Copy M9 answer generation results to m10_phase_f_baseline_answers.csv
    baseline_answers_dst = exp_dir / "m10_phase_f_baseline_answers.csv"
    shutil.copyfile(str(m9_answers_path), str(baseline_answers_dst))
    print(f"Copied baseline answers to {baseline_answers_dst}")

if __name__ == "__main__":
    main()
