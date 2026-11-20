import asyncio
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "backend"))

from app.models.schemas import DocumentSource, QueryScript, QueryLanguage
from app.query.processor import process_query
from app.retrieval.engine import retrieve
from app.retrieval.evidence_controller import EvidenceController
from app.generation.generator import generate_answer

async def test_all_hi_hits():
    m9_file = root / "backend" / "data" / "experiments" / "m9" / "m9_evaluation_dataset.jsonl"
    with open(m9_file, "r", encoding="utf-8") as f:
        m9_queries = [json.loads(line) for line in f]
        
    ctrl = EvidenceController()
    for qid in ["M9-Q002", "M9-Q010", "M9-Q014", "M9-Q030"]:
        q_hi = next(q for q in m9_queries if q["query_id"] == qid)
        print(f"\n==========================================")
        print(f"Query ID: {q_hi['query_id']} | Intent: {q_hi['intent_id']}")
        print(f"Query Text: {q_hi['query_text']}")
        
        qa = process_query(q_hi["query_text"])
        ret_res = retrieve(qa, [DocumentSource.OFFICIAL], top_k=5, rerank_strategy="adaptive_e6b")
        ev_dec = ctrl.evaluate(ret_res)
        ans_res = await generate_answer(qa, ev_dec)
        
        print(f"Evidence Status: {ev_dec.status} | CECI: {ev_dec.ceci_score}")
        print(f"Response Status: {ans_res.status} | Citations: {len(ans_res.citations)}")
        print(f"Answer: {ans_res.answer[:300]}...")

if __name__ == "__main__":
    asyncio.run(test_all_hi_hits())
