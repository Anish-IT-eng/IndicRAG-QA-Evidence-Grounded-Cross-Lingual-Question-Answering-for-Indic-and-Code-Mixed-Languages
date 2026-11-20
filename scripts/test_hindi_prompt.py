import sys, asyncio
sys.path.insert(0, 'backend')
from app.query.processor import process_query
from app.retrieval.multi_hop_reasoner import MultiHopReasoner
from app.generation.generator import _call_ollama, _format_evidence, _SYSTEM_PROMPT, _LANG_INSTRUCTIONS

q_hi = 'विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?'
qa = process_query(q_hi)
reasoner = MultiHopReasoner(max_hops=3, max_evidence_items=12)
ev_set = reasoner.reason(qa)

instructions = (
    "Answer the question directly using the evidence passages above. "
    "State the exact start date and schedule for the Odd Semester End Semester Examination. "
    "Cite every factual claim with [Source: passage_id, page X] referring to the passages above. "
    "If the answer cannot be determined from the evidence, output UNANSWERABLE."
)

evidence_text = _format_evidence(ev_set.all_passages)

# Compare Prompt 1: English answer vs Prompt 2: Hindi answer
prompt_en_ans = f"Answer in English.\n\nQuestion: When do odd semester end semester examinations start and finish?\n\nEvidence passages:\n{evidence_text}\n\nInstructions: {instructions}"

prompt_hi_ans = f"कृपया उत्तर हिंदी में दें।\n\nQuestion: विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?\n\nEvidence passages:\n{evidence_text}\n\nInstructions: {instructions}"

async def test():
    print("=== TESTING HINDI PROMPT ===")
    ans_hi = await _call_ollama(prompt_hi_ans, _SYSTEM_PROMPT)
    print("HINDI ANSWER:\n", ans_hi)

asyncio.run(test())
