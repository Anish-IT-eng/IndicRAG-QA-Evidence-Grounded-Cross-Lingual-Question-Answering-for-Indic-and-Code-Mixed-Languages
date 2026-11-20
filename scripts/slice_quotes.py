import sqlite3
import re

conn = sqlite3.connect("backend/data/db/indicrag.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

def find_substring(pid, pattern):
    row = c.execute("SELECT text FROM passages WHERE passage_id = ?", (pid,)).fetchone()
    text = row["text"]
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if m:
        exact_slice = text[m.start():m.end()]
        assert exact_slice in text, "Slice not in text!"
        return exact_slice
    else:
        raise ValueError(f"Pattern '{pattern}' not found in passage {pid}!")

patterns = {
    # 1. B.Tech Duration
    "ee63431f-398b-4717-aa04-8c456a3ab928": r"The duration of the UG programs leading to degree of B\. Tech shall be minimum four years.*?registration for BCA and B\.Sc\.",
    # 2. Phasing Out
    "124457f2-1670-4208-88d5-84808860454c": r"A program may be phased out on recommendations of the Academic Council.*?becoming obsolete etc\.",
    # 3. Semester Duration
    "4fb20336-4a76-4e21-8422-f3d9e08a4c27": r"A semester will be of approximately 18-20 weeks duration\. Of these, 90 days will be available for actual\s+instruction",
    # 4. Internship Semester
    "cfb81e36-8477-4083-aa37-f671c6202263": r"A student may be\s+allowed to start with the internship in the 7 th semester in case of B\.Tech and 5 th semester in case of BCA and B\.Sc",
    # 5. Seminar Requirement
    "c4d08811-efad-4c12-8f9a-3a7c7938ff28": r"Seminar is a course requirement wherein under the guidance of a faculty member a student is expected to do in-depth study in a specified area",
    # 6. Credit Registration
    "5fce6f7d-77a5-4f39-a240-072d84c12334": r"Students must ensure correctness of same as they shall be awarded grades in the registered courses, irrespective of his/\s*her attendance in that course",
    # 7. Add/Drop Timeline
    "380bfc8e-cd43-4343-8db3-11fd7c5b400b": r"within one week of the beginning of the semester \(i\.e\., after the classes start\) or withdraw from a course up to two weeks before the end of Semester",
    # 8. Minimum Elective Registration
    "7de500cb-6f25-49bc-8e53-5f3415b2c054": r"An undergraduate elective course shall normally run only if a minimum of 15 students register for the course\.",
    # 9. Learning Outcomes
    "29bf25f8-7683-45da-8dea-f1c4c5815b74": r"\(v\) Objective\(s\)\s+\(vi\) Learning Outcomes\s+\(vii\) Course Outline\s+\(viii\) Equivalent course – if any\.",
    # 10. Continuous Evaluation
    "664e460c-3448-49bf-b051-e050a597d3ee": r"Each course shall be evaluated through continuous evaluation, Mid\s*-Term Examination, and End-Semester Examination",
    # 11. D Grade Minimum Marks
    "505e552e-35e0-4b5d-98ba-10dff85f4eab": r"the range for D grade shall start from 30 marks onwards for all the courses",
    # 12. Medical Makeup Procedure
    "dc9034e1-88aa-4a45-ad01-34fd28c21411": r"They should report absence from the Examination\(s\) by sending an e\s*-mail to the Student Counselor/Welfare Officer along with the medical documents",
    # 13. Makeup Application Deadline
    "dab03ad7-0094-481e-82d9-98260bc33caf": r"not later than 5 days after the last date of\s+Examination\.",
    # 14. Supplementary Exam Max Grade
    "5f9028f1-69ee-4e2d-9aa0-68ca2f510deb": r"The maximum grade awarded for t he supplementary Examination shall be up to C\+",
    # 15. Supplementary for Project
    "278fa408-518b-4c53-9cc2-c49ac347c87a": r"The students who take supplementary examination as make up for the end semester major examination shall be awarded regular grades",
    # 16. Relative Grading Approval
    "c22770f9-e383-480d-9f9c-925d0eeffff3": r"The Grades may be awarded by any of the methods as approved by the Academic Council and\s+generally as a relative grading",
    # 17. Grade Points Structure
    "5fd38f8d-e1ec-406e-aa70-06317b4e3d72": r"Grade Grade Points Description of Performance\s+O 10 Extra Ordinary Performance\s+A\+ 10 Outstanding\s+A 9 Excellent\s+B\+ 8 Very Good\s+B 7 Good\s+C\+ 6 Above Average\s+C 5 Average\s+D 4 Pass\s+F 0 Fail\s+I\s+Incomplete Grade",
    # 18. Incomplete Grade 'I' Conversion
    "9bbbab01-3fe3-4864-99ab-57128db19748": r"The ‘I’ must be converted to a performance grade \(A to F\) within 90 days after the first day of classes in the subsequent Semester\.",
    # 19. Equated Percentage Formula
    "f6d95cc5-2c08-4aee-ba5c-72429cbef467": r"For this the CGPA\s+shall be multiplied by 10 and resulting figure rounded off to the second digit\.",
    # 20. B.Tech Honors Credit Requirement
    "232928ea-fe34-4563-8c67-6f714317a64d": r"A student shall be eligible to get an Honours degree by earning at least eighteen more credits over\s+and above the minimum credits specified for the degree",
    # 21. B.Tech Honors CGPA Requirement
    "53ed3206-b2a4-4ebe-aad2-3ab9a646264a": r"To opt for honors, a student should possess a minimum CGPA of 7\.5 on 10-point scale and have no\s+backlogs by the end of 3rd semester\.",
    # 22. Minors CGPA Requirement
    "e58d460e-7817-44ac-9f2c-628791b338b2": r"a student should possess a minimum CGPA of 7 on 10-point scale by the end of 2nd semester\.",
    # 23. Continuous Absence Struck Off Rolls
    "9773d6a7-12e2-4b0e-9b5f-45a8be226a95": r"If a student is continuously absent from the University for more than 21 working days without\s+notifying the University, his/her name will be struck off the rolls of the University\.",
    # 24. Notification 307 Attendance 75%
    "0280358a-ff3c-4964-88ab-419a9147b1f0": r"The minimum attendance required for appearing in the End Semester Examinations shall be 75% across all courses of study for the academic year 2022-23 onwards\.",
    # 25. Ordinance 2017 Clause 30.1 Attendance 70%
    "f88ec726-74ba-426f-a01f-4b9665c1a8b8": r"A student must have a minimum attendance of 70% in a course to be eligible to appear in the end\s*-semester examination of that course\.",
    # 26. Calendar 2026-27 Convocation Date
    "bbaac776-23eb-4535-85f9-6f181b238d3f": r"13-11-2026 Friday Teaching Day Convocation \(Tentative\) Odd Semester Mid-Term Marks Submission in ERP – End Date",
    # 27. Calendar 2026-27 Make-up Exam Start
    "23db7904-2f93-4c62-a74d-f159a5d11acd": r"01-07-2026 Wednesday Registration for Even Semester Make-up Examination-Start Date",
}

print(f"Testing {len(patterns)} patterns...")
exact_quotes = {}
for pid, pat in patterns.items():
    q = find_substring(pid, pat)
    exact_quotes[pid] = q
    print(f"Matched {pid}: len={len(q)}")

print("ALL 27 EXACT SLICES FOUND AND VERIFIED IN TEXT!")
conn.close()
