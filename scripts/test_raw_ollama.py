import asyncio
import sys
from pathlib import Path

backend_dir = Path("backend").resolve()
sys.path.insert(0, str(backend_dir))

from app.generation.generator import _call_ollama

async def test_ollama():
    prompt = """Answer in English.

Question: What attendance is required to sit for end semester exams?

Evidence passages:
[1] passage_id=0280358a-ff3c-4964-88ab-419a9147b1f0, page 1
Ref No.: BU/R0/Notification/307/2022
08th September, 2022
NOTIFICATION
The minimum attendance criteria for the students to appear in the End Semester Examination was reviewed in the 13th Academic Council Meeting held on 29th July 2022 in consonance with the UGC Regulations 2003. The Competent Authority has approved that the students should have a minimum attendance of 75% to become eligible for appearing in the End Semester Examination with effect from the current semester onwards i.e. AY 2022-23.

Instructions: Answer the question based solely on the above evidence.
Cite every factual claim with [Source: passage_id, page X].
If the evidence is insufficient, respond with exactly:
UNANSWERABLE — Insufficient information available in the provided documents."""

    sys_prompt = "You are a precise academic regulation assistant for Bennett University. Cite every claim with [Source: passage_id, page X]."
    print("Calling Ollama...")
    res = await _call_ollama(prompt, sys_prompt)
    print("--- RAW RESPONSE ---")
    print(res)
    print("--------------------")

if __name__ == "__main__":
    asyncio.run(test_ollama())

