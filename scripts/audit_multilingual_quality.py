import sys
import json
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path("backend").resolve()))

from app.query.processor import process_query
from app.retrieval.multi_hop_reasoner import MultiHopReasoner, answer_multi_hop_question

async def audit_multilingual():
    reasoner = MultiHopReasoner(max_hops=3, max_evidence_items=12)

    queries = [
        {
            "language": "English",
            "query": "When do odd semester end semester examinations start and finish?",
            "semantic_intent": "Start and conclusion dates of Odd Semester 2026-27 End Semester Examination",
            "expected_evidence": "Academic Calendar 2026-27, Page 4: 10-12-2026 to 22-12-2026",
        },
        {
            "language": "Devanagari Hindi",
            "query": "विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?",
            "semantic_intent": "Start and conclusion dates of Odd Semester 2026-27 End Semester Examination",
            "expected_evidence": "Academic Calendar 2026-27, Page 4: 10-12-2026 to 22-12-2026",
        },
        {
            "language": "Romanized Hindi",
            "query": "Odd semester end semester exams kab start aur finish hote hain?",
            "semantic_intent": "Start and conclusion dates of Odd Semester 2026-27 End Semester Examination",
            "expected_evidence": "Academic Calendar 2026-27, Page 4: 10-12-2026 to 22-12-2026",
        },
        {
            "language": "Hinglish",
            "query": "Odd semester examinations ki start date aur end date kya hai?",
            "semantic_intent": "Start and conclusion dates of Odd Semester 2026-27 End Semester Examination",
            "expected_evidence": "Academic Calendar 2026-27, Page 4: 10-12-2026 to 22-12-2026",
        },
    ]

    results = {}
    for item in queries:
        lang = item["language"]
        q = item["query"]
        print(f"\nEvaluating language: {lang} -> '{q}'")
        qa = process_query(q)
        ev_set = reasoner.reason(qa)

        # 1. Retrieval Verification
        total_retrieved = len(ev_set.all_passages)
        has_start_date = any("10-12-2026" in p.text for p in ev_set.all_passages)
        has_end_date = any("22-12-2026" in p.text for p in ev_set.all_passages)
        has_cal_page4 = any(p.page_number == 4 and "calendar" in (p.document_filename or "").lower() for p in ev_set.all_passages)
        retrieval_success = has_start_date and has_end_date and has_cal_page4

        # 2. Answer Generation & Correctness
        try:
            ans_response = await answer_multi_hop_question(query=q)
            answer_text = ans_response.answer or ""
            ans_contains_start = any(s in answer_text for s in ["10-12-2026", "10 दिसंबर", "10 Dec", "10th December", "10"])
            ans_contains_end = any(s in answer_text for s in ["22-12-2026", "22 दिसंबर", "22 Dec", "22nd December", "22"])
            answer_correctness = ans_contains_start and ans_contains_end
            citations = ans_response.citations or []
            valid_citations = [
                c for c in citations 
                if "calendar" in (c.filename or "").lower() and c.page in (4, 5)
            ]
            citation_correctness = len(citations) > 0 and len(valid_citations) == len(citations)
        except Exception as exc:
            answer_text = f"GENERATION_ERROR: {str(exc)}"
            answer_correctness = False
            citations = []
            valid_citations = []
            citation_correctness = False

        results[lang] = {
            "query": q,
            "detected_language": qa.detected_language.value if hasattr(qa.detected_language, "value") else str(qa.detected_language),
            "passages_retrieved": total_retrieved,
            "retrieval_success": retrieval_success,
            "has_start_date_in_evidence": has_start_date,
            "has_end_date_in_evidence": has_end_date,
            "answer_correctness": answer_correctness,
            "answer_excerpt": answer_text[:200],
            "total_citations": len(citations),
            "valid_calendar_citations": len(valid_citations),
            "citation_correctness": citation_correctness,
        }
        print(f"  Retrieval: {retrieval_success} ({total_retrieved} passages)")
        print(f"  Answer Correctness: {answer_correctness}")
        print(f"  Citation Correctness: {citation_correctness} ({len(valid_citations)}/{len(citations)})")

    with open("docs/r4_1_multilingual_audit.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nSaved multilingual audit to docs/r4_1_multilingual_audit.json")

if __name__ == "__main__":
    asyncio.run(audit_multilingual())
