"""Retrieval package exports."""
from app.retrieval.engine import (
    RetrieverIndex,
    get_official_index,
    get_upload_index,
    get_index,
    retrieve,
    rerank,
    expand_to_parents,
    validate_versions,
    _rrf_fuse,
    _deduplicate,
)
from app.retrieval.router import (
    AdaptiveRouter,
    RoutingDecision,
    RoutingStrategy,
    route_query,
)
from app.retrieval.adaptive_budget import (
    AdaptiveBudgetRetriever,
    BudgetDecision,
    get_adaptive_budget_retriever,
)
from app.retrieval.evidence_controller import (
    EvidenceController,
    get_evidence_controller,
)

__all__ = [
    "RetrieverIndex",
    "get_official_index",
    "get_upload_index",
    "get_index",
    "retrieve",
    "rerank",
    "expand_to_parents",
    "validate_versions",
    "_rrf_fuse",
    "_deduplicate",
    "AdaptiveRouter",
    "RoutingDecision",
    "RoutingStrategy",
    "route_query",
    "AdaptiveBudgetRetriever",
    "BudgetDecision",
    "get_adaptive_budget_retriever",
    "EvidenceController",
    "get_evidence_controller",
]

