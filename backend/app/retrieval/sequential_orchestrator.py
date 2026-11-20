"""
Sequential User-Document Retrieval with Automatic Official-Corpus Fallback.

Implements the 3-stage sequential retrieval policy for IndicRAG-QA:
  Stage 1 — Search user-uploaded documents (scoped to user_id).
             If evidence is SUFFICIENT, answer using user documents alone.
  Stage 2 — Automatic fallback to pre-loaded official university documents
             if user documents are missing, insufficient, or only partial.
             Handles reconciliation, compatibility checking, and partial combinations.
  Stage 3 — Final institutional abstention if neither source provides sufficient evidence.
"""
from __future__ import annotations

import time
from typing import Any, Optional

from app.core.logging_config import logger
from app.ingestion.pipeline import get_all_documents
from app.models.schemas import (
    DocumentSource,
    EvidenceDecision,
    EvidenceStatus,
    QueryAnalysis,
    RegulatoryRelationship,
    RetrievalResult,
    RetrievedPassage,
)
from app.retrieval.engine import retrieve
from app.retrieval.evidence_controller import get_evidence_controller
from app.retrieval.regulatory_classifier import classify_regulatory_relationship


class SequentialRetrievalOrchestrator:
    """
    Orchestrates sequential retrieval across user-uploaded documents and official corpus.
    """

    def __init__(self, evidence_controller=None):
        self.evidence_controller = evidence_controller or get_evidence_controller()

    def get_user_uploads(self, user_id: Optional[str] = None) -> list[dict]:
        """Fetch indexed user-uploaded documents, scoped to user_id."""
        return get_all_documents(source_type=DocumentSource.UPLOAD, user_id=user_id)

    def execute(
        self,
        query_analysis: QueryAnalysis,
        user_id: Optional[str] = None,
        top_k: int = 10,
        use_reranker: bool = True,
        use_mqr: bool = False,
        use_pdr: bool = True,
        academic_year: Optional[str] = None,
        program: Optional[str] = None,
    ) -> tuple[EvidenceDecision, RetrievalResult, dict[str, Any]]:
        """
        Execute sequential retrieval workflow.

        Returns:
            (final_evidence_decision, primary_retrieval_result, stage_metadata)
        """
        t0 = time.perf_counter()
        user_uploads = self.get_user_uploads(user_id=user_id)
        has_uploads = len(user_uploads) > 0

        logger.info(
            "[Sequential RAG] Initiating query execution. User ID: '%s', Uploaded docs count: %d",
            user_id or "default_user",
            len(user_uploads),
        )

        user_retrieval: Optional[RetrievalResult] = None
        user_decision: Optional[EvidenceDecision] = None
        partial_user_decision: Optional[EvidenceDecision] = None

        # ── STAGE 1: Search User-Uploaded Documents ────────────────────────────
        if has_uploads:
            logger.info("[Sequential RAG] Stage 1: Searching user-uploaded documents...")
            user_retrieval = retrieve(
                query_analysis=query_analysis,
                collections=[DocumentSource.UPLOAD],
                top_k=top_k,
                use_reranker=use_reranker,
                use_mqr=use_mqr,
                use_pdr=use_pdr,
                academic_year=academic_year,
                program=program,
                user_id=user_id,
            )

            user_decision = self.evidence_controller.evaluate(user_retrieval, attempt=1)
            logger.info(
                "[Sequential RAG] Stage 1 Decision: status=%s, valid_passages=%d, CECI=%.3f",
                user_decision.status.value,
                len(user_decision.valid_passages),
                user_decision.ceci_score or 0.0,
            )

            # Check if user evidence is sufficient
            sufficient_statuses = {
                EvidenceStatus.SUFFICIENT,
                EvidenceStatus.MULTI_CONDITION_DISCLOSURE,
            }

            user_covers_query = (
                user_decision.status in sufficient_statuses or
                (user_decision.status == EvidenceStatus.PARTIAL and (user_decision.coverage_score or 0.0) >= 0.8 and not query_analysis.is_multi_part)
            )

            if user_covers_query:
                logger.info(
                    "[Sequential RAG] Stage 1 SUFFICIENT: Query satisfied entirely by user-provided documents (status=%s, coverage=%.2f). Bypassing official fallback.",
                    user_decision.status.value,
                    user_decision.coverage_score or 0.0,
                )
                user_decision.status = EvidenceStatus.SUFFICIENT
                latency_ms = (time.perf_counter() - t0) * 1000
                summary = {
                    "stage": "user_upload_sufficient",
                    "fallback_triggered": False,
                    "user_docs_count": len(user_uploads),
                    "user_status": user_decision.status.value,
                    "official_status": None,
                    "combined_sources": False,
                    "orchestrator_latency_ms": round(latency_ms, 2),
                }
                return user_decision, user_retrieval, summary

            elif user_decision.status == EvidenceStatus.PARTIAL:
                logger.info(
                    "[Sequential RAG] Stage 1 PARTIAL: User document satisfies partial query. Fallback needed for remaining requirements."
                )
                partial_user_decision = user_decision

            else:
                logger.info(
                    "[Sequential RAG] Stage 1 INSUFFICIENT/MISSING (%s): Triggering automatic official fallback.",
                    user_decision.status.value,
                )
        else:
            logger.info(
                "[Sequential RAG] Stage 1 skipped: No user-uploaded documents found. Proceeding directly to official corpus."
            )

        # ── STAGE 2: Fallback to Pre-Loaded Official Corpus ────────────────────
        logger.info("[Sequential RAG] Stage 2: Retrieving from pre-loaded official university corpus...")
        
        # Check if query requires multi-hop relationship reasoning (calendar, medical, complex)
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
                user_id=user_id,
                academic_year=academic_year,
                program=program,
            )
            official_decision = reasoner.to_evidence_decision(ev_set)
            official_retrieval = RetrievalResult(
                query_analysis=query_analysis,
                retrieved_passages=ev_set.all_passages,
                total_candidates=len(ev_set.all_passages),
                used_relationship_expansion=True,
            )
        else:
            official_retrieval = retrieve(
                query_analysis=query_analysis,
                collections=[DocumentSource.OFFICIAL],
                top_k=top_k,
                use_reranker=use_reranker,
                use_mqr=use_mqr,
                use_pdr=use_pdr,
                academic_year=academic_year,
                program=program,
            )
            official_decision = self.evidence_controller.evaluate(official_retrieval, attempt=1)
        logger.info(
            "[Sequential RAG] Stage 2 Decision: status=%s, valid_passages=%d, CECI=%.3f",
            official_decision.status.value,
            len(official_decision.valid_passages),
            official_decision.ceci_score or 0.0,
        )

        # ── STAGE 2.B: Reconcile Partial User Evidence + Official Evidence ────
        if partial_user_decision and partial_user_decision.valid_passages:
            logger.info("[Sequential RAG] Reconciling partial user evidence with official evidence...")
            # Check for direct regulatory contradiction between user and official passages
            contradictions = []
            for up in partial_user_decision.valid_passages:
                for op in official_decision.valid_passages:
                    rel = classify_regulatory_relationship(up, op)
                    if rel == RegulatoryRelationship.GENUINE_CONFLICT:
                        contradictions.append((up, op))

            if contradictions:
                logger.warning(
                    "[Sequential RAG] Direct contradiction detected between user-provided document and official university regulations."
                )
                combined_conflicting = list(partial_user_decision.valid_passages) + list(official_decision.valid_passages)
                conflict_decision = EvidenceDecision(
                    status=EvidenceStatus.CONFLICTING,
                    valid_passages=combined_conflicting,
                    conflicting_passages=combined_conflicting,
                    explanation=(
                        "CONFLICTING REGULATIONS DETECTED — Discrepancy observed between the user-provided "
                        "document and official university regulations. Please consult university administration."
                    ),
                    retry_recommended=False,
                    ceci_score=official_decision.ceci_score,
                )
                latency_ms = (time.perf_counter() - t0) * 1000
                summary = {
                    "stage": "conflicting_user_and_official",
                    "fallback_triggered": True,
                    "user_status": partial_user_decision.status.value,
                    "official_status": official_decision.status.value,
                    "combined_sources": True,
                    "has_contradiction": True,
                    "orchestrator_latency_ms": round(latency_ms, 2),
                }
                return conflict_decision, official_retrieval, summary

            # Compatible: Merge user passages and official passages without duplicating
            seen_ids = set()
            combined_passages: list[RetrievedPassage] = []
            for p in partial_user_decision.valid_passages:
                if p.passage_id not in seen_ids:
                    seen_ids.add(p.passage_id)
                    combined_passages.append(p)
            for p in official_decision.valid_passages:
                if p.passage_id not in seen_ids:
                    seen_ids.add(p.passage_id)
                    combined_passages.append(p)

            combined_retrieval = RetrievalResult(
                query_analysis=query_analysis,
                retrieved_passages=combined_passages,
                total_candidates=len(combined_passages),
                retrieval_attempts=1,
            )
            combined_decision = self.evidence_controller.evaluate(combined_retrieval, attempt=1)
            # If combined evidence covers the query sufficiently:
            if combined_decision.status in (EvidenceStatus.SUFFICIENT, EvidenceStatus.PARTIAL, EvidenceStatus.MULTI_CONDITION_DISCLOSURE):
                latency_ms = (time.perf_counter() - t0) * 1000
                summary = {
                    "stage": "combined_user_and_official",
                    "fallback_triggered": True,
                    "user_status": partial_user_decision.status.value,
                    "official_status": official_decision.status.value,
                    "combined_sources": True,
                    "orchestrator_latency_ms": round(latency_ms, 2),
                }
                return combined_decision, combined_retrieval, summary

        # Standard Fallback: Use official decision if sufficient, partial, or clarification needed
        if official_decision.status not in (EvidenceStatus.MISSING, EvidenceStatus.INSUFFICIENT):
            latency_ms = (time.perf_counter() - t0) * 1000
            summary = {
                "stage": "official_fallback",
                "fallback_triggered": True,
                "user_docs_count": len(user_uploads),
                "user_status": user_decision.status.value if user_decision else "NO_UPLOADS",
                "official_status": official_decision.status.value,
                "combined_sources": False,
                "orchestrator_latency_ms": round(latency_ms, 2),
            }
            return official_decision, official_retrieval, summary

        # ── STAGE 3: Final Institutional Abstention ────────────────────────────
        logger.info(
            "[Sequential RAG] Stage 3: Neither user-provided documents nor official university regulations contain sufficient evidence."
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        abstain_decision = EvidenceDecision(
            status=EvidenceStatus.INSUFFICIENT,
            valid_passages=[],
            explanation=(
                "UNANSWERABLE — Sufficient evidence was not found in the user's uploaded documents "
                "or the available official university regulations."
            ),
            retry_recommended=False,
            ceci_score=0.0,
        )
        summary = {
            "stage": "final_abstention",
            "fallback_triggered": True,
            "user_docs_count": len(user_uploads),
            "user_status": user_decision.status.value if user_decision else "NO_UPLOADS",
            "official_status": official_decision.status.value,
            "combined_sources": False,
            "orchestrator_latency_ms": round(latency_ms, 2),
        }
        return abstain_decision, official_retrieval, summary


# Singleton accessor
_orchestrator: Optional[SequentialRetrievalOrchestrator] = None


def get_sequential_orchestrator() -> SequentialRetrievalOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SequentialRetrievalOrchestrator()
    return _orchestrator
