import re
import sys
sys.path.insert(0, 'backend')

from app.retrieval.relationship_store import RelationshipStore


def lookup_calendar_event_reconciled(
    feedback_query: str,
    prev_query: str = "",
    prev_answer: str = "",
    user_id: str = None
) -> dict:
    fb_lower = feedback_query.lower()
    prev_lower = prev_query.lower()
    combined = f"{fb_lower} {prev_lower}".strip()

    # Disambiguation flags
    is_asking_regular = any(k in fb_lower for k in ["regular", "end sem", "end term", "not make-up", "not makeup", "asked about regular"])
    is_makeup_datesheet = ("date sheet" in combined or "datesheet" in combined or "display" in combined) and ("make-up" in combined or "makeup" in combined)
    is_makeup_exam = ("make-up" in combined or "makeup" in combined) and not is_makeup_datesheet and not is_asking_regular
    is_midterm = "mid term" in combined or "mid sem" in combined
    is_period_query = any(k in fb_lower for k in ["period", "duration", "interval", "kahan se kahan tak", "actual examination period"])
    
    # Check for specific date pattern (e.g. 18-01-2027 or 18 january 2027)
    date_match = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", combined)
    specific_date = date_match.group(0) if date_match else None
    if not specific_date:
        nat_date_match = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{4})\b", combined)
        if nat_date_match:
            months = {'january': '01', 'jan': '01', 'february': '02', 'feb': '02', 'march': '03', 'mar': '03', 'april': '04', 'apr': '04', 'may': '05', 'june': '06', 'jun': '06', 'july': '07', 'jul': '07', 'august': '08', 'aug': '08', 'september': '09', 'sep': '09', 'october': '10', 'oct': '10', 'november': '11', 'nov': '11', 'december': '12', 'dec': '12'}
            d_num = int(nat_date_match.group(1))
            m_num = months.get(nat_date_match.group(2).lower(), '01')
            y_num = nat_date_match.group(3)
            specific_date = f"{d_num:02d}-{m_num}-{y_num}"

    # Determine search target
    reconciliation_type = "general"
    if is_asking_regular:
        search_term = "End Semester Examination"
        reconciliation_type = "regular_override"
    elif is_makeup_datesheet:
        search_term = "Display of Date Sheet of Odd Semester Make-up Examinations"
        reconciliation_type = "makeup_datesheet"
    elif is_makeup_exam:
        search_term = "Odd Semester Make-up Examinations"
        reconciliation_type = "makeup_exam"
    elif is_midterm:
        search_term = "Mid Term Examination"
        reconciliation_type = "midterm"
    elif specific_date:
        search_term = specific_date
        reconciliation_type = "specific_date"
    elif any(k in combined for k in ["end sem", "end term", "examination", "exam", "odd sem"]):
        search_term = "End Semester Examination"
        reconciliation_type = "regular_end_sem"
    else:
        # Ambiguous query without examination cues
        return {"is_ambiguous": True}

    events = RelationshipStore.get_event_details(search_term, user_id=user_id)
    if not events:
        events = RelationshipStore.get_event_details(search_term, user_id=None)

    if not events:
        return {"is_ambiguous": True}

    # Filter out announcements if looking for exams
    cand_events = events
    if not is_makeup_datesheet and reconciliation_type != "specific_date":
        filtered = [e for e in events if not e.get("event_name", "").lower().startswith("announcement")]
        if filtered:
            cand_events = filtered

    # Filter for Odd Semester if odd mentioned or implied
    if "odd" in combined or not any("even" in combined for _ in [1]):
        odd_cand = [e for e in cand_events if "odd" in e.get("event_name", "").lower() or e.get("page_number") in (3, 4, 5)]
        if odd_cand:
            cand_events = odd_cand

    selected = cand_events[0]
    selected["is_ambiguous"] = False
    selected["reconciliation_type"] = reconciliation_type
    selected["is_period_query"] = is_period_query
    return selected


# Test the scenarios
tests = [
    ("Scenario A", "When will odd semester end semester examinations start?", "", ""),
    ("Scenario B", "When will the odd semester make-up examination date sheet be displayed?", "", ""),
    ("Scenario C", "What is the actual examination period?", "When will odd semester end semester examinations start?", "Starts on 10-12-2026"),
    ("Scenario D", "Your answer is wrong.", "When will odd semester end semester examinations start?", "Starts on 18-01-2027"),
    ("Scenario E", "You gave the make-up examination date, but I asked about regular end semester examinations.", "When will odd semester examinations start?", "Make-up date sheet displayed on 18-01-2027"),
    ("Scenario F", "What happens on 18 January 2027?", "", ""),
]

print("================================================================================")
print("TESTING RECONCILED EVENT SELECTION ACROSS SCENARIOS A - F")
print("================================================================================")
for label, fb, prev_q, prev_ans in tests:
    res = lookup_calendar_event_reconciled(fb, prev_q, prev_ans)
    print(f"\n>>> {label}")
    print(f"  Input Question: '{fb}'")
    if prev_q:
        print(f"  Preceding Question: '{prev_q}' | Preceding Answer: '{prev_ans}'")
    print(f"  Selected Event: {res.get('event_name')}")
    print(f"  Page: {res.get('page_number')} | Row: {res.get('source_row_id')}")
    print(f"  Start Date: {res.get('start_date')} ({res.get('start_day')})")
    print(f"  End Date: {res.get('end_date')} ({res.get('end_day')})")
    print(f"  Date Range: {res.get('date_range')}")
    print(f"  Reconciliation Type: {res.get('reconciliation_type')}")
