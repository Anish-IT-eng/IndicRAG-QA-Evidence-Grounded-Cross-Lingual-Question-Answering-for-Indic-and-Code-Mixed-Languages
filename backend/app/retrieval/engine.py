"""
Hybrid retrieval engine: BM25 + Dense (FAISS) + RRF fusion.

Features implemented:
- BM25 lexical retrieval via rank_bm25
- Dense retrieval via FAISS (flat L2 index)
- Reciprocal Rank Fusion (RRF)
- Multi-Query Retrieval (MQR) — enabled selectively
- Parent Document Retrieval (PDR) — expands child hits to parent contexts
- Cross-encoder reranking via sentence-transformers CrossEncoder
- Candidate deduplication
- Metadata-based filtering (source type, version validity)
- Retrieval retry with alternative queries
"""
from __future__ import annotations

import json
import os
import pickle
import re
import time
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging_config import logger
from app.models.schemas import (
    DocumentSource,
    DocumentVersionInfo,
    QueryAnalysis,
    QueryLanguage,
    QueryScript,
    RetrievedPassage,
    RetrievalResult,
    TemporalIntentMode,
)
from app.retrieval.regulatory_classifier import classify_passage_condition

# ─── Lazy-loaded singletons ────────────────────────────────────────────────────

_embedding_model: Optional[SentenceTransformer] = None
_cross_encoder = None           # loaded only if available


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _embedding_model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded.")
    return _embedding_model


def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        try:
            from sentence_transformers import CrossEncoder
            _cross_encoder = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
                max_length=512,
            )
            logger.info("Cross-encoder reranker loaded.")
        except Exception as exc:
            logger.warning("Cross-encoder unavailable (%s). Skipping reranker.", exc)
            _cross_encoder = False
    return _cross_encoder if _cross_encoder else None


# ─── Index management ──────────────────────────────────────────────────────────

class RetrieverIndex:
    """
    Holds BM25 and FAISS indexes for one corpus slice
    (official or uploaded documents).
    """

    def __init__(self, index_name: str):
        self.index_name = index_name
        self.index_dir = settings.indexes_dir / index_name
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.passage_ids: list[str] = []
        self.passage_texts: list[str] = []
        self.passage_meta: list[dict] = []   # per-passage metadata

        self.bm25: Optional[BM25Okapi] = None
        self.faiss_index: Optional[faiss.IndexFlatL2] = None
        self._dirty = True

    # ── Build / update ─────────────────────────────────────────────────────────

    def add_passages(
        self,
        passage_ids: list[str],
        texts: list[str],
        meta: list[dict],
    ) -> None:
        """Add passages to in-memory store. Call build() after all passages added."""
        self.passage_ids.extend(passage_ids)
        self.passage_texts.extend(texts)
        self.passage_meta.extend(meta)
        self._dirty = True

    def remove_document_passages(self, document_id: str) -> None:
        """Remove passages belonging to document_id before re-indexing."""
        keep_indices = [
            i for i, m in enumerate(self.passage_meta)
            if m.get("document_id") != document_id
        ]
        if len(keep_indices) < len(self.passage_ids):
            self.passage_ids = [self.passage_ids[i] for i in keep_indices]
            self.passage_texts = [self.passage_texts[i] for i in keep_indices]
            self.passage_meta = [self.passage_meta[i] for i in keep_indices]
            self._dirty = True

    def build(self) -> None:
        """Build BM25 and FAISS indexes from current passage store."""
        if not self.passage_texts:
            logger.warning("No passages to index for %s.", self.index_name)
            return

        logger.info("Building BM25 index (%d passages)…", len(self.passage_texts))
        tokenized = [t.lower().split() for t in self.passage_texts]
        self.bm25 = BM25Okapi(tokenized)

        logger.info("Building FAISS index…")
        model = get_embedding_model()
        embeddings = model.encode(
            self.passage_texts,
            batch_size=settings.embedding_batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        embeddings = np.array(embeddings, dtype="float32")
        self.faiss_index = faiss.IndexFlatIP(embeddings.shape[1])  # inner-product (cosine after norm)
        self.faiss_index.add(embeddings)

        self._dirty = False
        logger.info("Indexes built for %s.", self.index_name)
        self.save()

    def save(self) -> None:
        idx_path = self.index_dir / "faiss.index"
        meta_path = self.index_dir / "meta.pkl"
        if self.faiss_index:
            faiss.write_index(self.faiss_index, str(idx_path))
        with open(meta_path, "wb") as f:
            pickle.dump({
                "passage_ids": self.passage_ids,
                "passage_texts": self.passage_texts,
                "passage_meta": self.passage_meta,
            }, f)
        logger.debug("Index saved to %s.", self.index_dir)

    def load(self) -> bool:
        idx_path = self.index_dir / "faiss.index"
        meta_path = self.index_dir / "meta.pkl"
        if not idx_path.exists() or not meta_path.exists():
            return False
        try:
            self.faiss_index = faiss.read_index(str(idx_path))
            with open(meta_path, "rb") as f:
                data = pickle.load(f)
            self.passage_ids = data["passage_ids"]
            self.passage_texts = data["passage_texts"]
            self.passage_meta = data["passage_meta"]
            # Rebuild BM25 (not serialisable)
            tokenized = [t.lower().split() for t in self.passage_texts]
            self.bm25 = BM25Okapi(tokenized)
            self._dirty = False
            logger.info("Loaded index %s (%d passages).", self.index_name, len(self.passage_ids))
            return True
        except Exception as exc:
            logger.error("Failed to load index %s: %s", self.index_name, exc)
            return False

    def is_ready(self) -> bool:
        return bool(self.passage_ids) and self.bm25 is not None and self.faiss_index is not None

    # ── Search ─────────────────────────────────────────────────────────────────

    def bm25_search(self, query: str, top_k: int, user_id: Optional[str] = None) -> list[tuple[str, float, dict]]:
        """Returns list of (passage_id, score, meta), optionally filtered by user_id."""
        if not self.bm25:
            return []
        tokens = re.findall(r"[\w\-]+", query.lower())
        if not tokens:
            tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)
        top_indices = np.argsort(scores)[::-1][:top_k * 4 if user_id else top_k]
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                meta = self.passage_meta[idx]
                if user_id and meta.get("user_id") != user_id:
                    continue
                results.append((self.passage_ids[idx], float(scores[idx]), meta))
                if len(results) >= top_k:
                    break
        return results

    def dense_search(self, query: str, top_k: int, user_id: Optional[str] = None) -> list[tuple[str, float, dict]]:
        """Returns list of (passage_id, score, meta), optionally filtered by user_id."""
        if self.faiss_index is None:
            return []
        model = get_embedding_model()
        q_emb = model.encode([query], normalize_embeddings=True)
        q_emb = np.array(q_emb, dtype="float32")
        scores, indices = self.faiss_index.search(q_emb, top_k * 4 if user_id else top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            meta = self.passage_meta[idx]
            if user_id and meta.get("user_id") != user_id:
                continue
            results.append((self.passage_ids[idx], float(score), meta))
            if len(results) >= top_k:
                break
        return results


# ─── Index registry ────────────────────────────────────────────────────────────

_indexes: dict[str, RetrieverIndex] = {}


def get_index(name: str) -> RetrieverIndex:
    if name not in _indexes:
        idx = RetrieverIndex(name)
        if not idx.load():
            logger.info("No saved index found for %s; starting empty.", name)
        _indexes[name] = idx
    return _indexes[name]


def get_official_index() -> RetrieverIndex:
    return get_index("official")


def get_upload_index() -> RetrieverIndex:
    return get_index("upload")


# ─── RRF fusion ────────────────────────────────────────────────────────────────

def _rrf_fuse(
    bm25_results: list[tuple[str, float, dict]],
    dense_results: list[tuple[str, float, dict]],
    k: int = settings.rrf_k,
    bm25_weight: float = settings.bm25_weight,
    dense_weight: float = settings.dense_weight,
) -> list[tuple[str, float, dict]]:
    """
    Reciprocal Rank Fusion of two ranked lists.
    Returns merged list sorted by RRF score descending.
    """
    scores: dict[str, float] = {}
    meta_map: dict[str, dict] = {}

    for rank, (pid, _, meta) in enumerate(bm25_results):
        scores[pid] = scores.get(pid, 0.0) + bm25_weight / (k + rank + 1)
        meta_map[pid] = meta

    for rank, (pid, _, meta) in enumerate(dense_results):
        scores[pid] = scores.get(pid, 0.0) + dense_weight / (k + rank + 1)
        meta_map[pid] = meta

    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(pid, score, meta_map[pid]) for pid, score in fused]


# ─── Deduplication ────────────────────────────────────────────────────────────

def _deduplicate(results: list[tuple[str, float, dict]]) -> list[tuple[str, float, dict]]:
    seen: set[str] = set()
    out = []
    for pid, score, meta in results:
        if pid not in seen:
            seen.add(pid)
            out.append((pid, score, meta))
    return out


# ─── Reranking ────────────────────────────────────────────────────────────────

def rerank(
    query: str,
    candidates: list[tuple[str, float, dict]],
    top_k: int = settings.rerank_top_k,
) -> list[tuple[str, float, dict]]:
    """Cross-encoder reranking. Falls back to original order on failure."""
    cross_enc = get_cross_encoder()
    if cross_enc is None or not candidates:
        return candidates[:top_k]
    try:
        pairs = [(query, meta.get("text", "")) for _, _, meta in candidates]
        rerank_scores = cross_enc.predict(pairs)
        ranked = sorted(
            zip(candidates, rerank_scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return [(pid, float(rs), meta) for (pid, _, meta), rs in ranked[:top_k]]
    except Exception as exc:
        logger.warning("Reranker failed (%s); using original order.", exc)
        return candidates[:top_k]


# ─── PDR: parent expansion ────────────────────────────────────────────────────

def expand_to_parents(
    candidates: list[tuple[str, float, dict]],
    index: RetrieverIndex,
) -> list[tuple[str, float, dict]]:
    """
    For each child passage hit, if a parent_passage_id is set,
    also return the parent passage (for richer generation context).
    Child citations are preserved exactly; parents are auxiliary.
    """
    expanded: list[tuple[str, float, dict]] = list(candidates)
    child_pids = {pid for pid, _, _ in candidates}

    for pid, score, meta in candidates:
        parent_id = meta.get("parent_passage_id")
        if parent_id and parent_id not in child_pids:
            # Find parent in index
            try:
                pidx = index.passage_ids.index(parent_id)
                parent_meta = dict(index.passage_meta[pidx])
                parent_meta["_is_pdr_expanded"] = True
                expanded.append((parent_id, score * 0.9, parent_meta))
                child_pids.add(parent_id)
            except ValueError:
                pass  # parent not in index (different slice)

    return expanded


def expand_with_relationships(
    candidates: list[tuple[str, float, dict]],
    user_id: Optional[str] = None,
    max_expanded: int = 5,
    decay_factor: float = 0.85,
) -> list[tuple[str, float, dict]]:
    """
    R3 Generic Relationship Expansion:
    Given top reranked candidates, traverses the relationship graph in SQLite to fetch
    related evidence (clauses, exceptions, rules, dates, tables) with strict tenant isolation.
    Decays score by decay_factor and tags provenance.
    """
    if not candidates:
        return []

    try:
        from app.retrieval.relationship_store import RelationshipStore

        seed_candidates = [
            {
                "passage_id": pid,
                "document_id": meta.get("document_id"),
                "page_number": meta.get("page_number"),
                "heading": meta.get("heading"),
                "section": meta.get("section"),
            }
            for pid, score, meta in candidates
        ]
        score_by_pid = {pid: score for pid, score, meta in candidates}

        expanded_passages = RelationshipStore.get_relationship_expanded_passages(
            seed_candidates=seed_candidates,
            user_id=user_id,
            max_expanded=max_expanded,
        )

        results: list[tuple[str, float, dict]] = []
        for ep in expanded_passages:
            pid = ep["passage_id"]
            source_seed_pid = ep.get("relationship_info", {}).get("source_seed_pid")
            base_score = score_by_pid.get(source_seed_pid, candidates[0][1] if candidates else 0.5)
            conf = ep.get("confidence", 0.90)
            exp_score = float(base_score) * float(conf) * decay_factor

            meta = dict(ep.get("metadata", {}))
            meta["text"] = ep["text"]
            meta["document_id"] = ep["document_id"]
            meta["filename"] = ep["document_filename"]
            meta["document_filename"] = ep["document_filename"]
            meta["page_number"] = ep["page_number"]
            meta["section"] = ep["section"]
            meta["heading"] = ep["heading"]
            meta["source_type"] = ep["source_type"]
            meta["relationship_expansion"] = ep["relationship_info"]
            meta["_is_relationship_expanded"] = True

            results.append((pid, exp_score, meta))

        return results
    except Exception as exc:
        logger.warning("Relationship expansion failed, returning original candidates: %s", exc)
        return []


# ─── Version validation ───────────────────────────────────────────────────────

def validate_versions(
    candidates: list[tuple[str, float, dict]],
    academic_year: Optional[str] = None,
    program: Optional[str] = None,
    query_analysis: Optional[QueryAnalysis] = None,
) -> list[tuple[str, float, dict]]:
    """
    Filter or flag passages based on version and applicability metadata.
    Superseded or mismatched passages are demoted but not silently dropped
    to support conflict detection, historical retrieval, and consensus verification.
    """
    valid, superseded, mismatched, others = [], [], [], []

    # Extract temporal constraints from query_analysis if available
    temporal_mode = getattr(query_analysis, "temporal_intent_mode", TemporalIntentMode.UNANCHORED) if query_analysis else TemporalIntentMode.UNANCHORED
    target_cohort = getattr(query_analysis, "target_cohort", None) if query_analysis else None
    target_ay = academic_year or (getattr(query_analysis, "target_academic_year", None) if query_analysis else None)

    for pid, score, meta in candidates:
        sup = meta.get("superseded_by")
        is_current = meta.get("is_current")
        pass_ay = str(meta.get("academic_year") or "")
        doc_id = str(meta.get("document_id") or "")

        # Check explicit academic year match if specified
        ay_mismatch = False
        if target_ay and pass_ay:
            # Match substring or 'onwards' scope (e.g. '2022-23' in '2022-23 onwards')
            if target_ay not in pass_ay and "onwards" not in pass_ay:
                ay_mismatch = True

        # Check if query explicitly asks for historical rules
        if temporal_mode == TemporalIntentMode.EXPLICIT_HISTORICAL:
            is_matching_historical = False
            if target_cohort and target_cohort in pass_ay:
                is_matching_historical = True
            elif target_cohort and ("2017" in target_cohort or "2018" in target_cohort) and ("2017" in doc_id or "2017" in pass_ay or "seas" in doc_id.lower()):
                is_matching_historical = True

            if is_matching_historical:
                # Historical passage matches user query intent! Keep full score, mark as valid!
                valid.append((pid, score, {**meta, "_version_flag": None}))
                continue
            elif is_current is True:
                # Newer active document retrieved during historical query: keep for reference but flag as comparison
                others.append((pid, score * 0.7, {**meta, "_version_flag": "historical_comparison"}))
                continue

        if sup:
            superseded.append((pid, score * 0.3, {**meta, "_version_flag": "superseded"}))
        elif ay_mismatch:
            mismatched.append((pid, score * 0.5, {**meta, "_version_flag": "academic_year_mismatch"}))
        elif is_current is False:
            # Historical document in general query: retain for consensus checking without excessive demotion
            others.append((pid, score * 0.85, {**meta, "_version_flag": "historical_candidate"}))
        else:
            valid.append((pid, score, meta))

    return valid + mismatched + superseded + others


# ─── Main retrieval function ──────────────────────────────────────────────────

def retrieve(
    query_analysis: QueryAnalysis,
    collections: list[DocumentSource],
    top_k: int = settings.retrieval_top_k,
    use_reranker: bool = True,
    use_mqr: bool = False,
    use_pdr: bool = True,
    academic_year: Optional[str] = None,
    program: Optional[str] = None,
    rerank_strategy: str = "production",
    user_id: Optional[str] = None,
) -> RetrievalResult:
    """
    Main retrieval entry point.

    1. Build query set (original + MQR alternatives if enabled).
    2. Run BM25 + dense search on requested collection indexes.
    3. Fuse with RRF.
    4. Optionally rerank (supports 'production' and 'adaptive_e6b' strategies).
    5. Optionally expand to parent passages (PDR).
    6. Validate versions.
    7. Return structured RetrievalResult.
    """
    t0 = time.perf_counter()

    primary_query = query_analysis.normalized_query or query_analysis.original_query
    queries = [primary_query]

    # MQR: add sub-questions and optionally translated query
    if use_mqr:
        if query_analysis.sub_questions:
            queries.extend(query_analysis.sub_questions[:3])
        if query_analysis.translated_query:
            queries.append(query_analysis.translated_query)
        queries = list(dict.fromkeys(queries))  # deduplicate preserving order

    # Collect indexes for requested collections
    indexes: list[RetrieverIndex] = []
    for coll in collections:
        idx = get_official_index() if coll == DocumentSource.OFFICIAL else get_upload_index()
        if idx.is_ready():
            indexes.append(idx)

    if not indexes:
        logger.warning("No ready indexes found for collections: %s", collections)
        return RetrievalResult(
            query_analysis=query_analysis,
            retrieved_passages=[],
            total_candidates=0,
        )

    # Detect Devanagari Hindi for adaptive routing
    is_devanagari = (
        getattr(query_analysis, "detected_script", None) == QueryScript.DEVANAGARI
        or (
            getattr(query_analysis, "detected_language", None) == QueryLanguage.HINDI
            and getattr(query_analysis, "detected_script", None) != QueryScript.MIXED
        )
        or any("\u0900" <= ch <= "\u097f" for ch in primary_query)
    )

    all_candidates: list[tuple[str, float, dict]] = []
    used_reranker = False

    if rerank_strategy == "adaptive_e6b" and is_devanagari:
        # Candidate E6b: Route Devanagari Hindi directly to dense bi-encoder candidates
        for idx in indexes:
            hits = idx.dense_search(primary_query, top_k * 2)
            for pid, score, meta in hits:
                if "text" not in meta:
                    try:
                        tidx = idx.passage_ids.index(pid)
                        meta["text"] = idx.passage_texts[tidx]
                    except ValueError:
                        pass
            all_candidates.extend(hits)
        used_reranker = False
    else:
        # Production path: Hybrid BM25 + Dense RRF fusion followed by Cross-Encoder
        for idx in indexes:
            eff_uid = user_id if idx.index_name == "upload" else None
            candidate_k = max(top_k * 5, 25)
            for q in queries:
                bm25_hits = idx.bm25_search(q, candidate_k, user_id=eff_uid)
                dense_hits = idx.dense_search(q, candidate_k, user_id=eff_uid)
                fused = _rrf_fuse(bm25_hits, dense_hits)
                # Tag text for reranker
                for pid, score, meta in fused:
                    if "text" not in meta:
                        try:
                            tidx = idx.passage_ids.index(pid)
                            meta["text"] = idx.passage_texts[tidx]
                        except ValueError:
                            pass
                all_candidates.extend(fused)

        # Deduplicate across indexes and queries
        all_candidates = _deduplicate(all_candidates)

        # Version validation (considering temporal anchors and program scope from query_analysis)
        eff_ay = academic_year or getattr(query_analysis, "target_academic_year", None)
        eff_prog = program or getattr(query_analysis, "target_programme", None)
        all_candidates = validate_versions(all_candidates, eff_ay, eff_prog, query_analysis)

        # Rerank
        if use_reranker and all_candidates:
            all_candidates = rerank(primary_query, all_candidates, top_k=top_k * 2)
            used_reranker = True

    # PDR: expand to parents
    used_pdr = False
    if use_pdr and indexes:
        primary_idx = indexes[0]
        all_candidates = expand_to_parents(all_candidates, primary_idx)
        used_pdr = True

    # Relationship-Aware Expansion (R3)
    used_relationship_expansion = False
    if all_candidates:
        expanded_candidates = expand_with_relationships(
            candidates=all_candidates[:top_k],
            user_id=user_id,
            max_expanded=5,
        )
        if expanded_candidates:
            used_relationship_expansion = True
            seen_ids = set()
            merged = []
            for item in (all_candidates[:top_k] + expanded_candidates):
                if item[0] not in seen_ids:
                    seen_ids.add(item[0])
                    merged.append(item)
            all_candidates = merged

    # Final top-k candidates (includes relationship expansions)
    top_candidates = all_candidates[: top_k + (len(expanded_candidates) if used_relationship_expansion else 0)]

    # Convert to RetrievedPassage objects
    retrieved = []
    for pid, score, meta in top_candidates:
        # Find the actual text
        text = meta.get("text", "")
        if not text:
            for idx in indexes:
                try:
                    tidx = idx.passage_ids.index(pid)
                    text = idx.passage_texts[tidx]
                    break
                except ValueError:
                    pass

        version_info = DocumentVersionInfo(
            effective_date=meta.get("effective_date"),
            academic_year=meta.get("academic_year"),
            is_current=meta.get("is_current"),
            superseded_by=meta.get("superseded_by"),
        )

        v_flag = meta.get("_version_flag")
        # Passage is valid if no negative flag or if it's a historical candidate retained for consensus/comparison
        is_valid = v_flag in (None, "historical_candidate")

        ret_method = "relationship_expansion" if meta.get("relationship_expansion") else "hybrid"
        rp = RetrievedPassage(
            passage_id=pid,
            document_id=meta.get("document_id", ""),
            document_filename=meta.get("filename") or meta.get("document_filename") or "",
            text=text,
            score=score,
            rerank_score=score if use_reranker else None,
            retrieval_method=ret_method,
            page_number=meta.get("page_number"),
            section=meta.get("section"),
            heading=meta.get("heading"),
            table_ref=meta.get("table_ref"),
            metadata=meta,
            source_type=DocumentSource(meta.get("source_type", "official")),
            version_info=version_info,
            is_valid_for_query=is_valid,
            relationship_expansion=meta.get("relationship_expansion"),
        )
        rp.regulatory_condition = classify_passage_condition(rp)
        retrieved.append(rp)

    latency_ms = (time.perf_counter() - t0) * 1000
    return RetrievalResult(
        query_analysis=query_analysis,
        retrieved_passages=retrieved,
        total_candidates=len(all_candidates),
        retrieval_attempts=1,
        used_mqr=use_mqr and len(queries) > 1,
        used_pdr=used_pdr,
        used_reranker=used_reranker,
        used_relationship_expansion=used_relationship_expansion,
        latency_ms=latency_ms,
    )
