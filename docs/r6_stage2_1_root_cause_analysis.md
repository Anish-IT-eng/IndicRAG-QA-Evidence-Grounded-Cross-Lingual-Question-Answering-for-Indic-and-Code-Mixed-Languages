# IndicRAG-QA — R6 Stage 2.1: Multilingual Event Alignment Root Cause Analysis

**Inspection Date:** 2026-11-19  
**Target Query:** `विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?`  
**Expected Outcome:**
- **Target Event:** End Semester Examination for All Students (Odd Semester 2026-27)
- **Start Date:** `10-12-2026` (Thursday)
- **Conclusion Date:** `22-12-2026` (Tuesday)
- **Provenance:** `Academic-Calendar-2026-27.pdf`, Page 4
**Observed Erroneous Outcome:**
- **Selected Event:** Registration for Even Semester Make-up Examination-Start Date (`01-07-2026`)
- **Provenance:** `Academic-Calendar-2026-27.pdf`, Page 1

---

## 1. Complete Query-Analysis Output Inspection

Live execution of `process_query("विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?")` via `app.query.processor`:

```json
{
  "original_query": "विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?",
  "detected_language": "hi",
  "detected_script": "Devanagari",
  "normalized_query": null,
  "romanized_query": null,
  "translated_query": null,
  "query_type": "direct",
  "is_multi_part": false,
  "sub_questions": [],
  "intent_keywords": [
    "\u0937\u092e",
    "\u091f\u0930",
    "\u092a\u0930",
    "\u0915\u092c",
    "\u0914\u0930",
    "\u0938\u092e"
  ],
  "complexity_score": 0.0,
  "temporal_intent_mode": "UNANCHORED",
  "target_cohort": null,
  "target_academic_year": null,
  "target_programme": null,
  "target_conditions": [],
  "feedback_subtype": null,
  "challenged_claim": null
}
```

### Analysis of Query-Analysis Output:
1. `detected_language: "hi"` and `detected_script: "Devanagari"` were accurately identified.
2. `normalized_query: null`: No cross-lingual canonicalization was performed. Key institutional concepts were not mapped to English regulatory equivalents:
   - `विषम सेमेस्टर` (Odd Semester) $\rightarrow$ unmapped.
   - `अंतिम परीक्षाएं` (End Semester Examinations) $\rightarrow$ unmapped.
   - `शुरू` (Start) / `समाप्त` (End/Finish) $\rightarrow$ unmapped.
   - `कब` (When) $\rightarrow$ unmapped.
3. `intent_keywords`: The keyword tokenizer fragmented Devanagari characters into partial character n-grams instead of semantic event keywords.

---

## 2. Event-Target Extraction Inspection

In `backend/app/generation/generator.py` (lines 398–420):
```python
event_match = re.search(
    r"(end\s+semester\s+exam(?:ination)?s?|mid[- ]term\s+exam(?:ination)?s?|make[- ]up\s+exam(?:ination)?s?|re[- ]appear\s+exam(?:ination)?s?|practical\s+exam(?:ination)?s?)",
    query_analysis.original_query,
    re.IGNORECASE,
)
```
- **Result for Hindi Query:** `event_match = None`.
- **Consequence:** The generator failed to identify the requested event as an `End Semester Examination` for an `Odd Semester`.
- Instead of injecting event-targeted instructions (which was done for English and Hinglish), the prompt builder fell back to generic instructions:
  `"Answer the question using the evidence passages above. Cite every factual claim with [Source: passage_id, page X] referring to the passages above. If the answer cannot be determined from the evidence, output UNANSWERABLE."`

---

## 3. Multi-Hop Reasoner Calendar Detection & Step 3b Bypass

The investigation revealed a second critical defect in `backend/app/retrieval/multi_hop_reasoner.py`:

```python
# multi_hop_reasoner.py line 152
is_calendar_query = any(w in q_lower for w in ["calendar", "schedule", "when"]) or (
    "date" in q_lower and ("exam" in q_lower or "semester" in q_lower)
)
```

1. **English Query:** `"When do odd semester end semester examinations start and finish?"`
   - Matches `"when"`. `is_calendar_query = True`.
2. **Hinglish Query:** `"Odd semester examinations ki start date aur end date kya hai?"`
   - Matches `"date"` + `"exam"` + `"semester"`. `is_calendar_query = True`.
3. **Devanagari Hindi Query:** `"विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?"`
   - Does NOT match English ASCII words `"calendar"`, `"schedule"`, `"when"`, `"date"`.
   - **`is_calendar_query = False`**.

### The Downstream Impact of `is_calendar_query = False`:
In Step 3b of `multi_hop_reasoner.py` (lines 359–415):
```python
if is_calendar_query:
  cal_events = RelationshipStore.get_event_details(
      "End Semester Examination", user_id=user_id
  )
  ...
  # Inserts authoritative Page 4 calendar schedule passage at index 0:
  all_passages.insert(0, rp_cal)  # cal_full_sched_0c174816 (Page 4)
```
Because `is_calendar_query` was `False`, **Step 3b was completely bypassed for the Hindi query**.
The dedicated Page 4 authoritative schedule passage (`cal_full_sched_0c174816`, Page 4: `10-12-2026` to `22-12-2026`) was **never injected into the Hindi evidence set**.

---

## 4. Evidence Passage Ordering and Composition

The Hindi query's retrieved 12 passages consisted of:
- `[1]` `ID=93982f8b...` | Page 1 | Deeksharambh
- `[2]` `ID=f018e449...` | Page 1 | Deeksharambh
- `[3]` `ID=dab03ad7...` | Page 11 | Supplementary Examination (Ordinance)
- `[4]` `ID=1026f70a...` | Page 2 | Deeksharambh
- `[5]` `ID=87a0156f...` | Page 35 | Conduct of Examinations (Ordinance)
- `[6]` `ID=ddcfcc9d...` | Page 11 | Grading System (SCSET UG Rules)
- `[7]` `ID=ff74febc...` | Page 1 | Massive 50 KB aggregated calendar table passage containing events from Page 1 to Page 8, prefixed with `Registration for Even Semester Make-up Examination-Start Date. Start Date: 01-07-2026...`
- `[8]` `ID=mhop_syn_rel_e5246064a51c` | Page 1 | Synthetic relationship passage: `[EVENT_HAS_DATE | Page 1 | Scope: exam_eligibility] Registration for Even Semester Make-up Examination-Start Date -> 01-07-2026`
- `[9]` `ID=mhop_syn_rel_1261bd475a14` | Page 1 | Returning PhD Students Registration (06-07-2026)
- `[10]` `ID=mhop_syn_rel_e96cdb109e41` | Page 1 | Reporting of PG Freshman Students (08-07-2026)
- `[11]` `ID=mhop_syn_rel_24a30eddfb94` | Page 1 | Make-up Examination End Date (09-07-2026)
- `[12]` `ID=mhop_syn_rel_df93719c4cc1` | Page 1 | Display of Date Sheet of Even Semester Make-up Examination (10-07-2026)

**Observation:**
No standalone Page 4 passage existed in the top 12 passages. The only mention of `10-12-2026` was buried deep at character offset ~22,000 inside Passage `[7]` (which was attributed to `Page 1` because of the table chunker).

---

## 5. Is the Correct Page 4 Event Explicitly Represented in Prompt?

- In the English prompt: **YES**. Passage `[1]` was `cal_full_sched_0c174816` (Page 4: "End Semester Examination for All Students (Odd Semester 2026-27) starts on 10-12-2026 and concludes on 22-12-2026").
- In the Hindi prompt: **NO**. The Page 4 schedule passage was absent due to the Step 3b bypass. The only representation was an unindexed date row in the middle of a 50 KB Page 1 text block, while 6 out of 12 passages were explicitly headed with Page 1 Even Semester Make-up Examination events.

---

## 6. Query Passed to Generator: Original vs Normalized

In `backend/app/generation/generator.py`:
```python
question_text = (
    query_analysis.normalized_query or query_analysis.original_query
)
user_prompt = f"{lang_instruction}\n\nQuestion: {question_text}\n\nEvidence passages:\n{evidence_text}\n\nInstructions: {instructions}"
```
Since `qa.normalized_query` was `None`, the generator received:
`Question: विषम सेमेस्टर की अंतिम परीक्षाएं कब शुरू और समाप्त होती हैं?`
The language instruction was:
`कृपया उत्तर हिंदी में दें।`
Because `qwen2.5:3b` has lower native Devanagari representation than English, and the evidence passages are written in English (`"Event Schedule: Registration for Even Semester Make-up Examination..."`), the model could not bridge the semantic gap between `"विषम सेमेस्टर"` and the English calendar records without explicit prompt guidance or query normalization.

---

## 7. Citation-Selection Logic Responsible for Citing Page 1

In `backend/app/generation/generator.py`:
- The model generated: `Registration for Even Semester Make-up Examination-Start Date is on 01-07-2026.` and cited `[Source: passage_id=mhop_syn_rel_e5246064a51c, page 1]`.
- `_extract_citations()` matched the passage ID `mhop_syn_rel_e5246064a51c` in `valid_passages`.
- That passage genuinely has `page_number = 1` and heading `"Registration for Even Semester Make-up Examination-Start Date"`.
- The citation parser operated strictly correctly: the model cited what it chose, but it chose the wrong passage because the wrong passages were prioritized and event intent was never resolved.

---

## 8. Summary of Identified Defects Across the Chain

| Component | Defect Description | Impact |
| :--- | :--- | :--- |
| **`app.query.processor`** | Lack of multilingual canonicalization / event concept mapping in `normalized_query`. Fragmented Devanagari keyword tokenization. | Query leaves analysis stage without semantic event intent tags or English concept anchors. |
| **`app.retrieval.multi_hop_reasoner`** | `is_calendar_query` regex/wordlist is English-only (`["calendar", "schedule", "when", "date"]`). | Step 3b calendar schedule linker is bypassed for Devanagari queries, omitting Page 4 authoritative evidence. |
| **`app.generation.generator`** | `event_match` regex is English-only (`r"(end\s+semester\s+exam...)"`). | Prompt instruction falls back to generic prompt without specifying target event or semester. |
