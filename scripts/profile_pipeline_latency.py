"""
Profile every stage of the IndicRAG-QA pipeline and benchmark before/after latencies.
"""
import sys
import time
import json
import httpx
from pathlib import Path

sys.path.insert(0, 'backend')
from app.models.schemas import DocumentSource, QueryLanguage
from app.query.processor import process_query
from app.retrieval.engine import (
    get_official_index,
    get_embedding_model,
    get_cross_encoder,
    _rrf_fuse,
    rerank,
    expand_to_parents,
    retrieve,
)
from app.retrieval.evidence_controller import get_evidence_controller
from app.generation.claim_grounding import get_claim_grounding_verifier

def profile_stages():
    print("=" * 65)
    print("STAGE-BY-STAGE PIPELINE LATENCY PROFILING (LOCAL CPU)")
    print("=" * 65)

    test_q = "What is the minimum attendance requirement for undergraduate engineering students?"
    
    # 1. Query Processing & Language Detection
    t0 = time.perf_counter()
    qa = process_query(test_q)
    primary_query = qa.normalized_query or qa.original_query
    t_qp = (time.perf_counter() - t0) * 1000

    idx = get_official_index()

    # 2. BM25 Search
    t0 = time.perf_counter()
    bm25_res = idx.bm25_search(primary_query, top_k=10)
    t_bm25 = (time.perf_counter() - t0) * 1000

    # 3. Dense FAISS Search
    t0 = time.perf_counter()
    dense_res = idx.dense_search(primary_query, top_k=10)
    t_dense = (time.perf_counter() - t0) * 1000

    # 4. RRF Fusion
    t0 = time.perf_counter()
    fused = _rrf_fuse(bm25_res, dense_res)
    t_rrf = (time.perf_counter() - t0) * 1000

    # 5. Cross-Encoder Reranking
    candidates_with_text = []
    for pid, score, meta in fused:
        m = dict(meta)
        if "text" not in m:
            tidx = idx.passage_ids.index(pid)
            m["text"] = idx.passage_texts[tidx]
        candidates_with_text.append((pid, score, m))

    t0 = time.perf_counter()
    reranked = rerank(primary_query, candidates_with_text, top_k=10)
    t_rerank = (time.perf_counter() - t0) * 1000

    # 6. PDR Parent Expansion
    t0 = time.perf_counter()
    expanded = expand_to_parents(reranked, idx)
    t_pdr = (time.perf_counter() - t0) * 1000

    # 7. Evidence Controller
    res = retrieve(qa, [DocumentSource.OFFICIAL], use_reranker=True, use_pdr=True)
    ctrl = get_evidence_controller()
    t0 = time.perf_counter()
    dec = ctrl.evaluate(res)
    t_ctrl = (time.perf_counter() - t0) * 1000

    # 8. Claim Grounding
    cg = get_claim_grounding_verifier()
    sample_answer = "Students must maintain a minimum of 75% attendance in all courses."
    t0 = time.perf_counter()
    c_res = cg.verify_claims(sample_answer, res.retrieved_passages)
    t_cg = (time.perf_counter() - t0) * 1000

    # 9. Ollama Generation Call (via active server endpoint)
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=120.0)
    t0 = time.perf_counter()
    r = client.post("/query", json={"query": test_q, "collection": ["official"]})
    t_e2e = (time.perf_counter() - t0) * 1000
    d = r.json()
    rs = d.get("retrieval_summary", {})
    t_gen = rs.get("generation_latency_ms", t_e2e - t_rerank)

    print(f"1. Query Processing & Lang ID:     {t_qp:8.2f} ms")
    print(f"2. Lexical Retrieval (BM25):        {t_bm25:8.2f} ms")
    print(f"3. Dense Search (FAISS L2):         {t_dense:8.2f} ms")
    print(f"4. Reciprocal Rank Fusion (RRF):    {t_rrf:8.2f} ms")
    print(f"5. Cross-Encoder Reranker:          {t_rerank:8.2f} ms")
    print(f"6. PDR Parent Expansion:            {t_pdr:8.2f} ms")
    print(f"7. Six-State Evidence Controller:   {t_ctrl:8.2f} ms")
    print(f"8. Claim Grounding Verifier:        {t_cg:8.2f} ms")
    print(f"9. Local Ollama Generation:         {t_gen:8.2f} ms")
    print("-" * 65)
    print(f"Total End-to-End Latency:           {t_e2e:8.2f} ms ({(t_e2e/1000):.2f}s)")
    print("=" * 65)

    profile_data = {
        "query_processing_ms": round(t_qp, 2),
        "bm25_ms": round(t_bm25, 2),
        "dense_faiss_ms": round(t_dense, 2),
        "rrf_fusion_ms": round(t_rrf, 2),
        "cross_encoder_rerank_ms": round(t_rerank, 2),
        "pdr_expansion_ms": round(t_pdr, 2),
        "evidence_controller_ms": round(t_ctrl, 2),
        "claim_grounding_ms": round(t_cg, 2),
        "ollama_generation_ms": round(t_gen, 2),
        "total_e2e_ms": round(t_e2e, 2),
    }
    
    with open("backend/data/experiments/m7/m7_latency_profiling.json", "w") as f:
        json.dump(profile_data, f, indent=2)
    print("Saved profiling telemetry to backend/data/experiments/m7/m7_latency_profiling.json")

if __name__ == "__main__":
    profile_stages()
