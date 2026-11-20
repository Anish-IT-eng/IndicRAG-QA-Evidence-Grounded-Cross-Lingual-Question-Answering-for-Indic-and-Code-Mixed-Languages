"""Structured logging setup for IndicRAG-QA."""
import logging
import sys


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "sentence_transformers", "faiss"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


logger = logging.getLogger("indicrag")
