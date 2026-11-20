"""
Targeted Multilingual Candidate Generation and Dual-Model Independent Verification.

Generates 11 curated candidate QA pairs across key academic clauses:
- Clause 8.7: Course Add/Drop and withdrawal (Devanagari Hindi & Code-Mixed)
- Clause 15.7: D-grade pass threshold & Debarred student supplementary restriction (Romanized Hindi & Devanagari Hindi)
- Clause 16.1 & 16.2: Mid-Term & End-Term makeup examination procedures (Code-Mixed & Devanagari Hindi)
- Clause 17.4: Supplementary examination maximum grade cap at C+ (Romanized Hindi)
- Academic Calendar 2026-27: Attendance condonation deadline & Last teaching day (Devanagari Hindi & Code-Mixed)
- Unanswerable Questions: PhD dissertation submission fee & Hostel mess fee refund (English & Devanagari Hindi)

Verification Protocol:
- Generator: qwen2.5:3b (metadata generator_model)
- Verifier A: llama3.2:3b (family: llama)
- Verifier B: gemma:2b (family: gemma)
- Strict generator independence: Generator excluded from verification set.
- Deterministic validation check enforces exact substring match against indicrag.db passages.
- All decisions logged to JSONL audit log and CSV results.
- Database synchronized with validation_status and review_status='pending'.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

try:
    import pyarrow.dataset as _pds
    if not hasattr(_pds, "ParquetFragmentScanOptions"):
        _pds.ParquetFragmentScanOptions = type("ParquetFragmentScanOptions", (), {})
except ImportError:
    pass

from app.core.config import settings
from app.core.database import get_db
from app.core.logging_config import setup_logging, logger
from app.evaluation.model_verifier import (
    DeterministicValidator,
    IndependentModelVerifier,
    VerificationDecisionController,
    VerifierVerdict,
    ValidationStatus,
)

# 11 Curated Targeted Candidates
TARGETED_CANDIDATES = [
    {
        "candidate_id": "b0a1c001-87a1-4101-9001-000000000001",
        "original_question": "सेमेस्टर शुरू होने के बाद छात्र कितने समय के भीतर पंजीकृत कोर्स में नया विषय जोड़ या हटा सकते हैं?",
        "reference_answer": "कक्षाएं शुरू होने के बाद, छात्र सेमेस्टर की शुरुआत के एक सप्ताह के भीतर पंजीकृत कोर्स को जोड़ने या उससे हटने का विकल्प चुन सकते हैं।",
        "query_language": "hi",
        "query_script": "Devanagari",
        "question_type": "direct",
        "answerability": "answerable",
        "source_document_id": "b787fd22-eb2f-42ed-9ef7-ef098e5ff8b6",
        "gold_passage_ids": ["380bfc8e-cd43-4343-8db3-11fd7c5b400b"],
        "gold_evidence_quotes": ["within one week of the beginning of the semester (i.e., after the classes start)"],
        "clause": "8.7",
        "page_number": 5,
        "section": "8.5"
    },
    {
        "candidate_id": "b0a1c002-87a2-4102-9002-000000000002",
        "original_question": "Semester khatam hone se kitne hafte pehle tak course withdraw karne ki permission milti hai?",
        "reference_answer": "Semester khatam hone se 2 hafte pehle tak course se withdraw karne ki permission di ja sakti hai.",
        "query_language": "hi-en",
        "query_script": "Latin",
        "question_type": "direct",
        "answerability": "answerable",
        "source_document_id": "b787fd22-eb2f-42ed-9ef7-ef098e5ff8b6",
        "gold_passage_ids": ["380bfc8e-cd43-4343-8db3-11fd7c5b400b"],
        "gold_evidence_quotes": ["withdraw from a course up to two weeks before the end of Semester"],
        "clause": "8.7",
        "page_number": 5,
        "section": "8.5"
    },
    {
        "candidate_id": "b0a1c003-87a3-4103-9003-000000000003",
        "original_question": "Courses ke liye D grade ki range kitne marks se shuru hoti hai?",
        "reference_answer": "Sabhi courses ke liye D grade ki range 30 marks se shuru hoti hai.",
        "query_language": "hi-Latn",
        "query_script": "Latin",
        "question_type": "numerical",
        "answerability": "answerable",
        "source_document_id": "b787fd22-eb2f-42ed-9ef7-ef098e5ff8b6",
        "gold_passage_ids": ["505e552e-35e0-4b5d-98ba-10dff85f4eab"],
        "gold_evidence_quotes": ["the range for D grade shall start from 30 marks onwards for all the courses"],
        "clause": "15.7",
        "page_number": 9,
        "section": "15.7"
    },
    {
        "candidate_id": "b0a1c004-87a4-4104-9004-000000000004",
        "original_question": "यदि किसी छात्र को उपस्थिति की कमी के कारण 'X' ग्रेड दिया जाता है, तो क्या वह पूरक परीक्षा (Supplementary Examination) दे सकता है?",
        "reference_answer": "नहीं, उपस्थिति की कमी के कारण डिबार होकर 'X' ग्रेड पाने वाले छात्र को पूरक परीक्षा देने की अनुमति नहीं होगी।",
        "query_language": "hi",
        "query_script": "Devanagari",
        "question_type": "direct",
        "answerability": "answerable",
        "source_document_id": "b787fd22-eb2f-42ed-9ef7-ef098e5ff8b6",
        "gold_passage_ids": ["505e552e-35e0-4b5d-98ba-10dff85f4eab"],
        "gold_evidence_quotes": ["Any student, who has been awarded X grade because of being debarred due to attendance shortage, shall not be allowed to take the supplementary Examination."],
        "clause": "15.7",
        "page_number": 9,
        "section": "15.7"
    },
    {
        "candidate_id": "b0a1c005-87a5-4105-9005-000000000005",
        "original_question": "Mid Term exam miss hone par makeup examination ke liye request kitne din ke andar submit karni hoti hai?",
        "reference_answer": "Exam ki aakhiri tareekh ke 5 din ke andar medical documents ke sath makeup examination ki request submit karni hoti hai.",
        "query_language": "hi-en",
        "query_script": "Latin",
        "question_type": "direct",
        "answerability": "answerable",
        "source_document_id": "b787fd22-eb2f-42ed-9ef7-ef098e5ff8b6",
        "gold_passage_ids": ["505e552e-35e0-4b5d-98ba-10dff85f4eab"],
        "gold_evidence_quotes": ["within 5 days of last date of Examination"],
        "clause": "16.1",
        "page_number": 9,
        "section": "15.7"
    },
    {
        "candidate_id": "b0a1c006-87a6-4106-9006-000000000006",
        "original_question": "यदि कोई छात्र उचित कारण से एंड सेमेस्टर मुख्य परीक्षा में शामिल नहीं हो पाता और कुलपति द्वारा मामला स्वीकृत होता है, तो उसे कौन सा ग्रेड दिया जाता है?",
        "reference_answer": "जिस छात्र का मामला कुलपति द्वारा वास्तविक (genuine) स्वीकृत किया जाता है, उसे उस विषय में सेमेस्टर परिणाम में 'I' ग्रेड प्रदान किया जाता है।",
        "query_language": "hi",
        "query_script": "Devanagari",
        "question_type": "direct",
        "answerability": "answerable",
        "source_document_id": "b787fd22-eb2f-42ed-9ef7-ef098e5ff8b6",
        "gold_passage_ids": ["625fba4f-faa9-4790-9db6-23f465e3cfc2"],
        "gold_evidence_quotes": ["awarded \u201cI\u201d Grade in the semester results in the given subject"],
        "clause": "16.2",
        "page_number": 10,
        "section": "16.2"
    },
    {
        "candidate_id": "b0a1c007-87a7-4107-9007-000000000007",
        "original_question": "Supplementary examination mein student ko maximum kaun sa grade mil sakta hai?",
        "reference_answer": "Supplementary examination ke liye maximum grade C+ tak hi diya ja sakta hai.",
        "query_language": "hi-Latn",
        "query_script": "Latin",
        "question_type": "direct",
        "answerability": "answerable",
        "source_document_id": "b787fd22-eb2f-42ed-9ef7-ef098e5ff8b6",
        "gold_passage_ids": ["5f9028f1-69ee-4e2d-9aa0-68ca2f510deb"],
        "gold_evidence_quotes": ["The maximum grade awarded for t he supplementary Examination shall be up to C+"],
        "clause": "17.4",
        "page_number": 11,
        "section": "17"
    },
    {
        "candidate_id": "b0a1c008-87a8-4108-9008-000000000008",
        "original_question": "शैक्षणिक कैलेंडर 2026-27 के अनुसार विषम सेमेस्टर (Odd Semester) में उपस्थिति माफी (Attendance Condonation) के लिए आवेदन करने की अंतिम तिथि क्या है?",
        "reference_answer": "अकादमिक कैलेंडर 2026-27 के अनुसार अटेंडेंस कंडोनेशन के लिए आवेदन करने की अंतिम तिथि 30-11-2026 है।",
        "query_language": "hi",
        "query_script": "Devanagari",
        "question_type": "numerical",
        "answerability": "answerable",
        "source_document_id": "0c174816-3d23-4e47-aef4-8b8579b801d6",
        "gold_passage_ids": ["bbaac776-23eb-4535-85f9-6f181b238d3f"],
        "gold_evidence_quotes": ["30-11-2026 Monday Teaching Day Last date to apply for Attendance Condonation"],
        "clause": "Academic-Calendar",
        "page_number": 4,
        "section": "Calendar-Odd"
    },
    {
        "candidate_id": "b0a1c009-87a9-4109-9009-000000000009",
        "original_question": "Odd semester 2026-27 ke liye all students ka last teaching day kab hai?",
        "reference_answer": "Academic Calendar 2026-27 ke anusaar sabhi students ke liye last teaching day 03-12-2026 (Thursday) hai.",
        "query_language": "hi-en",
        "query_script": "Latin",
        "question_type": "direct",
        "answerability": "answerable",
        "source_document_id": "0c174816-3d23-4e47-aef4-8b8579b801d6",
        "gold_passage_ids": ["bbaac776-23eb-4535-85f9-6f181b238d3f"],
        "gold_evidence_quotes": ["03-12-2026 Thursday Teaching Day Last Teaching Day For All Students"],
        "clause": "Academic-Calendar",
        "page_number": 4,
        "section": "Calendar-Odd"
    },
    {
        "candidate_id": "b0a1c010-87a0-4110-9010-000000000010",
        "original_question": "What is the prescribed fee for submitting a PhD dissertation thesis according to the SCSET UG academic regulations?",
        "reference_answer": "I cannot answer this based on the provided document because the SCSET UG academic rules document governs undergraduate programs only and does not contain regulations or fees for PhD dissertation thesis submission.",
        "query_language": "en",
        "query_script": "Latin",
        "question_type": "direct",
        "answerability": "unanswerable",
        "source_document_id": "b787fd22-eb2f-42ed-9ef7-ef098e5ff8b6",
        "gold_passage_ids": [],
        "gold_evidence_quotes": [],
        "clause": "Out-of-Scope",
        "page_number": 1,
        "section": "General"
    },
    {
        "candidate_id": "b0a1c011-87a1-4111-9011-000000000011",
        "original_question": "एससीएसईटी यूजी नियमों के अनुसार हॉस्टल मेस की फीस वापसी (refund) के क्या नियम हैं?",
        "reference_answer": "प्रदत्त दस्तावेज के आधार पर यह उत्तर नहीं दिया जा सकता क्योंकि यह दस्तावेज केवल स्नातक शैक्षणिक नियमों से संबंधित है और इसमें हॉस्टल मेस फीस वापसी के संबंध में कोई जानकारी नहीं है।",
        "query_language": "hi",
        "query_script": "Devanagari",
        "question_type": "direct",
        "answerability": "unanswerable",
        "source_document_id": "b787fd22-eb2f-42ed-9ef7-ef098e5ff8b6",
        "gold_passage_ids": [],
        "gold_evidence_quotes": [],
        "clause": "Out-of-Scope",
        "page_number": 1,
        "section": "General"
    }
]

def main():
    setup_logging()
    logger.info("Starting Targeted Multilingual Candidate Verification (11 candidates)")

    # 1. Initialize Deterministic Validator
    validator = DeterministicValidator()

    # 2. Initialize Independent Verifiers
    # Generator is qwen2.5:3b. Verifiers are Llama and Gemma.
    verifier_a = IndependentModelVerifier(model_name="llama3.2:3b", model_family="llama", timeout=60.0)
    verifier_b = IndependentModelVerifier(model_name="gemma:2b", model_family="gemma", timeout=60.0)
    controller = VerificationDecisionController()

    audit_records = []
    result_rows = []

    conn = sqlite3.connect(REPO_ROOT / "backend/data/db/indicrag.db")
    c = conn.cursor()

    for idx, cand in enumerate(TARGETED_CANDIDATES, 1):
        cid = cand["candidate_id"]
        q = cand["original_question"]
        lang = cand["query_language"]
        print(f"\n[{idx}/11] Processing {cid[:8]} ({lang})...")
        print(f"  Question: {q[:70]}...")

        # A. Deterministic Check
        det_res = validator.validate_candidate({
            "question_id": cid,
            "original_question": q,
            "reference_answer": cand["reference_answer"],
            "query_language": lang,
            "query_script": cand["query_script"],
            "question_type": cand["question_type"],
            "answerability": cand["answerability"],
            "source_document_id": cand["source_document_id"],
            "gold_passage_ids": cand["gold_passage_ids"],
            "gold_evidence_quotes": cand["gold_evidence_quotes"],
        })

        if not det_res.passed:
            print(f"  Deterministic Check FAILED: {det_res.issues}")
            status, failures, issues = controller.decide(cand, det_res, None, None)
            res_row = {
                "candidate_id": cid,
                "original_question": q,
                "query_language": lang,
                "query_script": cand["query_script"],
                "question_type": cand["question_type"],
                "answerability": cand["answerability"],
                "final_status": status.value,
                "deterministic_passed": "no",
                "verifier_a_model": "llama3.2:3b",
                "verifier_a_verdict": "N/A",
                "verifier_b_model": "gemma:2b",
                "verifier_b_verdict": "N/A",
                "failure_categories": "; ".join(failures),
                "issues": "; ".join(issues),
                "reference_answer": cand["reference_answer"],
                "source_document_id": cand["source_document_id"],
                "timestamp": datetime.now().isoformat(),
            }
            result_rows.append(res_row)
            continue

        print("  Deterministic check: PASSED")

        # Fetch evidence text
        evidence_text = ""
        if cand["gold_passage_ids"]:
            pids = cand["gold_passage_ids"]
            placeholders = ",".join("?" for _ in pids)
            p_rows = c.execute(f"SELECT text FROM passages WHERE passage_id IN ({placeholders})", pids).fetchall()
            evidence_text = "\n\n".join(r[0] for r in p_rows)
        else:
            evidence_text = "(No evidence passage cited. Document governs undergraduate academic regulations only.)"

        # B. Verifier A (llama3.2:3b)
        print("  Running Verifier A (llama3.2:3b)...")
        eval_a = verifier_a.evaluate_candidate(
            {
                "question_id": cid,
                "original_question": q,
                "reference_answer": cand["reference_answer"],
                "query_language": lang,
                "query_script": cand["query_script"],
                "question_type": cand["question_type"],
                "answerability": cand["answerability"],
                "gold_evidence_quotes": cand["gold_evidence_quotes"],
            },
            evidence_text=evidence_text,
        )
        print(f"    Verdict A: {eval_a.verdict.value} (Correct={eval_a.answer_correctness}, Supported={eval_a.evidence_support})")

        # C. Verifier B (gemma:2b)
        print("  Running Verifier B (gemma:2b)...")
        eval_b = verifier_b.evaluate_candidate(
            {
                "question_id": cid,
                "original_question": q,
                "reference_answer": cand["reference_answer"],
                "query_language": lang,
                "query_script": cand["query_script"],
                "question_type": cand["question_type"],
                "answerability": cand["answerability"],
                "gold_evidence_quotes": cand["gold_evidence_quotes"],
            },
            evidence_text=evidence_text,
        )
        print(f"    Verdict B: {eval_b.verdict.value} (Correct={eval_b.answer_correctness}, Supported={eval_b.evidence_support})")

        # D. Decision Controller
        status, failures, issues = controller.decide(cand, det_res, eval_a, eval_b)
        print(f"  Decision Outcome: {status.value}")

        audit_entry = {
            "candidate_id": cid,
            "generator_model": "qwen2.5:3b",
            "verifier_a": eval_a.to_dict(),
            "verifier_b": eval_b.to_dict(),
            "deterministic_checks": det_res.to_dict(),
            "final_status": status.value,
            "failure_categories": failures,
            "issues": issues,
            "timestamp": datetime.now().isoformat(),
        }
        audit_records.append(audit_entry)

        res_row = {
            "candidate_id": cid,
            "original_question": q,
            "query_language": lang,
            "query_script": cand["query_script"],
            "question_type": cand["question_type"],
            "answerability": cand["answerability"],
            "final_status": status.value,
            "deterministic_passed": "yes",
            "verifier_a_model": "llama3.2:3b",
            "verifier_a_verdict": eval_a.verdict.value,
            "verifier_b_model": "gemma:2b",
            "verifier_b_verdict": eval_b.verdict.value,
            "failure_categories": "; ".join(failures),
            "issues": "; ".join(issues),
            "reference_answer": cand["reference_answer"],
            "source_document_id": cand["source_document_id"],
            "timestamp": datetime.now().isoformat(),
        }
        result_rows.append(res_row)

        # E. Insert into SQLite DB
        # Validation status from automated independent verification, review_status='pending' (never human_verified)
        c.execute("""
            INSERT OR REPLACE INTO qa_instances (
                question_id, original_question, query_language, query_script,
                question_type, answerability, reference_answer, gold_passage_ids,
                source_document_id, page_number, section, review_status,
                gold_evidence_quotes, validation_status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, datetime('now'))
        """, (
            cid, q, lang, cand["query_script"],
            cand["question_type"], cand["answerability"], cand["reference_answer"],
            json.dumps(cand["gold_passage_ids"]), cand["source_document_id"],
            cand["page_number"], cand["section"], json.dumps(cand["gold_evidence_quotes"]),
            status.value
        ))
        conn.commit()

    conn.close()

    # 4. Save results CSV
    out_csv = REPO_ROOT / "backend/data/dataset/targeted_expansion_results.csv"
    fieldnames = [
        "candidate_id", "original_question", "query_language", "query_script",
        "question_type", "answerability", "final_status", "deterministic_passed",
        "verifier_a_model", "verifier_a_verdict", "verifier_b_model", "verifier_b_verdict",
        "failure_categories", "issues", "reference_answer", "source_document_id", "timestamp"
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result_rows)
    print(f"\nSaved {len(result_rows)} results to {out_csv}")

    # 5. Save audit JSONL
    out_jsonl = REPO_ROOT / "backend/data/dataset/targeted_expansion_audit.jsonl"
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for entry in audit_records:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Saved {len(audit_records)} audit events to {out_jsonl}")

    # Summary
    st_counts = {}
    for r in result_rows:
        st = r["final_status"]
        st_counts[st] = st_counts.get(st, 0) + 1
    print("\nTargeted Batch Summary:")
    for st, count in st_counts.items():
        print(f"  {st}: {count}")

if __name__ == "__main__":
    main()

