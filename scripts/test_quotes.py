import sqlite3
import json

conn = sqlite3.connect("backend/data/db/indicrag.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

def get_passage(pid):
    r = c.execute("SELECT passage_id, parent_passage_id, document_id, page_number, section, heading, text FROM passages WHERE passage_id = ?", (pid,)).fetchone()
    return dict(r) if r else None

# 1. B.Tech Duration
p1 = get_passage("ee63431f-398b-4717-aa04-8c456a3ab928")
q1_quote = "The duration of the UG programs leading to degree of B. Tech shall be minimum four years, BCA shall be minimum three years  and B.Sc shall be minimum of three years ."
print("P1 quote in text:", q1_quote in p1["text"])

# 2. Program Phasing Out
p2 = get_passage("124457f2-1670-4208-88d5-84808860454c")
q2_quote = "A program may be phased out on recommendations of the Academic Council and approval of the Executive Council , on account of continuous low registration in the program or any other justifiable reason like becoming obsolete etc."
print("P2 quote in text:", q2_quote in p2["text"])

# 3. Semester Duration (Days for instruction)
p3 = get_passage("4fb20336-4a76-4e21-8422-f3d9e08a4c27")
q3_quote = "A semester will be of approximately 18-20 weeks duration. Of these, 90 days will be available for actual instruction"
print("P3 quote in text:", q3_quote in p3["text"])

# 4. Internship Semester
p4 = get_passage("cfb81e36-8477-4083-aa37-f671c6202263")
q4_quote = "A student may be  allowed to start with the internship in the 7 th semester in case of B.Tech and 5 th semester in case of BCA and B.Sc"
print("P4 quote in text:", q4_quote in p4["text"])

# 5. Seminar Requirement
p5 = get_passage("c4d08811-efad-4c12-8f9a-3a7c7938ff28")
q5_quote = "Seminar is a course requirement wherein under the guidance of a faculty member a student is expected to do in-depth study in a specified area"
print("P5 quote in text:", q5_quote in p5["text"])

# 6. Credit Registration Correctness
p6 = get_passage("5fce6f7d-77a5-4f39-a240-072d84c12334")
q6_quote = "Students must ensure correctness of same as they shall be awarded grades in the registered courses, irrespective of his/ her attendance in that course"
print("P6 quote in text:", q6_quote in p6["text"])

# 7. Add/Drop Timeline
p7 = get_passage("380bfc8e-cd43-4343-8db3-11fd7c5b400b")
q7_quote = "within one week of the beginning of the semester (i.e., after the classes start) or withdraw from a course up to two weeks before the end of Semester"
print("P7 quote in text:", q7_quote in p7["text"])

# 8. Minimum Elective Registration
p8 = get_passage("7de500cb-6f25-49bc-8e53-5f3415b2c054")
q8_quote = "An undergraduate elective course shall normally run only if a minimum of 15 students register for the course."
print("P8 quote in text:", q8_quote in p8["text"])

# 9. Learning Outcomes in Course Outline
p9 = get_passage("29bf25f8-7683-45da-8dea-f1c4c5815b74")
q9_quote = "(v) Objective(s) \n(vi) Learning Outcomes \n(vii) Course Outline \n(viii) Equivalent course – if any."
print("P9 quote in text:", q9_quote in p9["text"])

# 10. Continuous Evaluation Division
p10 = get_passage("664e460c-3448-49bf-b051-e050a597d3ee")
q10_quote = "Each course shall be evaluated through continuous evaluation, Mid -Term Examination, and End-Semester Examination"
print("P10 quote in text:", q10_quote in p10["text"])

# 11. D Grade Minimum Marks
p11 = get_passage("505e552e-35e0-4b5d-98ba-10dff85f4eab")
q11_quote = "the range for D grade shall start from 30 marks onwards for all the courses"
print("P11 quote in text:", q11_quote in p11["text"])

# 12. Medical Makeup Procedure
p12 = get_passage("dc9034e1-88aa-4a45-ad01-34fd28c21411")
q12_quote = "They should report absence from the Examination(s) by sending an e -mail to the Student Counselor/Welfare Officer along with the medical documents"
print("P12 quote in text:", q12_quote in p12["text"])

# 13. Makeup Application Deadline
p13 = get_passage("dab03ad7-0094-481e-82d9-98260bc33caf")
q13_quote = "not later than 5 days after the last date of Examination."
print("P13 quote in text:", q13_quote in p13["text"])

# 14. Supplementary Exam Max Grade
p14 = get_passage("5f9028f1-69ee-4e2d-9aa0-68ca2f510deb")
q14_quote = "The maximum grade awarded for t he supplementary Examination shall be up to C+"
print("P14 quote in text:", q14_quote in p14["text"])

# 15. Supplementary for Project
p15 = get_passage("278fa408-518b-4c53-9cc2-c49ac347c87a")
q15_quote = "The students who take supplementary examination as make up for the end semester major examination shall be awarded regular grades"
print("P15 quote in text:", q15_quote in p15["text"])

# 16. Relative Grading Approval
p16 = get_passage("c22770f9-e383-480d-9f9c-925d0eeffff3")
q16_quote = "The Grades may be awarded by any of the methods as approved by the Academic Council and generally as a relative grading"
print("P16 quote in text:", q16_quote in p16["text"])

# 17. Grade Points Structure
p17 = get_passage("5fd38f8d-e1ec-406e-aa70-06317b4e3d72")
q17_quote = "O 10 Extra Ordinary Performance \nA+ 10 Outstanding \nA 9 Excellent \nB+ 8 Very Good \nB 7 Good \nC+ 6 Above Average \nC 5 Average \nD 4 Pass \nF 0 Fail \nI  Incomplete Grade"
print("P17 quote in text:", q17_quote in p17["text"])

# 18. Incomplete Grade 'I' Conversion
p18 = get_passage("9bbbab01-3fe3-4864-99ab-57128db19748")
q18_quote = "The ‘I’ must be converted to a performance grade (A to F) within 90 days after the first day of classes in the subsequent Semester."
print("P18 quote in text:", q18_quote in p18["text"])

# 19. Equated Percentage Formula
p19 = get_passage("f6d95cc5-2c08-4aee-ba5c-72429cbef467")
q19_quote = "For this the CGPA shall be multiplied by 10 and resulting figure rounded off to the second digit."
print("P19 quote in text:", q19_quote in p19["text"])

# 20. B.Tech Honors Credit Requirement
p20 = get_passage("232928ea-fe34-4563-8c67-6f714317a64d")
q20_quote = "A student shall be eligible to get an Honours degree by earning at least eighteen more credits over and above the minimum credits specified for the degree"
print("P20 quote in text:", q20_quote in p20["text"])

# 21. B.Tech Honors CGPA Requirement
p21 = get_passage("53ed3206-b2a4-4ebe-aad2-3ab9a646264a")
q21_quote = "To opt for honors, a student should possess a minimum CGPA of 7.5 on 10-point scale and have no backlogs by the end of 3rd semester."
print("P21 quote in text:", q21_quote in p21["text"])

# 22. Minors CGPA Requirement
p22 = get_passage("e58d460e-7817-44ac-9f2c-628791b338b2")
q22_quote = "a student should possess a minimum CGPA of 7 on 10-point scale by the end of 2nd semester."
print("P22 quote in text:", q22_quote in p22["text"])

# 23. Continuous Absence Struck Off Rolls
p23 = get_passage("9773d6a7-12e2-4b0e-9b5f-45a8be226a95")
q23_quote = "If a student is continuously absent from the University for more than 21 working days without notifying the University, his/her name will be struck off the rolls of the University."
print("P23 quote in text:", q23_quote in p23["text"])

# 24. Notification 307 Attendance 75%
p24 = get_passage("0280358a-ff3c-4964-88ab-419a9147b1f0")
q24_quote = "The minimum attendance required for appearing in the End Semester Examinations shall be 75% across all courses of study for the academic year 2022-23 onwards."
print("P24 quote in text:", q24_quote in p24["text"])

# 25. Ordinance 2017 Clause 30.1 Attendance 70%
p25 = get_passage("f88ec726-74ba-426f-a01f-4b9665c1a8b8")
q25_quote = "A student must have a minimum attendance of 70% in a course to be eligible to appear in the end -semester examination of that course."
print("P25 quote in text:", q25_quote in p25["text"])

# 26. Calendar 2026-27 Convocation Date
p26 = get_passage("bbaac776-23eb-4535-85f9-6f181b238d3f")
q26_quote = "13-11-2026 Friday Teaching Day Convocation (Tentative) Odd Semester Mid-Term Marks Submission in ERP – End Date"
print("P26 quote in text:", q26_quote in p26["text"])

# 27. Calendar 2026-27 Make-up Exam Start
p27 = get_passage("23db7904-2f93-4c62-a74d-f159a5d11acd")
q27_quote = "01-07-2026 Wednesday Registration for Even Semester Make-up Examination-Start Date"
print("P27 quote in text:", q27_quote in p27["text"])

conn.close()

