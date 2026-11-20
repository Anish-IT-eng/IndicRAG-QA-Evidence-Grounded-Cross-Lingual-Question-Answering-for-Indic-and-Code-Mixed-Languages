"""
Definitions of the 60 semantic intent groups for Milestone M9.
45 answerable intents across all 7 official documents + 15 unanswerable intents.
"""

INTENT_SPECS = [
    # ── Category 1: Attendance Regulations (Intents 1-8) ───────────────────────────
    {
        "intent_id": "M9-INT-01",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Notification-Minimum-Attendance.pdf"],
        "passage_snippet": "minimum attendance criteria for the students to appear in the End Semester Examination",
        "expected_claims": ["The minimum attendance criteria to appear in End Semester Examinations is 75%."],
        "expected_answer": "The minimum attendance criteria to appear in the End Semester Examination is 75%.",
        "applicability_constraints": {"purpose": "EXAMINATION_ELIGIBILITY"},
        "variants": {
            "en": "What is the minimum attendance required to appear in the End Semester Examination?",
            "hi": "एंड सेमेस्टर परीक्षा में बैठने के लिए न्यूनतम कितनी उपस्थिति आवश्यक है?",
            "hi_latn": "End semester exam mein baithne ke liye minimum kitni attendance chahiye?",
            "hinglish": "End sem exam dene ke liye minimum attendance requirement kya hai?"
        }
    },
    {
        "intent_id": "M9-INT-02",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "minimum attendance of 70% in a course during a semester",
        "expected_claims": ["A student must have a minimum attendance of 70% in a course to avoid receiving an X grade."],
        "expected_answer": "A student must maintain a minimum attendance of 70% in a course during a semester to avoid receiving an 'X' grade.",
        "applicability_constraints": {"purpose": "COURSE_GRADING", "programme": "SCSET_UG"},
        "variants": {
            "en": "How much attendance is required in a course to avoid an X grade?",
            "hi": "किसी कोर्स में 'X' ग्रेड से बचने के लिए कितनी उपस्थिति की आवश्यकता होती है?",
            "hi_latn": "Kisi course mein X grade se bachne ke liye kitni attendance required hoti hai?",
            "hinglish": "Course mein X grade na mile iske liye minimum attendance kitni honi chahiye?"
        }
    },
    {
        "intent_id": "M9-INT-03",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "Relaxation up to a maximum of 10% in the attendance may be granted",
        "expected_claims": ["Attendance relaxation up to 10% can be granted for continuous illness of two weeks or more."],
        "expected_answer": "Attendance relaxation up to a maximum of 10% can be granted on medical grounds in case of continuous illness of two weeks or more with proper medical certification.",
        "applicability_constraints": {"purpose": "MEDICAL_RELAXATION"},
        "variants": {
            "en": "Can attendance be relaxed on medical grounds, and by how much?",
            "hi": "क्या मेडिकल आधार पर उपस्थिति में छूट मिल सकती है और अधिकतम कितनी?",
            "hi_latn": "Kya medical grounds par attendance mein relaxation mil sakti hai aur kitni?",
            "hinglish": "Medical reason par maximum kitni attendance relaxation mil sakti hai?"
        }
    },
    {
        "intent_id": "M9-INT-04",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "Absences for shorter durations shall not count towards this relaxation",
        "expected_claims": ["Shorter duration absences do not count towards the 10% medical relaxation."],
        "expected_answer": "No, short sporadic absences for medical reasons do not qualify for the 10% relaxation; only continuous illness of two weeks or more qualifies.",
        "applicability_constraints": {"purpose": "MEDICAL_RELAXATION_SHORT_ABSENCE"},
        "variants": {
            "en": "Do short medical absences of 2 or 3 days count towards attendance relaxation?",
            "hi": "क्या 2 या 3 दिनों की छोटी मेडिकल अनुपस्थिति को उपस्थिति छूट में गिना जाता है?",
            "hi_latn": "Kya do teen din ki short medical leave par attendance relaxation milti hai?",
            "hinglish": "Agar 2-3 days ki illness ho toh kya attendance relaxation count hogi?"
        }
    },
    {
        "intent_id": "M9-INT-05",
        "query_type": "COMPARATIVE",
        "expected_status": "ANSWERED",
        "expected_documents": ["Notification-Minimum-Attendance.pdf", "Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "minimum attendance of 70% in a course",
        "expected_claims": [
            "70% attendance is required to avoid an X grade in a course.",
            "75% attendance is required to appear in the End Semester Examination."
        ],
        "expected_answer": "70% attendance is sufficient to avoid an 'X' grade in a course, but it is not sufficient to sit for End Semester Examinations, which requires 75% attendance.",
        "applicability_constraints": {"comparison": "70_VS_75"},
        "variants": {
            "en": "Is 70% attendance enough for both course passing and semester examinations?",
            "hi": "क्या 70% उपस्थिति कोर्स पास करने और सेमेस्टर परीक्षा दोनों के लिए पर्याप्त है?",
            "hi_latn": "Kya 70 percent attendance course pass karne aur semester exam dono ke liye kaafi hai?",
            "hinglish": "Kya 70% attendance se course aur end sem exam dono clear ho jayenge?"
        }
    },
    {
        "intent_id": "M9-INT-06",
        "query_type": "HISTORICAL",
        "expected_status": "ANSWERED",
        "expected_documents": ["SEAS-Ordinance-Rules-Regulations-2017.pdf"],
        "passage_snippet": "A student must have a minimum attendance of 70% in a course during a semester",
        "expected_claims": ["The 2017 SEAS ordinance required 70% minimum attendance to avoid an X grade."],
        "expected_answer": "Under the 2017 SEAS Ordinance, a student was required to maintain a minimum of 70% attendance in a course to avoid an 'X' grade.",
        "applicability_constraints": {"temporal": "2017", "cohort": "2017"},
        "variants": {
            "en": "What was the course attendance requirement under the 2017 SEAS rules?",
            "hi": "2017 SEAS नियमों के तहत कोर्स उपस्थिति की क्या आवश्यकता थी?",
            "hi_latn": "2017 SEAS rules ke mutabiq course attendance requirement kya thi?",
            "hinglish": "2017 batch ke SEAS ordinance mein attendance rule kya tha?"
        }
    },
    {
        "intent_id": "M9-INT-07",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "by the Dean of the School / Vice Chancellor",
        "expected_claims": ["The Dean of the School or the Vice Chancellor is authorized to grant attendance relaxation."],
        "expected_answer": "The Dean of the School or the Vice Chancellor is authorized to grant attendance relaxation on approved grounds.",
        "applicability_constraints": {"purpose": "RELAXATION_AUTHORITY"},
        "variants": {
            "en": "Who has the authority to approve attendance relaxation for students?",
            "hi": "छात्रों के लिए उपस्थिति में छूट स्वीकृत करने का अधिकार किसके पास है?",
            "hi_latn": "Students ke liye attendance relaxation approve karne ki authority kiske paas hai?",
            "hinglish": "Attendance relaxation approve karne ki power kiske paas hoti hai?"
        }
    },
    {
        "intent_id": "M9-INT-08",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "in lectures, tutorials and practicals taken together",
        "expected_claims": ["Course attendance calculation combines lectures, tutorials, and practicals together."],
        "expected_answer": "Attendance is calculated based on lectures, tutorials, and practicals taken together in a course during the semester.",
        "applicability_constraints": {"purpose": "ATTENDANCE_COMPUTATION"},
        "variants": {
            "en": "Are lectures, tutorials, and practicals counted together for course attendance?",
            "hi": "क्या कोर्स उपस्थिति के लिए व्याख्यान, ट्यूटोरियल और प्रैक्टिकल एक साथ गिने जाते हैं?",
            "hi_latn": "Kya course attendance ke liye lectures, tutorials aur practicals saath mein count hote hain?",
            "hinglish": "Lectures, tutorials aur practicals ki attendance alag count hoti hai ya saath mein?"
        }
    },

    # ── Category 2: Grading System & Evaluation (Intents 9-16) ─────────────────────
    {
        "intent_id": "M9-INT-09",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "structure of grading for academic performance",
        "expected_claims": ["The grading structure uses letter grades including O, A+, A, B+, B, C+, C, D, and F."],
        "expected_answer": "The university follows a letter grading scale with grades O, A+, A, B+, B, C+, C, D, and F, carrying grade points from 10 down to 0.",
        "applicability_constraints": {"purpose": "GRADING_STRUCTURE"},
        "variants": {
            "en": "What is the letter grading system used for student academic performance?",
            "hi": "छात्रों के शैक्षणिक प्रदर्शन के लिए किस लेटर ग्रेडिंग प्रणाली का उपयोग किया जाता है?",
            "hi_latn": "Students ke academic performance ke liye kaunsa letter grading system use hota hai?",
            "hinglish": "Academic grading scale mein kaun kaun se letter grades hote hain?"
        }
    },
    {
        "intent_id": "M9-INT-10",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "award of 'X' grade",
        "expected_claims": ["An X grade indicates debarment due to low attendance and requires repeating the course."],
        "expected_answer": "An 'X' grade is awarded to students who fail to meet the minimum 70% attendance requirement, requiring them to reregister and repeat the course.",
        "applicability_constraints": {"grade": "X"},
        "variants": {
            "en": "What does an X grade mean and what is the consequence of receiving it?",
            "hi": "'X' ग्रेड का क्या अर्थ है और इसे प्राप्त करने का क्या परिणाम होता है?",
            "hi_latn": "X grade ka kya matlab hai aur ye milne par kya hota hai?",
            "hinglish": "Agar kisi course mein X grade mil jaye toh uska consequence kya hai?"
        }
    },
    {
        "intent_id": "M9-INT-11",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "The range for D grade shall start from 30 marks onwards",
        "expected_claims": ["The minimum passing threshold for a D grade starts from 30 marks."],
        "expected_answer": "The minimum passing range for a 'D' grade starts from 30 marks onwards for all courses.",
        "applicability_constraints": {"grade": "D"},
        "variants": {
            "en": "What is the minimum marks threshold required to secure a D grade?",
            "hi": "'D' ग्रेड प्राप्त करने के लिए न्यूनतम कितने अंकों की आवश्यकता होती है?",
            "hi_latn": "D grade secure karne ke liye minimum kitne marks chahiye?",
            "hinglish": "Course mein passing D grade ke liye minimum marks cutoff kya hai?"
        }
    },
    {
        "intent_id": "M9-INT-12",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "award of 'I' grade",
        "expected_claims": ["An I grade represents Incomplete and must be converted through makeup examination."],
        "expected_answer": "An 'I' grade signifies 'Incomplete', awarded when a student is permitted to miss an examination due to verified medical or extenuating circumstances.",
        "applicability_constraints": {"grade": "I"},
        "variants": {
            "en": "Under what circumstances is an I grade awarded to a student?",
            "hi": "छात्र को किन परिस्थितियों में 'I' ग्रेड दिया जाता है?",
            "hi_latn": "Student ko kin situations mein I grade milta hai?",
            "hinglish": "Report card mein I grade kab award kiya jata hai?"
        }
    },
    {
        "intent_id": "M9-INT-13",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "students shall be awarded AU for pass",
        "expected_claims": ["Audit courses award an AU grade upon passing and do not carry degree credit."],
        "expected_answer": "For audit courses, students receive an 'AU' grade upon passing, which does not earn credits toward degree requirements.",
        "applicability_constraints": {"grade": "AU"},
        "variants": {
            "en": "Do audit courses award credits and what grade is given for them?",
            "hi": "क्या ऑडिट कोर्स में क्रेडिट मिलते हैं और उनके लिए क्या ग्रेड दिया जाता है?",
            "hi_latn": "Kya audit courses mein credit milte hain aur kaunsa grade milta hai?",
            "hinglish": "Audit courses ke liye kya AU grade milta hai aur kya credits count hote hain?"
        }
    },
    {
        "intent_id": "M9-INT-14",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "21 Grade Moderation",
        "expected_claims": ["A Grade Moderation Committee reviews and moderates grade distributions."],
        "expected_answer": "Grade moderation is conducted by a Grade Moderation Committee to review course grading boundaries and ensure consistency.",
        "applicability_constraints": {"purpose": "GRADE_MODERATION"},
        "variants": {
            "en": "How is grade moderation conducted for course evaluations?",
            "hi": "कोर्स मूल्यांकन के लिए ग्रेड मॉडरेशन कैसे किया जाता है?",
            "hi_latn": "Course evaluation ke liye grade moderation kaise conduct hota hai?",
            "hinglish": "Exam ke baad grade moderation ka process kya hota hai?"
        }
    },
    {
        "intent_id": "M9-INT-15",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "Cumulative Grade Point Average (CGPA)",
        "expected_claims": ["CGPA is calculated as the weighted average of grade points across all registered courses."],
        "expected_answer": "CGPA is calculated by dividing the sum of credits multiplied by grade points earned across all registered courses by the total registered credits.",
        "applicability_constraints": {"purpose": "CGPA_CALCULATION"},
        "variants": {
            "en": "How is the Cumulative Grade Point Average (CGPA) calculated?",
            "hi": "कम्युलेटिव ग्रेड प्वाइंट एवरेज (CGPA) की गणना कैसे की जाती है?",
            "hi_latn": "Cumulative Grade Point Average yaani CGPA kaise calculate hota hai?",
            "hinglish": "Bennett University mein overall CGPA calculate karne ka formula kya hai?"
        }
    },
    {
        "intent_id": "M9-INT-16",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "Grade Point Average of 5.0",
        "expected_claims": ["A minimum CGPA of 5.0 is required for the award of undergraduate degree."],
        "expected_answer": "A student must attain a minimum Cumulative Grade Point Average (CGPA) of 5.0 to be eligible for the award of an undergraduate degree.",
        "applicability_constraints": {"purpose": "DEGREE_ELIGIBILITY"},
        "variants": {
            "en": "What is the minimum CGPA required to graduate and receive a B.Tech degree?",
            "hi": "बी.टेक डिग्री प्राप्त करने और स्नातक होने के लिए न्यूनतम कितने CGPA की आवश्यकता होती है?",
            "hi_latn": "B.Tech degree lene aur graduate hone ke liye minimum kitna CGPA hona chahiye?",
            "hinglish": "Degree award ke liye minimum CGPA requirement kitni hai?"
        }
    },

    # ── Category 3: Examination & Make-Up Regulations (Intents 17-22) ──────────────
    {
        "intent_id": "M9-INT-17",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "16.2 Makeup of End Semester Examination",
        "expected_claims": ["Makeup examinations are permitted only on approved medical or extenuating grounds."],
        "expected_answer": "Makeup examinations for End Semester Examinations are permitted only for students who obtained prior approval due to severe illness or extenuating circumstances.",
        "applicability_constraints": {"purpose": "MAKEUP_EXAMINATION"},
        "variants": {
            "en": "Who is eligible to take a make-up examination for end-semester exams?",
            "hi": "एंड-सेमेस्टर परीक्षा के लिए मेक-अप परीक्षा देने का पात्र कौन है?",
            "hi_latn": "End-semester exam ke liye make-up examination kaun de sakta hai?",
            "hinglish": "End sem exams miss hone par makeup exam ki eligibility kya hai?"
        }
    },
    {
        "intent_id": "M9-INT-18",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "17. Supplementary Examination",
        "expected_claims": ["Supplementary examinations provide an opportunity to clear courses with an F grade."],
        "expected_answer": "Supplementary examinations allow students who received an 'F' grade in a course to re-appear and clear the course without repeating the entire semester.",
        "applicability_constraints": {"purpose": "SUPPLEMENTARY_EXAMINATION"},
        "variants": {
            "en": "What is the policy for supplementary examinations?",
            "hi": "पूरक (सप्लीमेंट्री) परीक्षाओं के लिए क्या नीति है?",
            "hi_latn": "Supplementary exams ke liye university ki policy kya hai?",
            "hinglish": "Supplementary examination ka rule kya hai aur F grade wale kaise de sakte hain?"
        }
    },
    {
        "intent_id": "M9-INT-19",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "15.2 Practical/Clinical Courses",
        "expected_claims": ["Practical courses are evaluated based on continuous lab assessment and viva."],
        "expected_answer": "The examination criteria for practical courses are decided through continuous laboratory evaluation, practical tests, and viva voce.",
        "applicability_constraints": {"purpose": "PRACTICAL_EVALUATION"},
        "variants": {
            "en": "How are practical and laboratory courses evaluated?",
            "hi": "प्रैक्टिकल और प्रयोगशाला पाठ्यक्रमों का मूल्यांकन कैसे किया जाता है?",
            "hi_latn": "Practical aur lab courses ka evaluation kaise kiya jata hai?",
            "hinglish": "Lab practical courses ka grading aur examination criteria kya hai?"
        }
    },
    {
        "intent_id": "M9-INT-20",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "Officer to the Registrar/Controller of Examination",
        "expected_claims": ["Medical documents must be submitted within 5 days of the missed examination."],
        "expected_answer": "Medical documents for missing an examination must be submitted to the competent authority no later than 5 days after the examination date.",
        "applicability_constraints": {"purpose": "MEDICAL_SUBMISSION_TIMELINE"},
        "variants": {
            "en": "Within how many days must medical documents be submitted after missing an exam?",
            "hi": "परीक्षा छूटने के कितने दिनों के भीतर मेडिकल दस्तावेज जमा करने होते हैं?",
            "hi_latn": "Exam miss hone ke kitne din ke andar medical documents submit karne hote hain?",
            "hinglish": "Exam miss karne par medical certificate submit karne ki deadline kitne days hai?"
        }
    },
    {
        "intent_id": "M9-INT-21",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Calendar-2026-27.pdf"],
        "passage_snippet": "Admit Card Issue- Start Date",
        "expected_claims": ["Admit cards are mandatory to appear in end-semester examinations."],
        "expected_answer": "Students must possess an officially issued Admit Card to be permitted into the End Semester Examination hall.",
        "applicability_constraints": {"purpose": "ADMIT_CARD"},
        "variants": {
            "en": "Is an admit card required to enter the end-semester examination hall?",
            "hi": "क्या एंड-सेमेस्टर परीक्षा हॉल में प्रवेश के लिए एडमिट कार्ड आवश्यक है?",
            "hi_latn": "Kya end-semester examination hall mein enter karne ke liye admit card chahiye?",
            "hinglish": "End sem exam hall mein admit card compulsory hota hai kya?"
        }
    },
    {
        "intent_id": "M9-INT-22",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "17.5 Supplementary for Projects",
        "expected_claims": ["Supplementary evaluation for projects requires submission within a specified period."],
        "expected_answer": "Supplementary evaluation for project work requires students to re-submit or present revised project deliverables within the prescribed university timeline.",
        "applicability_constraints": {"purpose": "PROJECT_SUPPLEMENTARY"},
        "variants": {
            "en": "Is there a supplementary examination option available for project courses?",
            "hi": "क्या प्रोजेक्ट पाठ्यक्रमों के लिए पूरक (सप्लीमेंट्री) परीक्षा का विकल्प उपलब्ध है?",
            "hi_latn": "Kya project courses ke liye supplementary exam ka option hota hai?",
            "hinglish": "Project work mein fail hone par supplementary evaluation kaise hoti hai?"
        }
    },

    # ── Category 4: Academic Progression, Credits & Curriculum (Intents 23-28) ─────
    {
        "intent_id": "M9-INT-23",
        "query_type": "NUMERICAL",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "A semester will be of approximately 18-20 weeks duration",
        "expected_claims": ["A semester is approximately 18-20 weeks with 90 available teaching days."],
        "expected_answer": "A semester lasts approximately 18 to 20 weeks, of which 90 days are allocated for teaching.",
        "applicability_constraints": {"purpose": "SEMESTER_DURATION"},
        "variants": {
            "en": "What is the duration of a semester and how many teaching days are scheduled?",
            "hi": "एक सेमेस्टर की अवधि क्या होती है और इसमें कितने शिक्षण दिन निर्धारित हैं?",
            "hi_latn": "Ek semester ki duration kya hoti hai aur usme kitne teaching days hote hain?",
            "hinglish": "Semester kitne weeks ka hota hai aur kitne days teaching ke liye hote hain?"
        }
    },
    {
        "intent_id": "M9-INT-24",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "promoted to 3rd year, it is essential that he/she does not have any backlog",
        "expected_claims": ["To be promoted to 3rd year, a student must clear all 1st year backlog courses."],
        "expected_answer": "For a student to be promoted to the 3rd year, it is mandatory to have cleared all backlog courses from the 1st year.",
        "applicability_constraints": {"purpose": "YEAR_PROMOTION"},
        "variants": {
            "en": "What is the backlog requirement for promotion to the 3rd year?",
            "hi": "तीसरे वर्ष में पदोन्नति (प्रमोशन) के लिए बैकलॉग की क्या आवश्यकता है?",
            "hi_latn": "Third year mein promotion ke liye backlog ka kya rule hai?",
            "hinglish": "3rd year mein promote hone ke liye 1st year ke backlogs clear hona zaroori hai kya?"
        }
    },
    {
        "intent_id": "M9-INT-25",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "8.5 Credit Restriction",
        "expected_claims": ["Students under academic probation face restrictions on maximum registered credits."],
        "expected_answer": "Students facing academic performance monitoring or probation are subject to credit load restrictions per semester.",
        "applicability_constraints": {"purpose": "CREDIT_RESTRICTION"},
        "variants": {
            "en": "What are credit restrictions for students with low academic performance?",
            "hi": "कम शैक्षणिक प्रदर्शन वाले छात्रों के लिए क्रेडिट प्रतिबंध क्या हैं?",
            "hi_latn": "Low academic performance wale students ke liye credit restrictions kya hoti hain?",
            "hinglish": "Agar CGPA kam ho toh semester mein credit restriction kaise lagti hai?"
        }
    },
    {
        "intent_id": "M9-INT-26",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "28 B. Tech. with Minors",
        "expected_claims": ["Students can earn a Minor by completing prescribed additional elective credits."],
        "expected_answer": "Undergraduate engineering students can earn a B.Tech with Minor by registering for and completing specified additional minor credits.",
        "applicability_constraints": {"purpose": "MINOR_PROGRAMME"},
        "variants": {
            "en": "How can a B.Tech student earn a Minor specialization?",
            "hi": "एक बी.टेक छात्र माइनर विशेषज्ञता कैसे प्राप्त कर सकता है?",
            "hi_latn": "Ek B.Tech student Minor specialization kaise earn kar sakta hai?",
            "hinglish": "B.Tech mein Minor lene ka kya procedure aur credit requirement hai?"
        }
    },
    {
        "intent_id": "M9-INT-27",
        "query_type": "NUMERICAL",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "8.9 Minimum Number of Students to be Registered in a Course",
        "expected_claims": ["An elective course runs only if a minimum number of students register for it."],
        "expected_answer": "An elective course is offered only if the minimum prescribed student enrollment threshold is satisfied.",
        "applicability_constraints": {"purpose": "COURSE_OFFERING_THRESHOLD"},
        "variants": {
            "en": "What is the minimum number of students required to run an elective course?",
            "hi": "किसी ऐच्छिक (इलेक्टिव) पाठ्यक्रम को चलाने के लिए न्यूनतम कितने छात्रों की आवश्यकता होती है?",
            "hi_latn": "Kisi elective course ko run karne ke liye minimum kitne students hone chahiye?",
            "hinglish": "Elective course offer hone ke liye minimum student enrollment kitni chahiye?"
        }
    },
    {
        "intent_id": "M9-INT-28",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Rules-for-SCSET_UG.pdf"],
        "passage_snippet": "7.2 Preparatory English Course",
        "expected_claims": ["Students deficient in English proficiency must take a Preparatory English Course."],
        "expected_answer": "Students who require foundational language skills are required to register for and complete a non-credit Preparatory English Course.",
        "applicability_constraints": {"purpose": "PREPARATORY_COURSE"},
        "variants": {
            "en": "Who is required to take the Preparatory English Course?",
            "hi": "प्रारंभिक अंग्रेजी पाठ्यक्रम (प्रिपरेटरी इंग्लिश कोर्स) लेना किसके लिए आवश्यक है?",
            "hi_latn": "Preparatory English Course lena kiske liye compulsory hota hai?",
            "hinglish": "Preparatory English course kin students ko assign kiya jata hai?"
        }
    },

    # ── Category 5: Student Discipline & Conduct Rules 2024 (Intents 29-34) ────────
    {
        "intent_id": "M9-INT-29",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Students-Discipline-Conduct-Rules-2024.pdf"],
        "passage_snippet": "STUDENTS’ DISCIPLINE AND CONDUCT RULES",
        "expected_claims": ["The university maintains strict zero tolerance against ragging with penalties including expulsion."],
        "expected_answer": "Bennett University enforces a strict zero-tolerance policy against ragging, penalizing violators with immediate suspension, rustication, or expulsion.",
        "applicability_constraints": {"offence": "RAGGING"},
        "variants": {
            "en": "What is the university's policy and penalty regarding ragging?",
            "hi": "रैगिंग के संबंध में विश्वविद्यालय की क्या नीति और दंड है?",
            "hi_latn": "Ragging ke regarding university ki policy aur penalty kya hai?",
            "hinglish": "Ragging karne par university kya punishment aur action leti hai?"
        }
    },
    {
        "intent_id": "M9-INT-30",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Students-Discipline-Conduct-Rules-2024.pdf"],
        "passage_snippet": "Proctorial Committee proceedings",
        "expected_claims": ["Disciplinary cases are investigated by the Proctorial Board/Committee."],
        "expected_answer": "Disciplinary infractions on campus are investigated and adjudicated by the Proctorial Committee / Board.",
        "applicability_constraints": {"body": "PROCTORIAL_BOARD"},
        "variants": {
            "en": "Which university committee is responsible for investigating student indiscipline?",
            "hi": "छात्र अनुशासनहीनता की जांच के लिए कौन सी विश्वविद्यालय समिति जिम्मेदार है?",
            "hi_latn": "Student indiscipline ki investigation ke liye kaunsi university committee responsible hai?",
            "hinglish": "Campus mein disciplinary issues handle karne ke liye kaunsi committee hoti hai?"
        }
    },
    {
        "intent_id": "M9-INT-31",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Students-Discipline-Conduct-Rules-2024.pdf"],
        "passage_snippet": "prohibited materials (tobacco/ alcohol, drugs",
        "expected_claims": ["Possession or consumption of alcohol, drugs, or tobacco on campus is strictly prohibited."],
        "expected_answer": "Possession, consumption, or supplying of alcohol, narcotic drugs, or tobacco products inside university premises is strictly banned and attracts severe fines and suspension.",
        "applicability_constraints": {"offence": "SUBSTANCE_ABUSE"},
        "variants": {
            "en": "What are the rules and penalties concerning alcohol and drugs on campus?",
            "hi": "परिसर में शराब और नशीले पदार्थों के संबंध में क्या नियम और दंड हैं?",
            "hi_latn": "Campus mein alcohol aur drugs ke regarding kya rules aur penalties hain?",
            "hinglish": "Campus mein alcohol ya drugs possess karne par kya penalty lagti hai?"
        }
    },
    {
        "intent_id": "M9-INT-32",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Students-Discipline-Conduct-Rules-2024.pdf"],
        "passage_snippet": "6. Appeal:",
        "expected_claims": ["Students have the right to appeal against disciplinary decisions to the Vice Chancellor."],
        "expected_answer": "A student aggrieved by a disciplinary order may submit an appeal to the Vice Chancellor within the stipulated time frame.",
        "applicability_constraints": {"procedure": "DISCIPLINARY_APPEAL"},
        "variants": {
            "en": "Can a student appeal against a disciplinary decision of the Proctorial Committee?",
            "hi": "क्या कोई छात्र प्रॉक्टोरियल कमेटी के अनुशासनात्मक निर्णय के खिलाफ अपील कर सकता है?",
            "hi_latn": "Kya student Proctorial Committee ke disciplinary decision ke against appeal kar sakta hai?",
            "hinglish": "Proctorial board ke punishment order ke khilaaf appeal kahan ki ja sakti hai?"
        }
    },
    {
        "intent_id": "M9-INT-33",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Students-Discipline-Conduct-Rules-2024.pdf"],
        "passage_snippet": "Suspension for upto two weeks",
        "expected_claims": ["The Proctorial Committee can impose suspensions for periods up to multiple weeks."],
        "expected_answer": "Depending on the severity of the offense, the disciplinary authority can suspend a student from academic activities or hostels for up to two weeks or longer.",
        "applicability_constraints": {"penalty": "SUSPENSION"},
        "variants": {
            "en": "What is the typical duration of suspension imposed for misconduct?",
            "hi": "दुर्व्यवहार के लिए आमतौर पर निलंबन (सस्पेंशन) की अवधि क्या होती है?",
            "hi_latn": "Misconduct ke liye suspension ki typical duration kya hoti hai?",
            "hinglish": "Student ko misconduct ke case mein kitne time ke liye suspend kiya ja sakta hai?"
        }
    },
    {
        "intent_id": "M9-INT-34",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Students-Discipline-Conduct-Rules-2024.pdf"],
        "passage_snippet": "unauthorized entry of outsiders into the Campus",
        "expected_claims": ["Facilitating unauthorized entry of outsiders into campus or hostels is a punishable offense."],
        "expected_answer": "Aiding or facilitating the unauthorized entry of outside persons into the campus or hostels incurs monetary fines and disciplinary action.",
        "applicability_constraints": {"offence": "UNAUTHORIZED_ENTRY"},
        "variants": {
            "en": "Is bringing unauthorized outsiders into hostels or campus a punishable offense?",
            "hi": "क्या हॉस्टल या परिसर में अनाधिकृत बाहरी व्यक्तियों को लाना दंडनीय अपराध है?",
            "hi_latn": "Kya hostel ya campus mein unauthorized outsiders ko lana punishable offence hai?",
            "hinglish": "Outsiders ko bina permission hostel ya campus mein lane par kya action hota hai?"
        }
    },

    # ── Category 6: Unfair Means (UFM) Guidelines 2024 (Intents 35-39) ─────────────
    {
        "intent_id": "M9-INT-35",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["UFM-Guidelines-2024.pdf"],
        "passage_snippet": "FORMFORUNFAIRMEANS",
        "expected_claims": ["Carrying a mobile phone or electronic device inside the exam hall constitutes unfair means."],
        "expected_answer": "Possession of mobile phones, smartwatches, or unauthorized electronic gadgets inside the examination hall is treated as unfair means (UFM) and leads to paper cancellation.",
        "applicability_constraints": {"ufm_clause": "MOBILE_PHONE"},
        "variants": {
            "en": "What is the penalty for possessing a mobile phone in the examination hall?",
            "hi": "परीक्षा हॉल में मोबाइल फोन रखने पर क्या दंड दिया जाता है?",
            "hi_latn": "Exam hall mein mobile phone rakhne par kya penalty lagti hai?",
            "hinglish": "Examination room mein phone pakde jane par kya UFM lagta hai?"
        }
    },
    {
        "intent_id": "M9-INT-36",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["UFM-Guidelines-2024.pdf"],
        "passage_snippet": "impersonating another candidates",
        "expected_claims": ["Impersonating another candidate results in cancellation of registration and expulsion."],
        "expected_answer": "Impersonating another candidate or allowing impersonation in any examination results in cancellation of examination and severe penalties including expulsion.",
        "applicability_constraints": {"ufm_clause": "IMPERSONATION"},
        "variants": {
            "en": "What action is taken if a student impersonates someone else in an examination?",
            "hi": "यदि कोई छात्र परीक्षा में किसी अन्य का रूप धारण (इम्पर्सनेशन) करता है तो क्या कार्रवाई की जाती है?",
            "hi_latn": "Agar koi student exam mein kisi aur ki jagah baithe toh kya action hota hai?",
            "hinglish": "Exam mein impersonation ya proxy baithane par kya punishment hoti hai?"
        }
    },
    {
        "intent_id": "M9-INT-37",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["UFM-Guidelines-2024.pdf"],
        "passage_snippet": "allowing other student's to copy from his/her answer book",
        "expected_claims": ["Allowing another student to copy from one's answer book constitutes unfair means."],
        "expected_answer": "Allowing another student to copy from one's answer book or communicating during the exam is penalized under UFM guidelines.",
        "applicability_constraints": {"ufm_clause": "COPYING"},
        "variants": {
            "en": "Is allowing another student to copy from your exam answer script considered unfair means?",
            "hi": "क्या किसी अन्य छात्र को अपनी उत्तर पुस्तिका से नकल करने देना अनुचित साधन (UFM) माना जाता है?",
            "hi_latn": "Kya kisi doosre student ko apni answer sheet se copy karne dena UFM mana jata hai?",
            "hinglish": "Exam mein doosre student ko answer dikhana ya copy karwana kya punishable hai?"
        }
    },
    {
        "intent_id": "M9-INT-38",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["UFM-Guidelines-2024.pdf"],
        "passage_snippet": "4. Convening of Committee on Unfair Means",
        "expected_claims": ["The Committee on Unfair Means examines evidence and hears the student before deciding penalties."],
        "expected_answer": "The Committee on Unfair Means (UFM Committee) convenes to review reported cases, examine physical evidence, give the candidate an opportunity to explain, and recommend penalties.",
        "applicability_constraints": {"body": "UFM_COMMITTEE"},
        "variants": {
            "en": "How does the Committee on Unfair Means investigate cheating cases?",
            "hi": "अनुचित साधन समिति (UFM कमेटी) नकल के मामलों की जांच कैसे करती है?",
            "hi_latn": "Unfair Means Committee cheating ke cases ki investigation kaise karti hai?",
            "hinglish": "UFM committee unfair means ke cases mein student ko kaise hear karti hai?"
        }
    },
    {
        "intent_id": "M9-INT-39",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["UFM-Guidelines-2024.pdf"],
        "passage_snippet": "Guilty of serious misconduct in",
        "expected_claims": ["Serious misconduct during examinations may result in debarment for multiple semesters."],
        "expected_answer": "Students found guilty of serious exam misconduct may be debarred from taking university examinations for one or more subsequent semesters.",
        "applicability_constraints": {"penalty": "DEBARMENT"},
        "variants": {
            "en": "Can a student be debarred from future semester examinations under UFM rules?",
            "hi": "क्या UFM नियमों के तहत किसी छात्र को भविष्य की सेमेस्टर परीक्षाओं से वंचित किया जा सकता है?",
            "hi_latn": "Kya UFM rules ke under student ko aage ke semester exams se debar kiya ja sakta hai?",
            "hinglish": "Kya UFM case mein student multiple semesters ke liye debar ho sakta hai?"
        }
    },

    # ── Category 7: Academic Calendar 2026-27 (Intents 40-45) ──────────────────────
    {
        "intent_id": "M9-INT-40",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Calendar-2026-27.pdf"],
        "passage_snippet": "Registration for Even Semester Make-up Examination-Start Date",
        "expected_claims": ["Registration for Even Semester Make-up Examination starts on 01-07-2026."],
        "expected_answer": "According to the Academic Calendar 2026-27, registration for the Even Semester Make-up Examination starts on Wednesday, 01-07-2026.",
        "applicability_constraints": {"event": "MAKEUP_REGISTRATION_START"},
        "variants": {
            "en": "When does registration for the Even Semester Make-up Examination start in 2026?",
            "hi": "2026 में इवन सेमेस्टर मेक-अप परीक्षा के लिए पंजीकरण कब शुरू होता है?",
            "hi_latn": "2026 mein Even Semester Make-up Examination ka registration kab start hota hai?",
            "hinglish": "2026 even sem makeup exam registration start date kya hai?"
        }
    },
    {
        "intent_id": "M9-INT-41",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Calendar-2026-27.pdf"],
        "passage_snippet": "Admit Card Issue- Start Date",
        "expected_claims": ["Admit card issue starts on Monday, 07-12-2026 for the Odd Semester."],
        "expected_answer": "Admit card issuance for the Odd Semester begins on Monday, 07-12-2026.",
        "applicability_constraints": {"event": "ADMIT_CARD_ISSUE"},
        "variants": {
            "en": "On what date does the issuance of admit cards start for the Odd Semester in 2026?",
            "hi": "2026 में ऑड सेमेस्टर के लिए एडमिट कार्ड जारी करने की तिथि क्या है?",
            "hi_latn": "2026 mein Odd Semester ke liye admit card issue hone ki start date kya hai?",
            "hinglish": "Odd sem 2026 ke admit cards kis date se issue hone shuru honge?"
        }
    },
    {
        "intent_id": "M9-INT-42",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Calendar-2026-27.pdf"],
        "passage_snippet": "Convocation (Tentative)",
        "expected_claims": ["The tentative date for the Convocation in 2026 is Friday, 13-11-2026."],
        "expected_answer": "The tentative date scheduled for the university Convocation is Friday, 13-11-2026.",
        "applicability_constraints": {"event": "CONVOCATION"},
        "variants": {
            "en": "What is the scheduled tentative date for Convocation in the 2026-27 calendar?",
            "hi": "2026-27 शैक्षणिक कैलेंडर में दीक्षांत समारोह (कॉन्वोकेशन) की संभावित तिथि क्या है?",
            "hi_latn": "2026-27 academic calendar mein Convocation ki tentative date kya hai?",
            "hinglish": "Academic year 2026-27 mein university convocation ki tentative date kya rakhi gayi hai?"
        }
    },
    {
        "intent_id": "M9-INT-43",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Calendar-2026-27.pdf"],
        "passage_snippet": "Odd Semester Mid-Term Marks Submission in ERP – End Date",
        "expected_claims": ["Odd Semester mid-term marks submission in ERP ends on 13-11-2026."],
        "expected_answer": "The deadline for faculty to submit Odd Semester mid-term marks in ERP is Friday, 13-11-2026.",
        "applicability_constraints": {"event": "MIDTERM_MARKS_DEADLINE"},
        "variants": {
            "en": "What is the last date for submitting Odd Semester mid-term marks in ERP?",
            "hi": "ईआरपी में ऑड सेमेस्टर मिड-टर्म अंक जमा करने की अंतिम तिथि क्या है?",
            "hi_latn": "ERP mein Odd Semester mid-term marks submit karne ki last date kya hai?",
            "hinglish": "Odd semester mid term marks ERP par submit karne ki end date kya hai?"
        }
    },
    {
        "intent_id": "M9-INT-44",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["Academic-Calendar-2026-27.pdf"],
        "passage_snippet": "05-12-2026 Saturday Holiday",
        "expected_claims": ["05-12-2026 and 06-12-2026 are scheduled as holidays in December 2026."],
        "expected_answer": "Saturday, 05-12-2026 and Sunday, 06-12-2026 are scheduled as holidays in the academic calendar.",
        "applicability_constraints": {"event": "DECEMBER_HOLIDAYS"},
        "variants": {
            "en": "Are December 5 and 6, 2026 scheduled as holidays?",
            "hi": "क्या 5 और 6 दिसंबर 2026 को अवकाश (हॉलिडे) निर्धारित है?",
            "hi_latn": "Kya 5 aur 6 December 2026 ko holiday schedule kiya gaya hai?",
            "hinglish": "5-6 December 2026 ko calendar mein holiday mark hai ya class hogi?"
        }
    },
    {
        "intent_id": "M9-INT-45",
        "query_type": "DIRECT",
        "expected_status": "ANSWERED",
        "expected_documents": ["BU-First-Ordinance-2016.pdf"],
        "passage_snippet": "The Vice-Chancellor shall be the principal executive and academic officer",
        "expected_claims": ["The Vice-Chancellor is the principal executive and academic officer of the University."],
        "expected_answer": "Under the BU First Ordinance 2016, the Vice-Chancellor is the principal executive and academic officer of the University.",
        "applicability_constraints": {"statute": "FIRST_ORDINANCE"},
        "variants": {
            "en": "Who is designated as the principal executive and academic officer of Bennett University?",
            "hi": "बेनेट विश्वविद्यालय के मुख्य कार्यकारी और शैक्षणिक अधिकारी के रूप में किसे नामित किया गया है?",
            "hi_latn": "Bennett University ke principal executive aur academic officer kaun hote hain?",
            "hinglish": "University ka main academic aur executive head kaun hota hai according to ordinance?"
        }
    },

    # ── Category 8: Unanswerable / Insufficient Evidence (Intents 46-60) ───────────
    {
        "intent_id": "M9-INT-46",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Information regarding hostel mess menu voting is not available in official documents."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "HOSTEL_MESS_MENU"},
        "variants": {
            "en": "What is the voting procedure for students to select the hostel mess food menu?",
            "hi": "हॉस्टल मेस के खाने के मेनू को चुनने के लिए छात्रों की वोटिंग प्रक्रिया क्या है?",
            "hi_latn": "Hostel mess ke food menu ko decide karne ke liye student voting process kya hai?",
            "hinglish": "Hostel mess menu choose karne ke liye students ka voting system kaise kaam karta hai?"
        }
    },
    {
        "intent_id": "M9-INT-47",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Tuition fee refund percentages after six months are not defined in academic ordinances."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "FEE_REFUND_SCHEDULE"},
        "variants": {
            "en": "What percentage of tuition fee is refunded if a student withdraws after six months?",
            "hi": "यदि कोई छात्र छह महीने बाद नाम वापस लेता है तो शिक्षण शुल्क का कितने प्रतिशत वापस किया जाता है?",
            "hi_latn": "Agar koi student 6 month baad admission withdraw kare toh kitna fees refund milta hai?",
            "hinglish": "6 months baad admission cancel karne par tuition fee refund percentage kitna hai?"
        }
    },
    {
        "intent_id": "M9-INT-48",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Campus placement highest salary packages are not published in academic rulebooks."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "PLACEMENT_PACKAGES"},
        "variants": {
            "en": "What was the highest international salary package offered during campus placements in 2025?",
            "hi": "2025 में कैंपस प्लेसमेंट के दौरान पेश किया गया उच्चतम अंतरराष्ट्रीय वेतन पैकेज क्या था?",
            "hi_latn": "2025 ke campus placements mein highest international salary package kitna tha?",
            "hinglish": "2025 placements mein highest overseas CTC package kitna offer hua tha?"
        }
    },
    {
        "intent_id": "M9-INT-49",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Monthly PhD fellowship stipend amounts are not detailed in undergraduate regulations."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "PHD_STIPEND"},
        "variants": {
            "en": "What is the monthly stipend amount provided to full-time PhD research scholars?",
            "hi": "पूर्णकालिक पीएचडी शोधार्थियों को प्रति माह दी जाने वाली छात्रवृत्ति (स्टाइपेंड) की राशि क्या है?",
            "hi_latn": "Full-time PhD research scholars ko monthly stipend kitna milta hai?",
            "hinglish": "PhD scholars ko university se monthly kitna research stipend diya jata hai?"
        }
    },
    {
        "intent_id": "M9-INT-50",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Campus bus transport routes and morning timings are outside academic ordinances."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "TRANSPORT_BUS_TIMINGS"},
        "variants": {
            "en": "What are the morning bus pickup timings and designated stops from Delhi to campus?",
            "hi": "दिल्ली से परिसर के लिए सुबह की बस पिकअप का समय और निर्धारित स्टॉप क्या हैं?",
            "hi_latn": "Delhi se campus aane ke liye morning bus pickup timings aur stops kya hain?",
            "hinglish": "Delhi route ki university transport bus ka morning schedule aur stops kya hain?"
        }
    },
    {
        "intent_id": "M9-INT-51",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Mandatory daily dress code rules for law students are not specified in the corpus."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "LAW_DRESS_CODE"},
        "variants": {
            "en": "What is the mandatory uniform or dress code for School of Law students on weekdays?",
            "hi": "सप्ताह के दिनों में स्कूल ऑफ लॉ के छात्रों के लिए अनिवार्य ड्रेस कोड क्या है?",
            "hi_latn": "Weekdays par School of Law ke students ke liye mandatory dress code kya hai?",
            "hinglish": "Law school students ke liye daily mandatory dress code ya uniform kya hai?"
        }
    },
    {
        "intent_id": "M9-INT-52",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Daily fine rates for overdue library books are not defined in academic rules."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "LIBRARY_FINES"},
        "variants": {
            "en": "What is the daily overdue fine rate per book borrowed from the university library?",
            "hi": "विश्वविद्यालय के पुस्तकालय से ली गई पुस्तक पर दैनिक विलंब शुल्क की दर क्या है?",
            "hi_latn": "University library se li gayi book late return karne par daily fine kitna lagta hai?",
            "hinglish": "Library books late return karne par per day kitna fine charge hota hai?"
        }
    },
    {
        "intent_id": "M9-INT-53",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Sports quota admission criteria are not governed by the academic rules in the corpus."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "SPORTS_QUOTA"},
        "variants": {
            "en": "What are the specific eligibility criteria and trials for sports quota admissions?",
            "hi": "स्पोर्ट्स कोटा में प्रवेश के लिए विशिष्ट पात्रता मानदंड और ट्रायल क्या हैं?",
            "hi_latn": "Sports quota admission ke liye specific eligibility criteria aur trials kya hote hain?",
            "hinglish": "Sports quota ke through admission lene ke liye trial criteria kya hai?"
        }
    },
    {
        "intent_id": "M9-INT-54",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Off-campus private flat permission policies are not contained in the official regulations."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "OFF_CAMPUS_ACCOMMODATION"},
        "variants": {
            "en": "Can 2nd year students get permission to stay in off-campus private flats?",
            "hi": "क्या दूसरे वर्ष के छात्रों को परिसर से बाहर निजी फ्लैटों में रहने की अनुमति मिल सकती है?",
            "hi_latn": "Kya 2nd year students ko campus ke bahar private flat mein rehne ki permission milti hai?",
            "hinglish": "2nd year ke students ke liye off-campus flat permission ka kya rule hai?"
        }
    },
    {
        "intent_id": "M9-INT-55",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Internship stipends paid by external corporations are not regulated in the corpus."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "INTERNSHIP_STIPEND"},
        "variants": {
            "en": "What is the mandatory minimum stipend paid by companies during the 8th semester internship?",
            "hi": "8वें सेमेस्टर की इंटर्नशिप के दौरान कंपनियों द्वारा भुगतान किया जाने वाला अनिवार्य न्यूनतम वजीफा क्या है?",
            "hi_latn": "8th semester internship ke dauran companies kitna minimum stipend pay karti hain?",
            "hinglish": "Final semester internship mein minimum kitna corporate stipend milna compulsory hai?"
        }
    },
    {
        "intent_id": "M9-INT-56",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Foreign visa requirements for international exchange are outside academic ordinances."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "INTERNATIONAL_EXCHANGE_VISA"},
        "variants": {
            "en": "What visa documentation is required for students participating in semester exchange abroad?",
            "hi": "विदेश में सेमेस्टर एक्सचेंज में भाग लेने वाले छात्रों के लिए किस वीजा दस्तावेज की आवश्यकता होती है?",
            "hi_latn": "Abroad semester exchange ke liye students ko kaunse visa documents submit karne hote hain?",
            "hinglish": "Semester exchange program ke liye university se kaunse visa papers milte hain?"
        }
    },
    {
        "intent_id": "M9-INT-57",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Gym personal trainer subscription costs are not part of academic regulations."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "GYM_SUBSCRIPTION"},
        "variants": {
            "en": "How much does the university charge for personal gym trainer sessions per month?",
            "hi": "विश्वविद्यालय प्रति माह पर्सनल जिम ट्रेनर सत्र के लिए कितना शुल्क लेता है?",
            "hi_latn": "University per month personal gym trainer ke liye kitna charge karti hai?",
            "hinglish": "Campus gym mein personal fitness trainer hire karne ki monthly fee kya hai?"
        }
    },
    {
        "intent_id": "M9-INT-58",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["A 50% attendance allowance does not exist; the premise contradicts regulations."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "FALSE_PREMISE_50_ATTENDANCE"},
        "variants": {
            "en": "Why is 50% attendance allowed for final examinations at Bennett University?",
            "hi": "बेनेट विश्वविद्यालय में अंतिम परीक्षाओं के लिए 50% उपस्थिति की अनुमति क्यों दी जाती है?",
            "hi_latn": "Bennett University mein final exams ke liye 50 percent attendance kyu allow ki gayi hai?",
            "hinglish": "End sem exam dene ke liye 50% attendance rule kahan likha hai?"
        }
    },
    {
        "intent_id": "M9-INT-59",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Securing an A grade with 35% marks contradicts the university grading standards."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "FALSE_PREMISE_A_GRADE"},
        "variants": {
            "en": "How can an undergraduate student obtain an 'A' grade with only 35% overall marks?",
            "hi": "एक स्नातक छात्र केवल 35% कुल अंकों के साथ 'A' ग्रेड कैसे प्राप्त कर सकता है?",
            "hi_latn": "Ek student sirf 35 percent marks ke saath 'A' grade kaise score kar sakta hai?",
            "hinglish": "Kya kisi subject mein 35% marks lake A grade mil sakta hai?"
        }
    },
    {
        "intent_id": "M9-INT-60",
        "query_type": "UNANSWERABLE",
        "expected_status": "UNANSWERABLE",
        "expected_documents": [],
        "passage_snippet": "",
        "expected_claims": ["Cross-school branch transfer from Law to B.Tech is not provided for in the academic rules."],
        "expected_answer": "UNANSWERABLE — Insufficient information available in the provided documents.",
        "applicability_constraints": {"topic": "CROSS_SCHOOL_BRANCH_CHANGE"},
        "variants": {
            "en": "What is the procedure to change branch from BA-LLB to B.Tech Computer Science after first year?",
            "hi": "प्रथम वर्ष के बाद बीए-एलएलबी से बी.टेक कंप्यूटर साइंस में शाखा (ब्रांच) बदलने की प्रक्रिया क्या है?",
            "hi_latn": "First year ke baad BA-LLB se B.Tech Computer Science mein branch change karne ka procedure kya hai?",
            "hinglish": "Law school se B.Tech CSE mein stream switch karne ke rules kya hain?"
        }
    }
]
