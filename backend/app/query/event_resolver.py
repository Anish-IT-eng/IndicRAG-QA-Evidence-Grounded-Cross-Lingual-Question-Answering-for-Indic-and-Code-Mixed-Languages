"""
Multilingual Academic Event Resolver for IndicRAG-QA.

Canonicalizes institutional academic events across:
- English
- Devanagari Hindi
- Romanized Hindi
- Code-mixed Hinglish

Covers event categories:
- End Semester Examinations
- Make-up Examinations
- Mid-Term Examinations
- Supplementary / Re-appear Examinations
- Practical Examinations
- Registration Deadlines
- Holidays / Vacations

Distinguishes Odd Semester vs. Even Semester scopes and preserves query provenance.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.schemas import QueryAnalysis, QueryLanguage


@dataclass
class ResolvedEventIntent:
    event_category: Optional[str]        # e.g., "End Semester Examination", "Make-up Examination"
    semester: Optional[str]              # e.g., "Odd Semester", "Even Semester"
    temporal_aspect: Optional[str]        # e.g., "start", "end", "both", "schedule"
    canonical_english_query: str         # Standardized English query representation
    is_ambiguous: bool                   # True if exam/event is mentioned but type is unresolvable
    raw_event_token: Optional[str] = None


# Semester Patterns (Devanagari, Romanized Hindi, Hinglish, English)
_ODD_SEM_PATTERN = re.compile(
    r"(विषम\s*सेमेस्टर|विषम|\bodd\s+sem(?:ester)?\b|\bvisham\s+sem(?:ester)?\b)",
    re.IGNORECASE,
)
_EVEN_SEM_PATTERN = re.compile(
    r"(सम\s*सेमेस्टर|सम|\beven\s+sem(?:ester)?\b|\bsam\s+sem(?:ester)?\b)",
    re.IGNORECASE,
)

# Event Categories and Matchers
_EVENT_DEFINITIONS = [
    (
        "Make-up Examination",
        re.compile(
            r"(मेक[- ]?अप\s*परीक्षा(?:एं|एँ)?|मेकअप\s*परीक्षा(?:एं|एँ)?|\bmake[- ]?up\s+exam(?:ination)?s?\b|\bmakeup\s+exam(?:ination)?s?\b|\bback\s+paper\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "Mid-Term Examination",
        re.compile(
            r"(मिड[- ]?टर्म\s*परीक्षा(?:एं|एँ)?|मध्य\s*सत्रीय\s*परीक्षा(?:एं|एँ)?|\bmid[- ]?term\s+exam(?:ination)?s?\b|\bmid\s+sem(?:ester)?\s+exam(?:ination)?s?\b|\bmidterm\s+pariksha\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "End Semester Examination",
        re.compile(
            r"(अंतिम\s*परीक्षा(?:एं|एँ)?|सत्रांत\s*परीक्षा(?:एं|एँ)?|\bend\s+sem(?:ester)?\s+exam(?:ination)?s?\b|\bfinal\s+exam(?:ination)?s?\b|\bantim\s+pariksha\b|\bodd\s+sem(?:ester)?\s+exam(?:ination)?s?\b|\beven\s+sem(?:ester)?\s+exam(?:ination)?s?\b|\bvisham\s+sem(?:ester)?\s+pariksha\b|\bsam\s+sem(?:ester)?\s+pariksha\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "Supplementary Examination",
        re.compile(
            r"(पूरक\s*परीक्षा(?:एं|एँ)?|सप्लीमेंट्री\s*परीक्षा(?:एं|एँ)?|\bsupplementary\s+exam(?:ination)?s?\b|\bre[- ]?appear\s+exam(?:ination)?s?\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "Practical Examination",
        re.compile(
            r"(प्रैक्टिकल\s*परीक्षा(?:एं|एँ)?|प्रायोगिक\s*परीक्षा(?:एं|एँ)?|\bpractical\s+exam(?:ination)?s?\b|\blab\s+exam(?:ination)?s?\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "Registration",
        re.compile(
            r"(पंजीकरण|रजिस्ट्रेशन|नामांकन|\bregistration\b|\bonline\s+registration\b|\breg\s+date\b|\benrollment\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "Holiday / Vacation",
        re.compile(
            r"(छुट्टी|अवकाश|छुट्टियां|दीवाली|होली|ग्रीष्मावकाश|शीतावकाश|\bholiday\b|\bvacation\b|\bbreak\b|\brecess\b)",
            re.IGNORECASE,
        ),
    ),
]

# Temporal Action Matchers (supports English, Hindi, Romanized Hindi)
_START_PATTERNS = re.compile(
    r"(शुरू|आरंभ|प्रारंभ|कब\s*से|\bstart\b|\bbegin\b|\bcommence\b|\bfrom\b|\bshuru\b|\baarambh\b)",
    re.IGNORECASE,
)
_END_PATTERNS = re.compile(
    r"(समाप्त|खत्म|अंत|कब\s*तक|\bend\b|\bfinish\b|\bconclude\b|\bto\b|\bsamapt\b|\bkhatam\b|\bant\b)",
    re.IGNORECASE,
)
_WHEN_PATTERNS = re.compile(
    r"(कब|किस\s*तारीख|तारीख|दिनांक|तिथि|शेड्यूल|\bwhen\b|\bwhat\s+date\b|\bdates?\b|\bschedule\b|\bkab\b|\btarikh\b)",
    re.IGNORECASE,
)

# Generic Unspecified Exam Matcher (for Ambiguity Detection)
_GENERIC_EXAM_PATTERN = re.compile(
    r"(परीक्षा(?:एं|एँ)?|एग्जाम|\bexam(?:ination)?s?\b|\bpariksha\b)",
    re.IGNORECASE,
)


def resolve_academic_event_intent(query_text: str) -> ResolvedEventIntent:
    """
    Parses a multilingual query (English, Hindi, Romanized Hindi, Hinglish)
    and resolves the specific institutional event, semester scope, and temporal action.
    """
    text = query_text.strip()

    # 1. Resolve Semester Scope
    semester: Optional[str] = None
    if _ODD_SEM_PATTERN.search(text):
        semester = "Odd Semester"
    elif _EVEN_SEM_PATTERN.search(text):
        semester = "Even Semester"

    # 2. Resolve Event Category
    event_category: Optional[str] = None
    raw_matched_token: Optional[str] = None

    for cat_name, pattern in _EVENT_DEFINITIONS:
        m = pattern.search(text)
        if m:
            event_category = cat_name
            raw_matched_token = m.group(0)
            break

    # 3. Detect Ambiguity
    is_ambiguous = False
    if not event_category:
        # Check if user asked about exams generally without specifying the event type
        if _GENERIC_EXAM_PATTERN.search(text):
            is_ambiguous = True

    # 4. Resolve Temporal Aspect
    has_start = bool(_START_PATTERNS.search(text))
    has_end = bool(_END_PATTERNS.search(text))
    has_when = bool(_WHEN_PATTERNS.search(text))

    if has_start and has_end:
        temporal_aspect = "both"
    elif has_start:
        temporal_aspect = "start"
    elif has_end:
        temporal_aspect = "end"
    elif has_when:
        temporal_aspect = "schedule"
    else:
        temporal_aspect = "schedule"

    # 5. Formulate Canonical English Query
    if semester and event_category:
        event_phrase = f"{event_category}s for {semester}" if not event_category.endswith("s") else f"{event_category} for {semester}"
    elif semester:
        event_phrase = f"Examinations for {semester}"
    elif event_category:
        event_phrase = f"{event_category}s" if not event_category.endswith("s") else event_category
    elif is_ambiguous:
        event_phrase = "Examinations"
    else:
        event_phrase = "Academic Events"

    if temporal_aspect == "both":
        canonical = f"When do {event_phrase} start and finish?"
    elif temporal_aspect == "start":
        canonical = f"When do {event_phrase} start?"
    elif temporal_aspect == "end":
        canonical = f"When do {event_phrase} end?"
    else:
        canonical = f"What is the schedule for {event_phrase}?"

    return ResolvedEventIntent(
        event_category=event_category,
        semester=semester,
        temporal_aspect=temporal_aspect,
        canonical_english_query=canonical,
        is_ambiguous=is_ambiguous,
        raw_event_token=raw_matched_token,
    )


def is_multilingual_calendar_query(text: str) -> bool:
    """
    Returns True if the query relates to the academic calendar, schedules, or dates,
    supporting English, Hindi, and code-mixed expressions.
    """
    resolved = resolve_academic_event_intent(text)
    if resolved.event_category or resolved.is_ambiguous:
        return True

    text_lower = text.lower()
    keywords = [
        "calendar", "schedule", "when", "date", "holiday", "registration",
        "कैलेंडर", "शेड्यूल", "कब", "तारीख", "दिनांक", "तिथि", "अवकाश", "पंजीकरण",
        "pariksha", "tarikh", "chhutti",
    ]
    return any(k in text_lower for k in keywords)
