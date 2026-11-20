import sys, asyncio
sys.path.insert(0, 'backend')
from app.retrieval.multi_hop_reasoner import answer_multi_hop_question

async def main():
    q_hi = 'विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?'
    ans = await answer_multi_hop_question(query=q_hi)
    print("=== GENERATED ANSWER ===")
    print("Answer:", ans.answer)
    print("Status:", ans.status)
    print("Citations:", [(c.page, c.filename) for c in ans.citations])

asyncio.run(main())

