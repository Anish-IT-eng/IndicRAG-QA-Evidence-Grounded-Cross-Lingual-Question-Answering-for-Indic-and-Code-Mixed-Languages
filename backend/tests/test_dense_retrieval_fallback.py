"""
Tests for optional FAISS backend and NumPy cosine-similarity dense retrieval fallback.
Verifies:
1. FAISS available retrieval functionality.
2. NumPy fallback retrieval when FAISS is unavailable or force-disabled.
3. Equivalence of FAISS and NumPy ranking scores up to float tolerance.
4. RRF hybrid fusion under NumPy fallback.
5. Edge cases: empty index, dimension mismatch, missing embeddings.
6. Tenant/user isolation under NumPy fallback.
"""
import pytest
import numpy as np

from app.retrieval.engine import (
    RetrieverIndex,
    is_faiss_available,
    set_faiss_force_disabled,
    get_official_index,
    _rrf_fuse,
)


@pytest.fixture(autouse=True)
def reset_faiss_override():
    """Ensure FAISS force-disabled state is always reset after each test."""
    yield
    set_faiss_force_disabled(None)


def test_is_faiss_available_toggle():
    """Verify is_faiss_available reflects the force-disabled override."""
    set_faiss_force_disabled(True)
    assert is_faiss_available() is False

    set_faiss_force_disabled(False)
    # If FAISS is installed, it returns True; if not installed, False
    # Regardless, it reflects the environment cleanly without error
    set_faiss_force_disabled(None)


def test_dense_search_with_numpy_fallback():
    """When FAISS is disabled, dense_search seamlessly executes via NumPy cosine similarity."""
    set_faiss_force_disabled(True)
    idx = get_official_index()
    assert idx.is_ready() is True

    query = "What are the options for final semester internship or startup?"
    hits = idx.dense_search(query, top_k=5)
    assert len(hits) == 5

    scores = [score for pid, score, meta in hits]
    assert all(-1.0 <= s <= 1.0 for s in scores)
    assert scores == sorted(scores, reverse=True)

    pids = [pid for pid, score, meta in hits]
    # Gold passage for final semester options
    assert "1731cce9-583a-44b6-a7e4-e4dda7776056" in pids


def test_faiss_and_numpy_ranking_equivalence():
    """Verify FAISS and NumPy produce identical top-k passage rankings and scores."""
    idx = get_official_index()
    query = "attendance relaxation medical certificate"

    # Search with FAISS (if available)
    set_faiss_force_disabled(False)
    if is_faiss_available():
        hits_faiss = idx.dense_search(query, top_k=5)

        # Search with NumPy fallback
        set_faiss_force_disabled(True)
        hits_numpy = idx.dense_search(query, top_k=5)

        assert len(hits_faiss) == len(hits_numpy)
        pids_faiss = [h[0] for h in hits_faiss]
        pids_numpy = [h[0] for h in hits_numpy]
        assert pids_faiss == pids_numpy

        # Cosine scores should be nearly identical (within float32 precision)
        scores_faiss = [h[1] for h in hits_faiss]
        scores_numpy = [h[1] for h in hits_numpy]
        for sf, sn in zip(scores_faiss, scores_numpy):
            assert abs(sf - sn) < 1e-4


def test_hybrid_rrf_with_numpy_fallback():
    """Hybrid RRF fusion functions correctly when dense retrieval runs via NumPy."""
    set_faiss_force_disabled(True)
    idx = get_official_index()
    query = "B.Tech minimum duration"

    bm25_hits = idx.bm25_search(query, top_k=10)
    dense_hits = idx.dense_search(query, top_k=10)

    assert len(dense_hits) > 0
    assert len(bm25_hits) > 0

    fused = _rrf_fuse(bm25_hits, dense_hits, k=60, bm25_weight=1.0, dense_weight=1.0)
    assert len(fused) > 0

    fused_scores = [score for pid, score, meta in fused]
    assert fused_scores == sorted(fused_scores, reverse=True)


def test_empty_index_handling(tmp_path):
    """Empty index returns empty results without crashing."""
    set_faiss_force_disabled(True)
    empty_idx = RetrieverIndex("empty_test")
    empty_idx.index_dir = tmp_path

    assert empty_idx.is_ready() is False
    assert empty_idx.dense_search("test query", top_k=5) == []


def test_dimension_mismatch_handling(tmp_path):
    """Dimension mismatch between query embeddings and indexed embeddings is safely caught."""
    set_faiss_force_disabled(True)
    idx = RetrieverIndex("dim_mismatch_test")
    idx.index_dir = tmp_path
    idx.passage_ids = ["p1", "p2"]
    idx.passage_texts = ["text one", "text two"]
    idx.passage_meta = [{}, {}]
    # Set wrong dimension (e.g. 128 instead of 384)
    idx.embeddings = np.random.randn(2, 128).astype(np.float32)

    hits = idx.dense_search("query text", top_k=5)
    assert hits == []


def test_numpy_fallback_tenant_isolation(tmp_path):
    """NumPy fallback preserves multi-tenant user isolation."""
    set_faiss_force_disabled(True)
    idx = RetrieverIndex("tenant_numpy_test")
    idx.index_dir = tmp_path
    idx.passage_ids = ["p_alice", "p_bob", "p_shared"]
    idx.passage_texts = ["python code", "java code", "general university rules"]
    idx.passage_meta = [
        {"user_id": "alice"},
        {"user_id": "bob"},
        {"user_id": None},
    ]
    # Synthetic normalized embeddings
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=np.float32)
    # Replicate dimension to match embedding model (384)
    full_embeddings = np.zeros((3, 384), dtype=np.float32)
    full_embeddings[:, :3] = embeddings
    idx.embeddings = full_embeddings

    # Query with alice
    hits_alice = idx.dense_search("rules", top_k=10, user_id="alice")
    pids_alice = [h[0] for h in hits_alice]
    assert "p_alice" in pids_alice
    assert "p_shared" in pids_alice
    assert "p_bob" not in pids_alice

    # Query with bob
    hits_bob = idx.dense_search("rules", top_k=10, user_id="bob")
    pids_bob = [h[0] for h in hits_bob]
    assert "p_bob" in pids_bob
    assert "p_shared" in pids_bob
    assert "p_alice" not in pids_bob
