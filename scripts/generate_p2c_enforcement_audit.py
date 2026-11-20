import pandas as pd

# We analyze the runtime code paths in generator.py and claim_grounding.py:
# Path 1: Claim marked CONTRADICTED by claim_verifier.verify_claims()
# Path 2: Claim marked INSUFFICIENT_SUPPORT by claim_verifier.verify_claims()
# Path 3: Generated answer lacking [Source: ...] markers entirely (zero citations matched)
# Path 4: Controller state is PARTIAL but generator emits full unhedged claim
# Path 5: Controller state is SUFFICIENT but retrieved evidence doesn't support a hallucinated sub-clause

audit_records = [
    {
        "pipeline_stage": "Citation & Claim Validation",
        "tested_condition": "Claim marked CONTRADICTED by claim_grounding.py",
        "current_runtime_behavior": "Citation object sets claim_supported=False, but generator.py returns the raw text in QueryResponse(answer=cleaned_answer) with status=ResponseStatus.ANSWERED.",
        "enforcement_defect_present": True,
        "leakage_severity": "HIGH",
        "defect_description": "Contradicted factual claim is NOT stripped or suppressed from the user-facing answer string. The UI or client sees a fully answered response, with contradiction hidden in metadata.",
        "proposed_minimal_patch": "In generator.py, if claim_res.contains_contradiction is True: (a) strip contradicted sentences from cleaned_answer, or (b) downgrade resp_status to ResponseStatus.UNANSWERABLE with an explicit contradiction warning.",
        "verification_mechanism": "Unit test asserting that QueryResponse.answer cannot contain sentences flagged as CONTRADICTED."
    },
    {
        "pipeline_stage": "Citation & Claim Validation",
        "tested_condition": "Claim marked INSUFFICIENT_SUPPORT (low grounding ratio < 0.40)",
        "current_runtime_behavior": "Citation object sets claim_supported=False, but answer string is emitted without hedging or redaction.",
        "enforcement_defect_present": True,
        "leakage_severity": "MEDIUM",
        "defect_description": "Unsupported claims appear verbatim in the final answer if at least one citation marker was present. If grounding ratio < 0.40, the answer should be converted to a cautious partial disclosure.",
        "proposed_minimal_patch": "If claim_res.grounding_ratio < 0.40, enforce ResponseStatus.PARTIAL and prepend an uncertainty disclaimer: 'Based on available official records, full verification was not possible for all points.'",
        "verification_mechanism": "Assert that responses with grounding_ratio < 0.40 receive disclaimer headers."
    },
    {
        "pipeline_stage": "Citation Extraction",
        "tested_condition": "LLM emits answer without any [Source: ...] citation markers",
        "current_runtime_behavior": "pattern.finditer finds 0 matches; loop does not run; returns citations=[] and cleaned_answer=raw_output.",
        "enforcement_defect_present": True,
        "leakage_severity": "CRITICAL",
        "defect_description": "If the model hallucinates an answer and forgets citation tags, citations=[] is returned with ResponseStatus.ANSWERED. The answer completely bypasses citation grounding checks!",
        "proposed_minimal_patch": "In generator.py, if evidence_decision.status == SUFFICIENT but len(citations) == 0: reject generation and retry with citation-enforcing temperature=0 prompt, or fallback to UNANSWERABLE.",
        "verification_mechanism": "Assert that responses with 0 citations when evidence was SUFFICIENT trigger a regeneration or rejection."
    },
    {
        "pipeline_stage": "Controller-Generator Handoff",
        "tested_condition": "EvidenceController returns CONFLICTING",
        "current_runtime_behavior": "Generator suppresses standard direct answer and returns ResponseStatus.CONFLICTING_VERSIONS with version-differentiated disclosure.",
        "enforcement_defect_present": False,
        "leakage_severity": "NONE (Properly Enforced)",
        "defect_description": "Controller-level override is strictly enforced at generator.py line 209: if status == CONFLICTING, returns conflicting disclosure without hallucinated resolution.",
        "proposed_minimal_patch": "Maintain current controller-level abstention logic.",
        "verification_mechanism": "Verified in test_m6_phase2b_scoring_and_controller.py."
    },
    {
        "pipeline_stage": "Controller-Generator Handoff",
        "tested_condition": "EvidenceController returns CLARIFICATION_REQUIRED",
        "current_runtime_behavior": "EvidenceController flags clarification_needed, but generator currently defaults to ResponseStatus.ANSWERED if status is not explicitly handled.",
        "enforcement_defect_present": True,
        "leakage_severity": "HIGH",
        "defect_description": "generator.py lines 289-295 checks only CONFLICTING and PARTIAL, falling back to ANSWERED for CLARIFICATION_REQUIRED!",
        "proposed_minimal_patch": "Add explicit elif evidence_decision.status == EvidenceStatus.CLARIFICATION_REQUIRED: resp_status = ResponseStatus.CLARIFICATION_REQUIRED, returning a structured clarification question instead of a speculative answer.",
        "verification_mechanism": "Assert that CLARIFICATION_REQUIRED yields ResponseStatus.CLARIFICATION_REQUIRED."
    }
]

df_audit = pd.DataFrame(audit_records)
df_audit.to_csv('backend/data/experiments/m6/m6_phase2c_answer_enforcement_audit.csv', index=False)
print("Saved backend/data/experiments/m6/m6_phase2c_answer_enforcement_audit.csv with", len(df_audit), "records.")

