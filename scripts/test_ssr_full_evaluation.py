import sys
sys.path.insert(0, 'backend')
import asyncio
import json
from app.models.schemas import QueryRequest, DocumentSource
from app.api.main import query

TEST_QUERIES = [
    {
        "id": "Q1",
        "query": "what is total campus green spaces dedicated by campus",
        "expected": "over 12 acres",
        "type": "positive_numerical"
    },
    {
        "id": "Q2",
        "query": "What is the total campus green space?",
        "expected": "over 12 acres",
        "type": "positive_numerical"
    },
    {
        "id": "Q3",
        "query": "How many acres are dedicated to green spaces?",
        "expected": "over 12 acres",
        "type": "positive_numerical"
    },
    {
        "id": "Q4",
        "query": "How much campus area is covered by greenery?",
        "expected": "over 12 acres",
        "type": "positive_numerical"
    },
    {
        "id": "Q5",
        "query": "How many fully grown trees are present on campus?",
        "expected": "over 2,000",
        "type": "positive_numerical"
    },
    {
        "id": "Q6",
        "query": "How many geo-tagged trees are there?",
        "expected": "over 2,000",
        "type": "positive_numerical"
    },
    {
        "id": "Q7",
        "query": "What is the green campus initiative?",
        "expected": "automobiles / bicycles / pedestrian pathways / plastic",
        "type": "positive_initiative"
    },
    {
        "id": "Q8",
        "query": "What is the university's policy on plastic usage?",
        "expected": "ban on single-use plastic",
        "type": "positive_policy"
    },
    {
        "id": "Q9",
        "query": "What is the swimming pool depth?",
        "expected": "UNANSWERABLE",
        "type": "unanswerable"
    },
    {
        "id": "Q10",
        "query": "How many acres is the swimming pool?",
        "expected": "UNANSWERABLE",
        "type": "unanswerable"
    },
    {
        "id": "Q11",
        "query": "Campus mein green space kitna acre hai?",
        "expected": "over 12 acres",
        "type": "multilingual_hinglish"
    }
]

async def run_suite():
    results = []
    print(f"Executing {len(TEST_QUERIES)} Test Queries on Generic SSR Ingestion & Retrieval Pipeline...\n")
    
    for item in TEST_QUERIES:
        qid = item["id"]
        q_text = item["query"]
        print(f"--- Running [{qid}] '{q_text}' ---")
        
        req = QueryRequest(
            query=q_text,
            collection=[DocumentSource.UPLOAD],
            sequential_fallback=True,
            use_reranker=True,
            use_pdr=True
        )
        
        try:
            resp = await query(req)
            ans = resp.answer or ""
            cits = [
                {
                    "doc": c.filename,
                    "page": c.page,
                    "source": c.source_label
                }
                for c in resp.citations
            ]
            
            # Evaluate pass
            passed = False
            if "2,000" in item["expected"]:
                passed = ("2,000" in ans or "2000" in ans) and resp.status.value != "unanswerable"
            elif item["type"] in ("positive_numerical", "multilingual_hinglish"):
                passed = ("12" in ans.lower() or "twelve" in ans.lower()) and resp.status.value != "unanswerable"
            elif item["type"] == "positive_initiative":
                passed = any(w in ans.lower() for w in ["bicycle", "pedestrian", "plastic", "automobile", "green", "pathway"]) and resp.status.value != "unanswerable"
            elif item["type"] == "positive_policy":
                passed = any(w in ans.lower() for w in ["plastic", "ban", "single-use", "biodegradable"]) and resp.status.value != "unanswerable"
            elif item["type"] == "unanswerable":
                passed = resp.status.value == "unanswerable" or "unanswerable" in ans.lower()

            res_entry = {
                "id": qid,
                "query": q_text,
                "type": item["type"],
                "expected": item["expected"],
                "status": resp.status.value,
                "evidence_status": resp.evidence_status.value if resp.evidence_status else None,
                "answer": ans,
                "citations": cits,
                "passed": passed
            }
            results.append(res_entry)
            print(f"Result [{qid}]: Passed={passed} | Status={resp.status.value}")
            print(f"Answer: {ans[:160]}...")
            if cits:
                print(f"Citations: {[(c['doc'], c['page']) for c in cits]}")
            print()
        except Exception as e:
            print(f"ERROR executing [{qid}]: {e}\n")
            results.append({
                "id": qid,
                "query": q_text,
                "error": str(e),
                "passed": False
            })

    total_passed = sum(1 for r in results if r.get("passed"))
    print(f"\n==========================================")
    print(f"TOTAL SUITE PASS RATE: {total_passed}/{len(TEST_QUERIES)} ({total_passed/len(TEST_QUERIES)*100:.1f}%)")
    print(f"==========================================")
    
    with open("scripts/ssr_evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    asyncio.run(run_suite())
