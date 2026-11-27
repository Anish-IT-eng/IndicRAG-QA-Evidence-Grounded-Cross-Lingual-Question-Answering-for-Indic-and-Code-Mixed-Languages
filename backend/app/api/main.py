"""
FastAPI application — IndicRAG-QA backend.

Endpoints:
  GET  /health
  GET  /documents
  POST /documents/ingest          (official docs, admin)
  POST /uploads                   (user-uploaded PDFs)
  POST /query
  GET  /documents/{doc_id}/passages
  GET  /evaluation/summary        (dev/eval only — requires API key)
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import logger, setup_logging
from app.generation.generator import generate_answer
from app.ingestion.pipeline import (
    delete_document,
    get_all_documents,
    get_passages_for_document,
    ingest_pdf,
)
from app.models.schemas import (
    DocumentListItem,
    DocumentSource,
    DocumentVersionInfo,
    EvidenceStatus,
    FeedbackSubtype,
    HealthResponse,
    IngestRequest,
    IngestionStatus,
    QueryAnalysis,
    QueryLanguage,
    QueryRequest,
    QueryResponse,
    QuestionType,
    ResponseStatus,
)
from app.query.conversation_store import get_last_turn, save_turn
from app.query.feedback_repair import repair_feedback_turn
from app.query.processor import process_query
from app.retrieval.engine import (
    get_official_index,
    get_upload_index,
    retrieve,
)
from app.retrieval.evidence_controller import get_evidence_controller
from app.retrieval.sequential_orchestrator import get_sequential_orchestrator

# ─── App lifecycle ─────────────────────────────────────────────────────────────

setup_logging(settings.debug)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Evidence-grounded multilingual QA for Bennett University regulations.",
    docs_url="/api/docs" if settings.environment != "production" else None,
    redoc_url="/api/redoc" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def redirect_docs():
    return RedirectResponse(url="/api/docs")


# ─── Static files and Frontend UI ─────────────────────────────────────────────
_frontend_dir = Path(__file__).resolve().parent.parent.parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_frontend_dir)), name="static")


@app.get("/", include_in_schema=False)
async def serve_index():
    index_file = _frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": "IndicRAG-QA API Online. Frontend index.html not found."})


@app.on_event("startup")
async def startup() -> None:
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    init_db()
    # Warm up indexes from disk
    get_official_index()
    get_upload_index()
    # Pre-warm embedding and reranker models to eliminate first-query cold start
    try:
        from app.retrieval.engine import get_embedding_model, get_cross_encoder
        get_embedding_model()
        get_cross_encoder()
    except Exception as _e:
        logger.warning("Model pre-warming skipped: %s", _e)
    logger.info("Startup complete.")


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def _require_eval_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    if x_api_key != settings.eval_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key.")


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
@app.get("/api/health", response_model=HealthResponse, tags=["System"], include_in_schema=False)
async def health() -> HealthResponse:
    # Check Ollama
    import httpx as _httpx
    ollama_ok = False
    try:
        async with _httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception:
        pass

    # Count docs and passages
    from app.core.database import get_db
    with get_db() as conn:
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        passage_count = conn.execute("SELECT COUNT(*) FROM passages").fetchone()[0]
        child_count = conn.execute("SELECT COUNT(*) FROM passages WHERE parent_passage_id IS NOT NULL").fetchone()[0]
        parent_count = conn.execute("SELECT COUNT(*) FROM passages WHERE parent_passage_id IS NULL").fetchone()[0]

    # Embedding model status
    from app.retrieval.engine import _embedding_model
    emb_loaded = _embedding_model is not None

    return HealthResponse(
        version=settings.app_version,
        ollama_reachable=ollama_ok,
        embedding_model_loaded=emb_loaded,
        document_count=doc_count,
        passage_count=passage_count,
        child_passage_count=child_count,
        parent_passage_count=parent_count,
    )


# ─── Documents ────────────────────────────────────────────────────────────────

@app.get("/documents", tags=["Documents"])
async def list_documents(
    source_type: Optional[str] = Query(default=None, description="Filter: official | upload"),
    user_id: Optional[str] = Query(default=None, description="Filter upload docs by user_id"),
    x_user_id: Optional[str] = Header(default=None),
) -> list[dict]:
    effective_user_id = user_id or x_user_id
    src = None
    if source_type:
        try:
            src = DocumentSource(source_type)
        except ValueError:
            raise HTTPException(400, f"Invalid source_type: {source_type}")
    return get_all_documents(src, user_id=effective_user_id)


@app.post("/documents/ingest", tags=["Documents"])
async def ingest_official_document(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Trigger ingestion of an official document from a URL.
    The URL must point to a PDF already accessible locally or via HTTP.

    NOTE: For security, URL fetching is disabled in this endpoint.
    Use the upload endpoint or place the file in data/official/ manually.
    """
    raise HTTPException(
        status_code=501,
        detail=(
            "Remote URL ingestion is not enabled. "
            "Place the PDF in data/official/ and call POST /documents/ingest-file, "
            "or use POST /uploads for user documents."
        ),
    )


class IngestFileRequest(BaseModel):
    filename: str
    title: Optional[str] = None
    description: Optional[str] = None
    version_info: DocumentVersionInfo = DocumentVersionInfo()
    force: bool = False


@app.post("/documents/ingest-file", tags=["Documents"])
async def ingest_official_file(
    request: IngestFileRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Ingest an official PDF that has already been placed in data/official/.
    """
    pdf_path = settings.official_docs_dir / request.filename
    if not pdf_path.exists():
        raise HTTPException(
            404,
            f"File '{request.filename}' not found in official documents directory.",
        )
    if pdf_path.suffix.lower() not in settings.allowed_upload_extensions:
        raise HTTPException(400, "Only PDF files are accepted.")

    def _run():
        ingest_pdf(
            pdf_path=pdf_path,
            source_type=DocumentSource.OFFICIAL,
            title=request.title,
            description=request.description,
            version_info=request.version_info,
            force=request.force,
        )

    background_tasks.add_task(_run)
    return {"message": f"Ingestion of '{request.filename}' queued.", "filename": request.filename}


# ─── Uploads ──────────────────────────────────────────────────────────────────

@app.post("/uploads", tags=["Uploads"])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    academic_year: Optional[str] = Form(default=None),
    program_applicability: Optional[str] = Form(default=None),
    user_id: Optional[str] = Form(default=None),
    x_user_id: Optional[str] = Header(default=None),
    wait: bool = Form(default=False),
) -> dict:
    """
    Upload a user PDF. Uploaded docs remain isolated from the official corpus.
    Scoped to user_id for multi-user isolation.
    """
    effective_user_id = user_id or x_user_id

    # Validate extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")

    # Check file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            413,
            f"File size ({size_mb:.1f} MB) exceeds limit ({settings.max_upload_size_mb} MB).",
        )

    # Sanitize filename (no path traversal)
    safe_name = Path(file.filename).name
    dest = settings.uploads_dir / safe_name
    dest.write_bytes(content)
    logger.info("Uploaded file saved: %s (%.1f MB) for user: %s", safe_name, size_mb, effective_user_id or "anonymous")

    prog_list = None
    if program_applicability:
        try:
            prog_list = json.loads(program_applicability)
        except json.JSONDecodeError:
            prog_list = [program_applicability]

    vi = DocumentVersionInfo(
        academic_year=academic_year,
        program_applicability=prog_list,
    )

    if wait:
        try:
            doc_rec = ingest_pdf(
                pdf_path=dest,
                source_type=DocumentSource.UPLOAD,
                version_info=vi,
                user_id=effective_user_id,
            )
            if doc_rec.ingestion_status == IngestionStatus.FAILED:
                raise HTTPException(422, f"PDF extraction failed: {doc_rec.error_message}")
            return {
                "message": f"Upload and indexing complete. '{safe_name}' is ready for search.",
                "document_id": doc_rec.document_id,
                "filename": safe_name,
                "status": doc_rec.ingestion_status.value if hasattr(doc_rec.ingestion_status, "value") else str(doc_rec.ingestion_status),
                "page_count": doc_rec.page_count,
                "size_mb": round(size_mb, 2),
                "user_id": effective_user_id,
            }
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Synchronous ingestion failed for %s: %s", safe_name, exc)
            raise HTTPException(422, f"Failed to ingest document: {exc}")

    def _run():
        ingest_pdf(
            pdf_path=dest,
            source_type=DocumentSource.UPLOAD,
            version_info=vi,
            user_id=effective_user_id,
        )

    background_tasks.add_task(_run)
    return {
        "message": f"Upload received. '{safe_name}' is being processed.",
        "filename": safe_name,
        "size_mb": round(size_mb, 2),
        "user_id": effective_user_id,
    }


@app.delete("/documents/{document_id}", tags=["Documents"])
async def delete_doc(
    document_id: str,
    user_id: Optional[str] = Query(default=None),
    x_user_id: Optional[str] = Header(default=None),
) -> dict:
    """
    Cascading delete of a document, its passages, tables, relationships, and index entries.
    Guarantees tenant isolation for uploaded documents.
    """
    effective_user_id = user_id or x_user_id
    try:
        success = delete_document(document_id, user_id=effective_user_id)
        if not success:
            raise HTTPException(404, f"Document '{document_id}' not found.")
        return {"message": f"Document '{document_id}' deleted successfully.", "document_id": document_id}
    except PermissionError as pe:
        raise HTTPException(403, str(pe))


@app.get("/documents/{document_id}/status", tags=["Documents"])
async def get_document_status(
    document_id: str,
    user_id: Optional[str] = Query(default=None),
    x_user_id: Optional[str] = Header(default=None),
) -> dict:
    """Check ingestion status and health for a specific document."""
    effective_user_id = user_id or x_user_id
    from app.core.database import get_db
    with get_db() as conn:
        doc = conn.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,)).fetchone()
        if not doc:
            raise HTTPException(404, f"Document '{document_id}' not found.")
        if effective_user_id and doc["source_type"] == DocumentSource.UPLOAD.value:
            meta = json.loads(doc["metadata"]) if doc["metadata"] else {}
            if meta.get("user_id") and meta.get("user_id") != effective_user_id:
                raise HTTPException(403, "Access to another tenant's document is forbidden.")
        return {
            "document_id": doc["document_id"],
            "filename": doc["filename"],
            "status": doc["ingestion_status"],
            "page_count": doc["page_count"],
            "error_message": doc["error_message"],
            "source_type": doc["source_type"],
        }


# ─── Query ────────────────────────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query(request: QueryRequest) -> QueryResponse:
    """
    Main QA endpoint.

    Flow:
    1. Process query (language detection, normalization, decomposition).
    2. If sequential_fallback is enabled (default):
       - Stage 1: Search user documents (scoped to user_id).
       - Stage 2: Automatic fallback to official corpus if missing/insufficient/partial.
       - Stage 3: Final institutional abstention if neither source has evidence.
    3. Generate grounded answer.
    """
    t0 = time.perf_counter()
    session_id = request.session_id or request.user_id or "default_session"

    # 1. Process query
    query_analysis = process_query(request.query)
    logger.info(
        "Query: lang=%s, type=%s, subtype=%s, complexity=%.2f, sequential_fallback=%s, user_id=%s, session_id=%s",
        query_analysis.detected_language,
        query_analysis.query_type,
        query_analysis.feedback_subtype,
        query_analysis.complexity_score,
        request.sequential_fallback,
        request.user_id,
        session_id,
    )

    # Special Handler: Context-Aware Feedback & Answer Repair
    if query_analysis.query_type == QuestionType.FEEDBACK_CORRECTION:
        # Step 1: Recover preceding conversation turn (do not invent missing history)
        preceding_turn = get_last_turn(session_id=session_id, user_id=request.user_id)
        if not preceding_turn and request.conversation_history:
            last_client_item = request.conversation_history[-1]
            preceding_turn = {
                "user_query": last_client_item.get("query", ""),
                "assistant_answer": last_client_item.get("answer", ""),
                "evidence_status": last_client_item.get("evidence_status", "sufficient"),
                "citations": last_client_item.get("citations", []),
            }

        subtype = query_analysis.feedback_subtype or FeedbackSubtype.GENERAL_DISAGREEMENT
        response = repair_feedback_turn(
            feedback_query=request.query,
            subtype=subtype,
            preceding_turn=preceding_turn,
            user_id=request.user_id,
            session_id=session_id,
            response_language=request.response_language,
        )
        response.latency_ms = (time.perf_counter() - t0) * 1000
        response.query_analysis = query_analysis
        response.retrieval_summary = {
            "stage": "feedback_repair",
            "is_feedback": True,
            "feedback_subtype": subtype.value if hasattr(subtype, "value") else str(subtype),
            "repair_action": response.repair_action,
            "preceding_turn_found": preceding_turn is not None,
            "retrieval_latency_ms": 0.0,
            "generation_latency_ms": round(response.latency_ms, 2),
            "total_latency_ms": round(response.latency_ms, 2),
        }

        # Persist feedback turn to SQLite
        try:
            save_turn(
                session_id=session_id,
                user_id=request.user_id,
                user_query=request.query,
                assistant_answer=response.answer or "",
                evidence_status=(
                    response.evidence_status.value
                    if hasattr(response.evidence_status, "value")
                    else str(response.evidence_status)
                ),
                query_type=QuestionType.FEEDBACK_CORRECTION.value,
                feedback_subtype=subtype.value if hasattr(subtype, "value") else str(subtype),
                citations=response.citations,
            )
        except Exception as _e:
            logger.warning("Failed to save feedback turn: %s", _e)

        return response

    # Adaptive router: enable MQR for complex/code-mixed queries
    use_mqr = request.use_mqr or query_analysis.complexity_score >= 0.5
    top_k = request.top_k or settings.retrieval_top_k

    if request.sequential_fallback:
        orchestrator = get_sequential_orchestrator()
        evidence_decision, retrieval_result, stage_meta = orchestrator.execute(
            query_analysis=query_analysis,
            user_id=request.user_id,
            top_k=top_k,
            use_reranker=request.use_reranker,
            use_mqr=use_mqr,
            use_pdr=request.use_pdr,
            academic_year=request.academic_year,
            program=request.program,
        )
    else:
        # Check if query requires multi-hop relationship reasoning
        from app.query.event_resolver import is_multilingual_calendar_query
        q_raw = query_analysis.original_query
        q_norm = query_analysis.normalized_query or ""
        is_cal = (is_multilingual_calendar_query(q_raw) or (bool(q_norm) and is_multilingual_calendar_query(q_norm))) and not any(w in q_raw.lower() for w in ["attendance", "उपस्थिति", "marks", "grade", "grading", "cgpa", "sgpa", "credit"])
        needs_multi_hop = (
            query_analysis.complexity_score >= 0.5
            or query_analysis.is_multi_part
            or is_cal
            or any(w in q_raw.lower() for w in ["medical", "relaxation", "condon", "illness", "difference", "both", "मेडिकल", "छूट", "बीमारी"])
        )

        if needs_multi_hop:
            from app.retrieval.multi_hop_reasoner import MultiHopReasoner
            reasoner = MultiHopReasoner(max_hops=3, max_evidence_items=12)
            ev_set = reasoner.reason(
                query_analysis=query_analysis,
                user_id=request.user_id,
                academic_year=request.academic_year,
                program=request.program,
            )
            evidence_decision = reasoner.to_evidence_decision(ev_set)
            retrieval_result = RetrievalResult(
                query_analysis=query_analysis,
                retrieved_passages=ev_set.all_passages,
                total_candidates=len(ev_set.all_passages),
                used_relationship_expansion=True,
            )
        else:
            evidence_controller = get_evidence_controller()
            retrieval_result = retrieve(
                query_analysis=query_analysis,
                collections=request.collection,
                top_k=top_k,
                use_reranker=request.use_reranker,
                use_mqr=use_mqr,
                use_pdr=request.use_pdr,
                academic_year=request.academic_year,
                program=request.program,
                user_id=request.user_id,
            )
            evidence_decision = evidence_controller.evaluate(retrieval_result, attempt=1)

            retry_count = 0
            while evidence_decision.retry_recommended and retry_count < settings.max_retrieval_retries:
                retry_count += 1
                logger.info("Retrying retrieval (attempt %d)…", retry_count + 1)
                # On retry: force MQR and increase top_k
                retrieval_result = retrieve(
                    query_analysis=query_analysis,
                    collections=request.collection,
                    top_k=top_k * 2,
                    use_reranker=request.use_reranker,
                    use_mqr=True,
                    use_pdr=request.use_pdr,
                    academic_year=request.academic_year,
                    program=request.program,
                    user_id=request.user_id,
                )
                retrieval_result.retrieval_attempts = retry_count + 1
                evidence_decision = evidence_controller.evaluate(retrieval_result, attempt=retry_count + 1)

        stage_meta = {"stage": "direct", "fallback_triggered": False}

    # 3. Generate answer
    response = await generate_answer(
        query_analysis=query_analysis,
        evidence_decision=evidence_decision,
        response_language=request.response_language,
        debug=request.debug,
    )

    response.latency_ms = (time.perf_counter() - t0) * 1000
    response.query_analysis = query_analysis
    if response.retrieval_summary is None:
        response.retrieval_summary = {}
    ret_lat = retrieval_result.latency_ms if isinstance(getattr(retrieval_result, "latency_ms", None), (int, float)) else 0.0
    tot_lat = response.latency_ms if isinstance(getattr(response, "latency_ms", None), (int, float)) else 0.0
    response.retrieval_summary["retrieval_latency_ms"] = round(ret_lat, 2)
    response.retrieval_summary["total_latency_ms"] = round(tot_lat, 2)
    response.retrieval_summary["generation_latency_ms"] = round(max(0.0, tot_lat - ret_lat), 2)
    response.retrieval_summary["stage_summary"] = stage_meta

    # Persist completed turn to SQLite for multi-turn contextual tracking
    try:
        save_turn(
            session_id=session_id,
            user_id=request.user_id,
            user_query=request.query,
            assistant_answer=response.answer or "",
            evidence_status=(
                response.evidence_status.value
                if hasattr(response.evidence_status, "value")
                else str(response.evidence_status)
            ),
            query_type=(
                query_analysis.query_type.value
                if hasattr(query_analysis.query_type, "value")
                else str(query_analysis.query_type)
            ),
            normalized_query=query_analysis.normalized_query,
            citations=response.citations,
            retrieved_passages=(
                retrieval_result.retrieved_passages
                if hasattr(retrieval_result, "retrieved_passages")
                else None
            ),
            target_cohort=query_analysis.target_cohort,
            target_programme=query_analysis.target_programme,
            target_academic_year=query_analysis.target_academic_year,
        )
    except Exception as _e:
        logger.warning("Failed to save conversation turn: %s", _e)

    return response


# ─── Passages ────────────────────────────────────────────────────────────────

@app.get("/documents/{document_id}/passages", tags=["Documents"])
async def get_passages(document_id: str) -> list[dict]:
    passages = get_passages_for_document(document_id)
    if not passages:
        raise HTTPException(404, f"No passages found for document '{document_id}'.")
    return passages


# ─── Evaluation (protected) ───────────────────────────────────────────────────

@app.get(
    "/evaluation/summary",
    tags=["Evaluation"],
    dependencies=[Depends(_require_eval_key)],
)
async def evaluation_summary() -> dict:
    """Return evaluation run summaries (dev/eval environment only)."""
    if settings.environment == "production":
        raise HTTPException(403, "Evaluation endpoint disabled in production.")
    from app.core.database import get_db
    with get_db() as conn:
        rows = conn.execute(
            "SELECT run_id, run_name, timestamp, notes FROM evaluation_runs ORDER BY timestamp DESC LIMIT 50"
        ).fetchall()
    return {"runs": [dict(r) for r in rows]}
