import asyncio
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "backend"))

from app.models.schemas import DocumentSource, QueryScript, QueryLanguage, RegulatoryCondition, EvidenceStatus, EvidenceDecision
from app.query.processor import process_query
from app.retrieval.engine import retrieve
from app.generation.generator import _call_ollama, _SYSTEM_PROMPT, _format_evidence

async def inspect_raw():
    m9_file = root / "backend" / "data" / "experiments" / "m9" / "m9_evaluation_dataset.jsonl"
    with open(m9_file, "r", encoding="utf-8") as f:
        m9_queries = [json.loads(line) for line in f]
        
    q = next(item for item in m9_queries if item["query_id"] == "M9-Q010")
    qa = process_query(q["query_text"])
    res = retrieve(qa, [DocumentSource.OFFICIAL], top_k=5, rerank_strategy="adaptive_e6b")
    
    evidence_text = _format_evidence(res.retrieved_passages)
    print("--- EVIDENCE TEXT ---")
    print(evidence_text[:1200])
    user_prompt = f"कृपया उत्तर हिंदी में दें।\n\nQuestion: {qa.original_query}\n\nEvidence passages:\n{evidence_text}\n\nInstructions: Answer the question using the evidence passages above. Cite every factual claim with [Source: passage_id, page X] referring to the passages above. If the answer cannot be determined from the evidence, output UNANSWERABLE."
    print("\n--- USER PROMPT ---")
    print(user_prompt[:500])
    
    # Test with M8.8 specialized instructions
    instructions = (
        "Answer whether attendance can be relaxed due to medical reasons. "
        "Specify the conditions (continuous illness of two weeks, medical certificate, and maximum relaxation of up to 10%) under Clause 30.1(v), "
        "and note that short absences do not count towards relaxation under Clause 30.1(iii)/(v). "
        "Cite each claim with [Source: passage_id, page X]."
    )
    user_prompt_spec = f"Answer in English.\n\nQuestion: Can attendance be relaxed for medical reasons and by what maximum percentage?\n\nEvidence passages:\n{evidence_text}\n\nInstructions: {instructions}"
    raw_spec = await _call_ollama(user_prompt_spec, _SYSTEM_PROMPT)
    print("\n--- RAW SPECIALIZED OUTPUT ---")
    print(raw_spec)

if __name__ == "__main__":
    asyncio.run(inspect_raw())
