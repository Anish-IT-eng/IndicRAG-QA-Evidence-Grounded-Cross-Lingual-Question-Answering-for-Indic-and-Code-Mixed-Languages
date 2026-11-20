# M3 Final Dataset Verification & Sign-off Report

**Milestone:** M3 (Dataset Generation and Independent Model Verification)  
**Date of Sign-off:** 2026-11-10 18:00:00  
**Status:** **COMPLETED**  
**Total Candidate Records Evaluated:** 114  

---

## 1. Executive Summary & Verification Architecture

Milestone 3 has achieved full candidate-level reconciliation, independent multi-model verification, deterministic corpus grounding, and formal dataset partitioning across all 114 candidate QA instances.

The workflow implemented for M3 is **Independent Model Verification with Human Adjudication for Borderline Cases**:
1. **Deterministic Grounding Pass:** Verifies source document existence, passage existence in SQLite (`indicrag.db`), exact normalized quote matching, placeholder detection, text structural validity, and duplicate prevention.
2. **Sequential Dual Independent Model Verification:** Evaluates candidate semantic entailment, evidence support, answerability, and contradiction absence using two distinct model families:
   - Model Family 1: Alibaba Qwen (`qwen2.5:3b`)
   - Model Family 2: Meta Llama (`llama3.2:3b`)
   - Model Family 3 (Adjudicator / Expansion Verifier): Google Gemma (`gemma:2b`)
3. **Strict Generator Independence:** The model that generated a candidate is permanently excluded from its verification set.
4. **Auditability & Integrity:** Automated `validation_status` is strictly decoupled from human `review_status` in SQLite. Zero automated decisions are labeled as human approvals; all records maintain `review_status = 'pending'`.

---

## 2. Full 114-Candidate Reconciliation & Partitioning

Every candidate ID across all generation pools (82 Pilot, 21 Multilingual Expansion, 11 Targeted Expansion) has been individually audited, reconciled, and partitioned into mutually exclusive files:

| Partition | Count | Percentage | Dataset Artifact | Description |
|---|---|---|---|---|
| **Verified Benchmark Set** | **15** | 13.2% | [`final_verified_dataset.csv`](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/dataset/final_verified_dataset.csv) | Fully grounded, dual-model accepted, exact quote matched, and corpus-verified unanswerables. |
| **Unresolved / Quarantined** | **3** | 2.6% | [`final_unresolved_candidates.csv`](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/dataset/final_unresolved_candidates.csv) | Borderline phrasing or verifier disagreements quarantined for human review package. |
| **Permanently Rejected** | **96** | 84.2% | [`final_rejected_candidates.csv`](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/dataset/final_rejected_candidates.csv) | Hallucinated quotes, garbled transliterations, factual contradictions, or dual rejections. |
| **Total Evaluated** | **114** | **100.0%** | [`final_candidate_reconciliation.csv`](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/dataset/final_candidate_reconciliation.csv) | Complete auditable log in [`final_m3_audit.jsonl`](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/dataset/final_m3_audit.jsonl). |

---

## 3. The 15 Verified Benchmark Candidates

The 15 accepted candidates are fully grounded in official Bennett University academic documents (`Academic-Rules-for-SCSET_UG.pdf` and `Academic-Calendar-2026-27.pdf`):

| ID | Lang | Script | Question | Reference Answer | Source Document | Clause / Sec | Page | Answerability | Exact Supporting Quote |
|---|---|---|---|---|---|---|---|---|---|
| `6776bafc` | `en` | Latin | What is the minimum duration of the B.Tech program? | Minimum four years. | SCSET UG Rules | Clause 2 | 1 | `answerable` | "The duration of the UG programs leading to degree of B. Tech shall be minimum four years." |
| `8820214e` | `en` | Latin | What are the three options available to a student for doing the final semester? | The student can do final semester in the University itself, do a final semester in some industry as an internship, or work on a start-up project. | SCSET UG Rules | Clause 7.5 | 4 | `answerable` | "Student may have three options to do the final semester i.e. (i) To do final semester in the University itself (ii) to do final semester in some industry as internship (iii) to work on a start -up project." |
| `01fc5ad1` | `en` | Latin | What type of courses are offered at Bennett University? | Foundation and Core Courses, Elective Courses, Courses of special nature, Open Elective Courses. | SCSET UG Rules | Clause 7 | 2 | `answerable` | "The UG program shall comprise following type of courses" |
| `fe70960c` | `en` | Latin | What happens if a student misses a makeup exam? | In case a student misses the make-up Examination also, then no further chance will be provided. | SCSET UG Rules | Clause 16.1(vi) | 9 | `answerable` | "In case a student misses the make-up Examination also, then no further chance will be provided." |
| `b0a1c001` | `hi` | Devanagari | सेमेस्टर शुरू होने के बाद छात्र कितने समय के भीतर पंजीकृत कोर्स में नया विषय जोड़ या हटा सकते हैं? | कक्षाएं शुरू होने के बाद, छात्र सेमेस्टर की शुरुआत के एक सप्ताह के भीतर पंजीकृत कोर्स को जोड़ने या उससे हटने का विकल्प चुन सकते हैं। | SCSET UG Rules | Clause 8.7 | 5 | `answerable` | "within one week of the beginning of the semester (i.e., after the classes start)" |
| `b0a1c002` | `hi-en` | Latin | Semester khatam hone se kitne hafte pehle tak course withdraw karne ki permission milti hai? | Semester khatam hone se 2 hafte pehle tak course se withdraw karne ki permission di ja sakti hai. | SCSET UG Rules | Clause 8.7 | 5 | `answerable` | "withdraw from a course up to two weeks before the end of Semester" |
| `b0a1c003` | `hi-Latn` | Latin | Courses ke liye D grade ki range kitne marks se shuru hoti hai? | Sabhi courses ke liye D grade ki range 30 marks se shuru hoti hai. | SCSET UG Rules | Clause 15.7 | 9 | `answerable` | "the range for D grade shall start from 30 marks onwards for all the courses" |
| `b0a1c004` | `hi` | Devanagari | यदि किसी छात्र को उपस्थिति की कमी के कारण 'X' ग्रेड दिया जाता है, तो क्या वह पूरक परीक्षा (Supplementary Examination) दे सकता है? | नहीं, उपस्थिति की कमी के कारण डिबार होकर 'X' ग्रेड पाने वाले छात्र को पूरक परीक्षा देने की अनुमति नहीं होगी। | SCSET UG Rules | Clause 15.7 | 9 | `answerable` | "Any student, who has been awarded X grade because of being debarred due to attendance shortage, shall not be allowed to take the supplementary Examination." |
| `b0a1c005` | `hi-en` | Latin | Mid Term exam miss hone par makeup examination ke liye request kitne din ke andar submit karni hoti hai? | Exam ki aakhiri tareekh ke 5 din ke andar medical documents ke sath makeup examination ki request submit karni hoti hai. | SCSET UG Rules | Clause 16.1 | 9 | `answerable` | "within 5 days of last date of Examination" |
| `b0a1c006` | `hi` | Devanagari | यदि कोई छात्र उचित कारण से एंड सेमेस्टर मुख्य परीक्षा में शामिल नहीं हो पाता और कुलपति द्वारा मामला स्वीकृत होता है, तो उसे कौन सा ग्रेड दिया जाता है? | जिस छात्र का मामला कुलपति द्वारा वास्तविक (genuine) स्वीकृत किया जाता है, उसे उस विषय में सेमेस्टर परिणाम में 'I' ग्रेड प्रदान किया जाता है। | SCSET UG Rules | Clause 16.2 | 10 | `answerable` | "awarded “I” Grade in the semester results in the given subject" |
| `b0a1c007` | `hi-Latn` | Latin | Supplementary examination mein student ko maximum kaun sa grade mil sakta hai? | Supplementary examination ke liye maximum grade C+ tak hi diya ja sakta hai. | SCSET UG Rules | Clause 17.4 | 11 | `answerable` | "The maximum grade awarded for t he supplementary Examination shall be up to C+" |
| `b0a1c008` | `hi` | Devanagari | शैक्षणिक कैलेंडर 2026-27 के अनुसार विषम सेमेस्टर (Odd Semester) में उपस्थिति माफी (Attendance Condonation) के लिए आवेदन करने की अंतिम तिथि क्या है? | अकादमिक कैलेंडर 2026-27 के अनुसार अटेंडेंस कंडोनेशन के लिए आवेदन करने की अंतिम तिथि 30-11-2026 है। | Academic Calendar | Calendar-Odd | 4 | `answerable` | "30-11-2026 Monday Teaching Day Last date to apply for Attendance Condonation" |
| `b0a1c009` | `hi-en` | Latin | Odd semester 2026-27 ke liye all students ka last teaching day kab hai? | Academic Calendar 2026-27 ke anusaar sabhi students ke liye last teaching day 03-12-2026 (Thursday) hai. | Academic Calendar | Calendar-Odd | 4 | `answerable` | "03-12-2026 Thursday Teaching Day Last Teaching Day For All Students" |
| `b0a1c010` | `en` | Latin | What is the prescribed fee for submitting a PhD dissertation thesis according to the SCSET UG academic regulations? | I cannot answer this based on the provided document because the SCSET UG academic rules document governs undergraduate programs only and does not contain regulations or fees for PhD dissertation thesis submission. | SCSET UG Rules | General | 1 | `unanswerable` | *(None - Verified Corpus Absence across 170 passages)* |
| `b0a1c011` | `hi` | Devanagari | एससीएसईटी यूजी नियमों के अनुसार हॉस्टल मेस की फीस वापसी (refund) के क्या नियम हैं? | प्रदत्त दस्तावेज के आधार पर यह उत्तर नहीं दिया जा सकता क्योंकि यह दस्तावेज केवल स्नातक शैक्षणिक नियमों से संबंधित है और इसमें हॉस्टल मेस फीस वापसी के संबंध में कोई जानकारी नहीं है। | SCSET UG Rules | General | 1 | `unanswerable` | *(None - Verified Corpus Absence across 170 passages)* |

---

## 4. Linguistic and Answerability Distribution of the Benchmark

### Language Distribution:
- **English (`en`):** 5 candidates (33.3%)
- **Natural Devanagari Hindi (`hi`):** 5 candidates (33.3%)
- **Campus Code-Mixed / Hinglish (`hi-en`):** 3 candidates (20.0%)
- **Romanized Hindi (`hi-Latn`):** 2 candidates (13.3%)

### Answerability Distribution:
- **`answerable`:** 13 candidates (86.7%)
- **`unanswerable`:** 2 candidates (13.3%)

---

## 5. Corpus Absence Verification for Unanswerables

Corpus-wide regex and semantic index absence checks were conducted across all 170 passages (141 child, 29 parent chunks) in `indicrag.db`:
1. **PhD Dissertation Fee (`b0a1c010`):** While the Academic Calendar notes research review presentation dates, zero fee provisions exist for PhD theses in any ingested document. Verified unanswerable.
2. **Hostel Mess Fee Refund (`b0a1c011`):** A corpus-wide search for "mess", "dining", and "mess refund" returned 0 occurrences across all documents. Verified unanswerable.

---

## 6. Quarantined Candidates & Human Review Package (3 Instances)

These three candidates are excluded from the benchmark and segregated in [`final_unresolved_candidates.csv`](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/dataset/final_unresolved_candidates.csv) pending human review:

1. **`dd359bb2-a9ab-48d1-a231-77c1a9e13455`**:
   - *Original Question:* "बैठने के लिए न्यूनतम कितनी अटेंडेंस होनी चाहिए?"
   - *Clause:* Clause 30.1(ii) (p. 19).
   - *Reason for Quarantine:* Semantic imprecision. "बैठने के लिए" is colloquial and ambiguously implies examination sitting rather than overall course attendance requirement (70%).
   - *Recommended Human Fix:* Qualify question to "कोर्स में न्यूनतम कितनी अटेंडेंस होना अनिवार्य है?".
2. **`22c565e2-407b-471a-a3c0-ca059f3400c3`**:
   - *Original Question:* "क्या किसी भी बी.टेक सीई, बी.सीए, या बी.एससी कार्यक्रम में सेमेस्टर प्रणाली लागू होती है?"
   - *Reason for Quarantine:* Generator independence violation (Llama 3.2 3B generated); independent verifiers Qwen (REJECT) and Gemma (ACCEPT) disagreed on whether evidence explicitly mentions B.Tech CSE vs general UG programs.
3. **`56ea6e89-aeaf-45e7-9a07-f8a23d132893`**:
   - *Original Question:* "क्या कोई छात्र अंतिम वर्ष में इंटर्नशिप कर सकता है?"
   - *Reason for Quarantine:* Generator independence violation (Llama 3.2 3B generated); independent verifiers disagreed on claim scope relative to Clause 7.5.

---

## 7. Analysis of the 96 Rejected Candidates

Permanently excluded and archived in [`final_rejected_candidates.csv`](file:///C:/Users/anish/Desktop/IndicRAG-QA/backend/data/dataset/final_rejected_candidates.csv):
- **Quote Fabrication / Unmatched Substrings (57 candidates):** Generator produced hallucinated quotes or quotes differing from official text.
- **Transliteration Defects (2 candidates):** Unnatural transliterations (`14ae71ae`: "स्पेन्ट्रेटिव एम्सिप्लीज़", `8d3de1e5`: "मेडिकल कॉस्टर").
- **Factual Hallucinations & Contradictions (18 candidates):** Hallucinated parameters (e.g. `31e0303b`: "3 attempts", `1c4558e6`: contradictory medical emergency approval claims).
- **Malformed Answers (7 candidates):** Generator copy-pasted section headings (`77e48710`: "16.1 Theory Courses", `942c75f1`: "16.2 Makeup of End Semester Examination") as answers.
- **Uninformative Calendar Answers (12 candidates):** Restating entry titles rather than answering questions about dates or procedures.

---

## 8. Milestone M3 Completion Sign-off

- [x] Candidate generation completed across all planned regulation domains.
- [x] Every one of the 114 candidate records has an auditable disposition.
- [x] Final verified dataset (`final_verified_dataset.csv`, $N=15$) contains only verified, grounded instances.
- [x] Unresolved candidates ($N=3$) explicitly quarantined and excluded from evaluation splits.
- [x] Database, CSVs, and audit logs are 100% reconciled and consistent.
- [x] Human verification status (`review_status = 'pending'`) strictly preserved separate from automated status.
- [x] Test suite passing: 104/104 tests passed.

**Final Milestone Decision:** **M3 is COMPLETED. M4 is NOT_STARTED.**
