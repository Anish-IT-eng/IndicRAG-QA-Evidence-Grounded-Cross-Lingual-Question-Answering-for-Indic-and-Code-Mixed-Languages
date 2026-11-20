import sys, asyncio
sys.path.insert(0, 'backend')
from app.generation.generator import _call_ollama, _SYSTEM_PROMPT, _format_evidence
from app.query.processor import process_query
from app.retrieval.multi_hop_reasoner import MultiHopReasoner

async def main():
    q_hi = 'विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?'
    qa = process_query(q_hi)
    reasoner = MultiHopReasoner(max_hops=3, max_evidence_items=12)
    ev = reasoner.reason(qa)
    ev_text = _format_evidence(ev.all_passages)

    # Variant A: current prompt
    prompt_a = (
        f"कृपया उत्तर हिंदी में दें।\n\n"
        f"Question: {qa.original_query} (English intent: {qa.normalized_query})\n\n"
        f"Evidence passages:\n{ev_text}\n\n"
        f"Instructions: Answer the question directly using the evidence passages above. "
        f"State the exact start date and schedule for the Odd Semester End Semester Examination. "
        f"Cite every factual claim with [Source: passage_id, page X] referring to the passages above. "
        f"If the answer cannot be determined from the evidence, output UNANSWERABLE."
    )

    # Variant B: In Hindi instructions as well
    prompt_b = (
        f"Answer the question in Hindi (हिंदी में उत्तर दें).\n\n"
        f"Question: {qa.original_query}\n"
        f"English intent: When do Odd Semester End Semester Examination start and finish?\n\n"
        f"Evidence passages:\n{ev_text}\n\n"
        f"Instructions: State the exact start date and schedule for the Odd Semester End Semester Examination "
        f"(10-12-2026 to 22-12-2026) using the evidence passages. "
        f"Do not confuse with make-up or mid-term examinations. "
        f"Cite with [Source: passage_id, page X]."
    )

    # Variant C: Explicit target event clarity
    prompt_c = (
        f"कृपया उत्तर हिंदी में दें।\n\n"
        f"Question: {qa.original_query}\n"
        f"Target Event: Odd Semester End Semester Examination (विषम सेमेस्टर की अंतिम परीक्षा)\n\n"
        f"Evidence passages:\n{ev_text}\n\n"
        f"Instructions: Answer the question directly using the evidence passages above. "
        f"Find the passage describing 'End Semester Examination for All Students (Odd Semester 2026-27)' and state its exact start date and end date. "
        f"Cite every factual claim with [Source: passage_id, page X] referring to the passages above."
    )

    print("--- TESTING VARIANT A ---")
    out_a = await _call_ollama(prompt_a, _SYSTEM_PROMPT)
    print("A:", out_a)

    print("--- TESTING VARIANT C ---")
    out_c = await _call_ollama(prompt_c, _SYSTEM_PROMPT)
    print("C:", out_c)

asyncio.run(main())
