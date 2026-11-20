"""
IndicRAG-QA — Central Configuration
All paths and tunable settings come from environment variables (with safe defaults).
Never hard-code secrets or absolute paths here.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    app_name: str = "IndicRAG-QA"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "production", "test"] = "development"

    # ── Paths ──────────────────────────────────────────────────────────────────
    # All paths are anchored to the backend/ directory regardless of the
    # working directory from which the application is started.
    # Override any path via the corresponding environment variable.
    _BACKEND_DIR: Path = Path(__file__).resolve().parent.parent.parent

    data_dir: Path = _BACKEND_DIR / "data"
    official_docs_dir: Path = _BACKEND_DIR / "data" / "official"
    uploads_dir: Path = _BACKEND_DIR / "data" / "uploads"
    indexes_dir: Path = _BACKEND_DIR / "data" / "indexes"
    dataset_dir: Path = _BACKEND_DIR / "data" / "dataset"
    db_dir: Path = _BACKEND_DIR / "data" / "db"
    db_path: Path = _BACKEND_DIR / "data" / "db" / "indicrag.db"

    # ── Ollama / LLM ───────────────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma:2b"          # fallback; override via .env
    ollama_timeout: int = 180               # seconds
    generation_temperature: float = 0.1
    generation_max_tokens: int = 1024

    # ── Embedding model ────────────────────────────────────────────────────────
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_batch_size: int = 32
    embedding_dim: int = 384

    # ── Retrieval ──────────────────────────────────────────────────────────────
    retrieval_top_k: int = 10
    rerank_top_k: int = 5
    bm25_weight: float = 0.4
    dense_weight: float = 0.6
    rrf_k: int = 60                         # RRF constant

    # Evidence thresholds (calibrate on validation set, never test set)
    evidence_min_score: float = 0.35
    evidence_sufficient_count: int = 1

    # Retrieval retry budget
    max_retrieval_retries: int = 2

    # ── Chunking ───────────────────────────────────────────────────────────────
    chunk_size_tokens: int = 400
    chunk_overlap_tokens: int = 80
    parent_chunk_size_tokens: int = 1200

    # ── Upload limits ──────────────────────────────────────────────────────────
    max_upload_size_mb: int = 50
    allowed_upload_extensions: list[str] = [".pdf"]
    pdf_backend: str = "pypdf"              # Pure-Python table & relationship extraction

    # ── CORS ───────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── Evaluation / Admin ─────────────────────────────────────────────────────
    eval_api_key: str = "change-me-in-env"   # protect evaluation endpoints


# Singleton
settings = Settings()

# Ensure all data directories exist at import time
for _attr in ("data_dir", "official_docs_dir", "uploads_dir",
              "indexes_dir", "dataset_dir", "db_dir"):
    getattr(settings, _attr).mkdir(parents=True, exist_ok=True)
