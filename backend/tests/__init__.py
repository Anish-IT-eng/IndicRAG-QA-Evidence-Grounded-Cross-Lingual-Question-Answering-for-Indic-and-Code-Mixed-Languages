"""
Test suite for IndicRAG-QA backend.

Run:  cd backend && pytest tests/ -v

Tests are organized by module:
- test_query_processor: language detection, normalization, decomposition
- test_metrics: all evaluation metric functions
- test_database: schema and CRUD operations
- test_api: FastAPI endpoint integration tests (uses TestClient)
- test_evidence_controller: evidence decision logic

Tests use a temporary SQLite database and in-memory indexes.
They never touch the official document store or production indexes.
"""
