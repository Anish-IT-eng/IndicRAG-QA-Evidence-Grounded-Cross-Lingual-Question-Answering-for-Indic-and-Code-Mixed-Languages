# IndicRAG-QA — R4 Multi-Hop Evidence Reasoning Design

**Document Version:** 1.0  
**Phase:** R4 — Bounded Multi-Hop Evidence Reasoning  
**Date:** 2026-11-19  
**Status:** DESIGN APPROVED  

---

## 1. Objectives & Architectural Principles

IndicRAG-QA Phase R4 implements bounded, evidence-grounded multi-hop reasoning using the existing R1, R2, R3, and R5 architecture.

### Core Principles
1. **Bounded Traversal:** Maximum of 3 hops from the original query evidence. No unrestricted graph exploration.
2. **Cycle & Duplication Prevention:** Explicit tracking of visited passage IDs, visited relationship IDs, and traversed subjects.
3. **Strict Scope & Compatibility Guardrails:** Evidence items are tagged with institutional scope (`course_level`, `exam_eligibility`, `programme_specific`, `university_wide`). Course-level exceptions must never be transferred to examination eligibility.
4. **Honest Abstention:** When an intermediate hop (such as approval authority, prerequisite documentation, or cohort specification) is missing, the system detects the gap and abstains or asks for clarification rather than hallucinating unsupported facts.
5. **Multi-Tenant Isolation at Every Hop:** Every graph traversal step strictly queries:
   ```sql
   WHERE (r.user_id = :user_id OR (r.user_id IS NULL AND d.source_type = 'official'))
   ```
6. **Separation of Latencies:** Measures and reports `retrieval_ms`, `reasoning_ms`, and `generation_ms` independently.

---

## 2. Multi-Hop Reasoning Architecture

```mermaid
flowchart TD
    Q[User Query] --> Seed[Step 1: Seed Retrieval\nR3 Hybrid Retrieval & CE Rerank]
    Seed --> GapAnalysis[Step 2: Information Need & Target Gap Identification]
    
    subgraph TraversalLoop [Step 3: Bounded Traversal Loop: Hops 1 to 3]
        GapAnalysis --> Frontier[Frontier Expansion]
        Frontier --> StoreQuery[SQLite Relationship Store Query\n(Tenant Scoped)]
        StoreQuery --> EdgeEval[Predicate Priority Evaluation]
        EdgeEval --> CycleCheck{Visited / Cycle?}
        CycleCheck -- No --> ScoreDecay[Score Decay: gamma = 0.85 per hop]
        CycleCheck -- Yes --> Prune[Prune Edge]
        ScoreDecay --> NextFrontier[Add to Traversal Path]
    end
    
    NextFrontier --> ScopeCheck[Step 4: Scope Compatibility & Temporal Validation]
    ScopeCheck --> ConflictDetect[Step 5: Conflict & Contradiction Detection]
    ConflictDetect --> SufficiencyEval[Step 6: Multi-Hop Completeness Evaluation]
    
    SufficiencyEval -->|Complete & Compatible| ValidSet[MultiHopEvidenceSet]
    SufficiencyEval -->|Missing Intermediate Evidence| AbstainDecision[EvidenceDecision: INSUFFICIENT / CLARIFICATION]
    SufficiencyEval -->|Contradiction Detected| ConflictSet[MultiHopEvidenceSet with Conflict Attribution]
    
    ValidSet & ConflictSet --> Gen[Ollama Answer Generation with Provenance Grounding]
    AbstainDecision --> DirectAbstain[Immediate Honest Abstention / Clarification Response]
```

---

## 3. Detailed Traversal Mechanics

### 3.1 Frontier & Hop Progression
Let $F_0$ be the initial set of seed passages retrieved by R3 retrieval (top $k=5$).

At hop $h \in \{1, 2, 3\}$:
1. Extract entity subjects, clause numbers, and passage IDs from frontier $F_{h-1}$.
2. Query `document_relationships` for outgoing and transitive edges:
   ```sql
   SELECT r.*, d.filename as document_filename, d.source_type
   FROM document_relationships r
   JOIN documents d ON r.source_document_id = d.document_id
   WHERE (r.source_passage_id IN (:frontier_pids) OR r.subject_id IN (:frontier_subjects))
     AND (r.user_id = :user_id OR (r.user_id IS NULL AND d.source_type = 'official'))
   ```
3. Filter through `VisitedTracker`:
   - If `r.relationship_id in visited_rel_ids`, drop.
   - If target passage `p_target in visited_pids`, drop (cycle prevention).
4. Fetch target passage content from `passages` table (or construct coordinate-backed table evidence).
5. Calculate decayed candidate score:
   $$S_h = S_{h-1} \times \text{Confidence}(r) \times \gamma \quad (\gamma = 0.85)$$
6. Add newly discovered items to $F_h$.
7. Stop condition:
   - All query target requirements are satisfied; OR
   - Hop count reaches 3; OR
   - Maximum evidence items (default 12) reached; OR
   - Frontier $F_h$ is empty.

### 3.2 Predicate Priority Matrix
Edges are traversed according to semantic necessity:
$$\text{Exceptions} > \text{Prerequisites} > \text{Documents} > \text{Approvals} > \text{Subclauses} > \text{Thresholds} > \text{Dates} > \text{Applicability}$$

---

## 4. Reasoning Scenarios & Invariant Rules

### Scenario A: Academic Calendar Event Schedules
- **Hop 1:** Retrieve calendar event row / table entry (`ROW_DESCRIBES_EVENT`, `EVENT_HAS_TYPE`).
- **Hop 2:** Traverse to start date (`EVENT_HAS_DATE`), day of week (`EVENT_HAS_DAY`), and academic year.
- **Hop 3:** Traverse to conclusion date (`EVENT_HAS_DATE_RANGE`, multi-day span) or linked make-up schedule.
- **Invariant:** Connect exact start date, conclusion date, and page provenance. Never truncate a 10-day exam span to a single day.

### Scenario B: Attendance Rules vs Examination Eligibility
- **Hop 1:** Base attendance regulation in programme ordinance (e.g., Clause 30.1: 70% course attendance $\rightarrow$ awarded 'X' grade).
- **Hop 2:** University-wide examination eligibility notification (Notification 307/2022: 75% aggregate attendance $\rightarrow$ debarred from exams).
- **Hop 3:** Separate consequence evaluation: Course-level failure vs exam hall debarment.
- **Invariant:** Keep institutional scopes separate. Tag each rule with its distinct consequence.

### Scenario C: Medical Exception & Condonation Workflow
- **Hop 1:** Base attendance rule (`RULE_HAS_CLAUSE`).
- **Hop 2:** Medical exception clause (`RULE_HAS_EXCEPTION` $\rightarrow$ up to 10% relaxation).
- **Hop 3:** Required documentation (`EXCEPTION_REQUIRES_DOCUMENT` $\rightarrow$ Medical Certificate) and sanctioning authority (`EXCEPTION_REQUIRES_APPROVAL` $\rightarrow$ Dean of School / HoD).
- **Invariant:** Course-level medical relaxation does NOT grant automatic exemption from university-wide 75% exam eligibility.

### Scenario D: Historical & Cohort Applicability
- **Hop 1:** Query identifies candidate regulations.
- **Hop 2:** Trace cohort applicability (`RULE_APPLIES_TO_COHORT`) and program applicability (`RULE_APPLIES_TO_PROGRAM`).
- **Hop 3:** Check superseding circulars (`DOCUMENT_SUPERSEDES_RULE`, `DOCUMENT_CLARIFIES_RULE`).
- **Invariant:** If cohort or programme is not specified in the query and materially changes the applicable rule (e.g., 2017 Ordinance 70% vs 2022 Notification 75%), return `CLARIFICATION_REQUIRED`.

### Scenario E: Generic User-Uploaded Documents
- Operates automatically on any uploaded PDF without hardcoded document titles or filenames.
- Traverses dynamically extracted clauses, exceptions, and prerequisite links.

### Scenario F: Contradictory Evidence
- When two documents report conflicting dates, numbers, or rules for the same subject:
  Both sources are retained, the conflict is explicitly recorded, and both alternatives are presented with citations.

### Scenario G: Insufficient Evidence
- When an intermediate hop cannot be proven from evidence (e.g. required approval authority is not stated):
  The system declares `INSUFFICIENT` and abstains from inventing the missing link.

---

## 5. Performance, Provenance & Tenant Guardrails

- **Latency Budget:**
  - Retrieval: $< 5.0$ s (Cross-Encoder reranking)
  - Multi-Hop Graph Traversal: $< 20$ ms (indexed SQLite lookups)
  - Generation: $< 8.0$ s
- **Provenance Preservation:** Every expanded item carries `document_id`, `page_number`, `document_filename`, `hop_index`, and `traversed_predicate`.
- **Multi-Tenant Boundaries:** User $A$ cannot access User $B$'s uploaded documents or private relationships at any hop.
