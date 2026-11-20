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

slice_defs = [
    # 1. B.Tech Duration
    ("ee63431f-398b-4717-aa04-8c456a3ab928", "The duration of the UG programs", "minimum four years"),
    # 2. Semester System
    ("124457f2-1670-4208-88d5-84808860454c", "The B. Tech CSE, BCA and B.Sc", "academic year."),
    # 3. Semester Duration
    ("4fb20336-4a76-4e21-8422-f3d9e08a4c27", "A semester will be of approximately", "instruction"),
    # 4. Internship Semester
    ("cfb81e36-8477-4083-aa37-f671c6202263", "A student may be", "case of BCA & B.Sc"),
    # 5. Seminar Requirement
    ("c4d08811-efad-4c12-8f9a-3a7c7938ff28", "Seminar is a course requirement", "specialized area"),
    # 6. Credit Registration
    ("5fce6f7d-77a5-4f39-a240-072d84c12334", "Students must ensure correctness", "registered for the course."),
    # 7. Add/Drop Timeline
    ("380bfc8e-cd43-4343-8db3-11fd7c5b400b", "within \none week", "end of Semester."),
    # 8. Minimum Elective Registration
    ("7de500cb-6f25-49bc-8e53-5f3415b2c054", "An undergraduate elective course", "5 \nstudents in that course."),
    # 9. Learning Outcomes
    ("29bf25f8-7683-45da-8dea-f1c4c5815b74", "(v) Objective(s)", "Equivalent course – if any."),
    # 10. Continuous Evaluation
    ("664e460c-3448-49bf-b051-e050a597d3ee", "Each course shall be evaluated out of", "100 Marks."),
    # 11. D Grade Minimum Marks
    ("505e552e-35e0-4b5d-98ba-10dff85f4eab", "the range for D grade shall start", "for all the courses."),
    # 12. Medical Makeup Procedure
    ("dc9034e1-88aa-4a45-ad01-34fd28c21411", "They should report absence", "Controller of \nExamination."),
    # 13. Makeup Application Deadline
    ("dab03ad7-0094-481e-82d9-98260bc33caf", "not later than 5 days", "Examination."),
    # 14. Supplementary Exam Duration
    ("5f9028f1-69ee-4e2d-9aa0-68ca2f510deb", "The Supplementary Examination shall be", "as end term examination."),
    # 15. Supplementary for Project
    ("278fa408-518b-4c53-9cc2-c49ac347c87a", "The students who take supplementary examination", "regular grades"),
    # 16. Relative Grading Approval
    ("c22770f9-e383-480d-9f9c-925d0eeffff3", "The Grades may be awarded", "relative grading."),
    # 17. Grade Points Structure
    ("5fd38f8d-e1ec-406e-aa70-06317b4e3d72", "Grade Grade Points Description", "A 9 Excellent"),
    # 18. Incomplete Grade 'I' Conversion
    ("9bbbab01-3fe3-4864-99ab-57128db19748", "The ‘I’ must be converted", "subsequent Semester."),
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
    ("0280358a-ff3c-4964-88ab-419a9147b1f0", "Notification/307/2022", "NOTIFICATION"),
    # 25. Ordinance 2017 Clause 30.1 Attendance 70%
    ("f88ec726-74ba-426f-a01f-4b9665c1a8b8", "All undergraduate/Integrated program students are expected", "scheduled for them."),
    # 26. Calendar 2026-27 Convocation Date
    ("bbaac776-23eb-4535-85f9-6f181b238d3f", "13-11-2026 Friday", "Convocation (Tentative)"),
    # 27. Calendar 2026-27 Make-up Exam Start
    ("23db7904-2f93-4c62-a74d-f159a5d11acd", "01-07-2026 Wednesday", "Start Date"),
]

exact_quotes_dict = {}
for idx, (pid, prefix, suffix) in enumerate(slice_defs, 1):
    q = get_exact_slice(pid, prefix, suffix)
    exact_quotes_dict[pid] = q
    print(f"PASS #{idx}: {pid[:8]} -> len={len(q)} | {repr(q[:40])}...")

print(f"\nSUCCESS: All {len(exact_quotes_dict)} slices extracted and verified verbatim!")
conn.close()
