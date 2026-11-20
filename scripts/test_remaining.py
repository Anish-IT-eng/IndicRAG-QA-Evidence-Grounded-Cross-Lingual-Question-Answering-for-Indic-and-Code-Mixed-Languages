import sqlite3
import re

conn = sqlite3.connect("backend/data/db/indicrag.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

def get_text(pid):
    row = c.execute("SELECT text FROM passages WHERE passage_id = ?", (pid,)).fetchone()
    return row["text"]

def get_exact_slice(pid, prefix, suffix):
    text = get_text(pid)
    pat = re.escape(prefix) + r".*?" + re.escape(suffix)
    m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
    if not m:
        raise ValueError(f"Could not find prefix '{prefix}' and suffix '{suffix}' in passage {pid}!\nText: {repr(text[:150])}")
    exact = text[m.start():m.end()]
    assert exact in text
    return exact

# Test remaining
test_remaining = [
    # 18. Incomplete Grade 'I' Conversion
    ("9bbbab01-3fe3-4864-99ab-57128db19748", "The ‘I’ must be converted", "regular semester."),
    # 19. Equated Percentage Formula
    ("f6d95cc5-2c08-4aee-ba5c-72429cbef467", "For this the CGPA", "second digit."),
    # 20. B.Tech Honors Credit Requirement
    ("232928ea-fe34-4563-8c67-6f714317a64d", "A student shall be eligible to get an Honours degree", "regular B.Tech program."),
    # 21. B.Tech Honors CGPA Requirement
    ("53ed3206-b2a4-4ebe-aad2-3ab9a646264a", "To opt for honors, a student should possess a minimum CGPA of 7.5", "end of 3rd semester."),
    # 22. Minors CGPA Requirement
    ("e58d460e-7817-44ac-9f2c-628791b338b2", "a student should possess a minimum CGPA of 7", "end of 2nd semester."),
    # 23. Continuous Absence Struck Off Rolls
    ("9773d6a7-12e2-4b0e-9b5f-45a8be226a95", "If a student is continuously absent", "rolls of the University."),
    # 24. Notification 307 Attendance 75%
    ("0280358a-ff3c-4964-88ab-419a9147b1f0", "The Competent Authority has approved that the students should have a minimum", "semester onwards)."),
    # 25. Ordinance 2017 Clause 30.1 Attendance 70%
    ("f88ec726-74ba-426f-a01f-4b9665c1a8b8", "A student must have a minimum attendance of 70%", "(as applicable)."),
    # 26. Calendar 2026-27 Convocation Date
    ("bbaac776-23eb-4535-85f9-6f181b238d3f", "13-11-2026 Friday", "Convocation (Tentative)"),
    # 27. Calendar 2026-27 Make-up Exam Start
    ("23db7904-2f93-4c62-a74d-f159a5d11acd", "01-07-2026 Wednesday", "Start Date"),
]

for idx, (pid, prefix, suffix) in enumerate(test_remaining, 18):
    q = get_exact_slice(pid, prefix, suffix)
    print(f"PASS #{idx}: {pid[:8]} -> len={len(q)} | {repr(q[:40])}...")

conn.close()
