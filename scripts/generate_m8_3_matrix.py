import csv

matrix = [
    {
        'doc_a': 'Notification-Minimum-Attendance.pdf',
        'doc_b': 'Academic-Rules-for-SCSET_UG.pdf',
        'subject_area': 'Minimum Attendance Requirement',
        'doc_a_clause': 'Page 1 (Ref BU/RO/Notification/307/2022)',
        'doc_b_clause': 'Clause 30.1(ii), Page 19',
        'doc_a_condition': 'Eligibility to appear in End Semester Examination (75%)',
        'doc_b_condition': 'Course-level attendance profile & X-grade debarment (70%)',
        'relationship_type': 'DIFFERENT_REGULATORY_CONDITIONS',
        'evidence_rationale': 'Notification 307/2022 governs Controller of Examination admit card / exam hall eligibility under UGC 2003 regulations. SCSET Rule 30.1 governs course instructor semester grade debarment. Different regulatory stages and enforcement authorities.',
        'controller_gap_identified': 'Current controller treats them as a flat numerical contradiction rather than distinguishing exam hall eligibility from course grade debarment.'
    },
    {
        'doc_a': 'Academic-Rules-for-SCSET_UG.pdf',
        'doc_b': 'SEAS-Ordinance-Rules-Regulations-2017.pdf',
        'subject_area': 'Undergraduate Engineering Program Academic Regulations',
        'doc_a_clause': 'Full Document (AY 2022-23)',
        'doc_b_clause': 'Full Document (AY 2017-18)',
        'doc_a_condition': 'Academic promotion, grading, attendance for SCSET cohorts (2022 onwards)',
        'doc_b_condition': 'Academic promotion, grading, attendance for founding SEAS cohorts (2017-2021)',
        'relationship_type': 'HISTORICAL_RULE',
        'evidence_rationale': 'SEAS 2017 is a historical founding ordinance applicable to 2017-2021 batches. SCSET 2022 rules govern students enrolled under the restructured School of Computer Science Engineering & Technology.',
        'controller_gap_identified': 'When queries explicitly request historical rules (e.g. "in 2017"), controller fails to anchor to SEAS 2017 and instead flags CONFLICTING because SEAS is marked is_current=False.'
    },
    {
        'doc_a': 'Students-Discipline-Conduct-Rules-2024.pdf',
        'doc_b': 'UFM-Guidelines-2024.pdf',
        'subject_area': 'Student Disciplinary Framework',
        'doc_a_clause': 'Clause 4 (Acts of Indiscipline) & Clause 7 (Proctorial Procedures)',
        'doc_b_clause': 'Clause 2.1 - 2.6 (Categories of UFM Penalties)',
        'doc_a_condition': 'General non-academic student conduct, campus behavior, hostel discipline, anti-ragging',
        'doc_b_condition': 'Misconduct, unauthorized materials, and malpractice specifically within Examination Halls',
        'relationship_type': 'DIFFERENT_REGULATORY_CONDITIONS',
        'evidence_rationale': 'Distinct subject matters. UFM is an examination department code enforced by the Examination Disciplinary Committee. Conduct Rules are enforced by the Proctorial Board across campus.',
        'controller_gap_identified': 'None currently, provided retrieval routes query keywords appropriately.'
    },
    {
        'doc_a': 'BU-First-Ordinance-2016.pdf',
        'doc_b': 'Academic-Rules-for-SCSET_UG.pdf',
        'subject_area': 'Degree Conferment & Academic Structure',
        'doc_a_clause': 'Clauses 29-33 (Statutory Ordinances)',
        'doc_b_clause': 'Clauses 1-26 (SCSET Academic Rules)',
        'doc_a_condition': 'Statutory authority, maximum degree duration, university-wide governance',
        'doc_b_condition': 'Granular curriculum, course registration, semester credit limits, branch change criteria',
        'relationship_type': 'PROGRAMME_SPECIFIC_RULE',
        'evidence_rationale': 'First Ordinance is the primary statutory baseline enacted under UP Act No. 24 of 2016. SCSET rules are secondary operational rules formulated by the School Academic Committee subordinate to First Ordinance.',
        'controller_gap_identified': 'Controller lacks hierarchical authority modeling (statutory vs delegated operational rule).'
    },
    {
        'doc_a': 'BU-First-Ordinance-2016.pdf',
        'doc_b': 'Students-Discipline-Conduct-Rules-2024.pdf',
        'subject_area': 'Disciplinary Authority and Penalties',
        'doc_a_clause': 'Clause 31 (Maintenance of Discipline)',
        'doc_b_clause': 'Full Document (2024 Rules)',
        'doc_a_condition': 'Vests supreme disciplinary authority in the Vice Chancellor under UP Act 2016',
        'doc_b_condition': 'Operationalizes proctorial board procedures, committee hearings, and penalty guidelines',
        'relationship_type': 'DIFFERENT_REGULATORY_CONDITIONS',
        'evidence_rationale': 'First Ordinance delegates the power to frame detailed conduct rules to the Vice Chancellor/Executive Council. 2024 Conduct Rules operationalize this delegated statutory authority.',
        'controller_gap_identified': 'None.'
    },
    {
        'doc_a': 'Notification-Minimum-Attendance.pdf',
        'doc_b': 'SEAS-Ordinance-Rules-Regulations-2017.pdf',
        'subject_area': 'Minimum Attendance Threshold',
        'doc_a_clause': 'Page 1 (2022 Notification)',
        'doc_b_clause': 'Clause 30.1(ii), Page 28 (2017 Ordinance)',
        'doc_a_condition': '75% attendance for end semester examination eligibility (AY 2022-23 onwards)',
        'doc_b_condition': '70% attendance for engineering undergraduates (AY 2017-18 to 2021-22)',
        'relationship_type': 'SAME_CONDITION_DIFFERENT_VERSION',
        'evidence_rationale': 'Chronological shift in exam eligibility standard across university cohorts (from 70% in 2017 to 75% in 2022 pursuant to UGC Regulations 2003).',
        'controller_gap_identified': 'Controller correctly identifies version difference, but hardcodes incorrect 80% condonation text in explanation string.'
    }
]

out_path = 'backend/data/experiments/m8/m8_3_regulatory_relationship_matrix.csv'
fieldnames = [
    'doc_a', 'doc_b', 'subject_area', 'doc_a_clause', 'doc_b_clause',
    'doc_a_condition', 'doc_b_condition', 'relationship_type',
    'evidence_rationale', 'controller_gap_identified'
]

with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(matrix)

print(f'Wrote {len(matrix)} rows to {out_path}')

