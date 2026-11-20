"""
Pydantic data models for IndicRAG-QA.

These are the authoritative schemas shared across the application.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class DocumentSource(str, Enum):
    OFFICIAL = "official"
    UPLOAD = "upload"


class IngestionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"          # unchanged document, no re-ingestion needed


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVISION = "requires_revision"


class ValidationStatus(str, Enum):
    AUTO_VALIDATED = "auto_validated"
    AUTO_REJECTED = "auto_rejected"
    NEEDS_REVIEW = "needs_review"
    HUMAN_VERIFIED = "human_verified"


class QueryLanguage(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    ROMANIZED_HINDI = "hi-Latn"
    CODE_MIXED = "hi-en"
    UNKNOWN = "unknown"


class QueryScript(str, Enum):
    LATIN = "Latin"
    DEVANAGARI = "Devanagari"
    MIXED = "Mixed"
    UNKNOWN = "Unknown"


class QuestionType(str, Enum):
    DIRECT = "direct"
    NUMERICAL = "numerical"
    MULTI_PART = "multi_part"
    TABLE = "table"
    VERSION_DEPENDENT = "version_dependent"
    CODE_MIXED = "code_mixed"
    UNANSWERABLE = "unanswerable"
    FEEDBACK_CORRECTION = "feedback_correction"


class FeedbackSubtype(str, Enum):
    GENERAL_DISAGREEMENT = "general_disagreement"
    FACTUAL_CORRECTION = "factual_correction"
    MISSING_EXCEPTION = "missing_exception"
    WRONG_COHORT_OR_PROGRAM = "wrong_cohort_or_program"
    SOURCE_DISAGREEMENT = "source_disagreement"
    CITATION_CHALLENGE = "citation_challenge"
    CLARIFICATION_REQUEST = "clarification_request"
    ANSWER_REEXPLANATION = "answer_reexplanation"


class AnswerabilityLabel(str, Enum):
    ANSWERABLE = "answerable"
    UNANSWERABLE = "unanswerable"


class EvidenceStatus(str, Enum):
    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    CONFLICTING = "conflicting"
    MISSING = "missing"           # information may exist but not in selected corpus
    PARTIAL = "partial"           # some sub-questions answered
    CLARIFICATION_REQUIRED = "clarification_required"  # ambiguous query or missing cohort parameters
    MULTI_CONDITION_DISCLOSURE = "multi_condition_disclosure"  # complementary conditions (e.g. course grade vs exam hall)


class RegulatoryCondition(str, Enum):
    COURSE_GRADING = "COURSE_GRADING"
    EXAM_ELIGIBILITY = "EXAM_ELIGIBILITY"
    MEDICAL_CONDONATION = "MEDICAL_CONDONATION"
    DISCIPLINARY_ACTION = "DISCIPLINARY_ACTION"
    ACADEMIC_PROGRESSION = "ACADEMIC_PROGRESSION"
    PROGRAMME_REQUIREMENT = "PROGRAMME_REQUIREMENT"
    OTHER = "OTHER"


class RegulatoryRelationship(str, Enum):
    SAME_CONDITION_AGREEMENT = "SAME_CONDITION_AGREEMENT"
    SAME_CONDITION_DIFFERENT_VERSION = "SAME_CONDITION_DIFFERENT_VERSION"
    DIFFERENT_REGULATORY_CONDITIONS = "DIFFERENT_REGULATORY_CONDITIONS"
    EXPLICITLY_SUPERSEDES = "EXPLICITLY_SUPERSEDES"
    PROGRAMME_SPECIFIC_RULE = "PROGRAMME_SPECIFIC_RULE"
    HISTORICAL_RULE = "HISTORICAL_RULE"
    APPLICABILITY_UNRESOLVED = "APPLICABILITY_UNRESOLVED"
    GENUINE_CONFLICT = "GENUINE_CONFLICT"


class TemporalIntentMode(str, Enum):
    EXPLICIT_HISTORICAL = "EXPLICIT_HISTORICAL"
    EXPLICIT_CURRENT = "EXPLICIT_CURRENT"
    COHORT_BOUND = "COHORT_BOUND"
    UNANCHORED = "UNANCHORED"


class ResponseStatus(str, Enum):
    ANSWERED = "answered"
    UNANSWERABLE = "unanswerable"
    CLARIFICATION_NEEDED = "clarification_needed"
    CONFLICTING_VERSIONS = "conflicting_versions"
    ERROR = "error"


# ─────────────────────────────────────────────────────────────────────────────
# Relationship Taxonomy Models (Phase R2)
# ─────────────────────────────────────────────────────────────────────────────

class RelationshipCategory(str, Enum):
    TABLE = "TABLE"
    REGULATION = "REGULATION"
    CROSS_DOCUMENT = "CROSS_DOCUMENT"


class RelationshipPredicate(str, Enum):
    # A. Table and event relationships
    HEADER_OF = "HEADER_OF"
    CELL_BELONGS_TO_ROW = "CELL_BELONGS_TO_ROW"
    ROW_DESCRIBES_EVENT = "ROW_DESCRIBES_EVENT"
    EVENT_HAS_DATE = "EVENT_HAS_DATE"
    EVENT_HAS_DAY = "EVENT_HAS_DAY"
    EVENT_HAS_TYPE = "EVENT_HAS_TYPE"
    EVENT_CONTINUES_ON_PAGE = "EVENT_CONTINUES_ON_PAGE"
    EVENT_HAS_DATE_RANGE = "EVENT_HAS_DATE_RANGE"

    # B. Academic regulation relationships
    RULE_HAS_CLAUSE = "RULE_HAS_CLAUSE"
    CLAUSE_HAS_SUBCLAUSE = "CLAUSE_HAS_SUBCLAUSE"
    RULE_APPLIES_TO_PROGRAM = "RULE_APPLIES_TO_PROGRAM"
    RULE_APPLIES_TO_COHORT = "RULE_APPLIES_TO_COHORT"
    RULE_HAS_THRESHOLD = "RULE_HAS_THRESHOLD"
    RULE_HAS_EXCEPTION = "RULE_HAS_EXCEPTION"
    EXCEPTION_HAS_PREREQUISITE = "EXCEPTION_HAS_PREREQUISITE"
    EXCEPTION_REQUIRES_DOCUMENT = "EXCEPTION_REQUIRES_DOCUMENT"
    EXCEPTION_REQUIRES_APPROVAL = "EXCEPTION_REQUIRES_APPROVAL"
    RULE_HAS_EFFECTIVE_PERIOD = "RULE_HAS_EFFECTIVE_PERIOD"

    # C. Cross-document relationships
    DOCUMENT_CLARIFIES_RULE = "DOCUMENT_CLARIFIES_RULE"
    DOCUMENT_REFERENCES_RULE = "DOCUMENT_REFERENCES_RULE"
    DOCUMENT_SUPERSEDES_RULE = "DOCUMENT_SUPERSEDES_RULE"
    RULE_CONTRADICTS_RULE = "RULE_CONTRADICTS_RULE"
    RULE_HAS_APPLICABILITY_SCOPE = "RULE_HAS_APPLICABILITY_SCOPE"


class RelationshipExtractionMethod(str, Enum):
    STRUCTURAL_TABLE = "structural_table"
    DETERMINISTIC_REGULATION = "deterministic_regulation"
    GENERIC_EXTRACTION = "generic_extraction"
    LLM_PROPOSED = "llm_proposed"


class RelationshipVerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PROPOSED = "PROPOSED"
    REFUTED = "REFUTED"


class RelationshipRecord(BaseModel):
    relationship_id: str = Field(default_factory=lambda: f"rel_{uuid.uuid4().hex[:12]}")
    subject_id: str
    predicate: RelationshipPredicate
    object_id: Optional[str] = None
    object_value: str
    source_document_id: str
    source_passage_id: Optional[str] = None
    source_table_id: Optional[str] = None
    source_row_id: Optional[int] = None
    source_page: int
    temporal_anchor: Optional[str] = None
    cohort_scope: Optional[str] = None
    programme_scope: Optional[str] = None
    extraction_method: RelationshipExtractionMethod
    confidence: float = 1.0
    verification_status: RelationshipVerificationStatus = RelationshipVerificationStatus.VERIFIED
    user_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# Document and Passage Models
# ─────────────────────────────────────────────────────────────────────────────

class DocumentVersionInfo(BaseModel):
    effective_date: Optional[str] = None        # ISO-8601 or academic year string
    academic_year: Optional[str] = None         # e.g. "2023-24"
    program_applicability: Optional[list[str]] = None   # e.g. ["B.Tech", "MCA"]
    superseded_by: Optional[str] = None         # document_id of replacement
    supersedes: Optional[str] = None            # document_id this replaces
    is_current: Optional[bool] = None
    notes: Optional[str] = None


class DocumentRecord(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    source_url: Optional[str] = None
    source_type: DocumentSource
    file_hash: str                              # SHA-256 of raw file bytes
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)
    ingestion_status: IngestionStatus = IngestionStatus.PENDING
    page_count: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    version_info: DocumentVersionInfo = Field(default_factory=DocumentVersionInfo)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None        # set on failure


class PassageRecord(BaseModel):
    passage_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    parent_passage_id: Optional[str] = None    # PDR: link child → parent
    is_parent: bool = False
    text: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    heading: Optional[str] = None
    clause: Optional[str] = None
    table_ref: Optional[str] = None            # set for passages from tables
    chunk_index: int = 0
    total_chunks: int = 1
    source_type: DocumentSource
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Passage text must not be empty.")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Query Processing Models
# ─────────────────────────────────────────────────────────────────────────────

class QueryAnalysis(BaseModel):
    original_query: str
    detected_language: QueryLanguage = QueryLanguage.UNKNOWN
    detected_script: QueryScript = QueryScript.UNKNOWN
    normalized_query: Optional[str] = None
    romanized_query: Optional[str] = None       # Devanagari → Latin
    translated_query: Optional[str] = None      # to English for retrieval
    query_type: QuestionType = QuestionType.DIRECT
    is_multi_part: bool = False
    sub_questions: list[str] = Field(default_factory=list)
    intent_keywords: list[str] = Field(default_factory=list)
    complexity_score: float = 0.0               # 0..1
    temporal_intent_mode: TemporalIntentMode = TemporalIntentMode.UNANCHORED
    target_cohort: Optional[str] = None
    target_academic_year: Optional[str] = None
    target_programme: Optional[str] = None
    target_conditions: list[RegulatoryCondition] = Field(default_factory=list)
    feedback_subtype: Optional[FeedbackSubtype] = None
    challenged_claim: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Retrieval Models
# ─────────────────────────────────────────────────────────────────────────────

class RetrievedPassage(BaseModel):
    passage_id: str
    document_id: str
    text: str
    score: float
    retrieval_method: str                       # bm25 | dense | hybrid
    page_number: Optional[int] = None
    section: Optional[str] = None
    heading: Optional[str] = None
    table_ref: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_type: DocumentSource
    version_info: DocumentVersionInfo = Field(default_factory=DocumentVersionInfo)
    rerank_score: Optional[float] = None
    is_valid_for_query: Optional[bool] = None   # after version validation
    regulatory_condition: Optional[RegulatoryCondition] = None
    document_filename: Optional[str] = None
    relationship_expansion: Optional[dict[str, Any]] = None


class RetrievalResult(BaseModel):
    query_analysis: QueryAnalysis
    retrieved_passages: list[RetrievedPassage] = Field(default_factory=list)
    total_candidates: int = 0
    retrieval_attempts: int = 1
    used_mqr: bool = False
    used_pdr: bool = False
    used_reranker: bool = False
    used_relationship_expansion: bool = False
    latency_ms: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Evidence and Answerability Models
# ─────────────────────────────────────────────────────────────────────────────

class EvidenceDecision(BaseModel):
    status: EvidenceStatus
    valid_passages: list[RetrievedPassage] = Field(default_factory=list)
    conflicting_passages: list[RetrievedPassage] = Field(default_factory=list)
    coverage_score: float = 0.0                 # 0..1, how well evidence covers query
    sub_question_coverage: dict[str, bool] = Field(default_factory=dict)
    retry_recommended: bool = False
    clarification_needed: bool = False
    explanation: str = ""
    ceci_score: Optional[float] = None
    ceci_features: Optional[dict[str, float]] = None
    regulatory_relationships: list[dict[str, Any]] = Field(default_factory=list)
    detected_conditions: list[RegulatoryCondition] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Claim Grounding Models
# ─────────────────────────────────────────────────────────────────────────────

class ClaimVerificationVerdict(str, Enum):
    ENTAILED = "ENTAILED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_SUPPORT = "INSUFFICIENT_SUPPORT"


class AtomicClaim(BaseModel):
    claim_id: str
    claim_text: str
    cited_passage_id: Optional[str] = None
    verdict: ClaimVerificationVerdict = ClaimVerificationVerdict.INSUFFICIENT_SUPPORT
    numeric_verified: bool = True
    date_verified: bool = True
    negation_verified: bool = True
    semantic_entailed: bool = False
    explanation: str = ""
    discrepancies: list[str] = Field(default_factory=list)


class ClaimGroundingResult(BaseModel):
    total_claims: int = 0
    entailed_claims: int = 0
    contradicted_claims: int = 0
    unsupported_claims: int = 0
    all_claims_entailed: bool = False
    contains_contradiction: bool = False
    claims: list[AtomicClaim] = Field(default_factory=list)
    grounding_ratio: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Citation and Response Models
# ─────────────────────────────────────────────────────────────────────────────

class Citation(BaseModel):
    document_id: str
    filename: str
    page: Optional[int] = None
    passage_id: str
    quote: str                                  # exact text from the passage
    section: Optional[str] = None
    heading: Optional[str] = None
    version_info: DocumentVersionInfo = Field(default_factory=DocumentVersionInfo)
    claim_supported: bool = True                # validated against stored passage
    page_verified: bool = True                  # True if cited page matches stored passage page
    cited_page: Optional[int] = None            # page number cited by the model
    source_type: DocumentSource = DocumentSource.OFFICIAL
    source_label: str = "Official university document"


class QueryResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: ResponseStatus
    answer: Optional[str] = None
    language: str = "en"
    citations: list[Citation] = Field(default_factory=list)
    evidence_status: EvidenceStatus
    query_analysis: Optional[QueryAnalysis] = None
    retrieval_summary: Optional[dict[str, Any]] = None
    feedback_subtype: Optional[FeedbackSubtype] = None
    repair_action: Optional[str] = None
    repaired_turn_index: Optional[int] = None
    latency_ms: float = 0.0
    model_used: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# API Request/Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    collection: list[DocumentSource] = Field(
        default=[DocumentSource.OFFICIAL],
        description="Which collections to search: official, upload, or both.",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User identity for scoping uploaded documents.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session identity for preserving multi-turn conversation context.",
    )
    conversation_history: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Client-provided prior conversation history if available.",
    )
    sequential_fallback: bool = Field(
        default=True,
        description="Enable sequential user-first retrieval with automatic official-corpus fallback.",
    )
    response_language: Optional[str] = None     # override detected language
    top_k: Optional[int] = Field(default=None, ge=1, le=50)
    academic_year: Optional[str] = None
    program: Optional[str] = None
    use_reranker: bool = True
    use_mqr: bool = False                       # off by default; router enables when needed
    use_pdr: bool = True
    debug: bool = False                         # include retrieval trace in response


class IngestRequest(BaseModel):
    source_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    version_info: DocumentVersionInfo = Field(default_factory=DocumentVersionInfo)


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    title: Optional[str] = None
    source_type: DocumentSource
    page_count: Optional[int] = None
    ingestion_status: IngestionStatus
    ingestion_timestamp: datetime
    version_info: DocumentVersionInfo


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    ollama_reachable: bool
    embedding_model_loaded: bool
    document_count: int
    passage_count: int
    child_passage_count: Optional[int] = None
    parent_passage_count: Optional[int] = None


# ─────────────────────────────────────────────────────────────────────────────
# Dataset / Evaluation Models
# ─────────────────────────────────────────────────────────────────────────────

class QAInstance(BaseModel):
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_question: str
    normalized_question: Optional[str] = None
    translated_question: Optional[str] = None
    query_language: QueryLanguage
    query_script: QueryScript = QueryScript.UNKNOWN
    question_type: QuestionType
    answerability: AnswerabilityLabel
    reference_answer: Optional[str] = None
    gold_passage_ids: list[str] = Field(default_factory=list)
    source_document_id: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    source_version: Optional[str] = None
    effective_date: Optional[str] = None
    program_applicability: Optional[list[str]] = None
    expected_response_language: QueryLanguage = QueryLanguage.ENGLISH
    validation_status: ValidationStatus = ValidationStatus.NEEDS_REVIEW
    review_status: ReviewStatus = ReviewStatus.PENDING
    reviewer_notes: Optional[str] = None
    gold_evidence_quotes: list[str] = Field(default_factory=list)
    split: Optional[str] = None                # train | dev | test
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EvaluationMetrics(BaseModel):
    """Container for one evaluation run's metrics."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    config: dict[str, Any] = Field(default_factory=dict)

    # Retrieval
    recall_at_5: Optional[float] = None
    recall_at_10: Optional[float] = None
    precision_at_5: Optional[float] = None
    mrr: Optional[float] = None
    ndcg_at_10: Optional[float] = None

    # Answer quality
    exact_match: Optional[float] = None
    token_f1: Optional[float] = None
    citation_precision: Optional[float] = None

    # Answerability
    answerability_precision: Optional[float] = None
    answerability_recall: Optional[float] = None
    answerability_f1: Optional[float] = None
    false_answer_rate: Optional[float] = None
    unnecessary_abstention_rate: Optional[float] = None

    # Per-language breakdown
    per_language: dict[str, dict[str, float]] = Field(default_factory=dict)

    # Efficiency
    mean_latency_ms: Optional[float] = None
    mean_retrieval_attempts: Optional[float] = None

    notes: str = ""
