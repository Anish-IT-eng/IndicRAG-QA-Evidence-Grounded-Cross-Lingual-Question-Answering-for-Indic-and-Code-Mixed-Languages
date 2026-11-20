import csv

audit_rows = [
    {
        'query_id': 'AQ-01',
        'query_text': 'What is the minimum attendance required?',
        'retrieved_passage_ids': 'f88ec726, 0280358a, 505e552e, c31d716d, 1b631297',
        'source_documents': 'SEAS-Ordinance-Rules-Regulations-2017.pdf, Notification-Minimum-Attendance.pdf, Academic-Rules-for-SCSET_UG.pdf',
        'regulatory_condition_identified': 'UNANCHORED_GENERAL_ATTENDANCE (Dual threshold: Exam eligibility vs Course grade)',
        'applicability_determination': 'Ambiguous. Applies to general student population but lacks program, cohort, and condition anchors (75% for exam hall vs 70% for course debarment).',
        'existing_controller_status': 'CONFLICTING',
        'clarification_required': 'TRUE (User should specify whether asking about End Semester Exam eligibility or Course X-grade debarment, and cohort year)',
        'citation_supported': 'TRUE (Retrieved passages support 75% via Notification 307 and 70% via SCSET Clause 30.1)',
        'abstention_necessary': 'FALSE (Dual-threshold disclosure or clarification request should be returned, not outright refusal)',
        'gap_analysis_and_recommended_behavior': 'Existing controller flags generic version conflict. Should explain dual condition: 75% required by Registrar to sit for End Sem Exams; 70% required to avoid X grade in course.'
    },
    {
        'query_id': 'AQ-02',
        'query_text': 'What attendance is required to sit for end semester exams?',
        'retrieved_passage_ids': '0280358a, f88ec726, 505e552e, 2b15a3af, 278fa408',
        'source_documents': 'Notification-Minimum-Attendance.pdf, SEAS-Ordinance-Rules-Regulations-2017.pdf, Academic-Rules-for-SCSET_UG.pdf',
        'regulatory_condition_identified': 'END_SEMESTER_EXAM_ELIGIBILITY',
        'applicability_determination': 'Authoritatively governed by Notification 307/2022 (75% minimum attendance).',
        'existing_controller_status': 'PARTIAL',
        'clarification_required': 'FALSE (Query specifically names \"sit for end semester exams\", matching Notification 307 exactly)',
        'citation_supported': 'TRUE (Cites Notification 307/2022, Page 1)',
        'abstention_necessary': 'FALSE',
        'gap_analysis_and_recommended_behavior': 'Controller evaluated as PARTIAL due to heuristic CECI threshold (0.419). Should be SUFFICIENT because the top retrieved passage (0280358a) directly and fully answers the specific condition.'
    },
    {
        'query_id': 'AQ-03',
        'query_text': 'How much attendance is required to avoid an X grade?',
        'retrieved_passage_ids': 'f88ec726, 505e552e, c7c1dfa7, 9bbbab01, 5fd38f8d',
        'source_documents': 'SEAS-Ordinance-Rules-Regulations-2017.pdf, Academic-Rules-for-SCSET_UG.pdf',
        'regulatory_condition_identified': 'COURSE_LEVEL_GRADING_DEBARMENT (X Grade)',
        'applicability_determination': 'Authoritatively governed by Clause 30.1(ii) of SCSET UG Rules 2022 (and historical SEAS 2017): 70% minimum attendance.',
        'existing_controller_status': 'CONFLICTING',
        'clarification_required': 'FALSE (Both current SCSET 2022 and historical SEAS 2017 agree 100% that <70% results in X grade)',
        'citation_supported': 'TRUE (Cites SCSET UG Rules Clause 30.1(ii), Page 19)',
        'abstention_necessary': 'FALSE',
        'gap_analysis_and_recommended_behavior': 'Controller falsely triggered CONFLICTING because SEAS 2017 is marked is_current=False. This is a false conflict: both documents agree that 70% is required to avoid X grade. Should be SUFFICIENT.'
    },
    {
        'query_id': 'AQ-04',
        'query_text': 'Is 70% attendance enough?',
        'retrieved_passage_ids': 'f88ec726, 1b631297, c31d716d, 0280358a, 6ad292d8',
        'source_documents': 'SEAS-Ordinance-Rules-Regulations-2017.pdf, Academic-Rules-for-SCSET_UG.pdf, Notification-Minimum-Attendance.pdf',
        'regulatory_condition_identified': 'DUAL_THRESHOLD_INTERSECTION (70% vs 75%)',
        'applicability_determination': 'Conditional answer: 70% is sufficient to avoid course X-grade debarment under SCSET Clause 30.1, but insufficient to appear in End Semester Examinations (requires 75% under Notification 307).',
        'existing_controller_status': 'CONFLICTING',
        'clarification_required': 'FALSE (Can be directly answered with nuanced conditional explanation)',
        'citation_supported': 'TRUE (Cites both Notification 307 and SCSET Clause 30.1)',
        'abstention_necessary': 'FALSE',
        'gap_analysis_and_recommended_behavior': 'Existing controller labels this a conflict. The generator should output a structured conditional answer distinguishing course debarment from exam eligibility.'
    },
    {
        'query_id': 'AQ-05',
        'query_text': 'Is 75% compulsory for SCSET students?',
        'retrieved_passage_ids': 'b7549fd6, 4fb20336, 0280358a, cfb81e36, 7de500cb',
        'source_documents': 'Academic-Rules-for-SCSET_UG.pdf, Notification-Minimum-Attendance.pdf',
        'regulatory_condition_identified': 'JURISDICTIONAL_OVERLAP (University Notice vs School Rules)',
        'applicability_determination': 'Yes, for End Semester Examinations across all schools including SCSET (Notification 307/2022).',
        'existing_controller_status': 'INSUFFICIENT',
        'clarification_required': 'FALSE',
        'citation_supported': 'TRUE (Notification 307 applies to all schools; Controller of Examination calls for attendance from respective schools)',
        'abstention_necessary': 'FALSE',
        'gap_analysis_and_recommended_behavior': 'Controller dropped to INSUFFICIENT (CECI: 0.325) because SCSET UG document itself does not contain the string \"75%\". Cross-document inference needed: Notification 307 binds all respective schools.'
    },
    {
        'query_id': 'AQ-06',
        'query_text': 'What was the attendance rule in 2017?',
        'retrieved_passage_ids': 'f88ec726, c31d716d, 0280358a, 82bc0dd1, 6ad292d8',
        'source_documents': 'SEAS-Ordinance-Rules-Regulations-2017.pdf, Academic-Rules-for-SCSET_UG.pdf, Notification-Minimum-Attendance.pdf',
        'regulatory_condition_identified': 'HISTORICAL_COHORT_RULE (2017)',
        'applicability_determination': 'Exclusively governed by SEAS Ordinances 2017, Clause 30.1 (70% minimum attendance).',
        'existing_controller_status': 'CONFLICTING',
        'clarification_required': 'FALSE (Query provides explicit temporal anchor \"in 2017\")' ,
        'citation_supported': 'TRUE (Cites SEAS 2017 Ordinance Clause 30.1, Page 28)',
        'abstention_necessary': 'FALSE',
        'gap_analysis_and_recommended_behavior': 'Major controller gap: Query explicitly anchors to 2017, so the system should retrieve and answer from the 2017 ordinance without flagging a version conflict against newer documents.'
    },
    {
        'query_id': 'AQ-07',
        'query_text': 'Can attendance be relaxed due to medical reasons?',
        'retrieved_passage_ids': '6ad292d8, c31d716d, 505e552e, a40fe16a, 1163039d',
        'source_documents': 'SEAS-Ordinance-Rules-Regulations-2017.pdf, Academic-Rules-for-SCSET_UG.pdf',
        'regulatory_condition_identified': 'ATTENDANCE_CONDONATION_RELAXATION (Medical)',
        'applicability_determination': 'Up to 10% relaxation permitted for continuous illness of two weeks with medical certificate (Clause 30.1(v) in both SCSET 2022 and SEAS 2017).',
        'existing_controller_status': 'CONFLICTING',
        'clarification_required': 'FALSE (Unanimous rule across both regulations)',
        'citation_supported': 'TRUE (Cites SCSET UG Rules Clause 30.1(v), Page 19)',
        'abstention_necessary': 'FALSE',
        'gap_analysis_and_recommended_behavior': 'False conflict. Both 2017 and 2022 regulations contain identical 10% medical relaxation clauses. The controller flagged CONFLICTING solely because one document has is_current=False.'
    }
]

out_path = 'backend/data/experiments/m8/m8_3_attendance_query_audit.csv'
fieldnames = [
    'query_id', 'query_text', 'retrieved_passage_ids', 'source_documents',
    'regulatory_condition_identified', 'applicability_determination',
    'existing_controller_status', 'clarification_required',
    'citation_supported', 'abstention_necessary',
    'gap_analysis_and_recommended_behavior'
]

with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(audit_rows)

print(f'Wrote {len(audit_rows)} rows to {out_path}')

