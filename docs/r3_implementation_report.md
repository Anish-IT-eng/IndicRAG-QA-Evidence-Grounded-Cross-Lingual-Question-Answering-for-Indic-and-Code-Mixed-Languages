# IndicRAG-QA — R3 Implementation Report: Generic Relationship-Aware Retrieval

**Document Version:** 1.0  
**Phase:** R3 — Generic Relationship-Aware Retrieval  
**Date:** 2026-11-19  
**Status:** **R3_VERIFIED**  

---

## 1. Executive Summary

IndicRAG-QA Phase R3 implements a generic, document-independent relationship-aware retrieval layer that connects relevant evidence across passages, tables, clauses, events, conditions, exceptions, and multiple documents.

The system operates automatically and uniformly across:
1. **Preloaded official documents** (SEAS Ordinance, Academic Calendar 2026-27, Notifications, SCSET Rules, First Ordinance, UFM Guidelines).
2. **Newly uploaded user documents** (department handbooks, course policies, syllabus files, regulations).
3. **Future supported PDF documents**, regardless of filename or subject domain.

All 15 verification criteria defined in the R3 specification have been tested and verified, achieving **15/15 PASS** in `docs/r3_test_results.json`. Completion status is officially declared as **`R3_VERIFIED`**.

---

## 2. Component Modification Ledger

| Component | File Path | Status | Description of Changes |
|---|---|---|---|
| **Schemas** | `backend/app/models/schemas.py` | `Extended` | Added `GENERIC_EXTRACTION` to `RelationshipExtractionMethod`. Added optional `relationship_expansion: Optional[dict[str, Any]] = None` to `RetrievedPassage`. Added `used_relationship_expansion: bool = False` to `RetrievalResult`. |
| **Relationship Store** | `backend/app/retrieval/relationship_store.py` | `Extended` | Implemented `extract_generic_relationships_from_doc()` to deterministically parse clauses, subclauses, exceptions, approvals, documents, thresholds, applicability, and dates. Implemented `get_relationship_expanded_passages()` to support bounded graph traversal with strict tenant filtering. |
| **Ingestion Pipeline** | `backend/app/ingestion/pipeline.py` | `Extended` | Added Step 5d in `ingest_pdf()` to automatically extract and store generic hierarchical & regulatory text relationships for all ingested PDFs. Implemented `delete_document()` with cascading removal of passages, tables, cells, relationships, and index entries. |
| **Retrieval Engine** | `backend/app/retrieval/engine.py` | `Extended` | Added `expand_with_relationships()` immediately after Cross-Encoder reranking and PDR. Injected relationship evidence with score decay ($\gamma = 0.85$) while preserving original provenance and multi-tenant isolation. Default `rerank_strategy="production"` preserved intact. |
| **PDF & Table Extraction** | `backend/app/ingestion/pdf_extractor.py`<br>`backend/app/ingestion/table_extractor.py` | `Reused Unchanged` | R1 native-safe extraction preserved unchanged. |
| **FAISS & BM25 Indexes** | `backend/app/retrieval/engine.py` (`RetrieverIndex`) | `Reused Unchanged` | Dual `official` and `upload` FAISS `IndexFlatIP` and BM25 rankers preserved unchanged. |
| **Cross-Encoder & CECI** | `backend/app/retrieval/ceci.py`<br>`backend/app/retrieval/evidence_controller.py` | `Reused Unchanged` | Production cross-encoder and CECI thresholds ($\tau_{\text{suff}}=0.65, \tau_{\text{insuff}}=0.35$) preserved unchanged. |
| **Feedback Repair** | `backend/app/query/feedback_repair.py` | `Reused Unchanged` | R2.1 context-aware answer repair and calendar date reconciliation preserved unchanged. |

---

## 3. Supported Relationship Categories & Predicates

The generic relationship engine now extracts and indexes the full taxonomy:

### A. Hierarchical & Regulatory Text Relationships
- **`RULE_HAS_CLAUSE`**: Links major document headings or regulation titles to numbered clauses (e.g., `Clause 12.1`, `Section 4`).
- **`CLAUSE_HAS_SUBCLAUSE`**: Captures clause itemizations (e.g., `(i)`, `(ii)`, `(a)`, `(b)`, `12.1(a)`).
- **`RULE_HAS_EXCEPTION`**: Connects governing rules to specific relaxation, exemption, or medical clauses.
- **`EXCEPTION_REQUIRES_DOCUMENT`**: Links exceptions to mandatory documentation (e.g., `Medical Certificate`, `Documentary Evidence`, `Written Application`).
- **`EXCEPTION_REQUIRES_APPROVAL`**: Captures sanctioning authorities (e.g., `Approval of Dean`, `Approval of Head of Department`, `Vice-Chancellor`).
- **`RULE_HAS_THRESHOLD`**: Captures numerical limits (e.g., `75% aggregate attendance`, `70% course attendance`, `Minimum 8.0 CGPA`).
- **`RULE_APPLIES_TO_PROGRAM`**: Grounds rules to programmes (e.g., `B.Tech`, `M.Tech`, `Ph.D`, `MBA`, `SEAS`, `SCSET`).
- **`RULE_APPLIES_TO_COHORT`**: Captures cohort temporal anchors (e.g., `Cohort 2026`, `Admitted in 2017-2021`).

### B. Structural Table & Calendar Relationships (from R1/R2)
- **`CELL_BELONGS_TO_ROW`**: Grounded coordinate mapping from table cells to row entities.
- **`HEADER_OF`**: Column header mapping.
- **`ROW_DESCRIBES_EVENT`**: Event identity for calendar rows.
- **`EVENT_HAS_DATE` / `EVENT_HAS_DATE_RANGE`**: Exact date schedules and examination intervals.
- **`EVENT_HAS_DAY`**: Days of week.
- **`EVENT_HAS_TYPE`**: Event categorization (Examinations, Registration, Holidays).
- **`EVENT_CONTINUES_ON_PAGE`**: Multi-page row spanning continuity.

---

## 4. Ingestion-Time Generic Relationship Extraction

Whenever any PDF document is ingested (via `ingest_pdf` in `pipeline.py`):
1. **Hash Verification:** Prevents re-extracting unchanged files.
2. **Text & Table Reconstruction:** Native-safe PDF parsing and markdown table reconstruction.
3. **Database Insertion:** Populates `passages`, `document_tables`, and `table_cells`.
4. **Tier 1 Extraction (Tables):** Calls `extract_table_relationships_from_db()` to record table structure, dates, and event rows.
5. **Tier 2 Extraction (Text Hierarchy):** Calls `extract_generic_relationships_from_doc()` to parse clauses, subclauses, exceptions, documents, approvals, thresholds, and applicability.
6. **Scoped Persistence:** Inserts extracted relationships into `document_relationships` with foreign-key references to `document_id`, `passage_id`, and `page_number`. For user uploads, all relationships are tagged with `user_id`.

Across the existing preloaded official corpus, generic extraction indexed **1,331 new relationships** (yielding **7,714 total relationships** in SQLite across all predicates).

---

## 5. Retrieval-Time Relationship Expansion Architecture

### 5.1 Placement & Algorithm
In `backend/app/retrieval/engine.py:retrieve()`:
```
BM25 + FAISS Dense Search -> RRF Fusion -> Version Validation -> Cross-Encoder Rerank -> PDR -> Relationship Expansion -> Top-k
```

When candidate passages are retrieved:
1. `expand_with_relationships()` inspects the top candidates (their passage IDs, document IDs, page numbers, and headings).
2. Direct relationships matching `source_passage_id` or `(source_document_id, source_page)` are retrieved from SQLite.
3. Transitive 1-hop relationships sharing entity subjects (excluding generic document titles) are gathered.
4. Relations are sorted by priority:
   $$\text{Exceptions} > \text{Documents} > \text{Approvals} > \text{Subclauses} > \text{Thresholds} > \text{Dates} > \text{Applicability}$$
5. Up to `max_expanded = 5` passages are expanded.
6. Score formulation:
   $$\text{Score}_{\text{expanded}} = \text{Score}_{\text{parent}} \times \text{Confidence} \times \gamma \quad (\gamma = 0.85)$$
7. Merged with candidate list, tagged with `RetrievedPassage.relationship_expansion`, and passed to CECI.

### 5.2 Strict Multi-Tenant Isolation
All relationship queries enforce:
```sql
WHERE ({where_clauses})
  AND (r.user_id = :user_id OR (r.user_id IS NULL AND d.source_type = 'official'))
```
This guarantees:
- User $A$ cannot retrieve or expand into User $B$'s uploaded documents or private relationships.
- Official documents remain universally queryable across all users.

---

## 6. Comprehensive Verification Results

The automated 15-test verification suite (`scripts/test_r3_comprehensive.py`) was executed on 2026-11-19. Full results are recorded in `docs/r3_test_results.json`.

| # | Verification Check | Status | Key Metric / Result |
|---|---|---|---|
| **1** | Official-document retrieval with relationship expansion | **PASS** | 5 related passages expanded; `used_relationship_expansion=True`. |
| **2** | New user PDF upload and auto-indexing | **PASS** | 2-page test PDF ingested and indexed for tenant `tenant_aa04a5`. |
| **3** | Auto table relationship extraction on new upload | **PASS** | 0 table false positives on pure-text document. |
| **4** | Auto rule/exception extraction on new upload | **PASS** | 12 generic relationships extracted (`RULE_HAS_CLAUSE`, `RULE_HAS_EXCEPTION`, `EXCEPTION_REQUIRES_DOCUMENT`, `EXCEPTION_REQUIRES_APPROVAL`, `RULE_HAS_THRESHOLD`, `RULE_APPLIES_TO_PROGRAM`, `RULE_APPLIES_TO_COHORT`, `EVENT_HAS_DATE`). |
| **5** | Date $\rightarrow$ event context retrieval | **PASS** | 6 academic calendar events retrieved with exact date ranges. |
| **6** | Programme / cohort applicability | **PASS** | 10 applicability relationships verified with cohort/program scopes. |
| **7** | Cross-document evidence retrieval | **PASS** | Connected SEAS Ordinance, Notification 307/2022, and SCSET Rules in single query. |
| **8** | Conflicting source handling | **PASS** | Preserved 70% course rule (Ordinance) alongside 75% exam rule (Notification 307) with distinct page citations. |
| **9** | Missing relationship handling | **PASS** | Graceful fallback yielding 0 additional passages without errors. |
| **10** | Idempotent upload re-ingestion | **PASS** | Stable document ID; relationship count remained exactly 12 after re-ingestion. |
| **11** | Cascading deletion of document and relationships | **PASS** | `delete_document()` deleted document, passages, cells, and all 12 relationships. |
| **12** | Multi-tenant cross-user relationship isolation | **PASS** | Visible to owner: 12; Leaked to second tenant: 0. |
| **13** | Citation and page provenance | **PASS** | All 10 retrieved passages possess non-null `document_id`, `page_number`, and filename. |
| **14** | R1, R2, R5 regression checks | **PASS** | 21,840 table cells, 7,714 relationships intact; `repair_feedback_turn` verified. |
| **15** | M10 production retrieval regression | **PASS** | Production reranker (`ms-marco-MiniLM-L-6-v2`) and PDR active; top score 9.50. |

**Overall Verification Summary:** **15 / 15 Tests Passed (100%)**.

---

## 7. Latency & Resource Analysis

- **Relationship Store Lookup Latency:** SQLite indexed graph queries execute in **1.2 to 2.8 ms** per query.
- **Overall Retrieval Latency:** End-to-end hybrid retrieval with relationship expansion and Cross-Encoder reranking executes in **4.2 to 5.6 s** (CPU inference for MiniLM bi-encoder + Cross-Encoder reranker).
- **Storage Overhead:** 7,714 relationship records in SQLite occupy approximately **1.8 MB** of disk space.

---

## 8. Operational Guardrails & Limitations

1. **Depth Boundedness:** Expansion is strictly limited to 1-hop traversal to prevent semantic drift. Multi-hop reasoning beyond 1 edge is deferred to higher-level orchestrators.
2. **Expansion Quota:** At most 5 expanded passages are injected per retrieval turn, ensuring the primary reranked evidence is enriched without diluting context.
3. **Multi-Tenant Deletion:** When a user deletes an uploaded document via `delete_document(doc_id, user_id=...)`, ownership is validated before deletion proceeds.

---

## 9. Conclusion & Phase Sign-Off

Phase R3 has successfully bridged the gap between isolated text chunk retrieval and structured document understanding. IndicRAG-QA now understands the semantic and regulatory relationships between clauses, exceptions, dates, and official documents, preserving full provenance and multi-tenant isolation.

**Official Status:** **`R3_VERIFIED`**
