"""
IndicRAG-QA — Application Entry Point.
Forwards to app.api.main:app for convenient uvicorn startup.
"""
from app.api.main import app

__all__ = ["app"]

