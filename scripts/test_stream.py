import sys, asyncio, httpx
sys.path.insert(0, 'backend')
from app.core.config import settings

async def main():
    payload = {
        "model": settings.ollama_model,
        "prompt": "कृपया उत्तर हिंदी में दें।\n\nQuestion: विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?\n\nEvidence: Academic-Calendar-2026-27.pdf (Page 4): End Semester Examination for All Students (Odd Semester 2026-27) starts on 10-12-2026 and concludes on 22-12-2026.\n\nAnswer:",
        "stream": True,
        "options": {
            "temperature": 0.1,
            "num_predict": 256,
        }
    }
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", f"{settings.ollama_base_url}/api/generate", json=payload) as response:
            async for chunk in response.aiter_text():
                print(chunk, end="", flush=True)

asyncio.run(main())
