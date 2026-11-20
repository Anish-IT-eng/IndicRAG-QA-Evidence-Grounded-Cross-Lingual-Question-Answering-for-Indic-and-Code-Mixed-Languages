import asyncio
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "backend"))

from app.models.schemas import DocumentSource, QueryScript, QueryLanguage, RegulatoryCondition, EvidenceStatus, EvidenceDecision
from app.query.processor import process_query
from app.retrieval.engine import retrieve
from app.generation.generator import generate_answer

def check_medical_rule(q_text, passages, query_analysis):
    q_lower = q_text.lower()
    trans_lower = (query_analysis.translated_query or "").lower()
    
    is_med = (
        any(k in q_lower for k in ["medical", "illness", "relaxation", "relax", "condon", "मेडिकल", "छूट", "बीमारी"])
        or any(k in trans_lower for k in ["medical", "illness", "relaxation", "relax", "condon"])
    )
    if is_med:
        med_passages = [
            p for p in passages
            if (p.regulatory_condition == RegulatoryCondition.MEDICAL_CONDONATION)
            or ("30.1(v)" in p.text or "30.1 (v)" in p.text or "10%" in p.text)
        ]
        return med_passages
    return []

async def test():
    m9_file = root / "backend" / "data" / "experiments" / "m9" / "m9_evaluation_dataset.jsonl"
    with open(m9_file, "r", encoding="utf-8") as f:
        m9_queries = [json.loads(line) for line in f]
        
    for qid in ["M9-Q010", "M9-Q014"]:
        q = next(item for item in m9_queries if item["query_id"] == qid)
        qa = process_query(q["query_text"])
        res = retrieve(qa, [DocumentSource.OFFICIAL], top_k=5, rerank_strategy="adaptive_e6b")
        med = check_medical_rule(q["query_text"], res.retrieved_passages, qa)
        print(f"{qid}: retrieved {len(res.retrieved_passages)} passages. Med matches: {len(med)}")
        if med:
            dec = EvidenceDecision(
                status=EvidenceStatus.SUFFICIENT,
                valid_passages=med,
                coverage_score=0.85,
                detected_conditions=[RegulatoryCondition.MEDICAL_CONDONATION],
                explanation="Unanimous regulatory consensus: Relaxation up to a maximum of 10% may be granted by the Dean on valid medical grounds.",
                retry_recommended=False,
                ceci_score=0.85
            )
            ans = await generate_answer(qa, dec)
            print(f"Status: {ans.status} | Citations: {len(ans.citations)}")
            print(f"Answer:\n{ans.answer}\n")

if __name__ == "__main__":
    asyncio.run(test())
